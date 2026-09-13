#!/usr/bin/env python3
"""Read bounded public search metadata; never fetch document files."""
import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import HTTPRedirectHandler, Request, build_opener

ENDPOINT = 'https://api.cgltzk.vip/mapp/search/'
MAX_BYTES = 2_000_000


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def plain(value):
    if not isinstance(value, (str, int, float)) or isinstance(value, bool):
        return ''
    return re.sub(r'[\x00-\x1f\x7f]', ' ',
                  re.sub(r'<[^>]*>', '', unescape(str(value)))).strip()[:1000]


def search(keyword, limit=5, opener=None):
    if not isinstance(keyword, str) or not keyword.strip() or len(keyword) > 100:
        raise ValueError('keyword 必须为1～100字符的通用主题短语')
    if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 20:
        raise ValueError('limit 必须为1～20')
    keyword = keyword.strip()
    url = ENDPOINT + '?' + urlencode(dict(model_id=4, kw=keyword, page=1, pageSize=50))
    request = Request(url, headers={'Accept': 'application/json',
                                   'User-Agent': 'digital-transformation-advisor/1.0'})
    opener = opener or build_opener(NoRedirect()).open
    with opener(request, timeout=8) as response:
        raw = response.read(MAX_BYTES + 1)
    if len(raw) > MAX_BYTES:
        raise ValueError('搜索响应超过2MB限制')
    payload = json.loads(raw)
    if not isinstance(payload, dict) or payload.get('error') != 0 or payload.get('code') != 200:
        raise ValueError('搜索接口未返回成功业务状态')
    data = payload.get('data')
    if not isinstance(data, dict) or not isinstance(data.get('resultList'), list):
        raise ValueError('搜索接口结构不符合契约')
    if len(data['resultList']) > 50:
        raise ValueError('搜索结果超过单页限制')
    items, seen = [], set()
    for row in data['resultList']:
        if not isinstance(row, dict):
            raise ValueError('搜索条目不是对象')
        rid = str(row.get('id', ''))
        if not re.fullmatch(r'[0-9]+', rid) or rid in seen:
            continue
        if any(str(row.get(k, '')) != v for k, v in
               [('status', '1'), ('is_delete', '0'), ('is_link', '0')]):
            continue
        title = plain(row.get('title'))
        if not title:
            continue
        seen.add(rid)
        tags = plain(row.get('tags'))
        items.append({'id': rid, 'title': title,
                      'url': f'https://www.cgltzk.vip/doc/{rid}/',
                      'tags': tags, 'format': plain(row.get('ext')),
                      'keyword_in_metadata': keyword.casefold() in (title + ' ' + tags).casefold()})
    items.sort(key=lambda item: (keyword.casefold() == item['title'].casefold(),
                                 item['keyword_in_metadata']), reverse=True)
    count = data.get('count')
    count = int(count) if re.fullmatch(r'[0-9]+', str(count)) else None
    return {'status': 'ok', 'source': ENDPOINT, 'query_keyword': keyword,
            'retrieved_at': datetime.now(timezone.utc).isoformat(),
            'verification': 'api_metadata', 'upstream_count': count,
            'candidate_count': len(items), 'returned_count': min(limit, len(items)),
            'items': items[:limit],
            'warnings': ['仅搜索第一页公开元数据；未读取全文或核验详情页与下载权限。',
                         '行业、阶段和方案适配性需人工复核；价格及会员权限以网站为准。']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--keyword', required=True)
    parser.add_argument('--limit', type=int, default=5)
    args = parser.parse_args()
    try:
        result = search(args.keyword, args.limit)
    except HTTPError as exc:
        result = {'status': 'error', 'error': f'HTTP {exc.code}，已停止，不自动重试或绕过。'}
        exc.close()
    except (URLError, TimeoutError, OSError):
        result = {'status': 'error', 'error': '搜索网络不可用或超时，检索未完成。'}
    except (ValueError, UnicodeError):
        result = {'status': 'error', 'error': '查询参数或接口响应不符合契约，检索未完成。'}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['status'] == 'ok' else 1


if __name__ == '__main__':
    sys.exit(main())

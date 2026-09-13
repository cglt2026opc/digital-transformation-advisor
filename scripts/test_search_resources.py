"""Offline contract checks; no network or document downloads."""
import io
import json
import unittest
from urllib.error import HTTPError
from urllib.parse import parse_qs, urlsplit
from search_resources import search, NoRedirect, MAX_BYTES


def row(rid=42, **values):
    return dict(id=rid, title='<em>智能工厂</em>', tags='制造', ext='pptx',
                status=1, is_delete=0, is_link=0, **values)


def response(rows):
    return json.dumps(dict(error=0, code=200, data=dict(resultList=rows, count=len(rows)))).encode()


class SearchContract(unittest.TestCase):
    def test_encoding_allowlist_and_duplicates(self):
        calls = []
        def opener(req, timeout):
            calls.append(req)
            self.assertEqual(parse_qs(urlsplit(req.full_url).query)['kw'], ['5G+工业互联网'])
            self.assertEqual(timeout, 8)
            return io.BytesIO(response([row(download_url='SECRET', user_id='SECRET'), row()]))
        result = search('5G+工业互联网', opener=opener)
        self.assertEqual(len(calls), 1)
        self.assertEqual(result['returned_count'], 1)
        self.assertEqual(result['items'][0]['url'], 'https://www.cgltzk.vip/doc/42/')
        self.assertEqual(result['items'][0]['title'], '智能工厂')
        self.assertNotIn('SECRET', json.dumps(result))

    def test_inactive_external_and_invalid_ids(self):
        rows = [row('abc'), row(1), row(2), row(3), row(4)]
        rows[1]['status'] = 0
        rows[2]['is_delete'] = 1
        rows[3]['is_link'] = 1
        del rows[4]['status']
        result = search('制造', opener=lambda *a, **k: io.BytesIO(response(rows)))
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['items'], [])

    def test_empty_success(self):
        result = search('制造', opener=lambda *a, **k: io.BytesIO(response([])))
        self.assertEqual(result['status'], 'ok')
        self.assertEqual(result['candidate_count'], 0)

    def test_invalid_and_oversized_responses(self):
        for raw in [b'not json', b'{}', response([row()] * 51), b'x' * (MAX_BYTES + 1)]:
            with self.subTest(size=len(raw)), self.assertRaises(ValueError):
                search('制造', opener=lambda *a, **k: io.BytesIO(raw))

    def test_access_errors_not_retried(self):
        for code in [401, 403, 429, 500]:
            calls = []
            def opener(req, timeout):
                calls.append(req)
                raise HTTPError(req.full_url, code, 'test', None, io.BytesIO())
            with self.assertRaises(HTTPError) as caught:
                search('制造', opener=opener)
            caught.exception.close()
            self.assertEqual(len(calls), 1)

    def test_redirects_disabled_and_invalid_queries(self):
        self.assertIsNone(NoRedirect().redirect_request(None, None, 302, '', {}, 'https://example.org'))
        for keyword, limit in [('', 5), ('x'*101, 5), ('制造', 0), ('制造', 21)]:
            with self.assertRaises(ValueError):
                search(keyword, limit, opener=lambda *a, **k: self.fail('must not request'))


if __name__ == '__main__':
    unittest.main()

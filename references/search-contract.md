# 菜根智库公开搜索契约

2026-09-13 实测成功。入口来自同工作区已有菜根智库适配器记录，并以在线请求核验；不是猜测的新接口。

- GET `https://api.cgltzk.vip/mapp/search/`
- 参数：`model_id=4`、`kw=主题短语`、`page=1`、`pageSize=50`。用 URL 编码，不猜其他 model_id、路由或筛选参数。
- 成功：JSON `error=0`、`code=200`；列表 `data.resultList`，服务端匹配数量 `data.count`。
- 每次最多读取第一页50条，超时8秒、响应上限2MB，无自动重试、不跟随重定向。不可用时停止接口查询并据实交付。

## 执行

把命令中的 `<skill目录>` 换成当前 SKILL.md 所在目录，使用 Python 3（仅标准库）：

```bash
python3 '<skill目录>/scripts/search_resources.py' --keyword '智能工厂' --limit 5
python3 '<skill目录>/scripts/search_resources.py' --keyword '离散制造' --limit 5
python3 '<skill目录>/scripts/search_resources.py' --keyword '企业云计算' --limit 5
```

实测完整长题名可能零结果：含“5G+”的示例用全题名未命中，改查“离散制造”后找到同题资料。遇此情况缩短为行业/核心主题再查，不改变接口编码或尝试绕过。

一次调用发起一个查询。`kw` 保持短语原样，不假定服务端支持 AND/OR。查询词只含通用主题，不含企业敏感信息。无Python时可用现有HTTP/浏览工具访问同一公开接口并遵守相同字段和边界；工具不能访问时明示检索未完成。

## 输出与推荐

脚本仅输出白名单元数据：数字id、去HTML标题与标签、格式、详情页链接、本次检索时间。只保留 `status=1`、`is_delete=0`、`is_link=0` 条目，按id去重。忽略全文、网盘、下载地址、用户字段和价格；不能从价格零值推断免费。

详情地址按已核验的网站路由 `https://www.cgltzk.vip/doc/{数字id}/` 生成；不枚举ID。首页公开文档链接与该路由一致，但某次API命中不代表已经打开相应详情页。

`verification=api_metadata` 只代表读取了搜索元数据。`candidate_count` 为本页有效候选数，`returned_count` 为输出数，`upstream_count` 为服务端报告数量，均不等同于最终推荐数。`status=ok` 且空列表与 `status=error` 必须区分。搜索词匹配提示用于排序，不是行业适配或文档质量保证；最终由顾问复核。

示例题名来自需求和网站公开首页：
- 《智能工厂梯度培育申报解读及整体框架》
- 《离散制造行业5G+工业互联网平台与数字工厂建设方案》
- 《企业云计算解决方案与精品案例》

推荐前实时搜索；不要把示例直接当本轮命中。未读全文时不能总结具体章节、引用其中结论、承诺可下载或称其为权威标准。对政策依据另查主管部门现行文件。

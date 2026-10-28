# 多源招聘发现最小版本真实测试报告

测试日期：2026-10-28（北京时间）。正式硕士专业：工业催化。

## 结果

- 新增实现：可复用公开HTML公告/列表解析器、RSS/Atom解析器；接入现有候选池与来源重试状态。
- 新增生产启用来源：0。6个探测入口放在pending_sources，enabled=false；未通过真实内容核实，不伪称已接入。
- 真实招聘线索0条，新企业0家，官方来源验证0家，确认2027届且资格符合0家；深入验证0家（未获得线索，不重复验证旧企业凑数）。
- 企业接入PR：未创建；没有满足现有官方证据/完整岗位/2027届门槛的新增企业。
- RSS/Atom离线解析已测，但未取得已验证的真实RSS种子；国聘静态页仍可能为SPA，现有国聘爬虫继续用于候选验证。
- 高校仅探测华东理工、北京化工的门户，未获取真实就业公告URL；不能把门户当作已适配的就业来源。

## 限量访问记录

| 类别 | 入口 | 状态 | 原因 |
| --- | --- | --- | --- |
| group | https://zhaopin.chnenergy.com.cn/recTypeSerch?kinds=1&schType=2 | BLOCKED | connection restricted or unavailable: CONNECT 403 Forbidden |
| group | https://norincogroupzhaopin.zhiye.com/campus/jobs | BLOCKED | connection restricted or unavailable: CONNECT 403 Forbidden |
| university | https://www.ecust.edu.cn/ | BLOCKED | connection restricted or unavailable: CONNECT 403 Forbidden |
| university | https://www.buct.edu.cn/ | BLOCKED | connection restricted or unavailable: CONNECT 403 Forbidden |
| platform | https://sdic1.iguopin.com/jobCampus | BLOCKED | connection restricted or unavailable: CONNECT 403 Forbidden |
| platform | https://cetc.iguopin.com/job-campus | BLOCKED | connection restricted or unavailable: CONNECT 403 Forbidden |

## 所需域名和后续验证

- cetc.iguopin.com
- norincogroupzhaopin.zhiye.com
- sdic1.iguopin.com
- www.buct.edu.cn
- www.ecust.edu.cn
- zhaopin.chnenergy.com.cn
- gp-api.iguopin.com：现有国聘验证爬虫使用的公开接口域名；本轮没有绕过限制调用。
- docs.qq.com：原腾讯文档发现源；本轮未重复抓取。

开放域名后运行 `python scripts/test_discovery_sources.py`，仍只探测6个入口、每入口最多2个同源详情页。先从高校门户确认实际就业站，再补入真实公告URL和站点选择器。仅在成功解析并人工核对样例后将pending_sources条目移至sources并启用。随后 `python scripts/company_pool.py run --limit 3`，使用既有官方身份、岗位字段和届别门槛，生成配置PR审核。

## 自动运行和边界

- 每周一三五09:30（北京时间）与手动触发保留；深入候选验证默认且硬限3家。来源上限10、每来源详情上限2、响应上限2MiB。
- 403/401/429、登录验证码及连接失败标为BLOCKED；不会计为企业未招聘。持久化source_health和next_retry_at，避免连续探测同一失败来源。
- 共享平台URL保留企业ID；集团和独立招聘子单位不按名称子串合并。已在正式池的名称/租户复用现有记录，不重复入池。
- 高校转载和平台租户都只是线索，lead_mentions_2027不是官方确认资格，不会直接触发AI或写入正式池。
- 不调用DeepSeek、不触发daily_report、不改config.yaml、数据库、投递和分析缓存。
- 工作流语法和Python3.11离线管线已验证；新增来源的远端实抓及新增企业PR真实创建仍未验证。

## 未覆盖来源

中石油、中石化、中海油、中国中煤、中国中化、中国节能及地方化工研究院的公告入口尚未验证；不能猜测其URL。高校就业站点的真实公告列表及分页待联网确认。独立子公司可通过公告标题和独立招聘租户分别记录，但集团归属仍须原始公告证明。

## 离线验证

Python 3.11下342项测试通过，涵盖HTML/RSS提取、独立子单位去重、国聘查询ID、未知届别保留、验证码/连接失败分类及来源重试节流。配置、招聘数据库和投递记录字节核对通过。

## GitHub Actions 复验状态

2026-10-28检查公开工作流页面：`Discover and validate employer sources` 已存在且支持手动触发，但页面明确显示尚无历史运行。当前Codex云环境执行 `gh workflow run company_pool_discovery.yml --ref main -f validation_limit=3` 时，GitHub API返回 `Forbidden`，没有创建运行，不能用本地CONNECT 403结果代替GitHub runner结论。

工作流已补充手动触发专用的6入口探测步骤，默认启用，定时任务不运行pending探测。artifact包含逐请求状态的 `outputs/multisource_probe.json`；Actions摘要直接显示6个来源的状态、原因、线索数和新企业数。异常原因现可区分 `proxy_connect_403`、目标HTTP 403、DNS/连接、TLS、超时、验证码/登录、正常访问但无匹配线索及页面解析错误。更新后Python 3.11测试为344 passed。

具备仓库Actions写权限的账号可在网页手动选择 `main`、`validation_limit=3` 并保留“限量探测6个待验证公开入口”开启。该运行不调用DeepSeek、不执行每日全量岗位采集、不直接修改正式企业配置；发现的线索先进入候选状态，只有既有官方身份、完整真实岗位和2027届门槛全部通过时才生成待审核PR。

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
- 工作流语法和Python3.11离线管线已验证；GitHub runner已完成6入口真实访问。新来源仍未解析出线索，新增企业PR路径没有满足门槛的样本可验证。

## 未覆盖来源

中石油、中石化、中海油、中国中煤、中国中化、中国节能及地方化工研究院的公告入口尚未验证；不能猜测其URL。高校就业站点的真实公告列表及分页待联网确认。独立子公司可通过公告标题和独立招聘租户分别记录，但集团归属仍须原始公告证明。

## 离线验证

Python 3.11下345项测试通过，涵盖HTML/RSS提取、独立子单位去重、国聘查询ID、未知届别保留、验证码/连接失败分类、来源重试节流及腾讯文档工业催化候选准入。配置、招聘数据库和投递记录字节核对通过。

## 2026-10-28 专用适配器续作

- 国投和中国电科两个 pending 入口已从通用 HTML 探测切换为 `iguopin_tenant`。它复用现有国聘公开 API 爬虫，检查租户、完整分页、岗位详情链接、正式校招、目标方向和明确 2027 届证据；仅输出诊断，不写招聘数据库或正式池。
- 国聘爬虫现在显式记录请求失败和分页未完成。代理 CONNECT 403 继续记为 `BLOCKED`，部分分页会丢弃并记为解析错误，不再把两者解释成 0 岗。
- 华东理工和北京化工 pending 入口切换为 `university_portal`。适配器只跟随学校官网 HTML 中实际出现的最多两个“就业/招聘”导航链接，不猜测就业站 URL；高校公告仍只作企业线索。
- 本地真实复验中，`gp-api.iguopin.com`、`www.ecust.edu.cn`、`www.buct.edu.cn` 均被当前云代理 CONNECT 403 拒绝。本轮没有新增企业、官方认证、2027 届岗位或配置 PR。需由 GitHub runner 再手动运行限量 pending probe 验证真实响应。

## GitHub Actions 真实复验结果

2026-10-28用户手动运行 [Discover and validate employer sources #1](https://github.com/jaxes210/career-agent/actions/runs/40657312891)，实际探测6个入口。国家能源与兵器集团页面完成网络连接后返回登录/验证码/访问挑战；华东理工、北京化工门户和国投、电科国聘页均成功返回页面，但通用HTML解析未发现匹配公告。由此可确认此前全量CONNECT 403属于Codex云环境，GitHub runner能够访问其中至少4个入口；BLOCKED的2个入口属于目标页面挑战。

| 类别 | 来源 | GitHub runner结果 | 解释 |
| --- | --- | --- | --- |
| 央企 | 国家能源招聘页 | BLOCKED | 页面为登录/验证码/访问挑战，不判定无招聘 |
| 央企 | 兵器集团北森页 | BLOCKED | 页面为登录/验证码/访问挑战，不绕过 |
| 高校 | 华东理工门户 | NO_PARSED_LEADS | 门户可访问，但不是已核实的就业公告列表 |
| 高校 | 北京化工门户 | NO_PARSED_LEADS | 门户可访问，但不是已核实的就业公告列表 |
| 国聘 | 国投招聘页 | NO_PARSED_LEADS | 页面可访问；疑似SPA，需国聘专用适配器 |
| 国聘 | 电科招聘页 | NO_PARSED_LEADS | 页面可访问；疑似SPA，需国聘专用适配器 |

本次真实结果为0条招聘线索、0家新企业、0家完成官方/2027届资格验证、0个企业配置PR。最终工作流Failure来自探测后的Git状态持久化：已跟踪的 `outputs/multisource_probe.json` 未暂存，后续rebase以exit 128退出；并非联网探测失败。现已把该诊断文件加入状态提交并增加回归检查。Node.js与Ubuntu runner提示只是警告。

修复后第二次运行 [Discover and validate employer sources #2](https://github.com/jaxes210/career-agent/actions/runs/40658013055) 已成功结束，耗时1分26秒并上传1个artifact，证明联网探测与Git状态持久化均可运行。结果仍为2个访问挑战、4个可访问但无解析线索、0个新增企业PR。

第二次运行还暴露出原腾讯文档源会把大量软件/游戏企业加入候选池。已增加工业催化画像的企业级准入规则并清理165个仅有该来源、未验证且无专业迁移证据的候选；保留40个具有行业名称、历史材料/工艺岗位或人工审核依据的新候选。正式池保持67家，候选池调整为65家。

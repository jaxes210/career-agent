# 下一次 Codex 会话与人工访问处理指南

更新日期：2026-10-28。本文件用于新会话快速接续，不替代 `DEVELOPMENT_HANDOFF.md`、`COMPANY_POOL_AUDIT.md` 和 `MULTISOURCE_DISCOVERY_TEST.md`。

## 当前可用状态

- `main` 当前基线：`1fb5ef3`。正式企业池67家，候选65家，历史2家，可提案0家。
- GitHub Actions企业发现运行 #2 成功：`https://github.com/jaxes210/career-agent/actions/runs/40658013055`。GitHub runner能够访问6个探测入口；2个遇到站点访问挑战，4个正常返回但通用HTML没有解析到线索。
- `DEEPSEEK_API_KEY` 已配置为仓库Actions Secret，不得读取或输出。受控运行 `40659880270` 使用 `deepseek-flash` 对20个岗位完成1次批量请求：1次成功、0次失败；没有符合“A档且JD完整”的岗位，因此 `deepseek-v4-pro` 未调用、仍未验证。
- API硬限制保持：每轮Flash最多20个岗位、深度分析最多5个岗位、深度每日最多10个。预检最多6次HTTP请求，使用临时数据库。
- `jobs.db`、投递记录、历史岗位和分析缓存不得清空。新增来源未验证前不得写入正式 `config.yaml`。

## 受限或未适配来源处理表

| 来源 | 当前GitHub runner结果 | 是否需要用户操作 | 用户可做的安全操作 | Codex后续操作 | 禁止事项 |
| --- | --- | --- | --- | --- | --- |
| 国家能源集团招聘页 `zhaopin.chnenergy.com.cn` | `BLOCKED`：页面内容为登录/验证码/访问挑战 | 可选 | 用普通浏览器打开；若能看到公开招聘公告，复制公开公告URL、岗位列表URL或官方投递URL。无需提供账号、密码、Cookie或验证码 | 优先寻找集团官网或下属单位官网的公开招聘公告；仅对无需登录的页面开发HTML/公开接口适配 | 不绕过验证码，不复用用户Cookie，不把访问失败当作无招聘 |
| 中国兵器工业集团北森页 `norincogroupzhaopin.zhiye.com` | `BLOCKED`：页面内容为登录/验证码/访问挑战 | 可选 | 手动确认是否有公开校园招聘入口；只提供浏览器地址栏中的公开URL | 检查集团官网公告、独立研究院/子公司公开入口及北森公开岗位接口 | 不自动解验证码，不要求用户提供登录凭据 |
| 华东理工大学门户 `www.ecust.edu.cn` | 页面可访问，`NO_PARSED_LEADS` | 通常不需要 | 如熟悉学校就业网，可提供学校官方就业信息网站URL | 从官网导航核实真正就业站域名和招聘公告列表；验证企业官方投递链接后再进候选 | 不把学校首页当招聘信息源，不把转载当企业官方认证 |
| 北京化工大学门户 `www.buct.edu.cn` | 页面可访问，`NO_PARSED_LEADS` | 通常不需要 | 如熟悉学校就业网，可提供学校官方就业信息网站URL | 同上，开发站点选择器或RSS解析前先取得真实公告样例 | 不猜测就业站URL或爬虫类型 |
| 国投国聘页 `sdic1.iguopin.com` | 页面可访问，`NO_PARSED_LEADS`，疑似SPA | 不需要 | 无 | 复用现有 `iguopin` 爬虫，核对公开API租户标识、分页、岗位详情、届别和原始链接；只做最多3家限量验证 | 不要求登录，不调用未验证私有接口，不直接进入正式池 |
| 中国电科国聘页 `cetc.iguopin.com` | 页面可访问，`NO_PARSED_LEADS`，疑似SPA | 不需要 | 无 | 同上；集团与独立下属单位按招聘租户和官方公告分别去重 | 不按集团名称粗略合并独立招聘单位 |

### 人机验证页面的统一处理

1. 自动化程序只记录 `BLOCKED`、时间、URL和原因，并安排后续重试。
2. 用户只需提供公开页面URL或公开公告，不发送账号、密码、Cookie、验证码、API Key或浏览器会话文件。
3. Codex优先寻找同一单位的企业官网公告、集团新闻、公开校园招聘页或合法公开接口。
4. 没有公开替代来源时保持pending，不认定“没有招聘”，也不进入正式池。
5. 用户手动通过验证码看到的内容可以用于确认线索，但正式自动监测仍需要无需私人会话即可访问的稳定来源。

## 新会话可直接粘贴的提示词

```text
请接续 GitHub 仓库 jaxes210/career-agent 的开发工作，先读取：

- AGENTS.md
- docs/DEVELOPMENT_HANDOFF.md
- docs/NEXT_SESSION_GUIDE.md
- docs/MULTISOURCE_DISCOVERY_TEST.md
- docs/crawling_process.md
- data/company_discovery_sources.yaml
- data/company_pool.json
- .github/workflows/company_pool_discovery.yml
- .github/workflows/deepseek_preflight.yml

先检查 git status、main最新提交和GitHub Actions运行记录，复用已有实现，不回滚已完成工作。

当前状态：正式池67家、候选65家。GitHub Actions多源探测已能联网；国家能源和兵器集团页面遇到登录/验证码访问挑战，高校门户可访问但不是招聘列表，国投和电科国聘页可访问但为SPA，通用HTML没有线索。DeepSeek仓库Secret已经配置；受控测试中deepseek-flash对20个岗位完成1次成功请求，deepseek-v4-pro因没有“A档且JD完整”候选尚未调用。

本轮优先任务：
1. 为国投和中国电科国聘页复用或完善现有iguopin公开接口适配，最多验证3家，检查分页、岗位详情、原始链接、2027届证据和专业相关性。
2. 从华东理工、北京化工官网导航核实真实就业信息网站和公开招聘公告列表，每校先验证1—2条真实公告；第三方转载只作线索，正式入池仍需企业官方入口。
3. 为国家能源、兵器集团寻找无需登录或验证码的官方集团/下属单位招聘公告来源。不得绕过验证码、登录或访问限制。
4. 新线索先进入候选池；只有官方身份、真实完整岗位、明确2027届证据和爬虫验证全部通过时才生成待审核PR，不自动合并。
5. 更新 outputs/company_integration_status.md、docs/MULTISOURCE_DISCOVERY_TEST.md 和 docs/DEVELOPMENT_HANDOFF.md。

约束：不得打印或读取任何API Key；不运行每日全量采集；不清空jobs.db、投递记录或缓存；不进行大规模DeepSeek调用。若需要API验证，只使用现有受控预检硬限制。不要编造URL、岗位或届别。访问失败必须区分代理拒绝、目标403、验证码、正常空页面和解析失败。

请直接实施代码、限量联网测试、测试修复和文档更新，不只给建议。
```

## 推荐操作顺序

1. 新开Codex后粘贴上述提示词。
2. 如果用户已取得某个受限站点的公开URL，只补充URL，不提供任何凭据。
3. 先完成国聘适配和高校真实就业入口；这两类在GitHub runner已证明可访问，成功概率高于验证码页面。
4. 深度模型不必为了“测试成功”强行分析不相关岗位；等待出现A档且JD完整岗位，或另行设计明确、低费用且不写生产库的模型连通测试。

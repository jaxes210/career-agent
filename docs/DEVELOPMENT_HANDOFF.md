# Career Agent 开发交接

最后更新：2026-10-28。下次先读本文件、AGENTS.md、git status 和 git log；不要覆盖工作区或替换 jobs.db。

## 目标和约束

2027届工业催化硕士（正式专业），本科生物工程；山东大学仅交换培养，工业催化、催化材料、PMS氧化与水污染控制；稳定优先、全国不限、六级未达425。保留化工工艺、生产运行、材料研发、分析检测、环保技术。英语或届别不明保留待核实；仅确认2027届的岗位进入原有模型管线。不进行全量重复采集或无限额AI分析。

## 已恢复的历史成果

- f83233e：画像驱动筛选、英语条件、画像缓存失效与报告适配。
- 4a7a79c：12家扩大到68家，复用上游已支持来源；原始来源和历史成功证据见 outputs/environmental_enterprise_pool.md。
- 恢复时分支 work，本轮未提交修改全部仍在，未发生丢失或回滚。
- git fetch origin main 成功，开始时本地比 origin/main 多1个提交（4a7a79c）。GraphQL和REST PR查询均返回 Forbidden，不能判断是否存在未合并PR。

## 本轮完成

- 整理并完成上一轮未提交的 scripts/company_pool.py、候选状态和两条Actions。
- data/company_pool.json 保存正式/候选/失败/历史、发现时间、验证结果、失败历史、重试时间和来源证据。
- 复用 qq_docs_27_autumn_monitor 解析器；取消每日 main.py 直接追加 config.yaml 的行为。
- 已知平台推断采用域名边界，未知平台不再默认 render。
- validate_company.py 增加方向/正式校招过滤、字段覆盖、完整分页检查；至少一个岗位同时具备标题、地点、原始链接和任职要求才能自动提案。
- 官方身份单独设门槛：记录 official_status=verified 和 official_evidence_url。不能因平台可抓取而自动认定企业官方身份；最近岗位验证超过7天不能提案。
- 验证异常隔离；BLOCKED不当作EMPTY；候选按退避重试，连续EMPTY/ERROR进入失败池。
- 每周一三五限量发现验证，候选状态先持久化，再为正式配置创建PR；仅main运行这两条新增工作流。
- 每周日生成企业池报告；每日和无AI报告同步任务同时生成 company-pool.html，招聘报告侧栏添加入口。
- 文档及 outputs/company_integration_status.md 已更新。

## 本地验证和当前数据

- python -m pytest -q：307 passed，1个第三方pytest插件弃用警告。
- company_pool.py sync / report / propose 实际运行；本轮0家符合提案条件，config.yaml未新增未经验证企业。
- 正式池68；候选13；历史无效1；待适配12；关注名单16。
- 正式池历史：68/68有岗位，18063条，4599条确认2027届。
- 全库历史：496家、35297条，15038条确认2027届；这些是存量统计，不代表本轮实时成功。
- 本轮未启动main.py、未调用DeepSeek、未修改jobs.db。细分析额度仍为每轮5、每日10。
- 报告 outputs/company_pool_report.md；本地生成 reports/company-pool.html（reports被git忽略，CI重新生成）。

## 真实未完成项和阻碍

1. 新工作流尚未部署到远端并运行验证；本轮保存为本地提交，未推送或合并。GitHub API Forbidden，无法确认Actions、PR权限和运行结果。
2. 自动发现实际仅支持腾讯文档。watchlist只是关注名单，没有搜索执行器；高校就业网、集团官方公告、国聘跨企业发现、自动发现新来源尚未实现。禁止将注册表或关注名单描述成已实现的多源发现。
3. 招聘域名不在当前环境有效网络白名单，前轮验证是CONNECT 403。不能把网络阻碍算企业失效，也不能将历史数据库当本轮实时验证。
4. 官方身份目前需要人工将可核验的企业官网证据记录到候选JSON；尚无自动解析官网到租户链接的适配器。
5. 集团parent_group只记录元数据，尚无完整集团覆盖/独立子单位去重规则。不能按集团名称粗略合并独立招聘单位。
6. 同一企业多个URL记录在sources，但验证仍以careers_url为主，备用入口自动切换未完成。
7. 周报具备当前池和字段质量统计，尚缺长期增长快照、趋势及正式池实时健康抽检。
8. 150–200家扩容未完成；正式68家的前轮扩容主要依据上游配置和历史岗位，需在联网可用后分批实时复验。
9. 自动PR需仓库允许Actions创建PR；GITHUB_TOKEN创建的PR通常不触发常规后续CI，需要确认检查策略。新增PR工作流实际权限尚未验证。

## 下一轮直接执行顺序

1. git status / git log，读取本交接；检查远端main和PR，保留本地提交与数据库，勿force-push。
2. 开放必要的公开招聘域名后，限量验证1–3家，记录官方证据并检查自动提案diff；不运行main.py做测试。
3. 为高校/集团公告开发有fixture测试的公开HTML/RSS发现适配器；只注册真实验证的种子URL，发现的新来源先候选审核。
4. 补充集团与独立招聘租户的关系规则、备用来源轮换和正式池小批量健康检查、增长快照。
5. 在远端用PR集成这套代码及前轮68家扩容，验证Tests和无AI报告，再手动触发一次限量发现任务；确认PR权限后启用定时。
6. 按行业分批扩容至150–200；只把真实岗位验证成功且官方身份清楚的企业纳入正式池。


## 2026-10-28 工业催化画像修正

- 正式硕士：中国日用化学工业研究院，工业催化，2027届；本科武汉工程大学生物工程。山东大学2024.09—2025.06为交换培养，不授予本次学位。
- profile.yaml 记录教育、研究平台、三层目标岗位、科研项目、论文状态、实习边界、仪器层级待核实及四级527/六级未425。
- Applied Surface Science仅投稿且首轮修订，Chemistry of Materials共同一作已发表，日用化学工业综述一作接收待刊。
- 新增 job_eligibility 将博士限定、英语和专业目录核实与技能分开；工业催化不自动等同环境工程或化学工程。综合资格未知不能判为直接可投，模型推荐降为考虑并列核实项。
- 分析版本升级match-v3.1-industrial-catalysis-qualifications；画像全量指纹变化使旧筛选和分析缓存失效。保留历史数据，后续按既有费用上限渐进重算；未执行收费分析。
- 报告增加资格状态和核实原因，保留企业监测、爬虫、企业池与工作流。
- 测试：324 passed（随后增加规则时以最新测试结果为准）；未抓取、未改jobs.db。
- 待核实：具体专业代码和公告相近专业目录；每项仪器独立操作/参与测试/委托分析层级；企业实际经营稳定性；岗位完整学历条件及英语替代条件。

## 2026-10-28 工业催化企业池证据重构

- 本轮正式池68→67：6家高度匹配、61家潜在匹配。中国星网网络应用研究院在现有14条岗位中未见化学/材料/工艺迁移证据，移出正式配置，保留history、archived_config及理由；不宣称未来永远无岗位。
- 读取upstream/main（e169ebc）578家原始企业池，提取12家相关线索：万华化学、思摩尔、禾赛、中科曙光、韶音、瑞沃德、东风、一汽、东方电气、开立、卓胜微、小米；均为候选，没有强行加入正式池。
- 实测6个上游来源均为代理CONNECT403：万华、小米、禾赛、韶音、中科曙光、瑞沃德；公开Bing搜索也被拒绝。因此第一阶段实时官方核实/新增验收尚未完成，不能把存量岗位算本轮实抓成功。首次本地未提权验证另发现浏览器缺失；该EMPTY不是源站失效证据，未用于删除。
- data/backups/industrial_catalysis_pool保存本轮原config、pool与baseline计数/数据库SHA256；jobs.db与applications.json完全未修改，费用上限5/10保持。
- scripts/audit_industrial_company_pool.py：默认只读审计，--apply仅更新配置/池，--live-limit最多5；以备份的68家作为本次审计基线，便于重跑与恢复。outputs/industrial_company_audit.json保留原始URL、岗位ID、分类证据与限量裁决。
- data/company_relevance_policy.yaml分离企业行业/岗位迁移证据与岗位资格；过滤“强化学习/算法优化/数据质量”假命中。通用工艺、质量只算潜在，不当作专业资格符合。
- 自动接入新增门槛：同一相关岗位须有完整字段及明确2027届证据；不明届别继续候选。已移出来源不能被自动提案重新接入。
- 当前候选25、历史2、关注名单17；新加中国中化仅关注，未编造入口。正式池历史18049条，确认2027届4599条；其中按本轮规则相关且未发现硬性不符898条，仍有专业/英语/有效性待核实，不称为“确认可投”。
- 完整报告 docs/COMPANY_POOL_AUDIT.md。下一步首先解决公开招聘域名访问策略、安装Playwright浏览器，再限量复验候选官方归属、专业和2027届岗位；优先万华及石化/煤化工集团独立招聘单位，不能按数量目标接入。
- 本轮无DeepSeek调用；原有GitHub Actions未变更。代码与配置本地提交，尚未推送或验证远端运行。
- 最终离线测试：331 passed，1个第三方pytest插件弃用警告；git diff --check通过。数据库SHA256及投递JSON与本轮开始时一致。

## DeepSeek正式接入准备（2026-10-28）

- screening_model及默认更新deepseek-flash；Pro保持deepseek-v4-pro，尚无真实API验证。
- main共享Flash20岗位预算；batch_analyze硬限5，0禁用，取消无限额环境变量绕过，JD补全也先截5。日上限10保持。
- 新增deepseek_preflight.py与Controlled DeepSeek preflight工作流，默认dry-run；--execute明确付费，临时DB、不爬取/不通知/不改生产库。最多20Flash岗位+5Pro岗位，HTTP不重试，总请求上限6。
- 本地干跑20条，API0次，key_present=false（只指本地）。GitHub Actions/Secret名称API返回Forbidden，无法确认云端密钥、运行日志、实际模型可用。
- 离线测试333 passed；说明docs/DEEPSEEK_READINESS.md。同步main后应先execute=false，再人工确认execute=true，不要用main.py做首次连通测试。
- 8154565已成功非强制推送main（本地/远端SHA一致）；真实触发Tests 40642332641及Sync report 40642332642，网页确认执行8154565但因Python3.11旧f-string语法失败。
- 修复company_pool HTML表达式反斜杠；独立安装临时Python3.11.17复现旧错误，修复后333 passed、预检dry-run0调用、池报告生成成功。继续推送修复并检查新CI；不要误以为本地3.12通过即可证明云端3.11可用。
- 已同步main至3bb3c9f（应用代码），随后仅补文档。真实云端Tests通过、Sync report 40646915509成功、Pages40646958440成功。
- 通过新增push触发的零API预检40646987765，runner明确报DEEPSEEK_API_KEY is not configured for this workflow。已确认不是仅本地变量缺失，当前工作流拿不到Secret，需用户设置仓库级Secret或授权组织级Secret。未读取密钥值，未发起付费API。
- 下一步用户配置Secret后手动Controlled DeepSeek preflight execute=false，然后才execute=true。模型深度型号支持、余额和实际响应仍待受控验证。生产库SHA256保持原值，67家池不变。

## 2026-10-28 多源发现最小版本

- 新增scripts/public_discovery.py：公开HTML列表/公告和RSS/Atom解析，企业名、岗位要求摘要、原始公告及投递URL进入现有_merge_lead；第三方转载只作线索，不证明官方或资格。
- company_pool.discover支持注册public_html/public_rss，限制10来源、每来源最多2详情、2MiB响应；source_health保存BLOCKED等状态、next_retry_at；候选深入验证硬限3家。
- 修复未知共享URL忽略企业查询ID的问题，以及国聘www域名不同company?id的去重；集团独立下属单位使用完整名称，不按集团子串合并。
- 新增pending_sources6条（三类各2）：国家能源和兵器集团、两所高校门户、国投/电科国聘页。均未通过真实内容验证，disabled，不增加生产启用来源；高校门户不是就业公告URL。
- 实际运行scripts/test_discovery_sources.py，6入口全部代理连接ProxyError/BLOCKED，0真实招聘线索/0新企业/0官方验证/0届别资格验证/0深入企业验证/0新增企业PR。没有抓旧企业凑数；详见outputs/multisource_probe.json、docs/MULTISOURCE_DISCOVERY_TEST.md。
- 当前67家config、jobs.db和applications.json与本轮HEAD字节完全相同，无DeepSeek请求、无日常全量采集。仅保存失败发现源source_health，3天后重试。
- GitHub一三五及手动触发保留，默认深入验证3，新增诊断artifact。仍需网络开放后验证高校真正就业入口、集团公告及国聘SPA内容；不得将这轮标为已完成多源线上覆盖。
- 后续：按测试报告开放6个入口域名及gp-api.iguopin.com，运行限量探测；取得真实公告后启用注册来源，再company_pool.py run --limit 3走官方/2027届/字段门槛及PR审核。
- 最终Python3.11测试342 passed；git diff --check通过。未注册任何“已验证”新来源，线上真实覆盖仍为待完成项。

## 2026-10-28 GitHub Actions 联网复验准备

- 远端 `main` 起点与本地一致，均为 `219327b`；公开工作流页面显示 `Discover and validate employer sources` 已部署但 `This workflow has no runs yet`。仓库其他 Tests/报告/Pages 工作流有成功记录，说明 Actions 功能本身已启用。
- 工作流原来只运行 enabled 来源，无法触达6个 `pending_sources`。已修正为：仅 `workflow_dispatch` 默认执行 `scripts/test_discovery_sources.py`，定时任务仍不探测 pending 来源；诊断 artifact 同时上传 `data/company_pool.json` 与 `outputs/multisource_probe.json`。`validation_limit` 默认和硬上限保持3。
- 联网失败类型细分为代理CONNECT 403、代理错误、连接/DNS、TLS、连接/读取超时、目标HTTP状态、验证码/登录、无可解析线索和解析错误；仍统一遵守“访问失败不等于企业无招聘”。单个来源解析异常不再阻断其余5个入口，运行摘要会列出逐来源结果。
- 尝试使用 `gh workflow run company_pool_discovery.yml --ref main -f validation_limit=3`，GitHub API 返回 `Forbidden`，没有创建运行记录；当前云环境的 `GH_TOKEN` 无效，移除该变量后也没有已登录账户。Git推送可用不代表具有Actions API调度权限。
- 因未产生GitHub runner运行，本轮不能声称6入口在Actions中可访问，也没有新线索、新企业、官方验证或企业配置PR。用户需在 Actions 页面选择该工作流，点击 Run workflow，分支 `main`、`validation_limit=3`、保留 pending probe 开启；全程不调用DeepSeek或每日全量采集。
- 本轮新增回归后Python3.11为344 passed，工作流YAML可解析，`git diff --check`通过。正式67家配置、jobs.db、投递记录、历史分析及API费用上限未改。

## 2026-10-28 GitHub Actions 首次真实联网结果

- 用户手动运行 `Discover and validate employer sources #1`：`https://github.com/jaxes210/career-agent/actions/runs/40657312891`。探测步骤实际覆盖6/6入口，证明GitHub runner不存在Codex环境的全域CONNECT 403；运行最终Failure发生在后续Git持久化步骤，exit 128，不是联网或解析步骤失败。
- 国家能源招聘页和兵器集团北森页均已建立网络连接，但页面内容触发 `login/captcha/access challenge`，状态BLOCKED；这是目标页面访问挑战，不能判定无招聘，也不绕过。
- 华东理工、北京化工门户及国投/电科国聘页面均可访问，状态 `NO_PARSED_LEADS`。高校地址只是门户首页，不是已核实就业公告列表；两个国聘页面大概率为SPA，通用静态HTML解析没有岗位。四项均不能解释为企业没有招聘。
- 真实结果为0条招聘线索、0家新企业、0家官方/2027届资格验证、0个企业配置PR。6个来源继续保持pending/disabled。
- exit 128原因：手动探测改写已跟踪的 `outputs/multisource_probe.json`，持久化步骤只暂存池状态和报告，留下未暂存修改后执行 `git pull --rebase`。修复为把诊断JSON一并纳入状态提交，并增加工作流回归断言；artifact上传仍保留。
- `actions/upload-artifact@v4` 的Node.js 20弃用信息和ubuntu-latest迁移信息均为runner警告，不是本次失败原因。下一次手动探测用于验证持久化修复；在国聘专用适配器和真实高校就业入口完成前，不启用这6个来源做长期生产发现。

## 2026-10-28 GitHub Actions 第二次运行与候选池治理

- 用户再次运行 `Discover and validate employer sources #2`：`https://github.com/jaxes210/career-agent/actions/runs/40658013055`，Success，耗时1分26秒，1个诊断artifact；exit 128修复确认有效，自动状态提交 `8d73164` 成功写回main。
- 6入口结果与首次一致：国家能源/兵器集团为页面访问挑战，两个高校门户和两个国聘页面可访问但无通用HTML线索；0条线索、0家新企业、0个正式池PR。Node/Ubuntu annotation仅为warning/notice。
- 状态审计发现同一运行中的既有腾讯文档适配器把205家以软件、游戏、互联网为主的企业写入候选池，候选25→230；它们不是6入口结果，正式67家和config未变。
- 为腾讯文档新增候选准入：既有正式/候选继续更新；新企业须有行业名称证据、历史真实岗位标题证据或显式人工保留。严格岗位证据覆盖催化、化工工艺、材料、配方、理化检测、环保/水处理、生产/工艺技术，并排除算法、软件、模型优化、数据/代码质量、游戏等伪命中。
- 清理165个仅有腾讯文档来源且无专业迁移证据、未验证、未进入正式池的候选；保留40个有证据的新候选。当前正式67、候选65、历史2、可提案0；正式池集合与config完全一致。清理可由Git历史恢复，未删jobs.db、岗位、投递或分析缓存。
- Python3.11完整测试345 passed；后续腾讯文档运行会自动阻止同类候选污染。6个pending多源入口仍不启用，下一步开发真实高校就业入口和国聘专用适配器。

## 2026-10-28 DeepSeek接通与下一会话指南

- 用户已配置仓库级 `DEEPSEEK_API_KEY`。受控运行 `40659880270` 为execute模式：选择20个岗位，`deepseek-flash`合并为1次批量请求，1次成功、0次失败；临时数据库，未写生产库。
- `complete_analyses=0`：没有同时满足A档与JD完整的候选，因此 `deepseek-v4-pro` 未被调用，不能声称深度模型已验证。这不是Flash失败，也无需强行分析不相关岗位。
- 新增 `docs/NEXT_SESSION_GUIDE.md`，包含可直接粘贴的新Codex提示词、6个受限/未适配来源处理表以及人机验证边界。用户不应向Codex提供账号、密码、Cookie、验证码或API Key；只需提供公开URL。

## 2026-10-28 国聘与高校来源专用适配续作

- 本地 `HEAD` 与 `origin/main` 均为 `652c775`，开始时工作区干净。Git fetch 成功；`gh run list` 和无认证 GitHub Actions REST 均返回 Forbidden，近期已知运行仍以本文件和 `NEXT_SESSION_GUIDE.md` 记录的 #2 与受控 DeepSeek 运行作为证据，未伪称取得新运行结果。
- 国投和中国电科两个 pending 来源改用 `iguopin_tenant`，复用公开 API 爬虫并输出岗位总数、正式目标岗位数和明确 2027 届数。爬虫新增请求失败与分页完整性状态；失败或部分结果不会当成空来源，也不会合入候选或正式池。
- 华东理工和北京化工新增 `university_portal`：只从学校官网页面实际链接发现就业导航，最多跟随2页；不猜 URL，高校转载只作线索。fixture 覆盖跨子域就业导航和公告提取。
- 当前环境对 `gp-api.iguopin.com` 和两校官网均返回代理 CONNECT 403，真实限量验证未完成；国家能源和兵器集团也未绕过访问挑战。本轮未运行 main.py、未调用 DeepSeek、未修改 jobs.db 或正式 config。
- 下一步先在 GitHub Actions 手动运行 pending probe（limit 3）确认两个专用适配器的真实结果，再根据 artifact 中的国聘岗位/高校导航样例修正选择器；随后继续集团公开替代来源、来源轮换和小批健康检查。

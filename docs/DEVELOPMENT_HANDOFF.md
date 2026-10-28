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

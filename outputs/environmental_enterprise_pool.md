# 环境工程方向企业池与招聘来源报告

更新时间：2026-10-28

## 本批结果

- 正式企业池：12 → 68 家。
- 有真实历史抓取记录：68 家；数据库岗位合计 18,063 条。
- 官方证据确认 2027 届岗位：4,599 条。未明确届别的岗位仍保留待核实，不据此删除来源。
- 按当前画像执行确定性校招/方向过滤后保留 16,790 条，其中确认 2027 届 4,052 条、届别待核实 11,920 条。
- 英语资格：21 条明确要求六级至少425分且无替代条件，标记“不符合”；16,769 条标记“待核实”，未因英语信息缺失被删除。
- 验证依据：原始上游配置中的招聘 URL/爬虫 + 当前 `data/jobs.db` 的非空实抓记录；大多数来源最后见于 2026-10-28。
- 当前云运行时未放行招聘站域名，因此 `validate_company.py` 的在线复验会被代理 403 阻断；本报告不把网络阻断记为来源失效。
- 本次未运行 `main.py`，未调用 DeepSeek，未改写正式岗位数据库。

## 正式企业池

| 行业 | 企业 | 变更 | 平台 | crawler | 验证状态 | 历史岗位 | 确认2027届 | 原始招聘入口 |
|---|---|---|---|---|---|---:|---:|---|
| 综合能源与投资 | 国家开发投资集团 | 已有 | 国聘 | `iguopin` | 历史实抓通过（最后 2026-10-28） | 949 | 1 | [https://sdic1.iguopin.com/jobCampus](https://sdic1.iguopin.com/jobCampus) |
| 轨道交通装备 | 中国中车 | 已有 | Hotjob | `hotjob` | 历史实抓通过（最后 2026-10-28） | 824 | 31 | [https://crrc.hotjob.cn/SU64d47c466202cc36e27a52d4/pb/school.html](https://crrc.hotjob.cn/SU64d47c466202cc36e27a52d4/pb/school.html) |
| 国防工业与化工材料 | 中国兵器工业集团 | 已有 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 2409 | 40 | [https://norincogroupzhaopin.zhiye.com/campus/jobs](https://norincogroupzhaopin.zhiye.com/campus/jobs) |
| 光伏与储能 | 阳光电源 | 已有 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 182 | 71 | [https://app.mokahr.com/campus-recruitment/sungrow/94416](https://app.mokahr.com/campus-recruitment/sungrow/94416) |
| 流程工业自动化 | 中控 | 已有 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 27 | 5 | [https://app.mokahr.com/campus-recruitment/supcon/148189](https://app.mokahr.com/campus-recruitment/supcon/148189) |
| 检测认证与环境技术 | 华测 | 已有 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 43 | 1 | [https://huace.zhiye.com/campus/jobs](https://huace.zhiye.com/campus/jobs) |
| 风电与新能源 | 明阳智慧能源 | 已有 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 100 | 70 | [https://mywind.zhiye.com/campus/jobs](https://mywind.zhiye.com/campus/jobs) |
| 工业技术研究院 | 中国汽车工程研究院 | 来源优化 | Hotjob | `hotjob` | 历史实抓通过（最后 2026-10-28） | 131 | 0 | [https://wecruit.hotjob.cn/SU6603d5a01eb8054100c60436/pb/index.html](https://wecruit.hotjob.cn/SU6603d5a01eb8054100c60436/pb/index.html) |
| 汽车与工业制造 | 博世 | 已有 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 33 | 22 | [https://app.mokahr.com/campus-recruitment/bosch/73873](https://app.mokahr.com/campus-recruitment/bosch/73873) |
| 医药研发与化学分析 | 康龙化成 | 已有 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 178 | 104 | [https://app.mokahr.com/m/campus_apply/pharmaron/45318?recommendCode=DSFv5WjR#/jobs](https://app.mokahr.com/m/campus_apply/pharmaron/45318?recommendCode=DSFv5WjR#/jobs) |
| 汽车制造 | 奇瑞 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 3377 | 5 | [https://chery.zhiye.com/campus/jobs](https://chery.zhiye.com/campus/jobs) |
| 显示材料与制造 | 京东方 | 新增 | 京东方自建站 | `boe` | 历史实抓通过（最后 2026-10-28） | 1106 | 1 | [https://campus.boe.com/campus/jobs](https://campus.boe.com/campus/jobs) |
| 电池与储能 | 欣旺达 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 912 | 912 | [https://sunwodacampus.zhiye.com/campus/jobs](https://sunwodacampus.zhiye.com/campus/jobs) |
| 汽车制造 | 北汽集团 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 626 | 4 | [https://baicgroup.zhiye.com/campus/jobs](https://baicgroup.zhiye.com/campus/jobs) |
| 风电与储能 | 远景科技 | 新增 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 244 | 244 | [https://www.envision-career.com/campus-recruitment/envisiongroup/43123/#/jobs?project%5B0%5D=100124183&page=1&anchorName=jobsList](https://www.envision-career.com/campus-recruitment/envisiongroup/43123/#/jobs?project%5B0%5D=100124183&page=1&anchorName=jobsList) |
| 央企综合技术 | 中国联通 | 新增 | 国聘 | `iguopin` | 历史实抓通过（最后 2026-10-28） | 1380 | 170 | [https://zglt.iguopin.com/job](https://zglt.iguopin.com/job) |
| 央企科研与电子材料 | 中国电科 | 新增 | 国聘 | `iguopin` | 历史实抓通过（最后 2026-10-28） | 630 | 28 | [https://cetc.iguopin.com/job-campus](https://cetc.iguopin.com/job-campus) |
| 装备制造 | 三一集团 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 233 | 215 | [https://sany.zhiye.com/campus/jobs](https://sany.zhiye.com/campus/jobs) |
| 工业自动化与新能源 | 汇川技术 | 新增 | 汇川自建站 | `inovance` | 历史实抓通过（最后 2026-10-28） | 258 | 251 | [https://recruit.inovance.com/#/campus/jobs](https://recruit.inovance.com/#/campus/jobs) |
| 高分子材料 | 金发科技 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 99 | 69 | [https://kingfa.zhiye.com/campus/jobs](https://kingfa.zhiye.com/campus/jobs) |
| 显示材料与制造 | TCL华星 | 新增 | Hotjob | `hotjob` | 历史实抓通过（最后 2026-10-23） | 188 | 172 | [https://wecruit.hotjob.cn/SU6491506a2f9d24316e91b81b/mc/position/campus?acotycoCode=ndwsgd&orgId=100801%2C104101&projectId=308501&recruitType=1&isLimitShowPostScope=1](https://wecruit.hotjob.cn/SU6491506a2f9d24316e91b81b/mc/position/campus?acotycoCode=ndwsgd&orgId=100801%2C104101&projectId=308501&recruitType=1&isLimitShowPostScope=1) |
| 电子材料与制造 | 中航国际-深南电路 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 266 | 4 | [https://avicsz.zhiye.com/campus/jobs](https://avicsz.zhiye.com/campus/jobs) |
| 新能源化工材料 | 天赐材料 | 新增 | Hotjob | `hotjob` | 历史实抓通过（最后 2026-10-28） | 86 | 85 | [https://wecruit.hotjob.cn/SU62c3ea6b2f9d241e4c8e45ba/mc/position/campus?acotycoCode=qsjehk&projectId=201701&recruitType=1&isLimitShowPostScope=1](https://wecruit.hotjob.cn/SU62c3ea6b2f9d241e4c8e45ba/mc/position/campus?acotycoCode=qsjehk&projectId=201701&recruitType=1&isLimitShowPostScope=1) |
| 电池与储能 | 冠宇集团 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 91 | 89 | [https://cosmx.zhiye.com/campus/jobs?shareId=81f58b1a-e7be-43bf-87da-b2077ca1601e&shareSource=2](https://cosmx.zhiye.com/campus/jobs?shareId=81f58b1a-e7be-43bf-87da-b2077ca1601e&shareSource=2) |
| 汽车制造 | 长安 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 129 | 89 | [https://changan.zhiye.com/campus/jobs](https://changan.zhiye.com/campus/jobs) |
| 半导体材料与制造 | 佰维存储 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 135 | 89 | [https://biwin1.zhiye.com/campus/jobs](https://biwin1.zhiye.com/campus/jobs) |
| 电池与储能 | 新能安 | 新增 | Hotjob | `hotjob` | 历史实抓通过（最后 2026-10-28） | 59 | 59 | [https://wecruit.hotjob.cn/SU6618fd381eb8053acd5fc2b9/mc/position/campus?acotycoCode=uozkbk&projectId=505401%2C505501&recruitType=1&isLimitShowPostScope=1](https://wecruit.hotjob.cn/SU6618fd381eb8053acd5fc2b9/mc/position/campus?acotycoCode=uozkbk&projectId=505401%2C505501&recruitType=1&isLimitShowPostScope=1) |
| 电子制造 | 华勤 | 新增 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 88 | 32 | [https://app.mokahr.com/campus-recruitment/hq/44757](https://app.mokahr.com/campus-recruitment/hq/44757) |
| 油气装备与环保技术 | 杰瑞集团 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 61 | 61 | [https://future.jereh.com/campus/jobs?shareId=9c94dbea-93bf-4a5e-b2ad-eca3e586bd15&shareSource=2](https://future.jereh.com/campus/jobs?shareId=9c94dbea-93bf-4a5e-b2ad-eca3e586bd15&shareSource=2) |
| 电池与储能 | 东莞新能德 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 58 | 56 | [https://nvtpower.zhiye.com/campus/jobs](https://nvtpower.zhiye.com/campus/jobs) |
| 电池与储能 | 东莞新能源科技 | 新增 | Hotjob | `hotjob` | 历史实抓通过（最后 2026-10-28） | 62 | 55 | [https://wecruit.hotjob.cn/SU612e24992f9d247d0f41930e/pb/school.html](https://wecruit.hotjob.cn/SU612e24992f9d247d0f41930e/pb/school.html) |
| 半导体材料与制造 | 鹏芯微 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 22 | 22 | [https://career.pxwsemi.com/campus/jobs?shareId=b7ba1868-3017-4fbc-beb4-6fa0733a2d2d&shareSource=2](https://career.pxwsemi.com/campus/jobs?shareId=b7ba1868-3017-4fbc-beb4-6fa0733a2d2d&shareSource=2) |
| 半导体材料与制造 | 江波龙 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 92 | 45 | [https://longsys.zhiye.com/campus/jobs](https://longsys.zhiye.com/campus/jobs) |
| 半导体材料与制造 | 华虹集团 | 新增 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 98 | 0 | [https://app.mokahr.com/campus-recruitment/huahong/78009#/](https://app.mokahr.com/campus-recruitment/huahong/78009#/) |
| 半导体材料与制造 | 长鑫存储 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 224 | 0 | [https://cxmt.zhiye.com/campus/jobs](https://cxmt.zhiye.com/campus/jobs) |
| 先进材料 | 先导科技 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 185 | 0 | [https://vital.zhiye.com/campus/jobs](https://vital.zhiye.com/campus/jobs) |
| 能源装备与充电基础设施 | 特锐德 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 21 | 21 | [https://tgood.zhiye.com/campus/jobs?shareId=1eb59034-b367-4225-b950-c6366cff7d78&shareSource=2](https://tgood.zhiye.com/campus/jobs?shareId=1eb59034-b367-4225-b950-c6366cff7d78&shareSource=2) |
| 储能与新能源 | 启源芯动力 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 13 | 13 | [https://spicqyxdl.zhiye.com/campus/jobs](https://spicqyxdl.zhiye.com/campus/jobs) |
| 电池与储能 | 江苏海四达电源 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 12 | 12 | [https://highstar.zhiye.com/campus/jobs?shareId=0619c7c1-77c4-40bd-808c-60d38fffdeac&shareSource=2](https://highstar.zhiye.com/campus/jobs?shareId=0619c7c1-77c4-40bd-808c-60d38fffdeac&shareSource=2) |
| 新能源装备制造 | 赢合科技 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 33 | 28 | [https://yhwins2.zhiye.com/campus/jobs?shareId=8848ae0a-ca33-49f3-80a1-8e6153760225&shareSource=2&qr=1&memory=%7B%7D&silence=1](https://yhwins2.zhiye.com/campus/jobs?shareId=8848ae0a-ca33-49f3-80a1-8e6153760225&shareSource=2&qr=1&memory=%7B%7D&silence=1) |
| 工业技术研究院 | 广汽研究院 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 1 | 1 | [https://gacrnd.zhiye.com/campus/jobs](https://gacrnd.zhiye.com/campus/jobs) |
| 央企科研院所 | 中国星网网络应用研究院 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 14 | 0 | [https://cscnrczp.zhiye.com/campus/jobs](https://cscnrczp.zhiye.com/campus/jobs) |
| 央企科研与制造 | 航天恒星科技 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 45 | 10 | [https://spacestar.zhiye.com/campus/jobs](https://spacestar.zhiye.com/campus/jobs) |
| 央企科研与制造 | 中信科 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 63 | 63 | [https://cictmobile.zhiye.com/campus/jobs](https://cictmobile.zhiye.com/campus/jobs) |
| 电源与电子制造 | 广州金升阳 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 28 | 27 | [https://mornsun.zhiye.com/campus/jobs](https://mornsun.zhiye.com/campus/jobs) |
| 家电与制造 | 奥克斯集团 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 39 | 39 | [https://auxgroup.zhiye.com/campus/jobs?shareId=6275af13-0f7f-4634-b26f-7f02dea33054&shareSource=2](https://auxgroup.zhiye.com/campus/jobs?shareId=6275af13-0f7f-4634-b26f-7f02dea33054&shareSource=2) |
| 农业环保与生产技术 | 牧原集团 | 新增 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 41 | 41 | [https://app.mokahr.com/campus_apply/muyuan/70116?recommendCode=DSCHtb4w#/jobs](https://app.mokahr.com/campus_apply/muyuan/70116?recommendCode=DSCHtb4w#/jobs) |
| 水务产品与制造 | 九牧集团 | 新增 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 15 | 15 | [https://app.mokahr.com/m/campus-recruitment/jomoo/142937?recommendCode=DSYnYM2x#/jobs](https://app.mokahr.com/m/campus-recruitment/jomoo/142937?recommendCode=DSYnYM2x#/jobs) |
| 工业自动化与新能源 | 英威腾 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 106 | 0 | [https://invt.zhiye.com/campus/jobs](https://invt.zhiye.com/campus/jobs) |
| 电子制造 | 深科技 | 新增 | 官网渲染 | `render` | 历史实抓通过（最后 2026-10-28） | 24 | 0 | [https://zhaopin.kaifa.cn/Campus/Positions](https://zhaopin.kaifa.cn/Campus/Positions) |
| 家电与制造 | 海信集团 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 285 | 285 | [https://jobs.hisense.com/campus/jobs](https://jobs.hisense.com/campus/jobs) |
| 汽车材料与制造 | 延锋 | 新增 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 184 | 47 | [https://app.mokahr.com/m/campus-recruitment/yanfeng/45086](https://app.mokahr.com/m/campus-recruitment/yanfeng/45086) |
| 新能源汽车 | 零跑汽车 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 265 | 222 | [https://leapmotor1.zhiye.com/campus/jobs](https://leapmotor1.zhiye.com/campus/jobs) |
| 新能源汽车电源 | 威迈斯 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 57 | 40 | [https://vmax.zhiye.com/campus/jobs](https://vmax.zhiye.com/campus/jobs) |
| 汽车制造 | 均胜集团 | 新增 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 91 | 68 | [https://app.mokahr.com/campus-recruitment/joyson/94311](https://app.mokahr.com/campus-recruitment/joyson/94311) |
| 装备制造 | 春风动力 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 135 | 135 | [https://cfmoto.zhiye.com/campus/jobs?shareId=d6e4e863-ab41-4ef3-b95c-e5625950bedc&shareSource=2](https://cfmoto.zhiye.com/campus/jobs?shareId=d6e4e863-ab41-4ef3-b95c-e5625950bedc&shareSource=2) |
| 储能与电力电子 | 科华集团 | 新增 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 30 | 30 | [https://app.mokahr.com/campus_apply/kehua/92510?recommendCode=DSHV5wbF#/jobs](https://app.mokahr.com/campus_apply/kehua/92510?recommendCode=DSHV5wbF#/jobs) |
| 汽车制造 | 江淮汽车 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 51 | 0 | [https://jac.zhiye.com/campus/jobs](https://jac.zhiye.com/campus/jobs) |
| 医疗器械与分析检测 | 迈瑞医疗 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 56 | 0 | [https://mindray.zhiye.com/campus/jobs](https://mindray.zhiye.com/campus/jobs) |
| 医疗器械与制造 | 联影 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 192 | 0 | [https://united-imaging.zhiye.com/campus/jobs](https://united-imaging.zhiye.com/campus/jobs) |
| 半导体材料与制造 | 豪威集团 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 90 | 4 | [https://ovt-omnivision.zhiye.com/campus/jobs](https://ovt-omnivision.zhiye.com/campus/jobs) |
| 电力电子与制造 | 麦米电气 | 新增 | Hotjob | `hotjob` | 历史实抓通过（最后 2026-10-28） | 57 | 42 | [https://wecruit.hotjob.cn/SU6282075e0dcad413c09efe26/pb/school.html](https://wecruit.hotjob.cn/SU6282075e0dcad413c09efe26/pb/school.html) |
| 先进材料与半导体 | 睿创微纳 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 90 | 83 | [https://raytrontek.zhiye.com/campus/jobs](https://raytrontek.zhiye.com/campus/jobs) |
| 科研院所 | 中国网安/30所 | 新增 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 37 | 0 | [https://app.mokahr.com/campus_apply/cetc30/36270](https://app.mokahr.com/campus_apply/cetc30/36270) |
| 生命科学与分析检测 | 华大集团 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 163 | 83 | [https://genomics.zhiye.com/campus/jobs](https://genomics.zhiye.com/campus/jobs) |
| 电子制造 | 传音 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 128 | 128 | [https://transsion.zhiye.com/campus/jobs](https://transsion.zhiye.com/campus/jobs) |
| 半导体材料与制造 | 德州仪器 | 新增 | Moka | `moka` | 历史实抓通过（最后 2026-10-28） | 71 | 20 | [https://app.mokahr.com/su/vjlqkz](https://app.mokahr.com/su/vjlqkz) |
| 半导体材料与制造 | 艾为电子 | 新增 | 北森 | `beisen` | 历史实抓通过（最后 2026-10-28） | 41 | 40 | [https://awinic.zhiye.com/campus/jobs](https://awinic.zhiye.com/campus/jobs) |

## 失效来源与待人工核实清单

以下企业未加入正式配置；没有可靠 URL 时保留空值，未猜测 crawler。

| 行业 | 企业 | 已知入口 | 状态/原因 |
|---|---|---|---|
| 石油石化 | 中国石油 | — | 未在上游配置或数据库中建立可实抓入口 |
| 石油石化 | 中国石化 | — | 未在上游配置或数据库中建立可实抓入口 |
| 石油石化 | 中国海油 | — | 未在上游配置或数据库中建立可实抓入口 |
| 能源煤化工 | 国家能源集团 | — | 公开GitHub搜索未找到可验证入口 |
| 能源煤化工 | 中国中煤 | — | 未找到可实抓官方入口 |
| 能源煤化工 | 晋能控股 | — | 未找到可实抓官方入口 |
| 能源煤化工 | 山东能源 | — | 未找到可实抓官方入口 |
| 化工与材料 | 万华化学 | https://www.whchem.com/column/164/ | 历史仅2条，最后见于2026-07-16，移出正式池待复验 |
| 化工与材料 | 卫星化学 | — | 未找到可实抓官方入口 |
| 化工与材料 | 华鲁恒升 | — | 未找到可实抓官方入口 |
| 化工与材料 | 宝丰能源 | — | 未找到可实抓官方入口 |
| 化工与材料 | 荣盛石化 | — | 未找到可实抓官方入口 |
| 环保与水务 | 中国节能环保集团 | — | 未找到可实抓官方入口 |
| 环保与水务 | 北控水务 | — | 公开GitHub搜索未找到可验证入口 |
| 环保与水务 | 首创环保 | — | 未找到可实抓官方入口 |
| 环保与水务 | 光大环境 | — | 未找到可实抓官方入口 |
| 新能源 | 宁德时代 | https://talent.catl.com/campus-recruitment/catlhr/115953 | 历史数据库0条，移出正式池待复验 |

## 验证口径

1. 正式池只接纳上游已有适配器且数据库确有岗位记录的来源。
2. `2027届确认数=0` 不代表来源失效；它表示当前岗位缺少足够官方届别证据，继续保留待核实。
3. 英语条件不明确不删除岗位；明确要求六级425分且无替代条件时才标记不符合。
4. 后续在线复验应按平台分批运行 `scripts/validate_company.py`，再优先补石油石化、煤化工和水务集团。

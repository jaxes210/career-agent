import re
import os
import unicodedata
from pathlib import Path

from profile_config import load_profile


_INTERN_RE = re.compile(r"(^|[^a-z])intern(ship)?([^a-z]|$)", re.I)
_INTERN_PROJECT_RE = re.compile(
    r"日常实习|应届实习|暑期实习|寒假实习|春季实习|秋季实习|长期实习|短期实习|"
    r"寻梦实习招聘|实习生(?:专项)?招聘(?:计划)?|实习招聘|可转正实习|"
    r"实习薪酬(?:津贴)?|转正机会",
    re.I,
)
_INTERN_METADATA_RE = re.compile(r"(?:^|[\s|·])实习(?:[\s|·]|$)", re.I)
_INTERN_BODY_EN_RE = re.compile(
    r"(?:complete|undertake|join)\s+an?\s+internship|"
    r"internship\s+(?:position|program|programme|opportunity|duration)",
    re.I,
)
_INTERN_DURATION_RE = re.compile(
    r"(?:至少|能够|能|可)?实习(?:期)?(?:至少|不少于)?\s*"
    r"[一二三四五六七八九十两\d]+\s*个?月|"
    r"每周(?:至少)?(?:到岗|实习)\s*[一二三四五六七八九十两\d]+\s*天",
    re.I,
)
_INTERN_URL_RE = re.compile(
    r"(?:[?&#](?:type|recruitType)=|/)(?:internship|intern)(?:[/?&#]|$)",
    re.I,
)
_EARLY_BATCH_RE = re.compile(r"提前批|提前招聘|提前选拔|预招聘|early\s*batch", re.I)
_SOCIAL_URL_RE = re.compile(
    r"social[-_/]?recruitment|/social|experienced|campus\.51job\.com/greenvalley/si\.html",
    re.I,
)
_SOCIAL_TITLE_RE = re.compile(r"社会招聘|社招|三年及以上|五年及以上|资深|高级|专家", re.I)
_SOCIAL_BODY_RE = re.compile(
    r"(?:招聘类型|岗位类型|职位类型|招聘项目|项目类型)\s*[:：|·]\s*(?:社会招聘|社招)|"
    r"(?:^|[\r\n])\s*(?:社会招聘|社招)\s*(?:[|·]|$)",
    re.I,
)
_FORMAL_CAMPUS_BODY_RE = re.compile(
    r"(?:招聘类型|岗位类型|职位类型|招聘项目|项目类型)\s*[:：|·]\s*"
    r"(?:校园招聘|校招|应届生招聘)",
    re.I,
)


JOB_CATEGORY_LABELS = {
    "chemical_process": "化工工艺与生产技术",
    "environmental": "环境工程与污染治理",
    "materials_catalysis": "材料与催化研发",
    "chemical_quality": "分析检测与质量技术",
    "llm_agent": "大模型与智能体",
    "robotics": "机器人与具身智能",
    "vision_auto": "视觉感知与自动驾驶",
    "algorithm_ml": "算法与机器学习",
    "software_cpp": "C++与软件开发",
    "testing_quality": "测试与质量",
    "embedded_control": "嵌入式与控制",
    "hardware_mechanical": "硬件、机械与电气",
    "data_platform": "数据平台与安全",
    "other_technical": "其他技术岗位",
}

_JOB_CATEGORY_RULES = (
    ("environmental", re.compile(r"环境工程|环保|水处理|污染治理|三废|EHS", re.I)),
    ("materials_catalysis", re.compile(r"催化|材料研发|材料工程|材料表征", re.I)),
    ("chemical_process", re.compile(r"化工|工艺|生产技术|生产运行|能源化工|石油化工", re.I)),
    ("chemical_quality", re.compile(r"化学分析|理化分析|分析检测|质量检测|检测工程师|实验室", re.I)),
    ("llm_agent", re.compile(
        r"大模型|语言模型|LLM|AIGC|智能体|Agent|RAG|自然语言|NLP|多模态|生成式|生成模型",
        re.I,
    )),
    ("robotics", re.compile(
        r"具身|机器人|机械臂|VLA|强化学习|模仿学习|运动规划|路径规划|机器人导航|SLAM",
        re.I,
    )),
    ("vision_auto", re.compile(
        r"计算机视觉|视觉|图像|视频|感知|自动驾驶|智驾|点云|激光雷达|雷达算法|"
        r"三维重建|3D|图形学|定位算法",
        re.I,
    )),
    ("embedded_control", re.compile(
        r"嵌入式|固件|Firmware|驱动开发|底层开发|单片机|MCU|PLC|控制算法|"
        r"运动控制|电机控制|自动化工程|车载软件|AUTOSAR",
        re.I,
    )),
    ("hardware_mechanical", re.compile(
        r"硬件|机械|结构|电气|电子|芯片|集成电路|IC设计|FPGA|射频|天线|光学|"
        r"电源|电机|工艺|制造工程|热设计|仿真工程",
        re.I,
    )),
    ("testing_quality", re.compile(
        r"测试|测开|质量|可靠性|验证工程|SDET|QA(?:工程|开发|测试)",
        re.I,
    )),
    ("algorithm_ml", re.compile(
        r"算法|机器学习|深度学习|人工智能|推荐|搜索|数据挖掘|运筹|优化研究|AI研究",
        re.I,
    )),
    ("data_platform", re.compile(
        r"大数据|数据工程|数据开发|数据平台|数据仓库|数据库|云计算|云平台|DevOps|"
        r"运维|信息安全|网络安全|安全工程|基础设施|平台工程",
        re.I,
    )),
    ("software_cpp", re.compile(
        r"C\+\+|软件|开发工程师|后端|前端|客户端|服务端|全栈|"
        r"工程效能|操作系统|编译器|中间件|系统工程师|应用工程师",
        re.I,
    )),
)


def job_category(job: dict) -> str:
    """Return one stable primary category for a displayed technical job."""
    title = str(job.get("title") or "")
    for key, pattern in _JOB_CATEGORY_RULES:
        if pattern.search(title):
            return key
    return "other_technical"

# High-confidence role names outside this repository's technical target profile.
# Keep these title-based: scanning JD prose for words such as "sales" or
# "operations" would incorrectly reject engineering roles that collaborate
# with those teams.
_DIRECTION_OUT_TITLE_RE = re.compile(
    r"(?:"
    r"产品经理|产品总经理|产品运营|项目经理|项目管理|"
    r"\bProduct\s+Manager\b|"
    r"销售(?:经理|工程师|专员|代表|助理|顾问|管培生|培训生)|"
    r"大客户销售|电话销售|渠道销售|技术型销售|售前(?:工程师|顾问|支持)?|"
    r"(?:市场|品牌|内容|用户|渠道|商家|社区|新媒体|广告投放|策略|产品|数据|车辆|物流|客服)运营|"
    r"运营(?:经理|专员|主管|管理|管培生|培训生|中台岗)|技术运营|"
    r"财务|会计|审计|税务|人力资源|人力专员|HRBP|招聘(?:专员|助理|经理)|"
    r"行政|法务|合规专员|"
    r"采购(?:经理|专员|工程师|管理|商务)|供应链(?:计划|管理|运营|采购)|"
    r"物流(?:规划|运营|管理|专员)|仓储|"
    r"平面设计师|视觉设计师|UI设计师|UX设计师|交互设计师|工业设计师|"
    r"教师|主讲|竞赛教练|课程顾问|班主任|"
    r"公关专员|品牌专员|文案|编辑|主播|校园大使|生态合作专员|"
    r"商品开发|产品(?:规划)?(?:培训生|管培生)|产培生|"
    r"游戏(?:系统|营销|运营|数值|战斗|技术|关卡|任务)?策划|游戏策划(?:培训生)?|"
    r"游戏设计师|美术(?:经理|项目管理)|战略研究专员|"
    r"游戏[^\r\n]{0,12}运营|游戏交互/体验设计师|"
    r"发行(?:运营|管培生)|品牌管理培训生|采购管培生|策略分析师|"
    r"游戏原画设计|3D(?:角色|场景)模型|Spine动画|插画师|视频后期|"
    r"策划管培生|(?:游戏)?数据分析(?:师|工程师)|"
    r"User Growth Marketing|Marketing Campaigns|\bMarketing\b|开发者(?:区域|论坛|平台)"
    r")",
    re.I,
)

# Some product roles use branded titles that contain no role keyword. Only
# match explicit ownership of product planning/design in the JD; a broad search
# for "product" or "product manager" would reject engineers who merely work
# with a product team.
_DIRECTION_OUT_BODY_RE = re.compile(
    r"(?:本岗位|该岗位|职位)?\s*(?:主要)?负责.{0,35}"
    r"(?:产品的规划与设计|产品规划与设计|产品规划、设计|产品规划及设计)",
    re.I | re.S,
)

_TECHNICAL_TITLE_RE = re.compile(
    r"算法|软件|开发|测试|研发|机器人|大模型|智能体|视觉|SLAM|控制|仿真|"
    r"嵌入式|硬件|芯片|机械|电气|自动化|系统工程|数据工程|技术工程|"
    r"研究|模型|多模态|生成|化工|环境工程|环保|水处理|催化|材料|工艺|生产技术|化学分析|检测|EHS",
    re.I,
)

_NON_JOB_TITLE_RE = re.compile(
    r"欢迎使用|(?:AI|智能)助理[👏！!。]?$|"
    r"^\s*【原始职位】|^\s*(?:职位描述|岗位职责|任职要求)\s*$",
    re.I,
)


def is_job_record_noise(job: dict) -> bool:
    """Reject UI/chatbot fragments that a generic parser mistook for a job."""
    title = str(job.get("title") or "").strip()
    return not title or _NON_JOB_TITLE_RE.search(title) is not None


def is_intern_title(title: str) -> bool:
    text = title or ""
    return "实习" in text or _INTERN_RE.search(text) is not None


def is_intern_job(job: dict) -> bool:
    """Recognize internships even when the title is shared with a formal role."""
    return internship_reason(job) is not None


def internship_reason(job: dict) -> str | None:
    """Return the high-confidence signal proving that a role is an internship.

    Generic mentions such as "有实习经历者优先" deliberately do not match.
    """
    title = str(job.get("title") or "")
    job_type = str(job.get("job_type") or "")
    jd_raw = str(job.get("jd_raw") or "")
    jd_url = str(job.get("jd_url") or "")
    if is_intern_title(title):
        return "标题明确标注实习"
    if "实习" in job_type:
        return "招聘类型明确标注实习"
    if _INTERN_URL_RE.search(jd_url):
        return "岗位 URL 明确属于实习轨道"
    if _INTERN_PROJECT_RE.search(jd_raw):
        return "招聘项目或正文明确标注实习"
    if "实习生" in jd_raw[:260] or _INTERN_METADATA_RE.search(jd_raw[:260]):
        return "页面头部元数据明确标注实习"
    if _INTERN_BODY_EN_RE.search(jd_raw):
        return "英文正文明确要求参加实习"
    if _INTERN_DURATION_RE.search(jd_raw):
        return "岗位要求当前候选人连续实习"
    return None


def early_batch_reason(job: dict) -> str | None:
    """Return the field that explicitly identifies an early-batch role."""
    fields = (
        ("标题", job.get("title")),
        ("招聘类型", job.get("job_type")),
        ("岗位正文", job.get("jd_raw")),
        ("岗位 URL", job.get("jd_url")),
    )
    for label, value in fields:
        if _EARLY_BATCH_RE.search(str(value or "")):
            return f"{label}明确标注提前批"
    return None


def is_early_batch_job(job: dict) -> bool:
    return early_batch_reason(job) is not None


_COHORT_RE = re.compile(
    r"(?<!\d)(20\d{2}|[12]\d)\s*(?:届|年?\s*(?:春招|秋招|校招|校园招聘)|(?:春招|秋招|校招|校园招聘))",
    re.I,
)


def cohort_year(job: dict) -> int | None:
    """Return an explicitly advertised campus cohort year, otherwise None."""
    text = " ".join(
        str(job.get(field) or "") for field in ("title", "job_type", "jd_raw")
    )
    years = []
    for raw in _COHORT_RE.findall(text):
        year = int(raw)
        years.append(year if year >= 2000 else 2000 + year)
    return min(years) if years else None


def is_social_job(job: dict) -> bool:
    title = str(job.get("title") or "")
    url = str(job.get("jd_url") or "")
    body = str(job.get("jd_raw") or "")
    job_type = str(job.get("job_type") or "")
    verified_campus = _FORMAL_CAMPUS_BODY_RE.search(body[:300]) is not None
    return (
        _SOCIAL_URL_RE.search(url) is not None
        or (_SOCIAL_TITLE_RE.search(title) is not None and not verified_campus)
        or _SOCIAL_BODY_RE.search(job_type) is not None
        or _SOCIAL_BODY_RE.search(body[:500]) is not None
    )


def is_formal_campus_job(job: dict) -> bool:
    return (
        not is_intern_job(job)
        and not is_early_batch_job(job)
        and not is_social_job(job)
    )


def current_profile() -> dict:
    """Use the same profile path in reports, DB cleanup and the pipeline."""
    return load_profile(os.environ.get("PROFILE_PATH", Path(__file__).parent / "profile.yaml"))


def profile_role_keywords(profile: dict) -> list[str]:
    words = list(profile.get("directions") or []) + list(profile.get("secondary_directions") or [])
    for role in profile.get("target_roles") or []:
        if isinstance(role, str):
            words.append(role)
        elif isinstance(role, dict):
            words.extend([role.get("name", ""), *(role.get("keywords") or [])])
    return [unicodedata.normalize("NFKC", str(word)).casefold() for word in words if str(word).strip()]


def is_direction_out_job(job: dict, profile: dict | None = None) -> bool:
    profile = profile if profile is not None else current_profile()
    if is_job_record_noise(job):
        return True
    title = unicodedata.normalize("NFKC", str(job.get("title") or "")).casefold()
    if any(unicodedata.normalize("NFKC", str(word)).casefold() in title for word in profile.get("excluded_title_keywords", [])):
        return True
    # The candidate's configured roles take precedence over generic negatives,
    # including production operations, technical support and technical management.
    if any(word in title for word in profile_role_keywords(profile)):
        return False
    return _legacy_direction_out_job(job)


def _legacy_direction_out_job(job: dict) -> bool:
    """Return True for explicit non-target roles that should never enter DB.

    The rule intentionally uses the title only and matches concrete role names,
    not broad business-domain words. For example, "广告推荐算法工程师" and
    "软件开发-运营开发方向" remain eligible for the AI coarse screen.
    """
    title = str(job.get("title") or "").strip()
    body = str(job.get("jd_raw") or "").strip()
    if is_job_record_noise(job):
        return True
    if _DIRECTION_OUT_BODY_RE.search(body) and not _TECHNICAL_TITLE_RE.search(title):
        return True
    match = _DIRECTION_OUT_TITLE_RE.search(title)
    if match is None:
        return False

    # Domain words can occur inside a genuine engineering title, such as
    # "供应链管理系统开发工程师". Preserve those for AI evaluation unless
    # the title explicitly names a non-target role.
    explicit_role = re.search(
        r"产品(?:经理|总经理|运营)|\bProduct\s+Manager\b|项目(?:经理|管理)|销售|售前|"
        r"运营(?:经理|专员|主管|管理|管培生|培训生)|"
        r"财务|会计|审计|税务|人力资源|HRBP|招聘|行政|法务|合规专员|"
        r"商品开发|"
        r"平面设计师|视觉设计师|UI设计师|UX设计师|交互设计师|工业设计师|"
        r"教师|主讲|竞赛教练|课程顾问|班主任|公关专员|品牌专员|主播|"
        r"游戏(?:系统|营销|运营|数值|战斗|技术|关卡|任务)?策划|游戏策划|"
        r"游戏设计师|美术(?:经理|项目管理)|战略研究专员|"
        r"游戏[^\r\n]{0,12}运营|游戏交互/体验设计师|"
        r"发行(?:运营|管培生)|品牌管理培训生|采购管培生|策略分析师|"
        r"游戏原画设计|3D(?:角色|场景)模型|Spine动画|插画师|视频后期|"
        r"策划管培生|(?:游戏)?数据分析(?:师|工程师)|"
        r"开发者(?:区域|论坛|平台)",
        title,
        re.I,
    )
    if explicit_role is not None:
        return True

    technical_role = _TECHNICAL_TITLE_RE.search(title)
    return technical_role is None


def filter_formal_campus_jobs(jobs: list[dict]) -> tuple[list[dict], list[dict]]:
    kept, dropped = [], []
    for job in jobs:
        (kept if is_formal_campus_job(job) else dropped).append(job)
    return kept, dropped


def filter_target_direction_jobs(jobs: list[dict], profile: dict | None = None) -> tuple[list[dict], list[dict]]:
    """Drop high-confidence non-target roles and parser noise before upsert."""
    profile = profile if profile is not None else current_profile()
    kept, dropped = [], []
    for job in jobs:
        (dropped if is_direction_out_job(job, profile) else kept).append(job)
    return kept, dropped


def english_eligibility(job: dict, profile: dict) -> dict:
    """Conservative JD-only eligibility; unknown alternatives need verification."""
    candidate = profile.get("english") or {}
    body = str(job.get("jd_raw") or "")
    body = unicodedata.normalize("NFKC", body)
    six = r"(?:CET[\s-]*6|大学英语六级|英语六级|六级)"
    clauses = re.split(r"[。；;\n]", body)
    for clause in clauses:
        if not re.search(six, clause, re.I):
            continue
        # Only an explicit binding minimum is a hard failure. Preferences,
        # equivalent qualifications and exceptions do not establish exclusion.
        threshold = re.search(six + r"[^。；;\n]{0,35}?(\d{3})\s*分?", clause, re.I)
        if not threshold:
            continue
        score = int(threshold.group(1))
        if score < 425:
            continue
        if re.search(r"优先|建议|加分|或|或者|雅思|托福|IELTS|TOEFL|同等|相当|可替代|豁免|放宽|不限|不要求|不作|无需", clause, re.I):
            return {"status": "待核实", "reason": "英语要求包含替代、优先或例外条件，需核实适用性", "evidence": clause.strip()}
        mandatory = re.search(r"须|需|要求|达到|通过|不低于|不少于|至少|以上|及以上|>=|≥", clause)
        if not mandatory:
            continue
        candidate_score = candidate.get("cet6_score")
        below = candidate.get("cet6_below_425") is True
        if (candidate_score is not None and float(candidate_score) < score) or (below and score >= 425):
            return {"status": "不符合", "reason": f"JD明确要求英语六级至少{score}分，候选人未达到且未见替代条件", "evidence": clause.strip()}
        if candidate_score is not None and float(candidate_score) >= score:
            return {"status": "符合", "reason": "已达到JD明确的六级分数条件", "evidence": clause.strip()}
    four = re.search(r"(?:CET[\s-]*4|英语四级|大学英语四级|四级)(?:[^。；;\n]{0,12}?)(\d{3})\s*分", body, re.I)
    four_required = re.search(r"(?:要求|通过|须|达到)[^。；;\n]{0,8}(?:CET[\s-]*4|英语四级|大学英语四级|四级)", body, re.I)
    if (four or four_required) and not re.search(six, body, re.I):
        threshold = int(four.group(1)) if four else 425
        score = candidate.get("cet4_score")
        if score is not None:
            return {"status": "符合" if score >= threshold else "不符合",
                    "reason": f"四级已知分数{score}，岗位四级要求{threshold}分；其他英语条件仍需核实", "evidence": body}
    return {"status": "待核实", "reason": "JD未明确英语条件或现有信息不足，不能判定不符合", "evidence": ""}


def job_eligibility(job: dict, profile: dict) -> dict:
    """Separate deterministic qualifications from transferable skill scores."""
    body = unicodedata.normalize('NFKC', str(job.get('jd_raw') or ''))
    title = str(job.get('title') or '')
    english = english_eligibility(job, profile)
    degree = {'status': '待核实', 'reason': '未明确学历要求'}
    if re.search(r'博士后|博士专招|博士专项', title) or re.search(
        r'仅(?:限|招|接受)?博士|博士(?:研究生)?(?:学历|学位)(?:为必需|为必须)|学历要求[:：\s]*博士|(?:要求|须具备|须为)博士(?:学历|学位|研究生)', body
    ) or (re.search(r'博士(?:研究生)?', title) and not re.search(r'硕士|本科', title)):
        degree = {'status': '不符合', 'reason': '明确博士限定，当前为硕士'}
    elif re.search(r'硕士|研究生|本科及以上', body):
        degree = {'status': '待核实', 'reason': '学历表述包含硕士或研究生，需核实完整条件'}
    major = {'status': '待核实', 'reason': '专业目录、代码及相近专业范围须按公告核实'}
    if re.search(r'专业不限|不限专业', body):
        major = {'status': '符合', 'reason': '明确不限专业'}
    elif '工业催化' in body:
        major = {'status': '待核实', 'reason': '包含工业催化，仍需核对专业代码、学历阶段和其他限制'}
    checks = {'english': english, 'degree': degree, 'major': major}
    status = '不符合' if any(c['status'] == '不符合' for c in checks.values()) else '待核实'
    return {'status': status, 'checks': checks,
            'reason': '；'.join(c['reason'] for c in checks.values())}

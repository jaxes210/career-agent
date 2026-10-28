from pathlib import Path

import yaml


REQUIRED_FIELDS = (
    "degree",
    "job_type",
    "directions",
    "skills",
    "target_roles",
    "score_component_limits",
    "score_thresholds",
)


def load_profile(path: str | Path = "profile.yaml") -> dict:
    profile_path = Path(path)
    if not profile_path.exists():
        raise ValueError(f"找不到用户画像配置: {profile_path}")

    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8")) or {}
    missing = [field for field in REQUIRED_FIELDS if field not in profile]
    if missing:
        raise ValueError(f"profile.yaml 缺少字段: {', '.join(missing)}")

    for field in ("directions", "skills", "target_roles"):
        if not isinstance(profile[field], list) or not profile[field]:
            raise ValueError(f"profile.yaml 的 {field} 必须是非空列表")
    for role in profile["target_roles"]:
        if not isinstance(role, (str, dict)) or (isinstance(role, dict) and
                (not role.get("name") or not isinstance(role.get("keywords", []), list))):
            raise ValueError("target_roles 必须包含角色名和关键词列表")
    english = profile.get("english") or {}
    if not isinstance(english, dict):
        raise ValueError("english 必须是映射")
    if "cet6_below_425" in english and not isinstance(english["cet6_below_425"], bool):
        raise ValueError("cet6_below_425 必须是布尔值")
    if "cet6_score" in english and (isinstance(english["cet6_score"], bool) or
            not isinstance(english["cet6_score"], (int, float)) or not 0 <= english["cet6_score"] <= 710):
        raise ValueError("cet6_score 必须是0到710的分数")
    if english.get("cet6_below_425") and english.get("cet6_score", 0) >= 425:
        raise ValueError("英语六级分数与未达到425的声明冲突")

    for score_field in ("cet4_score",):
        value = english.get(score_field)
        if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 710):
            raise ValueError(f"{score_field} 必须是0到710的分数")
    if "education" in profile:
        if not isinstance(profile["education"], list) or any(not isinstance(e, dict) or not e.get("school") for e in profile["education"]):
            raise ValueError("education 必须是含学校信息的列表")
    for field in ("technique_experience", "scoring_policy"):
        if field in profile and not isinstance(profile[field], dict):
            raise ValueError(f"{field} 必须是映射")
    preferences = profile.get("employer_preferences") or {}
    if not isinstance(preferences, dict) or any(
        not isinstance(preferences.get(field, []), list)
        for field in ("preferred_natures", "preferred_industries", "industrial_role_keywords")
    ):
        raise ValueError("employer_preferences 必须包含偏好列表")

    limits = profile["score_component_limits"]
    expected_components = {
        "core_direction",
        "required_skills",
        "project_evidence",
        "engineering_stack",
        "basic_criteria",
    }
    if (
        not isinstance(limits, dict)
        or set(limits) != expected_components
        or sum(limits.values()) != 100
    ):
        raise ValueError(
            "profile.yaml 的 score_component_limits 必须包含五个评分项且合计 100"
        )

    thresholds = profile["score_thresholds"]
    recommend = int(thresholds.get("recommend", 80))
    consider = int(thresholds.get("consider", 60))
    if not 0 <= consider <= recommend <= 100:
        raise ValueError("评分阈值必须满足 0 <= consider <= recommend <= 100")

    directions = [
        str(item).strip() for item in profile.get("directions", [])
        if str(item).strip()
    ]
    profile["direction"] = " / ".join(directions)
    # Derive matching from current fields; old nested values must not win.
    profile["matching"] = {
        "primary_directions": directions,
        "secondary_directions": profile.get("secondary_directions", []),
        "project_evidence": profile.get("project_evidence", []),
        "supporting_skills": profile.get("skills", []),
        "learning_targets": profile.get("learning_targets", []),
        "unverified_skills": profile.get("unverified_skills", []),
    }

    return profile

"""Persistent discovery, validation, and proposal pipeline for employer sources.

The live monitoring pool remains ``config.yaml``.  This module owns the review
buffer between public recruitment leads and that file:

* ``formal``: already present in config.yaml;
* ``candidate``: a real lead that still needs validation, data completion, or
  a crawler adapter;
* ``failed`` / ``history``: repeated failures, duplicates, and retired leads.

Discovery and validation never call an LLM.  Promotion is an explicit command
that writes a reviewable config diff; the GitHub workflow opens a pull request
for that diff instead of changing the formal pool in place.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
DEFAULT_STATE = ROOT / "data" / "company_pool.json"
DEFAULT_CONFIG = ROOT / "config.yaml"
DEFAULT_SOURCES = ROOT / "data" / "company_discovery_sources.yaml"
DEFAULT_MD_REPORT = ROOT / "outputs" / "company_pool_report.md"
DEFAULT_HTML_REPORT = ROOT / "reports" / "company-pool.html"
DEFAULT_PROPOSAL = ROOT / "outputs" / "company_pool_proposal.md"
DEFAULT_INTEGRATION_STATUS = ROOT / "outputs" / "company_integration_status.md"
SCHEMA_VERSION = 1
STATUS_START = "<!-- COMPANY_POOL_AUTOMATION_START -->"
STATUS_END = "<!-- COMPANY_POOL_AUTOMATION_END -->"


def _now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def _iso(value: datetime) -> str:
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _parse_time(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _name_key(name: str) -> str:
    normalized = re.sub(r"[\s\-—_·（）()]", "", name).casefold()
    return re.sub(r"(?:集团|股份有限公司|有限责任公司|有限公司)$", "", normalized)


def _url_key(url: str) -> str:
    parsed = urlparse(url.strip())
    return f"{parsed.netloc.casefold()}{parsed.path.rstrip('/').casefold()}"


def _source_key(url: str, crawler: str | None = None) -> str:
    from scripts.qq_docs_27_autumn_monitor import recruitment_source_identity

    return recruitment_source_identity(url, crawler) or _url_key(url)


def _platform_name(crawler: str | None, url: str = "") -> str:
    names = {
        "moka": "Moka", "beisen": "北森", "feishu": "飞书招聘",
        "hotjob": "Hotjob/e成", "iguopin": "国聘", "boe": "企业自建",
        "inovance": "企业自建", "render": "企业自建/渲染",
    }
    return names.get(str(crawler or ""), "待识别" if url else "未提供入口")


def _load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_state(path: Path = DEFAULT_STATE) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": SCHEMA_VERSION, "updated_at": None, "records": []}
    state = json.loads(path.read_text(encoding="utf-8"))
    if state.get("schema_version") != SCHEMA_VERSION or not isinstance(state.get("records"), list):
        raise ValueError(f"不支持的企业池状态格式: {path}")
    return state


def save_state(state: dict[str, Any], path: Path = DEFAULT_STATE) -> None:
    state["updated_at"] = _iso(_now())
    state["records"] = sorted(
        state.get("records") or [],
        key=lambda row: (row.get("pool_status", ""), row.get("name", ""), row.get("careers_url", "")),
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _record_indexes(records: list[dict[str, Any]]) -> tuple[dict[str, dict], dict[str, dict]]:
    by_name: dict[str, dict] = {}
    by_source: dict[str, dict] = {}
    for record in records:
        by_name.setdefault(_name_key(str(record.get("name") or "")), record)
        source = _source_key(str(record.get("careers_url") or ""), record.get("crawler"))
        if source:
            by_source.setdefault(source, record)
    return by_name, by_source


def sync_formal_pool(state: dict[str, Any], companies: list[dict[str, Any]]) -> None:
    """Make config.yaml authoritative for formal membership."""
    records = state.setdefault("records", [])
    by_name, by_source = _record_indexes(records)
    now = _iso(_now())
    formal_ids: set[int] = set()
    for company in companies:
        name = str(company.get("name") or "").strip()
        url = str(company.get("careers_url") or "").strip()
        crawler = str(company.get("crawler") or "").strip()
        source_key = _source_key(url, crawler)
        record = by_source.get(source_key) or by_name.get(_name_key(name))
        if record is None:
            record = {
                "name": name,
                "first_discovered_at": now,
                "failure_count": 0,
                "failure_history": [],
                "sources": [],
            }
            records.append(record)
        record.update({
            "name": name,
            "careers_url": url,
            "crawler": crawler,
            "platform": _platform_name(crawler, url),
            "official_status": record.get("official_status") or "existing_formal_source",
            "pool_status": "formal",
            "recruiting_status": record.get("recruiting_status") or "monitored",
            "last_config_sync_at": now,
            "industry": company.get("industry") or record.get("industry") or "",
            "company_nature": company.get("company_nature") or record.get("company_nature") or "",
            "parent_group": company.get("parent_group") or record.get("parent_group") or "",
            "promotion_ready": False,
        })
        formal_ids.add(id(record))
    for record in records:
        if record.get("pool_status") == "formal" and id(record) not in formal_ids:
            record["pool_status"] = "history"
            record["recruiting_status"] = "removed_from_config"
            record["status_reason"] = "已从正式 config.yaml 移除"


def migrate_legacy_tencent_status(
    state: dict[str, Any],
    status_path: Path = DEFAULT_INTEGRATION_STATUS,
) -> int:
    """Preserve unresolved leads written by the pre-pool onboarding code."""
    if not status_path.exists():
        return 0
    from scripts.qq_docs_27_autumn_monitor import SOURCE_URL, infer_crawler

    text = status_path.read_text(encoding="utf-8")
    match = re.search(
        r"<!-- TENCENT_DOCS_AUTO_ONBOARDING_START -->(.*?)"
        r"<!-- TENCENT_DOCS_AUTO_ONBOARDING_END -->",
        text,
        re.S,
    )
    if not match:
        return 0
    migrated = 0
    for line in match.group(1).splitlines():
        if not line.startswith("|") or line.startswith("| ---") or "腾讯文档链接" in line:
            continue
        cells = [cell.strip().strip("`") for cell in line.strip().strip("|").split("|")]
        if len(cells) < 5 or not cells[0] or cells[0] == "无":
            continue
        name, raw_url, _legacy_crawler, _status, reason = cells[:5]
        parsed = urlparse(raw_url)
        valid_url = (
            parsed.scheme in {"http", "https"}
            and bool(parsed.hostname)
            and "." in str(parsed.hostname)
            and str(parsed.hostname).isascii()
        )
        record = _merge_lead(state, {
            "name": name,
            "careers_url": raw_url if valid_url else "",
            "crawler": infer_crawler(raw_url) if valid_url else None,
            "source_id": "qq_docs_27_autumn_legacy",
            "source_url": SOURCE_URL,
            "cohort_status": "confirmed_2027",
            "evidence": reason,
        })
        if record.get("pool_status") != "formal" and not record.get("validation"):
            record["validation"] = {
                "verdict": "LEGACY-UNRESOLVED",
                "reason": reason,
                "count": 0,
                "promotion_ready": False,
            }
            record["status_reason"] = reason
            record["failure_count"] = max(1, int(record.get("failure_count") or 0))
        if not valid_url and record.get("pool_status") != "formal":
            record["pool_status"] = "history"
            record["recruiting_status"] = "invalid_source"
            record["status_reason"] = f"无效招聘链接：{raw_url}；{reason}"
        migrated += 1
    return migrated


def _merge_lead(state: dict[str, Any], lead: dict[str, Any]) -> dict[str, Any]:
    records = state.setdefault("records", [])
    by_name, by_source = _record_indexes(records)
    url = str(lead.get("careers_url") or "").strip()
    crawler = str(lead.get("crawler") or "").strip() or None
    record = by_source.get(_source_key(url, crawler)) if url else None
    record = record or by_name.get(_name_key(str(lead["name"])))
    now = _iso(_now())
    if record is None:
        record = {
            "name": lead["name"],
            "pool_status": "candidate",
            "first_discovered_at": now,
            "failure_count": 0,
            "failure_history": [],
            "sources": [],
            "promotion_ready": False,
        }
        records.append(record)
    if record.get("pool_status") not in {"formal", "history", "failed"}:
        record["pool_status"] = "candidate"
    record["last_discovered_at"] = now
    for field in ("industry", "company_nature", "parent_group"):
        if lead.get(field) and not record.get(field):
            record[field] = lead[field]
    if url and not record.get("careers_url"):
        record["careers_url"] = url
    if crawler and not record.get("crawler"):
        record["crawler"] = crawler
    record["platform"] = _platform_name(record.get("crawler"), url)
    if lead.get("cohort_status"):
        record["cohort_status"] = lead["cohort_status"]
    source = {
        "source_id": lead["source_id"],
        "source_url": lead.get("source_url") or "",
        "lead_url": url,
        "first_seen_at": now,
        "last_seen_at": now,
        "evidence": lead.get("evidence") or "",
    }
    existing = next(
        (
            item for item in record["sources"]
            if item.get("source_id") == source["source_id"] and item.get("lead_url") == url
        ),
        None,
    )
    if existing:
        existing["last_seen_at"] = now
        existing["evidence"] = source["evidence"] or existing.get("evidence") or ""
    else:
        record["sources"].append(source)
    return record


def discover_qq_docs(state: dict[str, Any], companies: list[dict[str, Any]]) -> dict[str, int]:
    """Reuse the existing 27-autumn smart-sheet parser as a lead adapter."""
    from scripts import qq_docs_27_autumn_monitor as qq

    result = qq.run(companies)
    discovered = 0
    for row in result["rows"]:
        links = list(dict.fromkeys(row.get("links") or [""]))
        for url in links:
            crawler = qq.infer_crawler(url) if url else None
            _merge_lead(state, {
                "name": row["canonical_name"],
                "careers_url": url,
                "crawler": crawler,
                "source_id": "qq_docs_27_autumn",
                "source_url": qq.SOURCE_URL,
                "cohort_status": "confirmed_2027",
                "evidence": f"{row['source_name']}：{qq.TARGET_TAG}",
            })
            discovered += 1
    return {"source_rows": len(result["rows"]), "lead_urls": discovered}


DISCOVERY_ADAPTERS: dict[str, Callable[[dict, list[dict]], dict[str, int]]] = {
    "qq_docs_27_autumn": discover_qq_docs,
}


def discover(state: dict[str, Any], companies: list[dict[str, Any]], sources_path: Path = DEFAULT_SOURCES) -> dict[str, Any]:
    source_config = _load_yaml(sources_path)
    summary: dict[str, Any] = {"sources": {}, "errors": {}}
    for source in source_config.get("sources") or []:
        if not source.get("enabled", True):
            continue
        adapter_name = str(source.get("adapter") or "")
        adapter = DISCOVERY_ADAPTERS.get(adapter_name)
        if adapter is None:
            summary["errors"][source.get("id") or adapter_name] = "未实现的发现适配器"
            continue
        try:
            summary["sources"][source.get("id") or adapter_name] = adapter(state, companies)
        except Exception as exc:  # A public source outage must not discard saved leads.
            summary["errors"][source.get("id") or adapter_name] = f"{type(exc).__name__}: {exc}"
    state["last_discovery"] = {"at": _iso(_now()), **summary}
    return summary


def _retry_after(verdict: str, failure_count: int) -> timedelta:
    if verdict == "BLOCKED":
        return timedelta(days=3)
    if verdict in {"SUSPECT-方向", "SUSPECT-社招"}:
        return timedelta(days=14)
    if verdict == "NEEDS-ADAPTER":
        return timedelta(days=30)
    if verdict == "NEEDS-URL":
        return timedelta(days=14)
    if verdict == "OK":
        return timedelta(days=30 if failure_count == 0 else 7)
    return timedelta(days=min(30, 2 ** min(failure_count, 4)))


def validate_candidates(
    state: dict[str, Any],
    *,
    limit: int = 12,
    validator: Callable[[dict], dict] | None = None,
    force: bool = False,
) -> list[dict[str, Any]]:
    from scripts.qq_docs_27_autumn_monitor import infer_crawler
    from scripts.validate_company import validate_one

    validator = validator or validate_one
    now = _now()
    candidates = []
    for record in state.get("records") or []:
        if record.get("pool_status") not in {"candidate", "failed"}:
            continue
        retry_at = _parse_time(record.get("next_retry_at"))
        if not force and retry_at and retry_at > now:
            continue
        candidates.append(record)
    candidates.sort(key=lambda row: (row.get("next_retry_at") or "", row.get("first_discovered_at") or ""))

    results = []
    for record in candidates[: max(0, limit)]:
        url = str(record.get("careers_url") or "").strip()
        crawler = str(record.get("crawler") or "").strip() or infer_crawler(url)
        if not url:
            result = {"verdict": "NEEDS-URL", "reason": "线索未提供招聘入口", "count": 0, "promotion_ready": False}
        elif not crawler:
            result = {"verdict": "NEEDS-ADAPTER", "reason": "未知招聘平台，需核实并开发爬虫", "count": 0, "promotion_ready": False}
        else:
            record["crawler"] = crawler
            record["platform"] = _platform_name(crawler, url)
            try:
                result = validator({"name": record["name"], "careers_url": url, "crawler": crawler})
            except Exception as exc:
                result = {"verdict": "ERROR", "reason": f"验证异常: {type(exc).__name__}",
                          "count": 0, "promotion_ready": False}

        verdict = str(result.get("verdict") or "ERROR")
        record["last_validated_at"] = _iso(now)
        record["validation"] = result
        record["recruiting_status"] = "active" if result.get("count", 0) else "unverified"
        hard_failure = verdict in {"EMPTY", "ERROR"}
        if hard_failure:
            record["failure_count"] = int(record.get("failure_count") or 0) + 1
            record.setdefault("failure_history", []).append({
                "at": _iso(now), "verdict": verdict, "reason": result.get("reason") or "",
            })
        elif verdict != "BLOCKED":
            record["failure_count"] = 0
        record["promotion_ready"] = bool(
            verdict == "OK"
            and result.get("promotion_ready") is True
            and int(result.get("formal_target_count") or 0) > 0
            and int(result.get("confirmed_2027_complete_count") or 0) > 0
            and crawler
            and record.get("official_status") == "verified"
            and record.get("official_evidence_url")
        )
        if record["promotion_ready"]:
            record["official_status"] = "verified"
            record["status_reason"] = "真实方向相关校招岗位及标题、地点、任职要求、原始链接均已验证"
        else:
            record["status_reason"] = result.get("reason") or (
                "岗位验证通过，企业官方归属尚待核实"
                if verdict == "OK" else verdict
            )
        if int(record.get("failure_count") or 0) >= 3:
            record["pool_status"] = "failed"
        elif record.get("pool_status") != "history":
            record["pool_status"] = "candidate"
        record["next_retry_at"] = _iso(now + _retry_after(verdict, int(record.get("failure_count") or 0)))
        results.append({"name": record["name"], **result})

    state["last_validation"] = {"at": _iso(now), "checked": len(results)}
    return results


def _proposal_entries(state: dict[str, Any], companies: list[dict[str, Any]]) -> list[dict[str, str]]:
    existing_names = {_name_key(str(company.get("name") or "")) for company in companies}
    existing_sources = {
        _source_key(str(company.get("careers_url") or ""), str(company.get("crawler") or ""))
        for company in companies
    }
    entries = []
    for record in state.get("records") or []:
        if (record.get("employer_review") or {}).get("category") == "移出正式监测":
            continue
        if (not record.get("promotion_ready") or record.get("pool_status") != "candidate"
                or record.get("official_status") != "verified"
                or not record.get("official_evidence_url")):
            continue
        if int((record.get("validation") or {}).get("confirmed_2027_complete_count") or 0) < 1:
            continue
        if not _parse_time(record.get("last_validated_at")) or (
            _now() - _parse_time(record.get("last_validated_at")) > timedelta(days=7)
        ):
            continue
        source = _source_key(str(record.get("careers_url") or ""), str(record.get("crawler") or ""))
        if _name_key(record["name"]) in existing_names or source in existing_sources:
            continue
        entries.append({
            "name": record["name"],
            "careers_url": record["careers_url"],
            "crawler": record["crawler"],
        })
    return entries


def _append_config_entries(config_path: Path, entries: list[dict[str, str]]) -> None:
    if not entries:
        return
    content = config_path.read_text(encoding="utf-8")
    block = ["", "# 企业发现系统验证通过（合并 PR 后进入正式监测池）"]
    for entry in entries:
        block.extend([
            f"- name: {json.dumps(entry['name'], ensure_ascii=False)}",
            f"  careers_url: {json.dumps(entry['careers_url'], ensure_ascii=False)}",
            f"  crawler: {entry['crawler']}",
        ])
    boundary = re.search(r"^[A-Za-z_][A-Za-z0-9_]*:\s*$", content[content.index("companies:") + len("companies:"):], re.M)
    if boundary:
        start = content.index("companies:") + len("companies:") + boundary.start()
        updated = content[:start].rstrip() + "\n" + "\n".join(block) + "\n" + content[start:]
    else:
        updated = content.rstrip() + "\n" + "\n".join(block) + "\n"
    config_path.write_text(updated, encoding="utf-8")
    yaml.safe_load(updated)


def write_proposal(
    state: dict[str, Any],
    companies: list[dict[str, Any]],
    *,
    output_path: Path = DEFAULT_PROPOSAL,
    config_path: Path | None = None,
) -> list[dict[str, str]]:
    entries = _proposal_entries(state, companies)
    lines = [
        "# 企业池自动扩展提案",
        "",
        f"生成时间：{_iso(_now())}",
        "",
        "仅包含已抓到方向相关正式校招岗位，且标题、地点、任职要求和原始链接均通过验证的来源。",
        "",
        "| 企业 | 招聘入口 | 爬虫 |",
        "| --- | --- | --- |",
    ]
    for entry in entries:
        lines.append(f"| {entry['name']} | {entry['careers_url']} | `{entry['crawler']}` |")
    if not entries:
        lines.append("| 无 | 本轮没有满足自动提案条件的新来源 | - |")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    if config_path:
        _append_config_entries(config_path, entries)
    return entries


def _database_metrics(db_path: Path, formal_names: list[str]) -> dict[str, int]:
    if not db_path.exists():
        return {"companies_with_jobs": 0, "jobs": 0, "confirmed_2027": 0,
                "formal_with_jobs": 0, "formal_jobs": 0, "formal_confirmed_2027": 0}
    conn = sqlite3.connect(db_path)
    try:
        columns = {row[1] for row in conn.execute("PRAGMA table_info(jobs)")}
        companies = conn.execute("SELECT COUNT(DISTINCT company) FROM jobs").fetchone()[0]
        jobs = conn.execute("SELECT COUNT(*) FROM jobs").fetchone()[0]
        confirmed = 0
        formal_with_jobs = formal_jobs = formal_confirmed = 0
        if {"cohort", "cohort_status"}.issubset(columns):
            confirmed = conn.execute(
                "SELECT COUNT(*) FROM jobs WHERE cohort = 2027 AND cohort_status = 'confirmed'"
            ).fetchone()[0]
        if formal_names:
            marks = ",".join("?" for _ in formal_names)
            formal_with_jobs = conn.execute(
                f"SELECT COUNT(DISTINCT company) FROM jobs WHERE company IN ({marks})", formal_names
            ).fetchone()[0]
            formal_jobs = conn.execute(
                f"SELECT COUNT(*) FROM jobs WHERE company IN ({marks})", formal_names
            ).fetchone()[0]
            if {"cohort", "cohort_status"}.issubset(columns):
                formal_confirmed = conn.execute(
                    f"SELECT COUNT(*) FROM jobs WHERE company IN ({marks}) "
                    "AND cohort = 2027 AND cohort_status = 'confirmed'",
                    formal_names,
                ).fetchone()[0]
        return {"companies_with_jobs": companies, "jobs": jobs, "confirmed_2027": confirmed,
                "formal_with_jobs": formal_with_jobs, "formal_jobs": formal_jobs,
                "formal_confirmed_2027": formal_confirmed}
    finally:
        conn.close()


def _metrics(state: dict[str, Any], db_path: Path) -> dict[str, int]:
    records = state.get("records") or []
    formal_names = [row["name"] for row in records if row.get("pool_status") == "formal"]
    metrics = {
        "formal": sum(row.get("pool_status") == "formal" for row in records),
        "candidate": sum(row.get("pool_status") == "candidate" for row in records),
        "promotion_ready": sum(bool(row.get("promotion_ready")) for row in records),
        "failed": sum(row.get("pool_status") == "failed" for row in records),
        "history": sum(row.get("pool_status") == "history" for row in records),
        "needs_adapter": sum(
            row.get("pool_status") == "candidate" and not row.get("crawler")
            for row in records
        ),
    }
    return {**metrics, **_database_metrics(db_path, formal_names)}


def generate_reports(
    state: dict[str, Any],
    *,
    db_path: Path = ROOT / "data" / "jobs.db",
    md_path: Path = DEFAULT_MD_REPORT,
    html_path: Path = DEFAULT_HTML_REPORT,
    integration_status_path: Path | None = DEFAULT_INTEGRATION_STATUS,
    sources_path: Path = DEFAULT_SOURCES,
) -> dict[str, int]:
    metrics = _metrics(state, db_path)
    records = state.get("records") or []
    generated = _iso(_now())
    source_config = _load_yaml(sources_path) if sources_path.exists() else {}
    watchlist = source_config.get("watchlist") or []
    metrics["watchlist"] = len(watchlist)
    rows = []
    for record in records:
        validation = record.get("validation") or {}
        rows.append([
            record.get("name") or "",
            record.get("pool_status") or "",
            record.get("industry") or "",
            record.get("platform") or _platform_name(record.get("crawler"), record.get("careers_url") or ""),
            record.get("crawler") or "待识别",
            validation.get("verdict") or "—",
            record.get("cohort_status") or "待核实",
            record.get("last_validated_at") or "—",
            record.get("next_retry_at") or "—",
            record.get("status_reason") or "",
            record.get("careers_url") or "",
        ])
    md = [
        "# 招聘企业发现与监测池报告", "", f"生成时间：{generated}", "",
        f"- 正式监测池：{metrics['formal']} 家",
        f"- 候选企业池：{metrics['candidate']} 家，其中 {metrics['promotion_ready']} 家可生成审核 PR",
        f"- 失败来源：{metrics['failed']} 家；历史记录：{metrics['history']} 家",
        f"- 待开发平台适配器：{metrics['needs_adapter']} 个来源",
        f"- 正式池历史抓取：{metrics['formal_with_jobs']}/{metrics['formal']} 家有岗位，累计 {metrics['formal_jobs']} 条，其中 {metrics['formal_confirmed_2027']} 条确认 2027 届",
        f"- 招聘数据库全量历史：{metrics['companies_with_jobs']} 家企业、{metrics['jobs']} 条岗位、{metrics['confirmed_2027']} 条确认 2027 届岗位",
        "", "| 企业 | 池状态 | 行业 | 平台 | 爬虫 | 最近裁决 | 届别 | 最近验证 | 下次重试 | 原因 | 招聘入口 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        safe = [str(value).replace("|", "\\|").replace("\n", " ") for value in row]
        md.append("| " + " | ".join(safe) + " |")
    md.extend(["", f"## 搜索关注名单（{len(watchlist)} 家，不等于已发现候选）", "", "| 企业 | 行业 |", "| --- | --- |"])
    md.extend(f"| {item.get('name', '')} | {item.get('industry', '')} |" for item in watchlist)
    md_path.parent.mkdir(parents=True, exist_ok=True)
    md_path.write_text("\n".join(md) + "\n", encoding="utf-8")

    if integration_status_path is not None:
        pending = [row for row in records if row.get("pool_status") in {"candidate", "failed"}]
        section = [
            "## 企业发现与候选池（自动维护）", STATUS_START,
            f"正式池 **{metrics['formal']}** 家；候选 **{metrics['candidate']}** 家；"
            f"可提案 **{metrics['promotion_ready']}** 家；失败 **{metrics['failed']}** 家。",
            "", "| 企业 | 状态 | 爬虫 | 最近裁决 | 原因 | 招聘入口 |",
            "| --- | --- | --- | --- | --- | --- |",
        ]
        for record in pending:
            validation = record.get("validation") or {}
            section.append(
                f"| {record.get('name', '')} | {record.get('pool_status', '')} | "
                f"`{record.get('crawler') or '待识别'}` | {validation.get('verdict') or '待验证'} | "
                f"{str(record.get('status_reason') or '').replace('|', '/')} | {record.get('careers_url') or '—'} |"
            )
        if not pending:
            section.append("| 无 | - | - | - | 当前无候选或失败来源 | - |")
        section.extend([STATUS_END, ""])
        managed = "\n".join(section)
        existing = (
            integration_status_path.read_text(encoding="utf-8")
            if integration_status_path.exists() else "# 公司招聘接入状态\n"
        )
        legacy_pattern = re.compile(
            r"\n*## 腾讯文档自动接入状态（自动维护）\n"
            r"<!-- TENCENT_DOCS_AUTO_ONBOARDING_START -->.*?"
            r"<!-- TENCENT_DOCS_AUTO_ONBOARDING_END -->\n?",
            re.S,
        )
        existing = legacy_pattern.sub("\n", existing)
        pattern = re.compile(
            rf"## 企业发现与候选池（自动维护）\n{re.escape(STATUS_START)}.*?{re.escape(STATUS_END)}\n?",
            re.S,
        )
        updated = pattern.sub(managed, existing) if pattern.search(existing) else existing.rstrip() + "\n\n" + managed
        integration_status_path.parent.mkdir(parents=True, exist_ok=True)
        integration_status_path.write_text(updated, encoding="utf-8")

    cards = "".join(
        f'<div class="metric"><strong>{value}</strong><span>{label}</span></div>'
        for label, value in [
            ("正式池", metrics["formal"]), ("候选池", metrics["candidate"]),
            ("可提案", metrics["promotion_ready"]), ("失败", metrics["failed"]),
            ("正式池有岗位", metrics["formal_with_jobs"]), ("正式池岗位", metrics["formal_jobs"]),
            ("确认27届", metrics["formal_confirmed_2027"]), ("搜索关注", metrics["watchlist"]),
        ]
    )
    body_rows = "".join(
        "<tr>" + "".join(
            "<td>" + ('<a rel="noopener" href="' + html.escape(row[10], quote=True) + '">原始入口</a>'
                      if index == 10 and row[10] else html.escape(str(value))) + "</td>"
            for index, value in enumerate(row)
        ) + "</tr>"
        for row in rows
    )
    watchlist_rows = "".join(
        f"<tr><td>{html.escape(str(item.get('name') or ''))}</td><td>{html.escape(str(item.get('industry') or ''))}</td></tr>"
        for item in watchlist
    )
    page = f"""<!doctype html><html lang="zh-CN"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>招聘企业池报告</title>
<style>body{{font-family:system-ui,sans-serif;margin:0;background:#f4f7f6;color:#233}}main{{max-width:1500px;margin:auto;padding:24px}}h1{{margin:0 0 6px}}.meta{{color:#687875}}.metrics{{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin:22px 0}}.metric{{background:white;border:1px solid #dce7e4;padding:16px}}.metric strong{{font-size:28px;display:block;color:#087f73}}.metric span{{color:#687875}}.table{{overflow:auto;background:white;border:1px solid #dce7e4}}table{{border-collapse:collapse;width:100%;min-width:1300px}}th,td{{padding:10px;border-bottom:1px solid #e8efed;text-align:left;vertical-align:top}}th{{position:sticky;top:0;background:#eef5f3}}a{{color:#087f73}}</style></head>
<body><main><h1>招聘企业发现与监测池</h1><div class="meta">生成时间 {html.escape(generated)} · 本流程不调用 DeepSeek</div><div class="metrics">{cards}</div><div class="table"><table><thead><tr><th>企业</th><th>池状态</th><th>行业</th><th>平台</th><th>爬虫</th><th>最近裁决</th><th>届别</th><th>最近验证</th><th>下次重试</th><th>原因</th><th>招聘入口</th></tr></thead><tbody>{body_rows}</tbody></table></div><h2>搜索关注名单（不等于已发现候选）</h2><div class="table"><table><thead><tr><th>企业</th><th>行业</th></tr></thead><tbody>{watchlist_rows}</tbody></table></div></main></body></html>"""
    html_path.parent.mkdir(parents=True, exist_ok=True)
    html_path.write_text(page, encoding="utf-8")
    return metrics


def _paths(args: argparse.Namespace) -> tuple[Path, Path, Path]:
    return Path(args.state), Path(args.config), Path(args.sources)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="招聘企业发现、验证与监测池管理")
    parser.add_argument("command", choices=["sync", "discover", "validate", "run", "propose", "report"])
    parser.add_argument("--state", default=str(DEFAULT_STATE))
    parser.add_argument("--config", default=str(DEFAULT_CONFIG))
    parser.add_argument("--sources", default=str(DEFAULT_SOURCES))
    parser.add_argument("--limit", type=int, default=12)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--write-config", action="store_true")
    args = parser.parse_args(argv)

    state_path, config_path, sources_path = _paths(args)
    state = load_state(state_path)
    config = _load_yaml(config_path)
    companies = config.get("companies") or []
    sync_formal_pool(state, companies)
    migrate_legacy_tencent_status(state)

    if args.command in {"discover", "run"}:
        print(json.dumps(discover(state, companies, sources_path), ensure_ascii=False))
    if args.command in {"validate", "run"}:
        results = validate_candidates(state, limit=args.limit, force=args.force)
        print(f"验证 {len(results)} 个候选来源")
    if args.command in {"sync", "discover", "validate", "run"}:
        save_state(state, state_path)
    if args.command in {"report", "run"}:
        metrics = generate_reports(state)
        print(json.dumps(metrics, ensure_ascii=False))
    if args.command == "propose":
        entries = write_proposal(
            state, companies,
            config_path=config_path if args.write_config else None,
        )
        print(f"提案 {len(entries)} 家；写配置={args.write_config}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

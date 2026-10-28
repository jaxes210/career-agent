import json
import sqlite3
from datetime import datetime, timezone

import yaml

from scripts import company_pool
from scripts.validate_company import _field_coverage


def _state():
    return {"schema_version": 1, "updated_at": None, "records": []}


def test_sync_formal_pool_uses_config_as_authority():
    state = _state()
    companies = [{
        "name": "环保集团",
        "careers_url": "https://green.zhiye.com/campus/jobs",
        "crawler": "beisen",
        "industry": "环保",
    }]

    company_pool.sync_formal_pool(state, companies)

    assert len(state["records"]) == 1
    assert state["records"][0]["pool_status"] == "formal"
    assert state["records"][0]["industry"] == "环保"


def test_validator_field_coverage_requires_location_requirements_and_original_link():
    coverage = _field_coverage([
        {
            "title": "催化剂研发工程师",
            "city": "宁波",
            "jd_url": "https://jobs.example.com/1",
            "jd_raw": "岗位职责：开展催化剂研发。任职要求：环境工程、化学工程或材料相关专业硕士。",
        },
        {"title": "化工工艺工程师", "city": "", "jd_url": "", "jd_raw": ""},
    ])

    assert coverage == {"title": 2, "location": 1, "original_url": 1, "requirements": 1}


def test_legacy_pending_sources_are_migrated_without_trusting_old_render_guess(tmp_path):
    status = tmp_path / "status.md"
    status.write_text(
        "<!-- TENCENT_DOCS_AUTO_ONBOARDING_START -->\n"
        "| 公司 | 腾讯文档链接 | 识别爬虫 | 状态 | 原因 |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| 新平台企业 | https://careers.example.com/campus | `render` | 待人工接入 | render 返回 0 个岗位 |\n"
        "<!-- TENCENT_DOCS_AUTO_ONBOARDING_END -->\n",
        encoding="utf-8",
    )
    state = _state()

    assert company_pool.migrate_legacy_tencent_status(state, status) == 1

    record = state["records"][0]
    assert record["pool_status"] == "candidate"
    assert not record.get("crawler")
    assert record["validation"]["verdict"] == "LEGACY-UNRESOLVED"


def test_merge_lead_deduplicates_same_platform_tenant():
    state = _state()
    base = {
        "name": "材料公司",
        "crawler": "moka",
        "source_id": "source-a",
        "source_url": "https://source.example/list",
        "cohort_status": "confirmed_2027",
        "evidence": "27届秋招",
    }
    company_pool._merge_lead(state, {
        **base,
        "careers_url": "https://app.mokahr.com/campus_apply/material/100#/jobs",
    })
    company_pool._merge_lead(state, {
        **base,
        "source_id": "source-b",
        "careers_url": "https://app.mokahr.com/campus_apply/material/200#/jobs",
    })

    assert len(state["records"]) == 1
    assert len(state["records"][0]["sources"]) == 2


def test_candidate_requires_all_job_fields_before_promotion(monkeypatch):
    state = _state()
    company_pool._merge_lead(state, {
        "name": "催化材料公司",
        "careers_url": "https://catalyst.zhiye.com/campus/jobs",
        "crawler": "beisen",
        "source_id": "test",
        "source_url": "https://source.example",
        "cohort_status": "pending",
    })

    results = company_pool.validate_candidates(
        state,
        validator=lambda entry: {
            "verdict": "OK",
            "count": 3,
            "formal_target_count": 2,
            "promotion_ready": False,
            "field_coverage": {"title": 2, "location": 2, "original_url": 2, "requirements": 0},
            "reason": "关键字段待补全: requirements",
        },
        force=True,
    )

    assert results[0]["verdict"] == "OK"
    assert state["records"][0]["pool_status"] == "candidate"
    assert state["records"][0]["promotion_ready"] is False


def test_fully_validated_candidate_becomes_proposal_ready():
    state = _state()
    company_pool._merge_lead(state, {
        "name": "水处理技术院",
        "careers_url": "https://water.zhiye.com/campus/jobs",
        "crawler": "beisen",
        "source_id": "test",
        "source_url": "https://source.example",
        "cohort_status": "pending",
    })

    state["records"][0].update(official_status="verified", official_evidence_url="https://official.example/careers")
    company_pool.validate_candidates(
        state,
        validator=lambda entry: {
            "verdict": "OK",
            "count": 4,
            "formal_target_count": 3,
            "confirmed_2027_complete_count": 1,
            "promotion_ready": True,
            "field_coverage": {"title": 3, "location": 3, "original_url": 3, "requirements": 2},
            "reason": "",
        },
        force=True,
    )

    record = state["records"][0]
    assert record["promotion_ready"] is True
    assert record["cohort_status"] == "pending"
    assert "真实方向相关" in record["status_reason"]


def test_unknown_platform_stays_candidate_without_guessed_crawler():
    state = _state()
    company_pool._merge_lead(state, {
        "name": "未知平台公司",
        "careers_url": "https://careers.example.com/jobs",
        "crawler": None,
        "source_id": "test",
        "source_url": "https://source.example",
    })

    company_pool.validate_candidates(state, force=True)

    record = state["records"][0]
    assert not record.get("crawler")
    assert record["validation"]["verdict"] == "NEEDS-ADAPTER"
    assert record["pool_status"] == "candidate"


def test_three_empty_validations_move_source_to_failed_history():
    state = _state()
    company_pool._merge_lead(state, {
        "name": "失效来源",
        "careers_url": "https://dead.zhiye.com/campus/jobs",
        "crawler": "beisen",
        "source_id": "test",
        "source_url": "https://source.example",
    })
    validator = lambda entry: {
        "verdict": "EMPTY", "count": 0, "formal_target_count": 0,
        "promotion_ready": False, "reason": "0 岗",
    }

    for _ in range(3):
        company_pool.validate_candidates(state, validator=validator, force=True)

    assert state["records"][0]["pool_status"] == "failed"
    assert len(state["records"][0]["failure_history"]) == 3


def test_proposal_writes_reviewable_config_diff(tmp_path):
    state = _state()
    state["records"].append({
        "official_status": "verified",
        "official_evidence_url": "https://official.example/careers",
        "last_validated_at": company_pool._iso(company_pool._now()),
        "validation": {"confirmed_2027_complete_count": 1},
        "name": "环境研究院",
        "careers_url": "https://env.zhiye.com/campus/jobs",
        "crawler": "beisen",
        "pool_status": "candidate",
        "promotion_ready": True,
    })
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "companies:\n- name: 已有公司\n  careers_url: https://old.zhiye.com/campus/jobs\n"
        "  crawler: beisen\ndeepseek:\n  model: test\n",
        encoding="utf-8",
    )
    proposal = tmp_path / "proposal.md"

    entries = company_pool.write_proposal(
        state,
        yaml.safe_load(config_path.read_text(encoding="utf-8"))["companies"],
        output_path=proposal,
        config_path=config_path,
    )

    assert [entry["name"] for entry in entries] == ["环境研究院"]
    parsed = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert [company["name"] for company in parsed["companies"]] == ["已有公司", "环境研究院"]
    assert "环境研究院" in proposal.read_text(encoding="utf-8")


def test_reports_include_database_and_pool_metrics(tmp_path):
    state = _state()
    state["records"] = [
        {"name": "正式企业", "pool_status": "formal", "careers_url": "https://a.example"},
        {"name": "候选企业", "pool_status": "candidate", "promotion_ready": False},
    ]
    db_path = tmp_path / "jobs.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE jobs (company TEXT, cohort INTEGER, cohort_status TEXT)")
    conn.executemany(
        "INSERT INTO jobs VALUES (?, ?, ?)",
        [("正式企业", 2027, "confirmed"), ("正式企业", 2027, "unknown")],
    )
    conn.commit()
    conn.close()

    metrics = company_pool.generate_reports(
        state,
        db_path=db_path,
        md_path=tmp_path / "pool.md",
        html_path=tmp_path / "pool.html",
        integration_status_path=tmp_path / "integration.md",
        sources_path=tmp_path / "missing-sources.yaml",
    )

    assert metrics["formal"] == 1
    assert metrics["jobs"] == 2
    assert metrics["confirmed_2027"] == 1
    assert "招聘数据库全量历史：1 家企业、2 条岗位" in (tmp_path / "pool.md").read_text(encoding="utf-8")
    assert "候选企业" in (tmp_path / "integration.md").read_text(encoding="utf-8")


def test_jobs_alone_do_not_prove_official_employer_identity():
    state = _state()
    company_pool._merge_lead(state, {
        'name': '未核实企业', 'careers_url': 'https://unknown.zhiye.com/campus/jobs',
        'crawler': 'beisen', 'source_id': 'public-list', 'source_url': 'https://list.example',
    })
    company_pool.validate_candidates(state, force=True, validator=lambda entry: {
        'verdict': 'OK', 'count': 1, 'formal_target_count': 1, 'promotion_ready': True,
    })
    assert not state['records'][0]['promotion_ready']
    assert '官方归属' in state['records'][0]['status_reason']


def test_discovery_does_not_reset_failed_source_retry_state():
    state = _state()
    lead = {'name': '失败企业', 'careers_url': 'https://dead.zhiye.com/campus/jobs',
            'crawler': 'beisen', 'source_id': 'public-list', 'source_url': 'https://list.example'}
    record = company_pool._merge_lead(state, lead)
    record.update(pool_status='failed', failure_count=3, next_retry_at='2099-01-01T00:00:00Z')
    company_pool._merge_lead(state, lead)
    assert record['failure_count'] == 3
    assert company_pool.validate_candidates(state) == []

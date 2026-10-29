"""2027 environmental/chemical profile regressions; all model calls are mocked."""
import json
from pathlib import Path
from unittest.mock import patch

import pytest

import analyzer
import db
import job_filters
import main
import reporter
from profile_config import load_profile

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def profile():
    return load_profile(ROOT / 'profile.yaml')


def job(title='催化剂研发工程师', body=None):
    return {
        'company': '样本企业', 'title': title, 'city': '上海',
        'jd_raw': body if body is not None else (
            '岗位职责：开展催化剂研发，进行催化材料制备与性能评价，使用XRD、XPS、SEM进行材料表征。'
            '任职要求：环境工程、化学工程、材料专业硕士，2027届毕业，有科研实验经验。' * 2
        ),
        'job_type': '校招', 'cohort': 2027, 'cohort_status': 'confirmed',
        'jd_url': 'https://example.com/campus/job/chemical', 'published_at': '', 'source': '样本企业',
    }


@pytest.mark.parametrize('title', [
    '化工工艺工程师', '环境工程师', '材料研发工程师', '催化剂研发工程师',
    '生产技术岗', '化学分析工程师', '质量检测工程师', '水处理工程师',
    '生产运行岗', '环保技术管理', '化工技术支持', '工艺优化工程师',
])
def test_target_roles_survive_all_local_gates(profile, title):
    item = job(title)
    assert not job_filters.is_direction_out_job(item, profile)
    assert analyzer.local_screening_tier(item, profile) == 'A'
    assert analyzer.analysis_screening_tier(item, profile) == 'A'
    assert analyzer._can_hydrate_to_tier_a({**item, 'jd_raw': ''}, profile)
    with patch('analyzer.call_deepseek_api', side_effect=AssertionError('unnecessary API')):
        assert analyzer.classify_job_tiers([item], profile) == ['A']


@pytest.mark.parametrize('title', ['C++软件开发工程师', '前端开发工程师', 'AI研发工程师', 'Java研发工程师', '机器人视觉工程师'])
def test_explicit_software_exclusions_cannot_be_overridden_by_model(profile, title):
    item = job(title)
    assert job_filters.is_direction_out_job(item, profile)
    with patch('analyzer.call_deepseek_api') as call:
        assert analyzer.classify_job_tiers([item], profile) == ['C']
    call.assert_not_called()


@pytest.mark.parametrize(('title', 'body', 'expected'), [
    ('SRE工程师【2027届】', '', False),
    ('推荐研发工程师【2027届】', '', False),
    ('基础架构研发工程师【2027届】', '', False),
    ('化工工艺工程师', '', True),
    ('研发工程师', '招聘工业催化、化学工程专业硕士', True),
    ('研发工程师', '负责服务器运维与网络安全', False),
])
def test_report_requires_industrial_profile_evidence(profile, title, body, expected):
    assert job_filters.is_report_relevant_job({'title': title, 'jd_raw': body}, profile) is expected


def test_profile_directions_and_configured_roles_override_generic_rejections(profile):
    profile = {**profile, 'target_roles': [{'name': '工业技术运营', 'keywords': ['技术运营']}],
               'directions': ['工业技术运营'], 'excluded_title_keywords': []}
    assert not job_filters.is_direction_out_job(job('技术运营工程师'), profile)
    assert analyzer.local_screening_tier(job('技术运营工程师'), profile) == 'A'


@pytest.mark.parametrize(('body', 'expected'), [
    ('必须达到大学英语六级425分及以上', '不符合'),
    ('英语要求：CET-6 >= 425', '不符合'),
    ('英语六级成绩不低于500分', '不符合'),
    ('要求大学英语四级425分及以上', '符合'),
    ('硕士，环境工程专业', '待核实'),
    ('英语六级425分以上优先', '待核实'),
    ('要求六级425分以上或雅思6.0', '待核实'),
    ('要求六级425分以上，可用同等英语能力证明替代', '待核实'),
    ('不要求六级425分以上', '待核实'),
    ('六级425分', '待核实'),
])
def test_english_is_conservative(profile, body, expected):
    assert job_filters.english_eligibility(job(body=body), profile)['status'] == expected


def test_missing_candidate_score_does_not_assume_failure(profile):
    profile.pop('english')
    assert job_filters.english_eligibility(job(body='要求六级425分以上'), profile)['status'] == '待核实'


def test_hard_english_failure_does_not_call_model(profile):
    item = job(body=job()['jd_raw'] + '必须达到英语六级425分以上。')
    with patch('analyzer.call_deepseek_api') as call:
        result = analyzer.analyze_job(item, profile)
    call.assert_not_called()
    assert result['recommendation'] == '不推荐'
    assert result['english_eligibility']['status'] == '不符合'
    assert any('英语条件：不符合' in gap for gap in result['gaps'])


def test_confirmed_2027_sparse_target_hydrates_before_pro(profile, tmp_path):
    conn = db.init_db(tmp_path / 'test.db')
    item = job(body='催化剂研发工程师')
    _, item['id'] = db.upsert_job(conn, item)
    response = {
        'score_breakdown': dict(profile['score_component_limits']),
        'evidence_level': 'direct',
        'evidence': [{'jd_requirement': '催化剂研发', 'profile_evidence': '催化剂制备',
                      'relation': 'direct', 'requirement_type': 'core'}],
        'advantages': ['催化材料研究'], 'gaps': [], 'summary': '研发方向相关',
    }
    with patch('job_details.fetch_full_job_description', return_value=job()['jd_raw']) as fetch, \
         patch('analyzer.call_deepseek_api', return_value=json.dumps(response)) as call:
        results = analyzer.batch_analyze([item], profile, conn, max_jobs=1, max_jobs_per_day=1)
    assert len(results) == 1
    fetch.assert_called_once()
    call.assert_called_once()
    assert results[0]['analysis']['recommendation'] != '不推荐'
    conn.close()


def test_no_hydration_or_models_before_cohort_confirmation(profile, tmp_path):
    conn = db.init_db(tmp_path / 'cohort.db')
    item = {**job(), 'cohort_status': 'unknown'}
    _, item['id'] = db.upsert_job(conn, item)
    with patch('job_details.fetch_full_job_description') as fetch, patch('analyzer.call_deepseek_api') as call:
        assert analyzer.batch_analyze([item], profile, conn) == []
    fetch.assert_not_called()
    call.assert_not_called()
    conn.close()


def test_screening_cache_changes_with_profile_model_and_rules(profile, tmp_path, monkeypatch):
    conn = db.init_db(tmp_path / 'cache.db')
    item = job()
    version = analyzer.screening_cache_version(profile, 'flash')
    db.save_screening_tiers(conn, [(item, 'C')], version)
    assert db.get_screening_tier(conn, item, version) == 'C'
    for field, value in [('directions', ['新方向']), ('english', {'cet6_score': 500}),
                         ('employer_preferences', {}), ('target_roles', ['其他岗位'])]:
        changed = {**profile, field: value}
        assert db.get_screening_tier(conn, item, analyzer.screening_cache_version(changed, 'flash')) is None
    assert db.get_screening_tier(conn, item, analyzer.screening_cache_version(profile, 'another-model')) is None
    monkeypatch.setattr(analyzer, 'SCREENING_VERSION', 'new-rules')
    assert db.get_screening_tier(conn, item, analyzer.screening_cache_version(profile, 'flash')) is None
    conn.close()


def test_stale_pro_scores_not_displayed_and_need_reanalysis(profile, tmp_path):
    conn = db.init_db(tmp_path / 'analysis.db')
    item = job()
    _, item['id'] = db.upsert_job(conn, item)
    old_profile = {**profile, 'directions': ['软件开发']}
    old = {'match_score': 99, 'advantages': [], 'gaps': [], 'summary': '旧画像评分',
           'recommendation': '推荐', **analyzer.analysis_metadata(item, old_profile, 'pro')}
    db.save_analysis(conn, item['id'], old)
    assert analyzer.needs_analysis(conn, item, profile, 'pro')
    current, _, _, _ = reporter._filter_items(db.get_active_report_data(conn)['items'])
    assert current[0]['analysis'] is None
    conn.close()


def test_employer_preference_is_small_tie_break_not_gate(profile):
    normal = job()
    preferred = {**normal, 'company_nature': '央企', 'industry': '化工制造'}
    assert analyzer._analysis_priority(preferred, profile) > analyzer._analysis_priority(normal, profile)
    assert analyzer.local_screening_tier(normal, profile) == analyzer.local_screening_tier(preferred, profile)
    assert not job_filters.is_direction_out_job(normal, profile)
    no_fit = {**preferred, 'title': '销售代表', 'jd_raw': ''}
    assert analyzer.local_screening_tier(no_fit, profile) == 'C'


def test_configured_employer_metadata_survives_to_queue():
    jobs = [job()]
    main._attach_company_metadata(jobs, [{'name': '样本企业', 'company_nature': '国企', 'industry': '环保'}])
    assert jobs[0]['company_nature'] == '国企'


def test_report_payload_exposes_english_for_unscored_jobs(profile):
    rows = reporter._jobs_payload([{'job': job(body='要求六级425分以上'), 'analysis': None}])
    assert rows[0]['english'] == '不符合'
    assert rows[0]['e'] is False
    assert reporter._jobs_payload([{'job': job(), 'analysis': None}])[0]['english'] == '待核实'


def test_profile_rebuilds_derived_matching_instead_of_using_old_software_context(profile, tmp_path):
    import yaml
    profile['matching'] = {'primary_directions': ['C++软件开发']}
    path = tmp_path / 'profile.yaml'
    path.write_text(yaml.safe_dump(profile, allow_unicode=True), encoding='utf-8')
    loaded = load_profile(path)
    assert loaded['matching']['primary_directions'] == loaded['directions']
    assert 'C++软件开发' not in analyzer._profile_context(loaded)


def test_materials_rd_category_is_not_software():
    assert job_filters.job_category(job('材料研发工程师')) == 'materials_catalysis'
    assert job_filters.job_category(job('化工工艺工程师')) == 'chemical_process'
    assert job_filters.job_category(job('化学分析工程师')) == 'chemical_quality'


def test_webapp_cache_signature_changes_when_profile_changes(tmp_path, monkeypatch):
    import webapp
    path = tmp_path / 'profile.yaml'
    path.write_text('directions: [环境工程]', encoding='utf-8')
    monkeypatch.setenv('PROFILE_PATH', str(path))
    before = webapp._data_signature()
    path.write_text('directions: [环境工程, 化工工艺]', encoding='utf-8')
    assert webapp._data_signature() != before


@pytest.mark.parametrize('english', [
    {'cet6_score': 800}, {'cet6_below_425': 'yes'},
    {'cet6_below_425': True, 'cet6_score': 500},
])
def test_profile_rejects_invalid_english_conditions(profile, tmp_path, english):
    import yaml
    profile['english'] = english
    path = tmp_path / 'profile.yaml'
    path.write_text(yaml.safe_dump(profile, allow_unicode=True), encoding='utf-8')
    with pytest.raises(ValueError):
        load_profile(path)

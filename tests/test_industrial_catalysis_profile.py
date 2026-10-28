import copy
import pytest
import analyzer
import job_filters
from profile_config import load_profile


def test_real_education_and_publication_status():
    profile = load_profile()
    assert profile['major'] == '工业催化'
    assert profile['education'][1]['degree_awarding'] is False
    assert profile['education'][2]['major'] == '生物工程'
    assert '未录用' in profile['publications'][0]['status']
    assert profile['english']['cet4_score'] == 527


@pytest.mark.parametrize('title', ['催化剂研发工程师', '化工工艺工程师', '日化配方研发', '表面活性剂研发', '材料研发工程师', '环境工程师', '工业水处理技术', '生产技术工程师'])
def test_related_roles_retained(title):
    assert not job_filters.is_direction_out_job({'title': title}, load_profile())


@pytest.mark.parametrize('body,status', [
    ('要求英语四级', '符合'), ('英语四级达到500分', '符合'),
    ('英语四级要求550分', '不符合'), ('要求英语六级达到425分', '不符合'),
    ('要求六级425分或雅思6分', '待核实'), ('开展催化剂研发', '待核实'),
])
def test_english(body, status):
    assert job_filters.english_eligibility({'jd_raw': body}, load_profile())['status'] == status


def test_phd_and_major_eligibility():
    profile = load_profile()
    assert job_filters.job_eligibility({'title': '博士后研究员'}, profile)['status'] == '不符合'
    result = job_filters.job_eligibility({'jd_raw': '硕士，化学工程与技术专业'}, profile)
    assert result['status'] == '待核实'
    assert result['checks']['major']['status'] == '待核实'


def test_profile_change_invalidates_cache():
    profile = load_profile()
    changed = copy.deepcopy(profile)
    changed['education'][0]['major'] = '其他专业'
    assert analyzer.screening_cache_version(profile, 'test') != analyzer.screening_cache_version(changed, 'test')

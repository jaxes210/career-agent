from pathlib import Path
import yaml
from scripts.audit_industrial_company_pool import assess_company
from scripts import company_pool

POLICY = yaml.safe_load((Path(__file__).resolve().parents[1] / 'data/company_relevance_policy.yaml').read_text())


def company(name='制造企业', industry='先进制造'):
    return {'name':name, 'industry':industry, 'careers_url':'https://official.example/campus','crawler':'beisen'}


def test_other_industry_with_chemical_evidence_is_retained():
    result = assess_company(company(), [{'title':'材料分析工程师','jd_raw':'材料化学、化学工程专业硕士'}], POLICY)
    assert result['category'] == '保留：潜在匹配'
    assert len(result['relevant_jobs']) == 1


def test_no_jobs_does_not_cause_deletion():
    assert assess_company(company(), [], POLICY)['category'] == '保留：潜在匹配'


def test_direct_chemical_industry_and_jobs():
    result = assess_company(company(industry='精细化工'), [{'title':'催化剂研发工程师'}], POLICY)
    assert result['category'] == '保留：高度匹配'


def test_ai_optimization_and_data_quality_are_not_chemical_evidence():
    result = assess_company(company(), [{'title':'强化学习算法优化工程师'}, {'title':'数据质量工程师'}], POLICY)
    assert result['relevant_jobs'] == []


def test_reviewed_removal_is_reversible_and_not_applied_with_positive_evidence():
    c = company('中国星网网络应用研究院')
    assert assess_company(c, [{'title':'网络安全工程师'}], POLICY)['category'] == '移出正式监测'
    assert assess_company(c, [{'title':'材料研发工程师'}], POLICY)['category'] == '保留：潜在匹配'


def test_removed_employer_cannot_be_automatically_reproposed():
    record = {'name':'已移除', 'pool_status':'candidate', 'promotion_ready':True,
              'official_status':'verified','official_evidence_url':'https://official.example',
              'careers_url':'https://tenant.zhiye.com/campus/jobs', 'crawler':'beisen',
              'last_validated_at':company_pool._iso(company_pool._now()),
              'employer_review':{'category':'移出正式监测'}}
    assert company_pool._proposal_entries({'records':[record]}, []) == []


def test_unconfirmed_cohort_is_kept_as_candidate_not_proposed():
    record = {'name':'届别待确认', 'pool_status':'candidate', 'promotion_ready':True,
              'official_status':'verified','official_evidence_url':'https://official.example',
              'careers_url':'https://tenant.zhiye.com/campus/jobs', 'crawler':'beisen',
              'last_validated_at':company_pool._iso(company_pool._now()),
              'validation':{'formal_target_count':2,'confirmed_2027_complete_count':0}}
    assert company_pool._proposal_entries({'records':[record]}, []) == []

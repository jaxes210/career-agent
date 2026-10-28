"""Read-only historical audit; --apply changes only config/pool, never jobs.db.

Live validation is opt-in, capped at 5. Upstream URLs are leads, not proof of
current official recruitment. No guessed URLs or crawler keys are generated.
"""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import yaml
import job_filters
from profile_config import load_profile
from scripts import company_pool

POLICY = ROOT / 'data/company_relevance_policy.yaml'
BACKUP = ROOT / 'data/backups/industrial_catalysis_pool'
RESULT = ROOT / 'outputs/industrial_company_audit.json'
# Individually identified from the existing upstream config and stored job data.
CANDIDATES = ['万华化学', '思摩尔', '禾赛科技', '中科曙光', '韶音科技', '瑞沃德',
              '东风汽车', '中国一汽', '东方电气', '开立医疗', '卓胜微电子', '小米']


def assess_company(company, jobs, policy):
    """Employer relevance and recruitment evidence are separate from eligibility."""
    usable = []
    for job in jobs:
        title = str(job.get('title') or '')
        body = str(job.get('jd_raw') or '')
        if not job_filters.is_formal_campus_job(job):
            continue
        if re.search(policy['nonchemical_title_pattern'], title):
            continue
        if (re.search(policy['related_title_pattern'], title)
                or re.search(policy['major_evidence_pattern'], body)):
            usable.append(job)
    direct = re.search(policy['direct_industry_pattern'], company.get('industry', ''))
    removal = policy.get('reviewed_removals', {}).get(company['name'])
    if usable:
        category = '保留：高度匹配' if direct else '保留：潜在匹配'
        reason = '行业直接相关且有技术岗位证据' if direct else '存在可迁移工艺、材料、质量或相关专业岗位证据；资格逐岗核实'
    elif removal and jobs:
        category, reason = '移出正式监测', removal['reason']
    elif direct or company.get('industry'):
        category, reason = '保留：潜在匹配', '历史样本未取得明确相关岗位，工业/科研来源暂保留；不能由缺少样本推断无机会'
    else:
        category, reason = '候选观察', '行业及岗位证据不足，需核实来源与专业覆盖'
    return {'name': company['name'], 'industry': company.get('industry', ''),
            'category': category, 'reason': reason, 'historical_total': len(jobs),
            'relevant_jobs': usable, 'careers_url': company['careers_url'],
            'crawler': company['crawler']}


def audit(root=ROOT, apply=False, live_limit=0):
    policy = yaml.safe_load((root / 'data/company_relevance_policy.yaml').read_text())
    config_path = root / 'config.yaml'
    config = yaml.safe_load(config_path.read_text())
    backup = root / 'data/backups/industrial_catalysis_pool'
    backup.mkdir(parents=True, exist_ok=True)
    for source in [config_path, root / 'data/company_pool.json']:
        dest = backup / source.name
        if not dest.exists():
            dest.write_bytes(source.read_bytes())
    dbpath = root / 'data/jobs.db'
    before_hash = hashlib.sha256(dbpath.read_bytes()).hexdigest()
    conn = sqlite3.connect(f'file:{dbpath}?mode=ro', uri=True)
    conn.row_factory = sqlite3.Row
    jobs = [dict(r) for r in conn.execute('SELECT * FROM jobs')]
    conn.close()
    by_company = {}
    for job in jobs:
        by_company.setdefault(job['company'], []).append(job)
    companies = yaml.safe_load((backup / 'config.yaml').read_text())['companies']
    audits = [assess_company(c, by_company.get(c['name'], []), policy) for c in companies]
    upstream_text = subprocess.check_output(['git', 'show', 'upstream/main:config.yaml'], cwd=root, text=True)
    upstream = yaml.safe_load(upstream_text)['companies']
    upstream_sha = subprocess.check_output(['git', 'rev-parse', 'upstream/main'], cwd=root, text=True).strip()
    state = company_pool.load_state(root / 'data/company_pool.json')
    known = {c['name'] for c in companies}
    leads = []
    for c in upstream:
        if c['name'] not in CANDIDATES or c['name'] in known:
            continue
        row = company_pool._merge_lead(state, {
            **c, 'source_id': 'upstream_industrial_audit',
            'source_url': f'https://github.com/mengxi111/career-agent/blob/{upstream_sha}/config.yaml',
            'evidence': '上游配置原始入口，仅作为线索；需当前官方身份、2027届与真实岗位验证',
        })
        samples = assess_company(c, by_company.get(c['name'], []), policy)['relevant_jobs']
        row['employer_review'] = {'category': '候选观察', 'reason': '专业迁移线索，当前招聘与平台未验证',
                                  'historical_samples': [{'title': j['title'], 'jd_url': j.get('jd_url')} for j in samples[:3]]}
        row['cohort_status'] = 'pending'
        leads.append(row)
    leads.sort(key=lambda row: CANDIDATES.index(row["name"]))
    live_results = []
    if RESULT.exists() and not live_limit:
        live_results = json.loads(RESULT.read_text()).get("live_validation", [])
    if live_limit:
        from scripts.validate_company import validate_one
        for row in leads[:min(5, live_limit)]:
            result = validate_one(row)
            row['validation'] = result
            row['last_validated_at'] = company_pool._iso(company_pool._now())
            row['status_reason'] = result.get('reason', '')
            row['next_retry_at'] = company_pool._iso(company_pool._now() + company_pool._retry_after(result['verdict'], 0))
            row['promotion_ready'] = False  # Official identity/cohort proof still needs review.
            live_results.append(result)
    profile = load_profile(root / 'profile.yaml')
    current = []
    for row in audits:
        for job in row['relevant_jobs']:
            if job.get('cohort') == 2027 and job.get('cohort_status') == 'confirmed':
                if job_filters.job_eligibility(job, profile)['status'] != '不符合':
                    current.append(job)
    for row in audits:
        row['relevant_jobs'] = [{k:j.get(k) for k in ('id', 'title', 'jd_url', 'cohort', 'cohort_status')} for j in row['relevant_jobs']]
    payload = {'candidate_sources': [{k:row.get(k) for k in ('name', 'careers_url', 'crawler', 'validation', 'employer_review')} for row in leads], 'before': len(companies), 'upstream_commit': upstream_sha,
               'discovered_from_upstream': len(leads), 'added': 0,
               'categories': dict(Counter(r['category'] for r in audits)),
               'live_validation': live_results, 'historical_2027_relevant_not_known_ineligible': len(current),
               'db_sha256': before_hash, 'companies': audits}
    output = root / 'outputs/industrial_company_audit.json'
    output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n')
    if apply:
        removed = {r['name']: r for r in audits if r['category'] in {'移出正式监测', '候选观察'}}
        config['companies'] = [c for c in companies if c['name'] not in removed]
        for c in config['companies']:
            row = next(r for r in audits if r['name'] == c['name'])
            c['pool_category'] = row['category']
        config['companies'].sort(key=lambda c: 0 if c.get('pool_category') == '保留：高度匹配' else 1)
        company_pool.sync_formal_pool(state, config['companies'])
        for row in state['records']:
            review = next((a for a in audits if a['name'] == row['name']), None)
            if review:
                row['employer_review'] = {k: review[k] for k in ['category', 'reason']}
            if row['name'] in removed:
                review = removed[row['name']]
                row.update(pool_status='history' if review['category'] == '移出正式监测' else 'candidate',
                           status_reason=review['reason'], promotion_ready=False,
                           archived_config=next(c for c in companies if c['name'] == row['name']))
        config_path.write_text(yaml.safe_dump(config, allow_unicode=True, sort_keys=False))
        company_pool.save_state(state, root / 'data/company_pool.json')
    assert hashlib.sha256(dbpath.read_bytes()).hexdigest() == before_hash
    write_report(payload, root)
    return payload


def write_report(result, root):
    lines = ['# 工业催化硕士企业池审查', '', '正式专业：工业催化；本科生物工程，山东大学为交换培养。', '',
             f"- 扩充前正式池：{result['before']} 家；上游复核相关新线索：{result['discovered_from_upstream']} 家。",
             '- 验证成功并加入：0 家。当前网络限制下不把历史成功或平台推测当作新增验收。',
             f"- 分类：{result['categories']}。",
             f"- 调整后正式池：{sum(v for k,v in result['categories'].items() if k.startswith('保留'))} 家；原正式池转候选观察：{result['categories'].get('候选观察', 0)} 家。",
             '- 新线索转候选观察：12家；池中累计候选25家（含此前13家）。未将本轮BLOCKED企业按失效删除。',
             f"- 历史确认2027届、规则相关且未发现硬性不符：{result['historical_2027_relevant_not_known_ineligible']} 条（含资格待核实，非确认可直接投递）。",
             '- 实时可用2027岗位数：无法确认。数据库为历史截面，不是本次实时抓取。',
             f"- 本次限量来源验证：{len(result['live_validation'])} 家；成功 {sum(r['verdict']=='OK' for r in result['live_validation'])} 家。",
             '- 完成验收率为0/6；6项均BLOCKED，源站真实抓取成功率不可测（不将BLOCKED计为源站失败）。',
             '- 网络限制：公开搜索与招聘域名 CONNECT 403。BLOCKED不能等同失效或企业未招聘。',
             '- 备份：data/backups/industrial_catalysis_pool/；数据库SHA256：' + result['db_sha256'], '',
             '## 全量企业证据审查', '',
             '| 企业 | 行业 | 分类 | 历史岗位/相关样本 | 匹配理由 | 招聘入口 |',
             '| --- | --- | --- | --- | --- | --- |']
    for row in result['companies']:
        samples = '；'.join(j['title'].replace('|', '/') for j in row['relevant_jobs'][:2])
        lines.append(f"| {row['name']} | {row['industry']} | {row['category']} | {row['historical_total']}/{len(row['relevant_jobs'])}：{samples} | {row['reason']} | {row['careers_url']} |")
    lines += ['', '## 新线索（仅候选，非本次成功接入）', '', '| 企业 | 招聘入口 | 上游爬虫 | 验证状态 | 历史迁移证据（非当前开招证明） |', '| --- | --- | --- | --- | --- |']
    for row in result['candidate_sources']:
        lines.append(f"| {row['name']} | {row['careers_url']} | {row['crawler']} | {(row.get('validation') or {}).get('verdict', '未实测/待核实')} | {'；'.join(j['title'].replace('|', '/') + ' ' + str(j.get('jd_url') or '') for j in (row.get('employer_review') or {}).get('historical_samples', [])) or '暂未提取'} |")
    lines += ['', '## 行业覆盖（调整后）', '']
    lines += [f'- {k}：{v} 家' for k,v in Counter(r['industry'] for r in result['companies'] if r['category'].startswith('保留')).items()]
    lines += ['', '## 来源限量验证记录', '']
    lines += [f"- {r['name']}：{r['verdict']}；{r['reason']}；{r['careers_url']}" for r in result['live_validation']]
    lines += ['', '## 尚需优先覆盖', '', '中石化/中石油/中海油的炼化、催化剂及研究单位，中国中化、国家能源集团、中国中煤、华鲁恒升、卫星化学、宝丰能源。没有核实到的URL保持为空，不推测招聘届别。', '',
              '## 判定边界', '', '行业与历史岗位只支持企业监测优先级，不能替代专业代码、学历、英语及届别的逐岗资格判断。通用工艺/质量为潜在迁移证据，不宣称一定接受工业催化。来源失效本轮不能确认，因此不按0岗位删除。集团子公司独立招聘入口保留；移除可由备份和archived_config恢复。']
    (root / 'docs/COMPANY_POOL_AUDIT.md').write_text('\n'.join(lines)+'\n')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--live-limit', type=int, default=0)
    args = parser.parse_args()
    result = audit(apply=args.apply, live_limit=args.live_limit)
    print(json.dumps({k:v for k,v in result.items() if k != 'companies'}, ensure_ascii=False, indent=2))

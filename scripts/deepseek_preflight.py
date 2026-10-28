"""Dry run by default. --execute permits at most 20 Flash jobs + 5 Pro jobs.

No crawling, JD hydration, notifications, DB purges, or production writes.
Only the formal monitoring pool and officially confirmed 2027 rows are eligible.
"""
import argparse
import json
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import analyzer
import db
import job_cohorts
import job_details
import job_filters
from main import _resolve_llm_models
from profile_config import load_profile
import yaml


def select_jobs(conn, companies, profile):
    names = {c['name'] for c in companies}
    conn.row_factory = sqlite3.Row
    selected = []
    for row in conn.execute('SELECT * FROM jobs ORDER BY last_seen_at DESC, id DESC'):
        job = dict(row)
        if (job['company'] not in names or not job_cohorts.is_confirmed_current(job)
                or not job_filters.is_formal_campus_job(job)
                or job_filters.is_direction_out_job(job, profile)
                or job_filters.job_eligibility(job, profile)['status'] == '不符合'):
            continue
        selected.append(job)
        if len(selected) == 20:
            break
    return selected


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--execute', action='store_true', help='Explicitly permit capped paid requests')
    parser.add_argument('--output', default=str(ROOT / 'outputs/deepseek_preflight.json'))
    args = parser.parse_args(argv)
    config = yaml.safe_load((ROOT / 'config.yaml').read_text())
    profile = load_profile(ROOT / 'profile.yaml')
    analyzer._load_env_file()
    present = bool(os.environ.get('DEEPSEEK_API_KEY', '').strip())
    models = _resolve_llm_models(config['deepseek'])
    report = {'mode':'execute' if args.execute else 'dry-run', 'key_present':present,
              'screening_model':models[0], 'analysis_model':models[1],
              'flash_job_cap':20, 'analysis_job_cap':5, 'request_attempt_cap':6,
              'api_requests':0, 'api_successes':0, 'api_failures':0}
    source = sqlite3.connect(f'file:{ROOT / "data/jobs.db"}?mode=ro', uri=True)
    with tempfile.TemporaryDirectory(prefix='career-preflight-') as directory:
        target = sqlite3.connect(str(Path(directory) / 'jobs.db'))
        source.backup(target)
        source.close()
        target.close()
        conn = db.init_db(str(Path(directory) / 'jobs.db'))
        jobs = select_jobs(conn, config['companies'], profile)
        report['selected_jobs'] = len(jobs)
        report['selected_job_ids'] = [j['id'] for j in jobs]
        if args.execute and not present:
            raise SystemExit('DEEPSEEK_API_KEY missing; no API request was made')
        original = analyzer.call_deepseek_api

        def capped_call(system, message, model, max_tokens):
            if report['api_requests'] >= 6:
                raise analyzer.LLMError('Preflight request cap reached')
            report['api_requests'] += 1
            try:
                response = original(system, message, model, max_tokens, retries=1)
            except Exception:
                report['api_failures'] += 1
                raise
            report['api_successes'] += 1
            return response

        if args.execute:
            analyzer.call_deepseek_api = capped_call
            try:
                tiers = analyzer.classify_job_tiers(jobs, profile, models[0], 600)
                for job, tier in zip(jobs, tiers):
                    job['screening_tier'] = tier
                candidates = [j for j in jobs if j['screening_tier']=='A' and not job_details.is_jd_incomplete(j)][:5]
                results = analyzer.batch_analyze(candidates, profile, conn, model=models[1],
                                                 max_tokens=1200, hydrate=False,
                                                 max_jobs=5, max_jobs_per_day=10)
                report['complete_analyses'] = len(results)
            finally:
                analyzer.call_deepseek_api = original
        conn.close()
    path = Path(args.output)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    print(json.dumps(report, ensure_ascii=False))
    return 1 if report['api_failures'] else 0


if __name__ == '__main__':
    raise SystemExit(main())

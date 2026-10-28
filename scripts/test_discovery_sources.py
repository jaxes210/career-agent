"""Small real-network probe. Never modifies formal config or recruitment DB."""
from pathlib import Path
import json
import os
import sys
from datetime import timedelta
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.public_discovery import discover_source
from scripts.company_pool import _merge_lead, load_state, save_state, _iso, _now


def _probe(source):
    """Keep one broken source from preventing diagnostics for the other five."""
    checked_at = _iso(_now())
    try:
        result = discover_source(source)
    except Exception as exc:  # The bounded probe must report parser defects by source.
        result = {
            'status': 'PROBE_ERROR',
            'reason': f'{type(exc).__name__}: {str(exc)[:300]}',
            'leads': [],
            'requests': [],
        }
    result.update(
        id=source['id'],
        category=source['category'],
        source_url=source['source_url'],
        checked_at=checked_at,
    )
    return result


def _write_step_summary(payload):
    path = os.environ.get('GITHUB_STEP_SUMMARY')
    if not path:
        return
    lines = [
        '## 待验证招聘入口联网探测', '',
        f"- 入口：{len(payload['sources'])}",
        f"- 招聘线索：{payload['lead_count']}",
        f"- 新企业：{payload['new_company_count']}", '',
        '| 类别 | 来源 | 结果 | 原因 |',
        '| --- | --- | --- | --- |',
    ]
    for row in payload['sources']:
        reason = str(row.get('reason') or '').replace('|', '\\|').replace('\n', ' ')
        lines.append(f"| {row['category']} | {row['id']} | {row['status']} | {reason} |")
    with open(path, 'a', encoding='utf-8') as handle:
        handle.write('\n'.join(lines) + '\n')


def main():
    registry=yaml.safe_load((ROOT/'data/company_discovery_sources.yaml').read_text())
    records=[_probe(source) for source in registry.get('pending_sources',[])[:6]]
    state=load_state()
    initial_names={r['name'] for r in state['records']}
    leads=[lead for result in records for lead in result['leads']]
    for lead in leads:
        _merge_lead(state,lead)
    # No fabricated candidates when the public sources are inaccessible.
    for result in records:
        state.setdefault('source_health', {})[result['id']] = {
            'status':result['status'], 'reason':result['reason'],
            'checked_at':result['checked_at'],
            'next_retry_at':_iso(_now()+timedelta(days=3)),
        }
    save_state(state)
    payload={'schema_version':1,
             'runner':'github-actions' if os.environ.get('GITHUB_ACTIONS')=='true' else 'local',
             'run_id':os.environ.get('GITHUB_RUN_ID'),
             'sources':records,'lead_count':len(leads),
             'new_company_count':len({l['name'] for l in leads}-initial_names),
             'official_verified':0,'confirmed_2027_eligible':0,'deep_validations':0,'pr_created':False}
    (ROOT/'outputs/multisource_probe.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    _write_step_summary(payload)
    print(json.dumps({k:v for k,v in payload.items() if k!='sources'},ensure_ascii=False))

if __name__=='__main__':main()

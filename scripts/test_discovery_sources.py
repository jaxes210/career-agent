"""Small real-network probe. Never modifies formal config or recruitment DB."""
from pathlib import Path
import json
import sys
from datetime import timedelta
import yaml
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.public_discovery import discover_source
from scripts.company_pool import _merge_lead, load_state, save_state, _iso, _now


def main():
    registry=yaml.safe_load((ROOT/'data/company_discovery_sources.yaml').read_text())
    records=[]
    for source in registry.get('pending_sources',[])[:6]:
        result=discover_source(source)
        result.update(id=source['id'],category=source['category'],source_url=source['source_url'],checked_at=_iso(_now()))
        records.append(result)
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
    payload={'sources':records,'lead_count':len(leads),
             'new_company_count':len({l['name'] for l in leads}-initial_names),
             'official_verified':0,'confirmed_2027_eligible':0,'deep_validations':0,'pr_created':False}
    (ROOT/'outputs/multisource_probe.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps({k:v for k,v in payload.items() if k!='sources'},ensure_ascii=False))

if __name__=='__main__':main()

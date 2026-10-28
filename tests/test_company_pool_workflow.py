from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_manual_discovery_workflow_runs_bounded_pending_probe():
    workflow = (ROOT / '.github/workflows/company_pool_discovery.yml').read_text()
    assert 'workflow_dispatch:' in workflow
    assert 'default: "3"' in workflow
    assert "github.event_name == 'workflow_dispatch' && inputs.probe_pending_sources" in workflow
    assert 'python scripts/test_discovery_sources.py' in workflow
    assert 'outputs/multisource_probe.json' in workflow

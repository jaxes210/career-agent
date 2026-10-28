import requests
from scripts.public_discovery import parse_html, parse_rss, fetch_public, discover_source
from scripts.company_pool import _merge_lead, _url_key

SOURCE={'id':'test','adapter':'public_html'}


def test_html_subsidiary_lead_has_no_assumed_official_or_cohort_qualification():
    content='''<h1>某能源集团化工研究院2027届校园招聘</h1><article>招聘材料、化工工艺、分析检测硕士。英语要求待核实。
    <a href="https://tenant.zhiye.com/campus/jobs">官方投递</a></article>'''
    leads,_=parse_html(content,'https://school.example/a',SOURCE)
    assert leads[0]['name']=='某能源集团化工研究院'
    assert leads[0]['careers_url']=='https://tenant.zhiye.com/campus/jobs'
    assert leads[0]['cohort_status']=='lead_mentions_2027'
    assert 'official_status' not in leads[0]


def test_unknown_cohort_and_missing_apply_url_retained():
    leads,_=parse_html('<h1>某材料有限公司校园招聘</h1><article>质量、生产技术招聘</article>', 'https://school.example/a',SOURCE)
    assert leads[0]['cohort_status']=='pending'
    assert leads[0]['careers_url']==''


def test_rss_extracts_lead_and_same_origin_detail_only():
    content='<rss><channel><item><title>某化工有限公司2027校园招聘</title><link>https://school.example/notice/1</link><description>工艺技术硕士</description></item></channel></rss>'
    leads,details=parse_rss(content,'https://school.example/rss',SOURCE)
    assert len(leads)==1 and details==['https://school.example/notice/1']


def test_distinct_subsidiaries_not_deduped_by_parent_name():
    state={'records':[]}
    for name,host in [('某能源集团化工研究院','one'),('某能源集团技术有限公司','two')]:
        _merge_lead(state,{'name':name,'careers_url':f'https://{host}.zhiye.com/campus/jobs','crawler':'beisen','source_id':'test'})
    assert len(state['records'])==2


def test_unknown_url_identity_preserves_company_query_ids():
    assert _url_key('https://platform.example/company?id=1')!=_url_key('https://platform.example/company?id=2')


def test_connection_failure_is_blocked_not_empty():
    class Session:
        def get(self,*a,**k):raise requests.ConnectionError('unavailable')
    assert fetch_public('https://example.com',Session())[1]=='BLOCKED'


def test_captcha_page_is_blocked_without_parsing_or_bypass():
    class Response:
        status_code=200
        encoding='utf-8'
        def __enter__(self):return self
        def __exit__(self,*a):pass
        def iter_content(self,*a):yield '请完成人机验证'.encode()
    class Session:
        headers={}
        def get(self,*a,**k):return Response()
    result=discover_source({**SOURCE,'source_url':'https://example.com'},Session())
    assert result['status']=='BLOCKED' and result['leads']==[]


def test_shared_iguopin_company_pages_keep_distinct_ids():
    from scripts.qq_docs_27_autumn_monitor import recruitment_source_identity
    assert recruitment_source_identity('https://www.iguopin.com/company?id=1') != recruitment_source_identity('https://www.iguopin.com/company?id=2')


def test_configured_public_source_uses_persistent_retry_health(tmp_path, monkeypatch):
    import yaml
    from scripts import company_pool, public_discovery
    path=tmp_path/'sources.yaml'
    path.write_text(yaml.safe_dump({'sources':[{'id':'one','adapter':'public_html','source_url':'https://example.com','enabled':True}]}))
    calls=[]
    def blocked(source):
        calls.append(source['id'])
        return {'status':'BLOCKED','reason':'HTTP 403','leads':[],'requests':[]}
    monkeypatch.setattr(public_discovery,'discover_source',blocked)
    state={'records':[]}
    company_pool.discover(state,[],path)
    second=company_pool.discover(state,[],path)
    assert calls==['one']
    assert second['sources']['one']['status']=='DEFERRED'
    assert state['records']==[]

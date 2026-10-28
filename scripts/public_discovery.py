"""Bounded public HTML/RSS discovery. No login, guessed APIs or AI calls.

All extracted links remain leads. A university repost or platform tenant alone
never proves employer identity, eligibility or a current recruitment cohort.
"""
from __future__ import annotations
import re
from urllib.parse import urljoin, urlparse
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
import requests

MAX_BYTES = 2 * 1024 * 1024
RECRUIT = re.compile(r'招聘|校招|毕业生|人才引进')
RELEVANT = re.compile(r'催化|化工|材料|化学|生产|工艺|理化|检测|质量|环保|水处理|日化|配方|能源|石油|石化|煤|研究院|生物')
COMPANY = re.compile(r'([\u4e00-\u9fffA-Za-z0-9·（）()]{2,60}(?:股份有限公司|有限责任公司|有限公司|集团|研究院|研究所|技术中心))')


def http_url(value, base):
    url = urljoin(base, value.strip())
    parsed = urlparse(url)
    if parsed.scheme not in {'https', 'http'} or not parsed.hostname or parsed.username or parsed.password:
        return ''
    return url


def company_name(title):
    clean = re.sub(r'\d{4}(?:届|年)?|27届|校园招聘|招聘公告|招聘简章|【[^】]*】|\[[^]]*\]', '', title)
    match = COMPANY.search(clean)
    return match.group(1).strip('：: -') if match else ''


def parse_announcement(title, text, url, anchors, source):
    if not RECRUIT.search(title + text) or not RELEVANT.search(title + text):
        return []
    name = company_name(title)
    if not name:
        return []
    from scripts.qq_docs_27_autumn_monitor import infer_crawler
    entries = []
    for label, target in anchors:
        target = http_url(target, url)
        if target and (infer_crawler(target) or re.search(r'投递|招聘官网|招聘网站|招聘平台|申请职位', label)):
            entries.append(target)
    # Preserve genuine announcements even when official application URLs are absent.
    return [{'name':name, 'careers_url':target, 'source_id':source['id'],
             'source_url':url, 'announcement_title':title,
             'cohort_status':'lead_mentions_2027' if re.search(r'2027|27届', title + text) else 'pending',
             'evidence':text[:2000], 'crawler':infer_crawler(target) if target else None}
            for target in dict.fromkeys(entries or [''])]


def parse_html(content, url, source):
    soup = BeautifulSoup(content, 'html.parser')
    for element in soup(['script','style','nav','footer']):
        element.decompose()
    article = soup.select_one(source.get('article_selector', 'article'))
    details = []
    if article:
        title = soup.find('h1') or soup.find('title')
        leads = parse_announcement(title.get_text(' ',strip=True) if title else '',
                                   article.get_text(' ',strip=True), url,
                                   [(a.get_text(' ',strip=True),a['href']) for a in article.select('a[href]')], source)
    else:
        leads = []
    for anchor in soup.select(source.get('link_selector', 'a[href]')):
        if not anchor.get('href'):
            continue
        label = anchor.get_text(' ',strip=True) or anchor.get('title', '')
        target = http_url(anchor['href'], url)
        if target and RECRUIT.search(label):
            if urlparse(target).netloc == urlparse(url).netloc:
                details.append(target)
            # A list row may be a true lead, but it is not an official application URL.
            leads.extend(parse_announcement(label, label, url, [(label,target)], source))
    return leads, list(dict.fromkeys(details))


def parse_rss(content, url, source):
    root = ET.fromstring(content)
    leads, details = [], []
    entries = root.findall('.//item') + root.findall('.//{http://www.w3.org/2005/Atom}entry')
    for entry in entries[:50]:
        def field(name):
            node = entry.find(name)
            if node is None:
                node = entry.find('{http://www.w3.org/2005/Atom}' + name)
            return node
        title = field('title')
        link = field('link')
        text = ' '.join(entry.itertext())
        target = http_url((link.text or link.get('href','')) if link is not None else '', url)
        if target:
            leads.extend(parse_announcement(title.text or '' if title is not None else '', text, target, [], source))
            if urlparse(target).netloc == urlparse(url).netloc:
                details.append(target)
    return leads, list(dict.fromkeys(details))


def fetch_public(url, session):
    try:
        response = session.get(url, timeout=15, stream=True)
        with response:
            if response.status_code in {401,403,407,429}:
                return None, 'BLOCKED', f'HTTP {response.status_code}'
            if response.status_code >= 400:
                return None, 'HTTP_ERROR', f'HTTP {response.status_code}'
            data = bytearray()
            for chunk in response.iter_content(65536):
                data.extend(chunk)
                if len(data)>MAX_BYTES:
                    return None,'TOO_LARGE','response exceeds 2 MiB'
            content = bytes(data).decode(response.encoding if response.encoding and response.encoding.lower() != 'iso-8859-1' else 'utf-8', errors='replace')
            if re.search(r'验证码|安全验证|人机验证|captcha|请先登录|登录后查看', content, re.I):
                return None,'BLOCKED','login/captcha/access challenge'
            return content,'OK',''
    except requests.RequestException as exc:
        message = str(exc)
        if isinstance(exc, requests.exceptions.ProxyError):
            failure = 'proxy_connect_403' if '403 Forbidden' in message else 'proxy_error'
        elif isinstance(exc, requests.exceptions.ConnectTimeout):
            failure = 'connect_timeout'
        elif isinstance(exc, requests.exceptions.ReadTimeout):
            failure = 'read_timeout'
        elif isinstance(exc, requests.exceptions.SSLError):
            failure = 'tls_error'
        elif isinstance(exc, requests.exceptions.ConnectionError):
            failure = 'dns_or_connect_error'
        else:
            failure = type(exc).__name__
        return None,'BLOCKED',f'connection restricted or unavailable: {failure}'


def discover_source(source, session=None):
    session = session or requests.Session()
    session.headers.update({'User-Agent':'career-agent public-source-monitor/1.0'})
    url = source['source_url']
    text, status, reason = fetch_public(url, session)
    requests_made = [{'url':url,'status':status,'reason':reason}]
    if text is None:
        return {'status':status,'reason':reason,'leads':[],'requests':requests_made}
    parser = parse_rss if source['adapter']=='public_rss' else parse_html
    try:
        leads, details = parser(text,url,source)
        for link in details[:min(2,max(0,int(source.get('max_detail_pages',2))))]:
            if link == url:
                continue
            body, state, detail = fetch_public(link,session)
            requests_made.append({'url':link,'status':state,'reason':detail})
            if body:
                new, _ = parse_html(body,link,source)
                leads.extend(new)
    except (ET.ParseError, ValueError, AttributeError, TypeError) as exc:
        return {'status':'PARSE_ERROR','reason':type(exc).__name__,'leads':[],'requests':requests_made}
    unique = {(lead['name'],lead['source_url'],lead['careers_url']):lead for lead in leads}
    return {'status':'OK' if unique else 'NO_PARSED_LEADS', 'leads':list(unique.values())[:50],
            'requests':requests_made,'reason':'' if unique else 'No matching public announcement parsed; may need a site-specific adapter'}

#!/usr/bin/env python3
"""Check generated metadata, canonical/sitemap consistency and real preview assets."""
from pathlib import Path
from html.parser import HTMLParser
from xml.etree import ElementTree as ET
import json
from site_seo import PAGES, SITE_URL

ROOT=Path(__file__).resolve().parent.parent
class Head(HTMLParser):
    def __init__(self):super().__init__();self.in_head=False;self.title=False;self.titles=[];self.meta={};self.canonical=[];self.jsonld=[];self.capture=False;self.buffer=''
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='head':self.in_head=True
        if not self.in_head:return
        if tag=='title':self.title=True;self.titles.append('')
        if tag=='meta':
            key=a.get('name',a.get('property'))
            if key:
                assert key not in self.meta,key
                self.meta[key]=a.get('content','')
        if tag=='link' and a.get('rel')=='canonical':self.canonical.append(a['href'])
        if tag=='script' and a.get('type')=='application/ld+json':self.capture=True;self.buffer=''
    def handle_data(self,data):
        if self.title:self.titles[-1]+=data
        if self.capture:self.buffer+=data
    def handle_endtag(self,tag):
        if tag=='title':self.title=False
        if tag=='script' and self.capture:self.jsonld.append(json.loads(self.buffer));self.capture=False
        if tag=='head':self.in_head=False

def main():
    titles=set();indexable=set()
    for filename,settings in PAGES.items():
        p=Head();p.feed((ROOT/filename).read_text())
        assert p.titles==[settings['title']],filename
        assert settings['title'] not in titles; titles.add(settings['title'])
        assert p.meta['description']==settings['description']
        assert p.canonical==[SITE_URL+settings['path']],filename
        assert p.meta['og:url']==p.canonical[0]
        assert p.meta['og:title']==p.titles[0]
        assert p.meta['twitter:card']=='summary_large_image'
        assert ('noindex' not in p.meta['robots'])==settings['index']
        if settings['index']:indexable.add(p.canonical[0])
        image=p.meta['og:image'].removeprefix(SITE_URL+'/')
        assert (ROOT/image).is_file()
        assert len(p.jsonld)==1 and p.jsonld[0]['@context']=='https://schema.org'
        graph=p.jsonld[0]['@graph']
        assert any(x['@type']=='WebSite' for x in graph)
        if filename in ['index.html','theogony-reader.html']:
            book=next(x for x in graph if x['@type']=='Book')
            assert book['author']['name']=='Hesiod' and book['isAccessibleForFree'] is True
    urls={x.text for x in ET.parse(ROOT/'sitemap.xml').iter('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')}
    assert urls==indexable,(urls,indexable)
    robots=(ROOT/'robots.txt').read_text()
    assert 'Sitemap: '+SITE_URL+'/sitemap.xml' in robots and 'Disallow: /\n' not in robots
    print(f'Passed: {len(PAGES)} unique page titles/descriptions/canonicals, social previews, valid JSON-LD, {len(urls)} consistent sitemap URLs, crawl access.')

if __name__=='__main__':main()

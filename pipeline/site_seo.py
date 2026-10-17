"""Shared, static discovery metadata for the actual public edition."""
from pathlib import Path
from PIL import Image
import html
import json
from xml.etree import ElementTree as ET

SITE_URL='https://theogony-reading.vercel.app'
SITE_NAME='Theogony: Read Hesiod'
SOCIAL_PATH='assets/theogony-share.jpg'
PAGES={
 'index.html':{
  'title':'Hesiod’s Theogony: Read in English',
  'description':'Read Hesiod’s Theogony in clear English. Explore the origins of the Greek gods with numbered verses, short passages and explanatory notes. Free online.',
  'path':'/','index':True},
 'theogony-reader.html':{
  'title':'Read Hesiod’s Theogony: English Translation',
  'description':'Read the English Theogony online, from the Muses to Zeus. Follow 1,022 numbered verses with passage summaries, Greek mythological names and reading settings.',
  'path':'/theogony-reader.html','index':True},
 'translation.html':{
  'title':'Theogony Translation: Greek Source and Passage Records',
  'description':'Explore the Greek source behind this English Theogony, its textual choices, and the models, prompts and generation records for all 66 passages.',
  'path':'/translation.html','index':True},
 'reuse.html':{
  'title':'Reuse and Licence: Theogony English Edition',
  'description':'Reuse this English Theogony edition in your own projects. Read the CC BY 4.0 attribution guidance and separate licence notice for the Perseus Greek source.',
  'path':'/reuse.html','index':True},
 'imprint.html':{
  'title':'Legal Notice / Impressum: Theogony',
  'description':'Publisher and contact details for the free online English reading edition of Hesiod’s Theogony. Legal notice in English and German.',
  'path':'/imprint.html','index':False},
 'privacy.html':{
  'title':'Datenschutz / Privacy: Theogony',
  'description':'Datenschutzhinweise für die Theogony-Leseseite: Hosting, technische Verbindungsdaten und freiwillige Speicherung von Lesestelle und Einstellungen.',
  'path':'/privacy.html','index':False,'language':'de'},
}

def metadata(page):
    data=PAGES[page]
    url=SITE_URL+data['path']
    language=data.get('language','en')
    tags=[f'<title>{html.escape(data["title"])}</title>',
          f'<meta name="description" content="{html.escape(data["description"],quote=True)}">',
          f'<link rel="canonical" href="{url}">',
          '<link rel="icon" href="favicon-column-v1-32.png" type="image/png" sizes="32x32">',
          '<link rel="icon" href="favicon-column-v1-48.png" type="image/png" sizes="48x48">',
          '<link rel="shortcut icon" href="favicon.ico">',
          '<link rel="apple-touch-icon" href="apple-touch-icon.png" sizes="180x180">',
          f'<meta name="robots" content="{"index, follow, max-image-preview:large" if data["index"] else "noindex, follow"}">']
    values={'og:type':'website','og:site_name':SITE_NAME,'og:title':data['title'],
            'og:description':data['description'],'og:url':url,'og:locale':'de_DE' if language=='de' else 'en_US',
            'og:image':SITE_URL+'/'+SOCIAL_PATH,'og:image:width':'1200','og:image:height':'500',
            'og:image:type':'image/jpeg','og:image:alt':'Hand-drawn illustrations of Gaia, Zeus and Athena on a blue background.'}
    tags += [f'<meta property="{key}" content="{html.escape(value,quote=True)}">' for key,value in values.items()]
    twitter={'twitter:card':'summary_large_image','twitter:title':data['title'],
             'twitter:description':data['description'],'twitter:image':SITE_URL+'/'+SOCIAL_PATH,
             'twitter:image:alt':values['og:image:alt']}
    tags += [f'<meta name="{key}" content="{html.escape(value,quote=True)}">' for key,value in twitter.items()]
    graph=[{'@type':'WebSite','@id':SITE_URL+'/#website','url':SITE_URL+'/',
            'name':SITE_NAME,'alternateName':'Theogony Reading','inLanguage':'en'},
           {'@type':'WebPage','@id':url+'#webpage','url':url,'name':data['title'],
            'description':data['description'],'inLanguage':language,
            'isPartOf':{'@id':SITE_URL+'/#website'}}]
    if page in {'index.html','theogony-reader.html'}:
        graph.append({'@type':'Book','@id':SITE_URL+'/#english-edition',
                      'name':'Theogony: English reading edition','author':{'@type':'Person','name':'Hesiod'},
                      'inLanguage':'en','bookFormat':'https://schema.org/EBook','isAccessibleForFree':True,
                      'url':SITE_URL+'/theogony-reader.html',
                      'isBasedOn':SITE_URL+'/sources/tlg0020.tlg001.perseus-grc2.xml',
                      'publisher':{'@type':'Person','name':'Onur Cirag'},
                      'description':'An AI-assisted English reading draft of Hesiod’s Theogony, with passage summaries and name notes.'})
        graph[1]['mainEntity']={'@id':SITE_URL+'/#english-edition'}
    tags.append('<script type="application/ld+json">'+json.dumps({'@context':'https://schema.org','@graph':graph},ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')+'</script>')
    tags.append('<link rel="stylesheet" href="assets/consent-notice-v1.css">')
    tags.append('<script defer src="assets/site-preferences-v1.js"></script>')
    tags.append('<script defer src="assets/site-analytics-v1.js"></script>')
    return ''.join(tags)

def write_discovery_files(root:Path):
    root.joinpath('robots.txt').write_text('User-agent: *\nAllow: /\n\nSitemap: '+SITE_URL+'/sitemap.xml\n')
    ET.register_namespace('','http://www.sitemaps.org/schemas/sitemap/0.9')
    namespace='{http://www.sitemaps.org/schemas/sitemap/0.9}'
    sitemap=ET.Element(namespace+'urlset')
    for data in PAGES.values():
        if data['index']:
            item=ET.SubElement(sitemap,namespace+'url')
            ET.SubElement(item,namespace+'loc').text=SITE_URL+data['path']
    ET.ElementTree(sitemap).write(root/'sitemap.xml',encoding='utf-8',xml_declaration=True)
    # Preserve the approved Imagegen original; only resize for browser icon formats.
    with Image.open(root/'assets/favicon-column-handdrawn-v1.png') as source:
        icon=source.convert('RGB')
        for size in (32,48):
            icon.resize((size,size),Image.Resampling.LANCZOS).save(root/f'favicon-column-v1-{size}.png',optimize=True)
        icon.resize((180,180),Image.Resampling.LANCZOS).save(root/'apple-touch-icon.png',optimize=True)
        icon.save(root/'favicon.ico',sizes=[(16,16),(32,32),(48,48)])

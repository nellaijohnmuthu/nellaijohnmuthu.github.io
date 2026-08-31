#!/usr/bin/env python3
"""Pre-publish check for nellaijohnmuthu.com — run: python3 validate.py"""
import json, os, re, sys, glob
from html.parser import HTMLParser

VOID={'meta','link','br','img','hr','input','source','area','base','col','embed','param','track','wbr'}
SOCIAL=["instagram.com/nellai_john_muthu","facebook.com/nellaijohnmuthu",
        "x.com/Nellaijohnmuthu","youtube.com/@NellaiJohnMuthu"]

class P(HTMLParser):
    def __init__(s):
        super().__init__(convert_charrefs=True); s.stack=[];s.errs=[];s.refs=[];s.ids=[];s.ext=[]
    def handle_starttag(s,t,a):
        d=dict(a)
        if 'id' in d: s.ids.append(d['id'])
        for k in ('href','src'):
            if k in d:
                (s.ext if d[k].startswith('http') else s.refs).append(d[k])
        if 'srcset' in d: s.refs.append(d['srcset'].split()[0])
        if t=='img' and not d.get('alt'): s.errs.append('img without alt')
        if t=='a' and not d.get('href'): s.errs.append('anchor without href')
        if t not in VOID: s.stack.append(t)
    def handle_endtag(s,t):
        if t in VOID: return
        if not s.stack: s.errs.append(f'stray </{t}>'); return
        if s.stack[-1]==t: s.stack.pop()
        else: s.errs.append(f'expected </{s.stack[-1]}>, got </{t}>')

BLOCK=[(r'class="fill"','rendered placeholder'),(r'FILL-','FILL- marker'),
       (r'\+91 00000 00000','dummy phone'),(r'0\.00\s*[–-]','dummy opening hours'),
       (r'@FILL-CHANNEL-HANDLE','placeholder YouTube handle')]

def main():
    fail=warn=0; pages=sorted(glob.glob('*.html'))
    if not pages: print('No HTML here.'); return 1
    allsocial=set()
    for f in pages:
        s=open(f,encoding='utf-8').read(); p=P(); p.feed(s); e=list(p.errs)
        if p.stack: e.append(f'unclosed: {p.stack}')
        for pat,why in BLOCK:
            n=len(re.findall(pat,s))
            if n: e.append(f'{why} x{n}')
        for need,why in [('<title>','no title'),('name="description"','no meta description'),
                         ('rel="canonical"','no canonical'),('og:image','no og:image'),
                         ('lang="ta"','no lang'),('site.js','site.js not loaded'),
                         ('action-bar','no mobile action bar'),('menuBtn','no mobile menu')]:
            if need not in s: e.append(why)
        for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>',s,re.S):
            try: json.loads(blk)
            except Exception as ex: e.append(f'bad JSON-LD: {ex}')
        d={i for i in p.ids if p.ids.count(i)>1}
        if d: e.append(f'duplicate ids: {sorted(d)[:5]}')
        for r in p.refs:
            if r.startswith('/') and not r.startswith('//'):
                t=r.lstrip('/').split('#')[0].split('?')[0] or 'index.html'
                if not os.path.exists(t): e.append(f'broken link: {r}')
        for u in p.ext: allsocial.update(x for x in SOCIAL if x in u)
        blocking=[x for x in e if any(k in x for k in ('placeholder','dummy','broken','unclosed','JSON-LD','duplicate','FILL'))]
        if blocking: fail+=1
        elif e: warn+=1
        print(f"{'FAIL' if blocking else ('WARN' if e else 'OK  ')} {f:20}{len(s)//1024:4} KB")
        for x in e: print('        -',x)

    missing=[x for x in SOCIAL if x not in allsocial]
    if missing: print(f'FAIL social profiles missing sitewide: {missing}'); fail+=1
    else: print(f'OK   all {len(SOCIAL)} social profiles linked')
    for x in ('sitemap.xml','robots.txt','style.css','site.js','search.js'):
        if not os.path.exists(x): print(f'FAIL missing {x}'); fail+=1
    print()
    if fail: print(f'{fail} problem(s). NOT ready to publish.'); return 1
    print(f'All checks passed{" (" + str(warn) + " warnings)" if warn else ""}. Ready to publish.')
    return 0
sys.exit(main())

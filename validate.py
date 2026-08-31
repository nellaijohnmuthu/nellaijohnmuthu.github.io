#!/usr/bin/env python3
"""Pre-publish check. Run:  python3 validate.py
Fails loudly on placeholders, broken links, duplicate IDs, missing alt/meta, bad JSON-LD."""
import json, os, re, sys, glob
from html.parser import HTMLParser

VOID = {'meta','link','br','img','hr','input','source','area','base','col','embed','param','track','wbr'}

class P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.stack=[]; self.errs=[]; self.refs=[]; self.ids=[]
    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        if 'id' in d: self.ids.append(d['id'])
        for k in ('href','src'):
            if k in d: self.refs.append(d[k])
        if 'srcset' in d: self.refs.append(d['srcset'].split()[0])
        if tag == 'img' and not d.get('alt'): self.errs.append('img without alt')
        if tag not in VOID: self.stack.append(tag)
    def handle_endtag(self, tag):
        if tag in VOID: return
        if not self.stack: self.errs.append(f'stray </{tag}>'); return
        if self.stack[-1] == tag: self.stack.pop()
        else: self.errs.append(f'expected </{self.stack[-1]}>, got </{tag}>')

BLOCKERS = [
    (r'class="fill"',            'unfilled placeholder'),
    (r'FILL-',                   'FILL- marker'),
    (r'\+91 00000 00000',        'dummy phone'),
    (r'0\.00\s*[–-]\s*',         'dummy opening hours'),
    (r'\[[^\]]*உண்மையான[^\]]*\]','Tamil placeholder note'),
]

def main():
    fail = warn = 0
    pages = sorted(glob.glob('*.html'))
    if not pages:
        print('No HTML found. Run this inside the site folder.'); return 1
    for f in pages:
        s = open(f, encoding='utf-8').read()
        p = P(); p.feed(s)
        errs = list(p.errs)
        if p.stack: errs.append(f'unclosed tags: {p.stack}')

        for pat, why in BLOCKERS:
            n = len(re.findall(pat, s))
            if n: errs.append(f'{why} x{n}')

        for need, why in [('<title>','no <title>'), ('name="description"','no meta description'),
                          ('rel="canonical"','no canonical'), ('og:image','no og:image'),
                          ('lang="ta"','no lang attribute')]:
            if need not in s: errs.append(why)

        for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
            try: json.loads(blk)
            except Exception as e: errs.append(f'invalid JSON-LD: {e}')

        dupes = {i for i in p.ids if p.ids.count(i) > 1}
        if dupes: errs.append(f'duplicate ids: {sorted(dupes)}')

        for r in p.refs:
            if r.startswith('/') and not r.startswith('//'):
                t = r.lstrip('/').split('#')[0].split('?')[0] or 'index.html'
                if not os.path.exists(t): errs.append(f'broken link: {r}')
            if r == '' or r == '#': errs.append('empty href')

        blocking = [e for e in errs if 'placeholder' in e or 'dummy' in e or 'broken' in e
                    or 'unclosed' in e or 'JSON-LD' in e or 'duplicate' in e]
        if blocking: fail += 1
        elif errs: warn += 1
        status = 'FAIL' if blocking else ('WARN' if errs else 'OK  ')
        print(f'{status} {f:20} {len(s)//1024:3} KB')
        for e in errs: print(f'        - {e}')

    for extra in ('sitemap.xml','robots.txt','style.css'):
        if not os.path.exists(extra):
            print(f'FAIL missing {extra}'); fail += 1

    print()
    if fail:
        print(f'{fail} file(s) NOT ready to publish.'); return 1
    if warn:
        print(f'Publishable, but {warn} file(s) have warnings.'); return 0
    print('All checks passed. Ready to publish.')
    return 0

sys.exit(main())

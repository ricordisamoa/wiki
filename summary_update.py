# -*- coding: utf-8  -*-
"""
released as CC0 — Creative Commons Public Domain Dedication:
To the extent possible under law, the person who associated CC0 with this work
has waived all copyright and related or neighboring rights to this work.
"""

import pywikibot

meta = pywikibot.Site('meta', 'meta')
summary = []
kwargs = {
    'namespace': 1198,
    'prefix': 'User:SamoaBot/Wikidata Summary/translate/1/',
    'filterredir': False
}
pages = list(meta.allpages(**kwargs))
kwargs['prefix'] = kwargs['prefix'].replace('/1/', '/2/')
pages = pages + list(meta.allpages(**kwargs))

for page in pages:
    text = page.get(force=True)

    # to make it compatible with pywikibot.i18n
    text = text.replace('{{plural:', '{{PLURAL:')
    text = text.replace('$counter', '%(counter)d')
    text = text.replace('$user', '%(user)s')
    text = text.replace('$params', '%(params)s')
    text = text.replace('$id', '%(id)s')

    spl = page.title().split('/')
    num = int(spl[-2])
    while num > len(summary):
        summary.append({})
    summary[num - 1][spl[-1]] = text

with open('wikidata_summary.py', 'w') as f:
    f.write(u'summary = ' + str(summary))

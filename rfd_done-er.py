#!/usr/bin/env python
"""
Copyright (C) 2013 Legoktm & Ricordisamoa

Permission is hereby granted, free of charge, to any person obtaining
a copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
IN THE SOFTWARE.
"""
import pywikibot
import re
pywikibot.handleArgs()
site = pywikibot.Site('wikidata','wikidata')
site.login()

optin = pywikibot.Page(site,'User:BeneBot*/RfD-optin#List').get(force=True)
user_regex = re.compile('^\*\s*\[\[User\:(?P<name>[^\[\]]+)\]\](\n|$)', flags=re.MULTILINE)
optin = [x.group('name') for x in user_regex.finditer(optin)]

regex = re.compile('== \[\[(?P<qid>Q\d*?)\]\] ==(?P<text>.*?)((?===)|$)', flags=re.DOTALL)
page = pywikibot.Page(site, 'Wikidata:Requests for deletions')
text = oldtext = page.get(force=True)
count = 0
x = list(regex.finditer(text))
for m in x:
    q = pywikibot.Page(site, m.group('qid'))
    print q
    if (not 'done}}' in m.group('text').lower() and not '{{deleted' in m.group('text').lower()) and (not q.exists()):
        t = m.group()
        by = list(q.site.logevents(logtype='delete',page=q))[0].user()
        if by in optin:
            print 'deleted by %s'%by
            t = re.sub(ur'\n+$','',t)+'\n:{{deleted|admin=%s}} --~~~~\n'%by
            text = text.replace(m.group(), t)
            count+=1
        else:
            print '%s has not opted-in, skipping'%by
pywikibot.showDiff(oldtext, text)

page.put(text, pywikibot.i18n.translate('en','Bot: marking %(count)d request{{PLURAL:%(count)d||s}} as deleted',{'count':count}), minorEdit=True, botflag=True)

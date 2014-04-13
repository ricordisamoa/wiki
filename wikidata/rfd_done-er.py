# -*- coding: utf-8  -*-
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
import re
import pywikibot

pywikibot.handleArgs()

site = pywikibot.Site().data_repository()
site.login()

user_regex = re.compile('^\*\s*\[\[User\:(?P<name>[^\[\]]+)\]\](\n|$)', flags=re.MULTILINE)
item_regex = re.compile('== \[\[(?P<qid>Q\d*?)\]\] ==(?P<text>.*?)((?===)|$)', flags=re.DOTALL)

"""
OLD CODE FOR OPT-IN LIST

optin = pywikibot.Page(site, 'BeneBot*/RfD-optin#List', ns=2).get(force=True)
optin = [x.group('name') for x in user_regex.finditer(optin)]
"""

optout = pywikibot.Page(site, 'BeneBot*/RfD-optout#List', ns=2).get(force=True)
optout = [x.group('name') for x in user_regex.finditer(optout)]

page = pywikibot.Page(site, 'Requests for deletions', ns=4)
text = page.get(force=True)

marked = []

for m in item_regex.finditer(text):
    q = pywikibot.ItemPage(site, m.group('qid'))
    print q
    if '{{done' not in m.group('text').lower() and '{{deleted' not in m.group('text').lower():
        t = m.group()
        deleted = None
        if (not q.exists()):
            deleted = q
        elif q.exists() and len(list(q.site.logevents(logtype='delete', page=q))) == 0:
            search = re.search(ur'([Dd]ouble with|[Dd]uplicate of|[Mm]erged (to|into|with)) \[\[(?P<qid>[Qq]\d+)\]\]', m.group())
            if search:
                deleted = pywikibot.ItemPage(site, search.group('qid'))
        if not deleted:
            pywikibot.output(u'no deleted item found, skipping')
            continue
        if deleted and deleted.exists():
            pywikibot.output(u'the item still exists, skipping')
            continue
        deleted_log = list(deleted.site.logevents(logtype='delete', page=deleted))
        if len(deleted_log) != 1:
            pywikibot.output(u'\03{lightyellow}deletion log for %s contains %d entries, skipping' % (deleted.getID(), len(deleted_log)))
            continue
        by = deleted_log[0].user()
        if by in optout:
            pywikibot.output(u'\03{lightyellow}%s has opted-out, skipping' % by)
            continue
        addition = ('{{deleted|admin=%s}}' if deleted.getID() == q.getID() else '{{deleted}} the other one by {{user|%s}}') % by
        pywikibot.output(u'\03{lightgreen}%s' % addition)
        t = re.sub(ur'\n+$', '', t) + '\n:' + addition + ' --~~~~\n'
        page.text = page.text.replace(m.group(), t)
        marked.append(q.getID())
if len(marked) > 0:
    summary = u'Bot: marking %(count)d request{{PLURAL:%(count)d||s}} as deleted'
    summary = pywikibot.i18n.translate(site, summary, {'count': len(marked)})
    if len(marked) == 1:
        summary = u'/* %s */ %s' % (marked[0], summary)
    pywikibot.showDiff(oldtext, text)
    page.text = text
    page.put(text, summary, minorEdit=True, botflag=True)
else:
    pywikibot.output(u'\03{lightgreen}no requests to be marked!')

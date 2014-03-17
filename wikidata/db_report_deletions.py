# -*- coding: utf-8  -*-

import re
import pywikibot

pywikibot.handleArgs()

site = pywikibot.Site().data_repository()
site.login()

ns = site.namespace(2)
page = pywikibot.Page(site, 'Database reports/Deletions', ns=4)
text = page.get(force=True)

admins = list(site.allusers(group='sysop'))
howmany = len(admins)

pywikibot.output(u'{num} {name} to check'.format(
    name=site.mediawiki_message('group-sysop').lower(),
    num=howmany))

table = '{| class="wikitable sortable plainlinks"\n|-\n! {{lcfirst:{{int:' \
        'userlogin-yourname}}}} !! {{lcfirst:{{int:deletionlog}}}} !! ns:0'
for admin in admins:
    deletions = list(site.logevents(logtype='delete', user=admin['name']))
    ns0 = len([True for entry in deletions if entry.ns() == 0])
    deletions = len(deletions)
    pywikibot.output(u'{user} has {deletions} deletions, out of which {ns0}'
                     u'in the main namespace; {rem} remaining'.format(
                         user=admin['name'],
                         deletions=deletions, ns0=ns0,
                         rem=howmany-admins.index(admin)-1))
    table += u'\n|-\n| [[{ns}:{user}|{user}]] || [{{{{fullurl:Special:Log/' \
             u'delete|user={usere}}}}} {{{{formatnum:{num}}}}}] || [{{{{' \
             u'fullurl:Special:Log/delete|namespace=0&user={usere}}}}} {{{{' \
             u'formatnum:{ns0}}}}}]'.format(ns=ns, user=admin['name'],
                                            usere=admin['name'].replace(' ',
                                                                        '_'),
                                            num=deletions, ns0=ns0)
table += '\n|}'

parts = re.split(ur'(\<\!\-\- *bot\:start *\-\-\>\n*)', page.text,
                 flags=re.IGNORECASE)[0:2]
parts.append(table)
parts += re.split(ur'(\n*\<\!\-\- *bot\:end *\-\-\>)', page.text,
                  flags=re.IGNORECASE)[1:3]

page.text = ''.join(parts)
pywikibot.showDiff(text, page.text)

page.save(comment=u'update database report', botflag=True)

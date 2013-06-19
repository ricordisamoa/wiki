# -*- coding: utf-8  -*-

import re
import pywikibot

pywikibot.handleArgs()

site = pywikibot.Site('wikidata','wikidata').data_repository()
site.login()

ns = site.namespace(2)
page = pywikibot.Page(site,'Database reports/Deletions',ns=4)
text = page.get(force=True)
table = '{| class="wikitable sortable plainlinks"\n|-\n! {{lcfirst:{{int:userlogin-yourname}}}} !! {{lcfirst:{{int:deletionlog}}}} !! ns:0'

admins = list(site.allusers(group='sysop'))
howmany = len(admins)
pywikibot.output('{num} {name} to check'.format(name=site.mediawiki_message('group-sysop').lower(),num=howmany))
for sysop in admins:
	deletions = list(site.logevents(logtype='delete',user=sysop['name']))
	ns0 = len([True for entry in deletions if entry.ns()==0])
	deletions = len(deletions)
	pywikibot.output('{user} has {deletions} deletions, out of which {ns0} in the main namespace; {rem} remaining'.format(user=sysop['name'],deletions=deletions,ns0=ns0,rem=len(admins)-admins.index(sysop)-1))
	table += u'\n|-\n| [[{ns}:{user}|{user}]] || [{{{{fullurl:Special:Log/delete|user={usere}}}}} {{{{formatnum:{num}}}}}] || [{{{{fullurl:Special:Log/delete|namespace=0&user={usere}}}}} {{{{formatnum:{ns0}}}}}]'.format(ns=ns,user=sysop['name'],usere=sysop['name'].replace(' ','_'),num=deletions,ns0=ns0)
table += '\n|}'
page.text = ''.join(re.split(ur'(\<\!\-\- *bot\:start *\-\-\>\n*)',page.text,flags=re.IGNORECASE)[0:2]) + table + ''.join(re.split(ur'(\n*\<\!\-\- *bot\:end *\-\-\>)',page.text,flags=re.IGNORECASE)[1:3])
pywikibot.showDiff(text,page.text)
print page.text
page.save(comment='[['+site.namespace(4)+':Bot|Bot]]: update database report',botflag=True)

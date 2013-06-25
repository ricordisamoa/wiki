# -*- coding: utf-8  -*-

import re
import pywikibot

pywikibot.handleArgs()

site = pywikibot.Site('wikidata','wikidata').data_repository()
site.login()

nlwiki = pywikibot.Site('nl','wikipedia')
enwiki = pywikibot.Site('en','wikipedia')

nlcat = u'Planetoïdenlijst'
nlmatch = ur'^Lijst van planetoïden (\d+)[\-\–](\d+)$'
enformat = u'List of minor planets/{}–{}'

for nlpage in pywikibot.Category(nlwiki,nlcat).articles():
	match = re.match(nlmatch,nlpage.title())
	if not match:
		continue
	print nlpage.title()
	print match.group(1),match.group(2)
	enpage = pywikibot.Page(enwiki,enformat.format(match.group(1),match.group(2)))
	print enpage.title()
	if not enpage.exists():
		continue
	nlitem = pywikibot.ItemPage.fromPage(nlpage)
	enitem = pywikibot.ItemPage.fromPage(enpage)
	if enitem.exists():
		if nlitem.exists():
			# TODO: compare and merge the two items
			pass
		else:
			try:
				enitem.get(force=True)
				newdata = {'sitelinks':{}}
				newdata['sitelinks'][nlwiki.dbName()] = {'site':nlwiki.dbName(),'title':nlpage.title()}
				if not nlwiki.lang in enitem.labels:
					newdata['labels'] = {}
					newdata['labels'][nlwiki.lang] = {'language':nlwiki.lang,'value':nlpage.title()}
				enitem.editEntity(newdata)
				pywikibot.output('\03{lightgreen}editEntity successful\03{default}')
			except:
				pywikibot.output('\03{lightred}editEntity failed\03{default}')

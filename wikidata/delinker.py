# -*- coding: utf-8  -*-

import pywikibot
import mwparserfromhell

def main(commands='User:SamoaBot/Delinker/commands'):
	yellow=u'\03{lightyellow}%s\03{default}'
	wd=pywikibot.Site('wikidata','wikidata').data_repository()
	if not wd.logged_in():
		wd.login()
	basepage=pywikibot.Page(wd,commands)
	text=basepage.get(force=True)
	code=mwparserfromhell.parse(text)
	for template in code.ifilter_templates():
		if unicode(template.name).replace(basepage.title(),'').lower().strip()=='/row':
			if template.has_param('status'):
				pywikibot.output(yellow%'"status" field already set')
				continue
			if template.has_param('items'):
				pywikibot.output(yellow%'"items" field already set')
				continue
			if not template.has_param('from'):
				pywikibot.output(yellow%'"from" field not set')
				continue
			if not template.has_param('to'):
				pywikibot.output(yellow%'"to" field not set')
				continue
			if not template.has_param('reason'):
				pywikibot.output(yellow%'no reason stated')
				continue
			if not template.has_param('by'):
				pywikibot.output(yellow%'no assignee specified')
				continue
			itemfrom=pywikibot.ItemPage(wd,'Q'+unicode(template.get('from').value))
			itemto=pywikibot.ItemPage(wd,'Q'+unicode(template.get('to').value))
			summary=u'[[User:SamoaBot/Delinker|SamoaBot Delinker]]: migrating [[{itemfrom}]] to [[{itemto}]]'.format(itemfrom=itemfrom.getID().upper(),itemto=itemto.getID().upper())
			status=None
			count=0
			refs=list(itemfrom.getReferences(namespaces=[0]))
			if len(refs)==0:
				pywikibot.output(yellow%(u'%s has no references'%itemfrom.getID()))
				template.add('status','nothingtodo')
			else:
				count=0
				for page in refs:
					item=pywikibot.ItemPage(wd,page.title())
					item.get(force=True)
					for prop in item.claims:
						for claim in item.claims[prop]:
							if claim.getTarget()==itemfrom:
								claim.changeTarget(itemto,summary=summary)
								item.get(force=True)
								pywikibot.output(u'\03{lightgreen}changed claim target\03{default}')
								count+=1
				if count and count==len(refs) and len(list(itemfrom.getReferences(namespaces=[0])))==0:
					pywikibot.output(u'\03{lightgreen}delinking successful for %s\03{default}'%itemfrom.getID())
					template.add('status','done')
					template.add('items',str(count))
				else:
					pywikibot.output('\03{lightred}delinking unsuccessful for %s\03{default}'%itemfrom.getID())
					template.add('status','error')
	newtext=unicode(code)
	if newtext!=text:
		basepage.text=newtext
		pywikibot.showDiff(text,basepage.text)
		basepage.save(comment='[[Wikidata:Bots|Bot]]: updating delinker status',botflag=True)

if __name__ == '__main__':
	main()

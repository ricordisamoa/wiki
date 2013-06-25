# -*- coding: utf-8  -*-

import re
import sys
import urllib2
import pywikibot
from wd_import import from_page as import_from_page

site = pywikibot.Site('wikidata','wikidata').data_repository()
site.login()

prop = 'p21'

male = pywikibot.ItemPage(site,'Q6581097')
personal_name = pywikibot.ItemPage(site,'Q1071027')

lines = list(urllib2.urlopen('https://tools.wmflabs.org/magnustools/static_data/male.txt'))

pywikibot.handleArgs()

pywikibot.output(u'{} items to process'.format(len(lines)))
if len(sys.argv)>1:
	limits = (int(sys.argv[1].split('-')[0]),int(sys.argv[1].split('-')[1]))
	lines = list(lines)[limits[0]:limits[1]]
	pywikibot.output(u'items limited from {0[0]} to {0[1]}'.format(limits))

def log(title,item,text=''):
	pywikibot.output(u'\03{{lightyellow}}item {qid}{text}\03{{default}}'.format(qid=item.getID(),text=text))
	page = pywikibot.Page(site,title)
	page.get(force=True)
	add = u'*{{{{Q|{qid}}}}}'.format(qid=item.getID().replace('q',''))+text
	if not add in page.text:
		page.text += '\n'+add
		page.save(u'[[Wikidata:Bots|Bot]]: [[{qid}]]{text}'.format(qid=item.getID(),text=text),minor=True,botflag=True)

for line in lines:
	item = pywikibot.ItemPage(site,line)
	if not item.exists():
		pywikibot.output(u'\03{{lightred}}item {qid} does not exist\03{{default}}'.format(qid=item.getID()))
		continue
	item.get(force=True)
	if 'itwiki' in item.sitelinks:
		pywikibot.output(u'\03{{lightyellow}}trying to import {propid} for {qid} from itwiki sitelink: {ittitle}\03{{default}}'.format(propid=prop,qid=item.getID(),ittitle=item.sitelinks['itwiki']))
		import_from_page(pywikibot.Page(pywikibot.Site('it','wikipedia'),item.sitelinks['itwiki']),import_data=[prop])
		item.get(force=True)
	if 'en' in item.labels:
		if re.search(ur'\bthe\b',item.labels['en']):
			log('User:SamoaBot/sex doubts',item,u' contains "the" in English label: "{label}"'.format(label=item.labels['en']))
			continue
		if re.search(ur'\band\b',item.labels['en']):
			log('User:SamoaBot/sex doubts',item,u' contains "and" in English label: "{label}"'.format(label=item.labels['en']))
			continue
	reference = pywikibot.Claim(site,'p143')
	reference.setTarget(personal_name)
	item.get(force=True)
	if not prop in item.claims:
		claim = pywikibot.Claim(site,prop)
		claim.setTarget(male)
		item.addClaim(claim)
		pywikibot.output(u'\03{{lightgreen}}{qid}: claim successfully added\03{{default}}'.format(qid=item.getID()))
		claim.addSource(reference,bot=1)
		pywikibot.output(u'\03{{lightgreen}}{qid}: source "personal name" successfully added\03{{default}}'.format(qid=item.getID()))
		continue
	item.get(force=True)
	if prop in item.claims and len(item.claims[prop])==1 and item.claims[prop][0].getTarget().getID()==male.getID():
		try:
			item.claims[prop][0].addSource(reference,bot=1)
			pywikibot.output(u'\03{{lightgreen}}{qid}: source "personal name" successfully added\03{{default}}'.format(qid=item.getID()))
		except:
			pass
		continue
	log('User:SamoaBot/sex conflicts',item,u' has "{{{{P|{propid}}}}} = {value}"'.format(propid=prop.replace('q',''),value=', '.join([u'{{{{Q|{qid}}}}}'.format(qid=claim.getTarget().getID().replace('q','')) for claim in item.claims[prop]])))

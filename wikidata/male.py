# -*- coding: utf-8  -*-

import re
import urllib2
import pywikibot

site = pywikibot.Site('wikidata','wikidata').data_repository()
site.login()

prop = 'p21'

male = pywikibot.Claim(site,prop)
male.setTarget(pywikibot.ItemPage(site,'Q6581097'))

reference = pywikibot.Claim(site,'p143')
reference.setTarget(pywikibot.ItemPage(site,'Q1071027'))

pywikibot.handleArgs()

def log(title,item,text=''):
	pywikibot.output(u'\03{{lightyellow}}item {qid}{text}\03{{default}}'.format(qid=item.getID(),text=text))
	page = pywikibot.Page(site,title)
	page.get(force=True)
	page.text += '\n'+u'*{{{{Q|{qid}}}}}'.format(qid=item.getID())+text
	page.save(u'[[Wikidata:Bots|Bot]]: [[{qid}]]{text}'.format(qid=item.getID(),text=text),minor=True,botflag=True)

for line in urllib2.urlopen('https://tools.wmflabs.org/magnustools/static_data/male.txt'):
	item = pywikibot.ItemPage(site,line)
	if not item.exists():
		pywikibot.output(u'\03{{lightred}}item {qid} does not exist\03{{default}}'.format(qid=item.getID()))
		continue
	item.get(force=True)
	if 'en' in item.labels:
		if re.search(ur'\bthe\b',item.labels['en']):
			log('User:SamoaBot/sex doubts',item,u'contains "the" in English label: "{label}"'.format(label=item.labels['en']))
			continue
		if re.search(ur'\band\b',item.labels['en']):
			log('User:SamoaBot/sex doubts',item,u'contains "and" in English label: "{label}"'.format(label=item.labels['en']))
			continue
	if not prop in item.claims:
		item.addClaim(male)
		pywikibot.output(u'\03{{lightgreen}}{qid}: claim successfully added\03{{default}}'.format(qid=item.getID()))
		male.addSource(reference,bot=1)
		pywikibot.output(u'\03{{lightgreen}}{qid}: source successfully added\03{{default}}'.format(qid=item.getID()))
		continue
	if prop in item.claims and len(item.claims[prop])==1 and item.claims[prop][0].getTarget().getID()==male.getTarget().getID():
		item.claims[prop][0].addSource(reference,bot=1)
		pywikibot.output(u'\03{{lightgreen}}{qid}: source successfully added\03{{default}}'.format(qid=item.getID()))
		continue
	log('User:SamoaBot/sex conflicts',item,u'has "{{{{P|{propid}}}}} = {value}"'.format(propid=prop.replace('q',''),value=', '.join([u'{{{{Q|{qid}}}}}'.format(qid=claim.getTarget().getID()) for claim in item.claims[prop]])))

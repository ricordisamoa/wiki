# -*- coding: utf-8  -*-

import re
import pywikibot

site = pywikibot.Site('wikidata','wikidata').data_repository()
site.login()

def del_msg(item):
	try:
		pywikibot.output(u'{item} was deleted by {sysop}'.format(item=item.getID(),sysop=list(site.logevents(logtype='delete',page=item,total=1))[0].user()))
	except:
		pywikibot.output(u'{item} does not exist'.format(item=item.getID()))

def merge_items(item1,item2,force_lower=True,taxon_mode=True):
	if force_lower:
		item1,item2=sorted((item1,item2),key=lambda j: int(j.getID().lower().replace('q','')))
	if not item1.exists():
		del_msg(item1)
		return
	if not item2.exists():
		del_msg(item2)
		return
	pywikibot.output(u'merging {item1} with {item2}'.format(item1=item1.getID(),item2=item2.getID()))
	# TODO: implement the actual merging mechanism

def main(source='User:Soulkeeper/dups',sourcetype=list,taxon_mode=True):
	text = pywikibot.Page(site,source).get(force=True)
	regex = re.compile('^\*\s*\w+[\w\s]*\[\[\:?(?P<item1>[Qq]\d+)\]\] \[\[\:?(?P<item2>[Qq]\d+)\]\]\n',flags=re.MULTILINE)
	for match in regex.finditer(text):
		item1 = pywikibot.ItemPage(site,match.group('item1'))
		item2 = pywikibot.ItemPage(site,match.group('item2'))
		merge_items(item1,item2,taxon_mode=taxon_mode)

if __name__=='__main__':
	pywikibot.handleArgs()
	main()

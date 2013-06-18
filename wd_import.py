# -*- coding: utf-8  -*-

import pywikibot
import mwparserfromhell

wd=pywikibot.Site('wikidata','wikidata').data_repository()

harvesting=[
	{
		'name':['authority control','normdaten',u'controllo di autorità',u'autorité'],
		'params':[
			{
				'name':'VIAF',
				'claims':'p214',
				'remove':'itwiki'
			},{
				'name':'LCCN',
				'claims':'p244',
				'remove':'itwiki'
			}
		]
	}
]

def from_page(page,import_data=True,remove=False):
	print page.title()
	text=page.get(force=True)
	code=mwparserfromhell.parse(text)
	for template in code.ifilter_templates():
		tname=template.name.lower().strip()
		for harv in harvesting:
			if tname==harv['name'] or tname in harv['name']:
				for param in harv['params']:
					for pname in ([param['name']] if isinstance(param['name'],basestring) else param['name']):
						if template.has_param(pname):
							pywikibot.output('\03{lightgreen}%s parameter found in %s: %s\03{default}'%(pname,template.name,template.get(pname)))
							break
				break

if __name__=='__main__':
	total=None
	import_data=True
	remove=False
	site=pywikibot.Site()
	cat=None
	recurse=None
	template=None
	start=None
	for arg in pywikibot.handleArgs():
		if arg.startswith('-total:'):
			total=int(arg[7:])
		elif arg.startswith('-noimport'):
			import_data=False
		elif arg.startswith('-remove'):
			remove=True
		elif arg.startswith('-wiki:'):
			site=pywikibot.Site(arg[6:],'wikipedia')
		elif arg.startswith('-cat:'):
			cat=arg[5:]
		elif arg.startswith('-category:'):
			cat=arg[10:]
		elif arg.startswith('-recurse:'):
			recurse=int(arg[9:])
		elif arg.startswith('-template:'):
			template=arg[10:]
		elif arg.startswith('-start:'):
			start=arg[7:]
	pages=[]
	if template:
		pages=pages+list(pywikibot.Page(site,template,ns=10).getReferences(namespaces=0,onlyTemplateInclusion=True,total=total))
	if cat:
		pages=pages+list(pywikibot.Category(site,cat).articles(namespaces=0,startsort=start,total=total,recurse=recurse))
	for page in sorted([page for page in list(set(pages)) if page.title()>=start]):
		from_page(page,import_data=import_data,remove=remove)

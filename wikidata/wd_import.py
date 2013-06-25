# -*- coding: utf-8  -*-

import string
import pywikibot
import mwparserfromhell
from references import languages as reference_languages

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
	},
	{
		'name':['bio'],
		'sites':['itwiki'],
		'params':[
			{
				'name':['Sesso','sesso'],
				'claims':'p21',
				'filter':[string.strip,string.upper],
				'map':{
					'M':pywikibot.ItemPage(wd,'Q6581097'),
					'F':pywikibot.ItemPage(wd,'Q6581072')
				}
			}
		]
	}
]

def from_page(page,import_data=True,remove=False):
	pywikibot.output(u'parsing {page}'.format(page=page))
	item=pywikibot.ItemPage.fromPage(page)
	if not item.exists():
		pywikibot.output(u'\03{{lightyellow}}item not found for {page}\03{{default}}'.format(page=page))
		return False
	text=page.get(force=True)
	code=mwparserfromhell.parse(text)
	imported=[]
	for template in code.ifilter_templates():
		tname=template.name.strip()
		for harv in harvesting:
			if tname==harv['name'] or tname in harv['name'] or tname.lower()==harv['name'] or tname.lower() in harv['name']:
				if 'sites' in harv and (not page.site.dbName() in harv['sites']):
					pywikibot.output(u'\03{lightyellow}%s template was found but skipped because site is not whitelisted\03{default}'%template.name)
					continue
				for param in harv['params']:
					for pname in ([param['name']] if isinstance(param['name'],basestring) else param['name']):
						if template.has_param(pname):
							rawvalue=value=unicode(template.get(pname).value)
							pywikibot.output(u'\03{lightgreen}%s parameter found in %s: %s\03{default}'%(pname,tname,value))
							if 'filter' in param:
								for func in (param['filter'] if isinstance(param['filter'],list) else [param['filter']]):
									value=func(value)
							if 'map' in param:
								if value in param['map']:
									value=param['map'][value]
								else:
									pywikibot.output(u'\03{lightyellow}%s value was skipped because it is not mapped\03{default}'%value)
									continue
							if value!=rawvalue:
								pywikibot.output(u'{pname} parameter formatted from {frm} to {to}'.format(pname=pname,frm=rawvalue,to=value))
							if import_data:
								for prop in (param['claims'] if isinstance(param['claims'],list) else [param['claims']]):
									if isinstance(import_data,list) and not prop in import_data:
										pywikibot.output(u'\03{lightyellow}%s claim was to be added but was skipped because it is not whitelisted\03{default}'%prop)
									else:
										claim=pywikibot.Claim(wd,prop)
										claim.setTarget(value)
										reference=pywikibot.Claim(wd,'p143')
										reference.setTarget(pywikibot.ItemPage(wd,'Q'+str(reference_languages[page.site.lang])))
										reference.getTarget().get()
										if not prop in item.claims:
											item.addClaim(claim)
											pywikibot.output(u'\03{{lightgreen}}{qid}: claim successfully added\03{{default}}'.format(qid=item.getID()))
											claim.addSource(reference,bot=1)
											pywikibot.output(u'\03{{lightgreen}}{qid}: source "{source}" successfully added\03{{default}}'.format(qid=item.getID(),source=reference.getTarget().labels['en']))
											item.get(force=True)
											imported.append(prop)
										elif prop in item.claims and len(item.claims[prop])==1 and item.claims[prop][0].getTarget()==claim.getTarget():
											try:
												item.claims[prop][0].addSource(reference,bot=1)
												pywikibot.output(u'\03{{lightgreen}}{qid}: source "{source}" successfully added\03{{default}}'.format(qid=item.getID(),source=reference.getTarget().labels['en']))
												item.get(force=True)
												imported.append(prop)
											except:
												pass
							break
				break
	return imported

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

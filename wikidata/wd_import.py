# -*- coding: utf-8  -*-

import re
import string
import pywikibot
import mwparserfromhell
from references import sites as reference_sites

wd=pywikibot.Site().data_repository()

def format_lccn(prev):
	prev=re.sub(r'^http:\/\/lccn\.loc\.gov\/(.+)$','\g<1>',prev)
	prev=prev.strip().replace(u'\u200f','').replace(' ','').replace('-','').replace('.','')
	try:
		prev=re.sub(r'(\w\/\d+)','\g<1>'+('0'*(6-len(re.search(r'\w\/\d+\/(\d+)',prev).group(1)))),prev,count=1)
	except:
		pass
	prev=re.sub(r'\/','',prev)
	try:
		prev=re.sub(r'(?<=\d{2})','0'*(8-len(re.search(r'\d+',prev).group(0))),prev,count=1)
	except:
		pass
	if re.match(ur'^\w+\d+$',prev):
		return prev
	return False

harvesting=[
	{
		'name':['authority control','normdaten',u'controllo di autorità',u'autorité'],
		'params':[
			{
				'name':'VIAF',
				'claims':'p214',
				'remove':'itwiki',
				'filter':[string.strip,'^\d+$']
			},{
				'name':'GND',
				'claims':'p227',
				'filter':[string.strip,'^(1|10)\d{7}[0-9X]|[47]\d{6}-\d|[1-9]\d{0,7}-[0-9X]|3\d{7}[0-9X]$'],
				'remove':'itwiki'
			},{
				'name':'LCCN',
				'claims':'p244',
				'filter':format_lccn,
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
	},
	{
		'name':['botanici','botanist'],
		'sites':['itwiki','enwiki'],
		'params':[
			{
				'name':'1',
				'displayed':'Botanici',
				'claims':'p428',
				'filter':ur'^[\w\.\s]+$',
				'remove':'itwiki'
			}
		]
	},
	{
		'name':['Divisione amministrativa'],
		'sites':['itwiki'],
		'params':[
			{
				'name':'Codice statistico',
				'claims':'p635',
				'filter':ur'^\d{6}$'
			},
			{
				'name':'Codice catastale',
				'claims':'p806',
				'filter':ur'^\w\d{3}$'
			}
		]
	},
	{
		'name':['Wdpa'],
		'sites':['frwiki'],
		'params':[
			{
				'name':'1',
				'displayed':'WDPA',
				'claims':'p809',
				'filter':[string.strip,ur'^\d+$']
			}
		]
	},
	{
		'name':[u'Infobox Aire protégée'],
		'sites':['frwiki'],
		'params':[
			{
				'name':'wdpa',
				'displayed':'WDPA',
				'claims':'p809',
				'filter':[string.strip,ur'^\d+$']
			}
		]
	}
]

field_removal_summary={
	'it':'[[Wikipedia:Bot|Bot]]: rimozione camp{{PLURAL:%(fields_num)d|o|i}} %(fields)s migrat{{PLURAL:%(fields_num)d|o|i}} a [[d:|Wikidata]]: [[d:%(qid)s]]'
}

def remove_if(removed,template,field,value,text,displayed=None):
	if not displayed:
		displayed=field
	template_text=unicode(template)
	if not template.has_param(field,False) and template.has_param(field.upper(),False):
		field=field.upper()
	conflict=True
	if template.has_param(field,False):
		try:
			if unicode(template.get(field).value).strip()==value or (field=='LCCN' and format_lccn(unicode(template.get(field).value).strip())==value):
				template.remove(field,force_no_field=True)
				pywikibot.output(u'\03{{lightgreen}}field {} matches: removed\03{{default}}'.format(field))
				conflict=False
				removed.append(displayed)
			elif unicode(template.get(field).value).strip()=='':
				template.remove(field,force_no_field=True)
				pywikibot.output(u'\03{{lightgreen}}field {} empty: removed\03{{default}}'.format(field))
				conflict=False
				removed.append(displayed)
			else:
				pywikibot.output(u'\03{{lightyellow}}field {} does not match: cannot be removed\03{{default}}'.format(field))
		except:
			pass
	else:
		pywikibot.output(u'\03{{lightyellow}}field {} not found in template\03{{default}}'.format(field))
	return text.replace(template_text,unicode(template)),removed,conflict

def from_page(page,import_data=True,remove=False,remove_all_only=True,autosave=False):
	pywikibot.output(u'parsing {page}'.format(page=page))
	item=pywikibot.ItemPage.fromPage(page)
	if not item.exists():
		pywikibot.output(u'\03{{lightyellow}}item not found for {page}\03{{default}}'.format(page=page))
		return False
	text=page.get(force=True)
	code=mwparserfromhell.parse(text)
	imported=[]
	removed=[]
	for template in code.ifilter_templates():
		tname=template.name.strip()
		for harv in harvesting:
			if tname==harv['name'] or tname in harv['name'] or tname.lower()==harv['name'] or tname.lower() in harv['name']:
				if 'sites' in harv and (not page.site.dbName() in harv['sites']):
					pywikibot.output(u'\03{lightyellow}%s template was found but skipped because site is not whitelisted\03{default}'%template.name)
					continue
				for param in harv['params']:
					can_remove=False
					if 'remove' in param and (param['remove']==True or param['remove']==page.site.dbName() or page.site.dbName() in param['remove']):
						can_remove=True
					for pname in ([param['name']] if isinstance(param['name'],basestring) else param['name']):
						if template.has_param(pname):
							rawvalue=value=unicode(template.get(pname).value)
							pywikibot.output(u'\03{lightgreen}%s parameter found in %s: %s\03{default}'%(pname,tname,value))
							if 'filter' in param:
								for filtr in (param['filter'] if isinstance(param['filter'],list) else [param['filter']]):
									if callable(filtr):
										value=filtr(value)
									else:
										match=re.search(filtr,value)
										if match:
											value=match.group(0)
										else:
											pywikibot.output(u'\03{{lightyellow}}{} value was skipped because it is excluded by filter\03{{default}}'.format(value))
											continue
							if 'map' in param:
								if value in param['map']:
									value=param['map'][value]
								else:
									pywikibot.output(u'\03{{lightyellow}}{} value was skipped because it is not mapped\03{{default}}'.format(value))
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
										reference.setTarget(pywikibot.ItemPage(wd,'Q'+str(reference_sites[page.site.dbName()])))
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
							if can_remove and remove and (isinstance(param['claims'],basestring) or len(param['claims'])==1):
								prop=(param['claims'] if isinstance(param['claims'],basestring) else param['claims'][0])
								if prop in item.claims and len(item.claims[prop])==1:
									page.text,removed,conflict=remove_if(removed,template,pname,item.claims[prop][0].getTarget(),page.text,displayed=(param['displayed'] if 'displayed' in param else pname))
									if conflict and remove_all_only:
										remove=False
								elif remove_all_only:
									remove=False
							break
						elif can_remove and template.has_param(pname,False):
							page.text,removed,conflict=remove_if(removed,template,pname,'',page.text,displayed=(param['displayed'] if 'displayed' in param else pname))
							if conflict and remove_all_only:
								remove=False
				break
	if remove and removed:
		pywikibot.showDiff(text,page.text)
		comment=pywikibot.i18n.translate(page.site,field_removal_summary,{'fields_num':len(removed),'fields':', '.join(removed),'qid':item.getID().upper()})
		if autosave or pywikibot.inputChoice(page.title()+' @ '+comment,['Yes', 'No'],['Y', 'N'],'N').strip().lower() in ['yes','y']:
			try:
				page.save(comment=comment,minor=True,botflag=True)
			except Exception, e:
				print e
	return (imported,removed)

if __name__=='__main__':
	total=None
	import_data=True
	remove=False
	autosave=False
	cat=None
	recurse=None
	template=None
	start=None
	titles=[]
	for arg in pywikibot.handleArgs():
		if arg.startswith('-total:'):
			total=int(arg[7:])
		elif arg.startswith('-noimport'):
			import_data=False
		elif arg.startswith('-import:'):
			import_data=(list(set(import_data+[arg[8:]])) if isinstance(import_data,list) and len(import_data)>0 else [arg[8:]])
		elif arg.startswith('-remove'):
			remove=True
		elif arg.startswith('-autosave'):
			autosave=True
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
		elif arg.startswith('-page:'):
			titles.append(arg[6:])
	site=pywikibot.Site()
	pages=[pywikibot.Page(site,title) for title in titles]
	if template:
		pages=pages+list(pywikibot.Page(site,template,ns=10).getReferences(namespaces=0,onlyTemplateInclusion=True,total=total))
	if cat:
		pages=pages+list(pywikibot.Category(site,cat).articles(namespaces=0,startsort=start,total=total,recurse=recurse))
	for page in sorted([page for page in list(set(pages)) if page.title()>=start]):
		from_page(page,import_data=import_data,remove=remove,autosave=autosave)

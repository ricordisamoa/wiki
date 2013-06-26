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

def dump(xdict):
	lines=[]
	maxlen=max([len(key) for key in xdict.keys()])
	for key in xdict:
		if len(xdict[key])==0:
			continue
		mlen=max([len(f) for f in xdict[key].keys()])
		for k in xdict[key]:
			lines.append(key+' '*(maxlen-len(key))+k+' '*(mlen-len(k))+' : '+str(xdict[key][k]))
	return '\n'.join(lines)

def empty(xdict):
	for key in xdict.keys():
		if isinstance(xdict[key],list):
			xdict[key]=[u'']*len(xdict[key])
		else:
			xdict[key]=u''
	return xdict

def compare(item1,item2,dictname):
	dict1=getattr(item1,dictname)
	dict2=getattr(item2,dictname)
	for key in dict1:
		if key in dict2 and dict2[key]!=dict1[key]:
			pywikibot.output(u'\03{{lightred}}{key} conflicting in {dictname}: {val1} in {item1} but {val2} in {item2}\03{{default}}'.format(key=key,dictname=dictname,item1=item1.getID(),item2=item2.getID(),val1=dict1[key],val2=dict2[key]))
			return False
	return True

def clean_data(xdict):
	for site in xdict['sitelinks'].keys():
		xdict['sitelinks'][site]={'site':site,'title':xdict['sitelinks'][site]}
	for language in xdict['labels'].keys():
		xdict['labels'][language]={'language':language,'value':xdict['labels'][language]}
	for language in xdict['descriptions'].keys():
		xdict['descriptions'][language]={'language':language,'value':xdict['descriptions'][language]}
	for language in xdict['aliases'].keys():
		for index,item in enumerate(xdict['aliases'][language]):
			xdict['aliases'][language][index]={'language':language,'value':item}
	for key in xdict.keys():
		if len(xdict[key])==0:
			del xdict[key]
	return xdict

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
	item1.get(force=True)
	item2.get(force=True)
	if compare(item1,item2,'sitelinks')==False:
		return
	if compare(item1,item2,'labels')==False:
		return
	if compare(item1,item2,'descriptions')==False:
		return
	dup_sl=list(set(item1.sitelinks.values()+item2.sitelinks.values()))
	if taxon_mode and len(dup_sl)!=1:
		pywikibot.output(u'\03{lightyellow}'+str(dup_sl)+'\03{default}')
		return
	new_data={
		'sitelinks':item1.sitelinks,
		'labels':item1.labels,
		'aliases':item1.aliases,
		'descriptions':item1.descriptions
	}
	old_dump=dump(new_data)
	new_data['sitelinks'].update(item2.sitelinks)
	new_data['labels'].update(item2.labels)
	new_data['descriptions'].update(item2.descriptions)
	for language in item2.aliases:
		if language in new_data['aliases']:
			new_data['aliases'][language]=list(set(new_data['aliases'][language]+item2.aliases[language]))
		else:
			new_data['aliases'][language]=item2.aliases[language]
	pywikibot.output(u'\03{lightblue}diff for new_data:\03{lightblue}')
	pywikibot.showDiff(old_dump,dump(new_data))
	new_data=clean_data(new_data)
	empty_data={
		'sitelinks':item2.sitelinks,
		'labels':item2.labels,
		'aliases':item2.aliases,
		'descriptions':item2.descriptions
	}
	old_dump=dump(empty_data)
	for key in empty_data.keys():
		empty_data[key]=empty(empty_data[key])
	pywikibot.output(u'\03{lightblue}diff for empty_data:\03{lightblue}')
	pywikibot.showDiff(old_dump,dump(empty_data))
	empty_data=clean_data(empty_data)
	item2.editEntity(empty_data)
	pywikibot.output(u'\03{{lightgreen}}{qid} successfully emptied\03{{lightblue}}'.format(qid=item2.getID()))
	item1.editEntity(new_data)
	pywikibot.output(u'\03{{lightgreen}}{qid} successfully filled\03{{lightblue}}'.format(qid=item1.getID()))
	item1.get(force=True)
	item2.get(force=True)
	for prop in item2.claims:
		for claim2 in item2.claims[prop]:
			if prop in item1.claims:
				for claim1 in item1.claims[prop]:
					if claim1.getTarget()==claim2.getTarget():
						for source in claim2.sources:
							try:
								claim1.addSource(source,bot=1)
								pywikibot.output(u'\03{{lightgreen}}imported a source for {propid} into {qid}\03{{lightblue}}'.format(propid=prop,qid=item1.getID()))
								item1.get(force=True)
							except:
								pass
			else:
				claim=pywikibot.Claim(claim2.site,prop)
				claim.setTarget(claim2.getTarget())
				item1.addClaim(claim)
				pywikibot.output(u'\03{{lightgreen}}imported a claim for {propid} into {qid}\03{{lightblue}}'.format(propid=prop,qid=item1.getID()))
				for source in claim2.sources:
					try:
						claim.addSource(source,bot=1)
						pywikibot.output(u'\03{{lightgreen}}imported a source for {propid} into {qid}\03{{lightblue}}'.format(propid=prop,qid=item1.getID()))
						item1.get(force=True)
					except:
						pass
	delete_item(item2,item1)

def error_merge_msg(item1,item2):
	pywikibot.output(u'\03{{lightred}}error while merging {item1} and {item2}\03{{lightblue}}'.format(item1=item1.getID(),item2=item2.getID()))

def delete_item(item,other,by=site.user()):
	item.get(force=True)
	other.get(force=True)
	if len(item.sitelinks)>0:
		error_merge_msg(item,other)
		return
	if compare(item,other,'sitelinks')==False:
		return
	if compare(item,other,'labels')==False:
		return
	if compare(item,other,'descriptions')==False:
		return
	for key in item.aliases:
		for alias in item.aliases[key]:
			if alias.strip()!='' and ((not key in other.aliases) or (not alias in other.aliases[key])):
				error_merge_msg(item,other)
				return
	for prop in item.claims:
		if (not prop in other.claims) or len(list(set([claim.getTarget() for claim in item.claims[prop]])-set([claim.getTarget() for claim in other.claims[prop]]))):
			error_merge_msg(item,other)
			return
	item.delete(reason=u'Merged with [[{qid}]] by [[User:{by}|{by}]]'.format(qid=other.getID().upper(),by=by))
	pywikibot.output(u'\03{{lightgreen}}{qid} successfully deleted\03{{lightblue}}'.format(qid=item.getID()))

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

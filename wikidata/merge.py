# -*- coding: utf-8  -*-

import re
import json
import pywikibot

site = pywikibot.Site().data_repository()
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

def fromDBName(dbname):
	s=pywikibot.site.APISite.fromDBName(dbname)
	return pywikibot.Site(s.code,s.family.name)

def user_link(user):
	page=pywikibot.Page(user.site,'Contributions/'+user.name(),ns=-1)
	if (not user.isAnonymous()) and user.getUserPage().exists():
		page=user.getUserPage()
	return u'[[{}|{}]]'.format(page.title(),user.name())

def check_deletable(item,safe=True):
	if not item.exists():
		del_msg(item)
		return
	item.get(force=True)
	if len(item.sitelinks)>0:
		pywikibot.output(u'\03{{lightyellow}}{item} has {num} sitelinks, skipping\03{{default}}'.format(item=item,num=len(item.sitelinks)))
		return
	if len(item.claims)>0:
		pywikibot.output(u'\03{{lightyellow}}{item} has {num} claims, skipping\03{{default}}'.format(item=item,num=len(item.claims)))
		return
	refs=len(list(item.getReferences(namespaces=0)))
	if refs>0:
		pywikibot.output(u'\03{{lightyellow}}{item} has {num} references in the main namespace, skipping\03{{default}}'.format(item=item,num=refs))
		return
	print item.getID()
	history=list(item.fullVersionHistory())
	if len(history)==1:
		print u'created empty by '+history[0][2]
	elif len(history)==2:
		prev=json.loads(history[1][3])
		cur=json.loads(history[0][3])
		if 'links' in prev and len(prev['links'])==1 and (len(cur['links'])==0 or not 'links' in cur):
			removed_link=pywikibot.Link(prev['links'][prev['links'].keys()[0]],fromDBName(prev['links'].keys()[0]))
			removed_page=pywikibot.Page(removed_link)
			moved_into=pywikibot.ItemPage.fromPage(removed_page)
			if moved_into.exists():
				user=pywikibot.User(item.site,history[0][2])
				msg=u'{user} moved {link} into [[{qid}]]'.format(link=removed_link.astext(onsite=item.site),qid=moved_into.getID().upper(),user=user_link(user))
				if safe==False or 'autoconfirmed' in user.groups():
					# safety check: only delete the item if the last editor is autoconfirmed
					delete_item(item,moved_into,msg=msg)
				else:
					pywikibot.output(u'\03{{lightyellow}}Skipped: {msg}\03{{default}}'.format(msg=msg))
			else:
				pywikibot.output(u'\03{{lightyellow}}{page} does NOT have an associated item, skipping\03{{default}}'.format(page=removed_page))
	elif len(history)>2:
		pywikibot.output(u'\03{{lightyellow}}{item}\'s history has {num} entries, skipping\03{{default}}'.format(item=item,num=len(history)))

def merge_items(tupl,force_lower=True,taxon_mode=True):
	item1,item2 = tupl
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
	pywikibot.output(u'\03{{lightred}}error while merging {item1} and {item2}\03{{default}}'.format(item1=item1.getID(),item2=item2.getID()))

def delete_item(item,other,msg=None,by=site.user(),rfd=False):
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
	if rfd:
		rfd_page=pywikibot.Page(site,'Requests for deletions',ns=4)
		rfd_page.get(force=True)
		rfd_page.text+=u'\n\n{{{{subst:Request for deletion|itemid={qid}|reason={msg}}}}} --~~~~'.format(qid=item.getID(),msg=(msg if msg else u'Merged with {other}{by}'.format(other=other.getID(),by=(u' by [[User:{by}|{by}]]'.format(by=by) if by!=site.user() else ''))))
		page.save(comment=u'[[Wikidata:Bots|Bot]]: nominating [[{qid}]] for deletion'.format(qid=item.getID().upper()),minor=False,botflag=True)
		pywikibot.output(u'\03{{lightgreen}}{item} successfully nominated for deletion\03{{default}}'.format(item=item))
	else:
		item.delete(reason=(msg if msg else u'Merged with [[{qid}]] by [[User:{by}|{by}]]'.format(qid=other.getID().upper(),by=by)))
		pywikibot.output(u'\03{{lightgreen}}{item} successfully deleted\03{{default}}'.format(item=item))

if __name__=='__main__':
	cat=None
	lang2=None
	recurse=None
	total=None
	bulk=None
	for arg in pywikibot.handleArgs():
		if arg.startswith('-cat:'):
			cat=arg[5:]
		elif arg.startswith('-lang2:'):
			lang2=arg[7:]
		elif arg.startswith('-recurse:'):
			recurse=int(arg[9:])
		elif arg.startswith('-total:'):
			total=int(arg[7:])
		elif arg.startswith('-bulk:'):
			bulk=arg[6:]
		elif arg.startswith('-bulk'):
			bulk=True
	if cat and lang2:
		site2=pywikibot.Site(lang2,pywikibot.Site().family.name)
		for page1 in pywikibot.Category(pywikibot.Site(),cat).articles(recurse=recurse,total=total):
			page2=pywikibot.Page(site2,page1.title())
			if page2.exists():
				item1=pywikibot.ItemPage.fromPage(page1)
				item2=pywikibot.ItemPage.fromPage(page2)
				if item1!=item2:
					merge_items((item1,item2))
	elif bulk:
		text = pywikibot.Page(site,u'Requests for deletions/Bulk'+('' if bulk==True else '/'+bulk),ns=4).get(force=True)
		regex = re.compile('\|(?P<item>[Qq]\d+)')
		for match in list(regex.finditer(text)):#[124:]:
			check_deletable(pywikibot.ItemPage(site,match.group('item')))
	else:
		text = pywikibot.Page(site,'Soulkeeper/dups',ns=2).get(force=True)
		regex = re.compile('^\*\s*\w+[\w\s]*\[\[\:?(?P<item1>[Qq]\d+)\]\] \[\[\:?(?P<item2>[Qq]\d+)\]\]\n',flags=re.MULTILINE)
		for match in regex.finditer(text):
			merge_items((pywikibot.ItemPage(site,match.group('item1')),pywikibot.ItemPage(site,match.group('item2'))))

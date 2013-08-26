# -*- coding: utf-8  -*-

import re
import json
import pywikibot

site = pywikibot.Site().data_repository()

def del_msg(item):
	try:
		pywikibot.output(u'{item} was deleted by {sysop}'.format(item=item.getID(),sysop=list(site.logevents(logtype='delete',page=item,total=1))[0].user()))
	except:
		pywikibot.output(u'{item} does not exist'.format(item=item.getID()))

def flu(pages):
	if not isinstance(pages,list):
		pages=[pages]
	print 'flu: ',pages
	pywikibot.data.api.Request(site=pages[0].site,action='purge',forcelinkupdate=1,titles='|'.join([x.title() for x in pages])).submit()

def dump(xdict):
	lines=[]
	maxlen=max([len(key) for key in xdict.keys()])
	for key in xdict:
		if len(xdict[key])==0:
			continue
		mlen=max([len(f) for f in xdict[key].keys()])
		for k in xdict[key]:
			lines.append(key+' '*(maxlen+1-len(key))+k+' '*(mlen+1-len(k))+' : '+unicode(xdict[key][k]))
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
	history=list(item.fullVersionHistory())
	if len(history)>2:
		for entry in list(history[1:len(history)-1]):
			if 'bot' in pywikibot.User(item.site,entry[2]).groups():
				pywikibot.output(u'{item}: removed {bot} from history'.format(item=item,bot=entry[2]))
				del history[history.index(entry)]
	if len(history)==1:
		pywikibot.output(u'{item} has been created empty by {user}'.format(item=item,user=history[0][2]))
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

def duplicates(tupl,force_lower=True):
	if force_lower:
		tupl=sort_items(tupl)
	sl=None
	for item in tupl:
		if not item.exists():
			del_msg(item)
			return
		item.get(force=True)
		if len(item.sitelinks)!=1:
			pywikibot.output(u'\03{{lightyellow}}{item} has {num} sitelinks\03{{default}}'.format(item=item,num=len(item.sitelinks)))
			return
		mysl=pywikibot.Page(fromDBName(item.sitelinks.keys()[0]),item.sitelinks[item.sitelinks.keys()[0]])
		if sl:
			if mysl!=sl or mysl.site!=sl.site or sl.site.sametitle(sl,mysl)==False:
				pywikibot.output(u'\03{{lightyellow}}{item} has "{mysl}" sitelink instead of "{sl}"\03{{default}}'.format(item=item,mysl=mysl,sl=sl))
				return
		else:
			sl=mysl
		if len(item.claims)>0:
			pywikibot.output(u'\03{{lightyellow}}{item} has {num} claims\03{{default}}'.format(item=item,num=len(item.claims)))
			return
		if len(item.descriptions)>0 and (len(item.descriptions)>1 or (not 'es' in item.descriptions) or item.descriptions['es']!=u'categoría de Wikipedia'):
			pywikibot.output(u'\03{{lightyellow}}{item} has {num} descriptions\03{{default}}'.format(item=item,num=len(item.descriptions)))
			return
		if len(item.aliases)>0:
			pywikibot.output(u'\03{{lightyellow}}{item} has {num} aliases\03{{default}}'.format(item=item,num=len(item.aliases)))
			return
	pywikibot.output(u'\03{{lightpurple}}{items} have the same "{sl}" sitelink, no claims, no descriptions, and no aliases: preparing deletion\03{{default}}'.format(items=obj_join(tupl),sl=sl))
	kept=tupl[0]
	for deletable in tupl[1:]:
		delete_item(deletable,kept,msg=u'[[{proj}:True duplicates|True duplicate]] of [[{kept}]] by {link}'.format(proj=item.site.namespace(4),kept=kept.getID().upper(),link=pywikibot.Link.fromPage(sl).astext(onsite=item.site)),allow_sitelinks=True)
	flu(kept)

def sort_items(tupl):
	return sorted(tupl,key=lambda j: int(j.getID().lower().replace('q','')))

def obj_join(args):
	args=[str(e) for e in args]
	return ', '.join(args[:-2]+[' and '.join(args[-2:])])

def merge_items(tupl,force_lower=True,taxon_mode=True):
	item1,item2 = tupl
	if force_lower:
		item1,item2=sort_items((item1,item2))
	if not item1.exists():
		del_msg(item1)
		return
	if not item2.exists():
		del_msg(item2)
		return
	pywikibot.output(u'merging {item1} with {item2}'.format(item1=item1,item2=item2))
	item1.get(force=True)
	item2.get(force=True)
	if compare(item1,item2,'sitelinks')==False:
		return
	if compare(item1,item2,'labels')==False:
		return
	if compare(item1,item2,'descriptions')==False:
		return
	if taxon_mode:
		dup_sl=item1.sitelinks
		dup_sl.update(item2.sitelinks)
		dup_pg=[]
		for dbname in dup_sl:
			pg=pywikibot.Page(fromDBName(dbname),dup_sl[dbname])
			dup_pg.append((pg.title(withNamespace=False),pg.namespace()))
		if len(list(set(dup_pg)))!=1:
			pywikibot.output(u'\03{lightyellow}'+str(dup_pg)+'\03{default}')
			return
	else:
		pywikibot.output(u'\03{lightyellow}Warning: taxon mode disabled\03{default}')
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
	item2.editEntity(empty_data,summary='moving to [[{item1}]]'.format(item1=item1.getID().upper()))
	pywikibot.output(u'\03{{lightgreen}}{qid} successfully emptied\03{{lightblue}}'.format(qid=item2.getID()))
	item1.editEntity(new_data,summary='moved from [[{item2}]]'.format(item2=item2.getID().upper()))
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

def delete_item(item,other,msg=None,by=site.user(),rfd=False,allow_sitelinks=False):
	item.get(force=True)
	other.get(force=True)
	if allow_sitelinks!=True and len(item.sitelinks)>0:
		error_merge_msg(item,other)
		return
	if compare(item,other,'sitelinks')==False:
		return
	if compare(item,other,'labels')==False:
		return
	if compare(item,other,'descriptions')==False:
		return
	if by is None:
		by=item.site.data_repository().user()
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

def matchmerge(iterable,**kwargs):
	for match in iterable:
		merge_items((pywikibot.ItemPage(site,match.group('item1')),pywikibot.ItemPage(site,match.group('item2'))),**kwargs)

if __name__=='__main__':
	cat=None
	lang2=None
	recurse=None
	total=None
	bulk=None
	mode=None
	unflood=False
	ids=[]
	for arg in pywikibot.handleArgs():
		if arg.startswith('-cat:'):
			cat=arg[5:]
		elif arg.startswith('-lang2:'):
			lang2=arg[7:]
		elif arg.startswith('-recurse:'):
			recurse=int(arg[9:])
		elif arg.startswith('-id:'):
			ids.append(arg[4:])
		elif arg.startswith('-total:'):
			total=int(arg[7:])
		elif arg.startswith('-bulk:'):
			bulk=arg[6:]
		elif arg.startswith('-bulk'):
			bulk=True
		elif arg.startswith('-mode:'):
			mode=arg[6:]
		elif arg.startswith('-unflood'):
			unflood=True
	site.login()
	if cat and lang2:
		site2=pywikibot.Site(lang2,pywikibot.Site().family.name)
		for page1 in pywikibot.Category(pywikibot.Site(),cat).articles(recurse=recurse,total=total):
			page2=pywikibot.Page(site2,page1.title())
			if page2.exists():
				item1=pywikibot.ItemPage.fromPage(page1)
				item2=pywikibot.ItemPage.fromPage(page2)
				if item1!=item2:
					merge_items((item1,item2))
	elif len(ids)==2:
		merge_items((pywikibot.ItemPage(site,ids[0]),pywikibot.ItemPage(site,ids[1])))
	elif len(ids)==1:
		check_deletable(pywikibot.ItemPage(site,ids[0]))
	elif bulk:
		text = pywikibot.Page(site,u'Requests for deletions/Bulk'+('' if bulk==True else '/'+bulk),ns=4).get(force=True)
		regex = re.compile('\|(?P<item>[Qq]\d+)')
		for match in regex.finditer(text):
			check_deletable(pywikibot.ItemPage(site,match.group('item')))
	elif mode=='truedups':# True duplicates
		text = pywikibot.Page(site,'Byrial/Duplicates',ns=2).get(force=True)
		regex = re.compile('\*\s*\[\[(?P<item1>[Qq]\d+)\]\] \(1 link\, 0 statements\)\, \[\[(?P<item2>[Qq]\d+)\]\] \(1 link\, 0 statements\)\, duplicate link')
		for match in regex.finditer(text):
			duplicates((pywikibot.ItemPage(site,match.group('item1')),pywikibot.ItemPage(site,match.group('item2'))))
	elif mode=='catitems':# all done
		text = pywikibot.Page(site,'Byrial/Category+name merge/ceb-war-Animalia',ns=2).get(force=True)
		regex = re.compile('^\*\s*\d+\:([Aa]rticle|[Cc]ategory)\:[\w\s]+\:\s+\[\[\:?(?P<item1>[Qq]\d+)\]\] \[\[\:?(?P<item2>[Qq]\d+)\]\](\n|$)',flags=re.MULTILINE)
		matchmerge(regex.finditer(text))
	elif mode=='shortpages':# ShortPages are often deletable ones
		gen = pywikibot.pagegenerators.ShortPagesPageGenerator(site=site,number=total)
		for page in pywikibot.pagegenerators.NamespaceFilterPageGenerator(gen,namespaces=[0]):
			check_deletable(pywikibot.ItemPage(page.site,page.title()))
	elif mode=='request':# temporary
		text = pywikibot.Page(site,u'Bot requests#Merge multiple items',ns=4).get(force=True)
		regex = re.compile('^\s*\*\s*\[http\:\/\/nssdc\.gsfc\.nasa\.gov\/nmc\/spacecraftDisplay\.do\?id\=[\w\d\-\s]+\]\: \{\{[Qq]\|(?P<item1>\d+)\}\}\, \{\{[Qq]\|(?P<item2>\d+)\}\}',flags=re.MULTILINE)
		for match in regex.finditer(text):
			merge_items((pywikibot.ItemPage(site,'Q'+match.group('item1')),pywikibot.ItemPage(site,'Q'+match.group('item2'))),taxon_mode=False)
	else:# 'standard' mode
		text = pywikibot.Page(site,'Soulkeeper/dups',ns=2).get(force=True)
		regex = re.compile('^\*\s*\w+[\w\s]*\[\[\:?(?P<item1>[Qq]\d+)\]\] \[\[\:?(?P<item2>[Qq]\d+)\]\](\n|$)',flags=re.MULTILINE)
		matchmerge(regex.finditer(text))
	if unflood:
		site.login(sysop=True)
		rightstoken=pywikibot.data.api.Request(site=site,action='query',list='users',ususers=site.user(),ustoken='userrights').submit()
		rightstoken=rightstoken['query']['users'][0]
		if rightstoken['name']==site.user():
			rightstoken=rightstoken['userrightstoken']
			pywikibot.data.api.Request(site=site,action='userrights',user=site.user(),token=rightstoken,remove='flood',reason='the current mass-deletion task has been completed').submit()
			pywikibot.output(u'\03{lightgreen}The flood flag has been removed successfully from the current user')

# -*- coding: utf-8  -*-

import pywikibot

def bot_link(site):
	botname=pywikibot.data.api.Request(site=site,action='expandtemplates',text='{{int:group-bot-member|'+site.user()+'}}').submit()['expandtemplates']['*']
	return '[['+pywikibot.Page(site,site.mediawiki_message('group-bot'),ns=4).title()+'|'+botname[0].upper()+botname[1:]+']]'

def log(user,pages):
	tp=user.getUserTalkPage()
	add=u'{{{{Oggetto|{titles[0]}}}}}'.format(titles=[page.title() for page in pages])
	old=tp.get(force=True)
	if add in tp.text:
		pywikibot.output(u'\03{lightgreen}already logged\03{default}')
		return
	tp.text+=u'\n\n== Avviso ==\n'+add+'--~~~~'
	pywikibot.showDiff(old,tp.text)
	#cmt=u'{bot}: reporting low frequency of edit summary'
	cmt=u'{bot}: bassa frequenza di sommario delle modifiche'
	tp.save(comment=cmt.format(bot=bot_link(user.site)),minor=False,botflag=True)

def summary_check(summary):
	if summary!='':
		pywikibot.output(u'\03{{lightyellow}}not-empty edit summary: "{}"\03{{default}}'.format(summary))
		return True
	return False

def main(site,total=50,min_edits=5,namespaces=[0],changetype='edit',groups=None,allow_blocked=False,**kwargs):
	site.login()
	users=[]
	for change in site.recentchanges(namespaces=namespaces,changetype=changetype,showBot=False,total=total,**kwargs):
		if change['user'] in users:
			pywikibot.output(u'\03{{lightyellow}}user has already been checked: {}\03{{default}}'.format(change['user']))
			continue
		users.append(change['user'])
		if summary_check(change['comment']):
			continue
		user=pywikibot.User(site,change['user'])
		if groups and len(list(set(groups)-set(user.groups())))==len(list(set(groups))):
			pywikibot.output(u'\03{{lightyellow}}user is not in {groups}: {}\03{{default}}'.format(user.name(),groups=groups))
			continue
		if user.isBlocked() and not allow_blocked:
			pywikibot.output(u'\03{{lightyellow}}blocked user: {}\03{{default}}'.format(change['user']))
			continue
		pywikibot.output(u'fetching contributions for {}'.format(user.name()))
		contribs=site.usercontribs(user=user.username,namespaces=namespaces,total=min_edits)
		if True in [summary_check(contrib['comment']) for contrib in contribs]:
			continue
		pywikibot.output(u'\03{{lightblue}}{user} has {num} edits with no edit summary\03{{default}}'.format(user=user.name(),num=min_edits))
		log(user,[pywikibot.Page(site,contrib['title']) for contrib in contribs])

if __name__ == '__main__':
	groups=None
	total=50
	for arg in pywikibot.handleArgs():
		if arg.startswith('-groups:'):
			groups=arg[8:].split('|')
		elif arg.startswith('-total:'):
			total=int(arg[7:])
	main(site=pywikibot.Site(),total=total,groups=groups)

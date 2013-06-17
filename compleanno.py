# -*- coding: utf-8  -*-

import re
import calendar
import datetime
import pywikibot

pages={
	'wikipedia':{
		'it':'Wikipedia:Wikipediani/Per giorno di nascita'
	},
	'wikinews':{
		'it':'Wikinotizie:Wikinotiziani/Compleanno'
	}
}

def main(site=pywikibot.Site('it','wikipedia'),basedate=datetime.date.today(),back=0,forward=0):
	if not site.logged_in():
		site.login()
	for date in [basedate+datetime.timedelta(days=num) for num in range(-back,forward+1)]:
		post=(' in anticipo' if date>datetime.date.today() else (' in ritardo' if date<datetime.date.today() else ''))
		mese=site.mediawiki_message(calendar.month_name[date.month].lower())
		tag='bot-compleanno-auguri-'+str(date.year)
		compleanni=pywikibot.Page(site,pages[site.family.name][site.lang]+'#'+mese[0].upper()+mese[1:])
		pywikibot.output(u'Sto cercando gli utenti di %s nati il giorno %d %s'%(site.sitename(),date.day,mese))
		utenti=re.search(ur"\*\s*'*\[\["+str(date.day)+" "+mese+"\]\]'*\s*(\:|\-)\s*(?P<utenti>[^\n]+)\n",compleanni.get()).group('utenti')
		utenti=list(set([pywikibot.User(site,link.group('nome')) for link in re.finditer(ur'\[\[\s*([Uu]ser|['+re.escape(site.namespace(2)[0].upper()+site.namespace(2)[0].lower())+']'+re.escape(site.namespace(2)[1:])+')\:(?P<nome>[^\|\{\}\[\]]+)(\]\]|\|[^\]]+\]\])',utenti)]))
		if len(utenti)==0:
			pywikibot.output('\03{lightyellow}non ci sono utenti con i criteri cercati\03{default}')
			return
		pywikibot.output(u'Invierò gli auguri a \03{lightblue}%s\03{default}'%(('\03{default}, \03{lightblue}'.join([utente.name() for utente in utenti[0:-1]])+'\03{default} e \03{lightblue}'+utenti[-1].name()) if len(utenti)>1 else utenti[0].name())) 
		for utente in utenti:
			yellow=u'\03{lightblue}'+utente.name()+'\03{default}: \03{lightyellow}%s\03{default}'
			if not utente.isRegistered():
				pywikibot.output(yellow%'il nome utente non risulta registrato')
				continue
			if utente.isBlocked(force=True):
				pywikibot.output(yellow%'l\'utente risulta bloccato')
				continue
			if not utente.getUserPage().exists():
				pywikibot.output(yellow%'la pagina utente non esiste')
				continue
			if utente.getUserPage().isRedirectPage():
				pywikibot.output(yellow%'la pagina utente è un redirect')
				continue
			discussione=utente.getUserTalkPage()
			if not discussione.exists():
				pywikibot.output(yellow%'la pagina di discussioni non esiste')
				continue
			if discussione.isRedirectPage():
				pywikibot.output(yellow%'la pagina di discussioni è un redirect')
				continue
			disc=discussione.get(force=True)
			if disc.find(tag)!=-1:
				pywikibot.output(u'\03{lightblue}%s\03{default}: \03{lightgreen}gli auguri sono già stati inviati\03{default}'%utente.name())
				continue
			discussione.text+='\n\n== Auguri'+post+' ==\nBuon compleanno! <small class="'+tag+'">&nbsp;&nbsp;&ndash; Messaggio automatico ([['+compleanni.title()+'|fonte]] | [['+site.namespace(3)+u':{{subst:REVISIONUSER}}|è sbagliato?]]) di</small> ~~~~'
			pywikibot.showDiff(disc,discussione.text)
			discussione.save(comment='[['+site.namespace(4)+':Bot|Bot]]: auguri'+post,minor=False)
		pywikibot.output(u'\03{lightgreen}completato\03{default}')

if __name__=='__main__':
	today=datetime.date.today()
	day=today.day
	month=today.month
	year=today.year
	back=0
	forward=0
	for arg in pywikibot.handleArgs():
		if arg.startswith('-day:'):
			day=int(arg[5:])
		elif arg.startswith('-month:'):
			month=int(arg[7:])
		elif arg.startswith('-back:'):
			back=int(arg[6:])
		elif arg.startswith('-forward:'):
			forward=int(arg[9:])
	main(basedate=datetime.date(year,month,day),back=back,forward=forward)

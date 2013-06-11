# -*- coding: utf-8  -*-

import re
import calendar
import datetime
import pywikibot

site=pywikibot.Site('it','wikipedia')

if not site.logged_in():
	site.login()

adesso=datetime.datetime.now()
mese=site.mediawiki_message(calendar.month_name[adesso.month].lower())
tag='bot-compleanno-auguri-'+str(adesso.year)
compleanni=pywikibot.Page(site,'Wikipedia:Wikipediani/Per giorno di nascita#'+mese[0].upper()+mese[1:])
pywikibot.output(u'Sto cercando gli utenti nati il giorno %d %s'%(adesso.day,mese))
utenti=re.search(ur"\*\s*'*\[\["+str(adesso.day)+" "+mese+"\]\]'*\s*(\:|\-)\s*(?P<utenti>[^\n]+)\n",compleanni.get()).group('utenti')
utenti=[pywikibot.User(site,link.group('nome')) for link in re.finditer(ur'\[\[\s*([Uu]ser|['+re.escape(site.namespace(2)[0].upper()+site.namespace(2)[0].lower())+']'+re.escape(site.namespace(2)[1:])+')\:(?P<nome>[^\|\{\}\[\]]+)(\]\]|\|[^\]]+\]\])',utenti)]
if len(utenti)==0:
	pywikibot.output(yellow%'il nome utente non risulta registrato') 
pywikibot.output(u'Invierò gli auguri a \03{lightblue}%s'%'\03{default}, \03{lightblue}'.join([utente.name() for utente in utenti[0:-1]])+('\03{default} e \03{lightblue}'+utenti[-1].name() if len(utenti)>1 else '')+'\03{default}')
for utente in utenti:
	yellow=u'\03{lightblue}'+utente.name()+'\03{default}: \03{lightyellow}%s\03{default}'
	if not utente.isRegistered():
		pywikibot.output(yellow%'il nome utente non risulta registrato')
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
	discussione.text+='\n\n== Auguri ==\nBuon compleanno! <small class="'+tag+'">&nbsp;&nbsp;&ndash; Messaggio automatico ([['+compleanni.title()+'|fonte]] | [['+it.namespace(3)+u':{{subst:REVISIONUSER}}|è sbagliato?]]) di</small> ~~~~'
	pywikibot.showDiff(disc,discussione.text)
	discussione.save(comment='[[Wikipedia:Bot|Bot]]: auguri',minor=False)
pywikibot.output(u'\03{lightgreen}completato\03{default}')

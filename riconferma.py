# -*- coding: utf-8  -*-

import re
import pywikibot
import mwparserfromhell

site = pywikibot.Site('it', 'wikipedia')


def isOTRS(user):
    users = pywikibot.Page(pywikibot.Site('meta', 'meta'), 'OTRS/Users').get()
    return bool(re.search(ur'\*\s*' + re.escape(user.name()) + '\n', users))


def isCU(user):
    return ('checkuser' in user.groups())


def quorum():
    r = pywikibot.Page(site, u'Wikipedia:Amministratori/Sistema di voto/Quorum#Quorum per la prossima elezione').get(force=True)
    r = pywikibot.data.api.Request(site=site, action='expandtemplates', text=r).submit()['expandtemplates']['*']
    m = re.search(ur'Il quorum dei voti favorevoli per la prossima elezione è pari a (?:\'\'\'|\<b\>)(\d+)(?:\'\'\'|\<\/ ?b\>)', r)
    if m:
        return m.group(1)


def aggiungiInElenco(utente, procedura):
    page = pywikibot.Page(site, 'Amministratori/Riconferma annuale', ns=4)
    text = page.get(force=True)
    page.text = re.sub(ur'(\n\<\!\-\-\s*\:?\s*\'\'\s*[Nn]essuna riconferma in corso\s*\'\'\s*\-\-\>)', u'\n----\n{{{{{}}}}}\g<1>'.format(procedura.title()), page.text, count=1)
    if page.text != text:
        pywikibot.showDiff(text, page.text)
        page.save(comment=u'[[Wikipedia:Bot|Bot]]: inclusione di [[{}|procedura]]'.format(procedura.title()), minor=False, botflag=True)
    return False


def aggiungiInVotazioni(utente, procedura, datafine, orainizio):
    page = pywikibot.Page(site, 'Wikipediano/Votazioni', ns=4)
    text = page.get(force=True)
    args = dict(nome=utente.name(), up=utente.getUserPage().title(), procedura=procedura.title(), datafine=datafine, orainizio=orainizio)
    template = u'* [[{up}|{nome}]]. La [[{procedura}|procedura]] termina il {datafine} alle {orainizio}.'.format(**args)
    if template in text:
        pywikibot.output(u'\03{{lightyellow}}procedura già elencata in {}'.format(page.title()))
        return
    header = u';È in corso la [[Wikipedia:Amministratori/Riconferma annuale#Amministratori in riconferma|riconferma tacita]] degli [[WP:A|amministratori]]:'
    template = header + '\n' + template
    page.text = text.replace(header, template, 1)
    if page.text == text:
        page.text = text + '\n\n' + template
    pywikibot.showDiff(text, page.text)
    page.save(comment=u'[[Wikipedia:Bot|Bot]]: collegamento a [[{}|procedura]]'.format(procedura.title()), minor=False, botflag=True)


def paginaProcedura(utente, num):
    return pywikibot.Page(site, u'Amministratori/Riconferma annuale/' + utente.name() + ('/' + str(num) if num > 0 else ''), ns=4)


def creaProcedura(utente, elezione, quorum, otrs, checkuser):
    num = 0
    while True:
        procedura = paginaProcedura(utente, num)
        if not procedura.exists():
            break
        num += 1
    pywikibot.output(u'sarà creata {}'.format(procedura))
    args = dict(utente=utente.name())
    datainizio = localtime('j xg Y')
    datafine = localtime('j xg Y|+7 days')
    orainizio = localtime('H:i')
    template = u'{{{{Wikipedia:Amministratori/Riconferma annuale/Schema|{utente}|{{{{#timel:j xg Y|{elezione}}}}}|{datainizio}|' \
               u'{orainizio}|{datafine}|{quorum}}}}}'.format(utente=utente.name(), elezione=elezione, datainizio=datainizio,
                                                             orainizio=orainizio, datafine=datafine, quorum=quorum)
    template = pywikibot.data.api.Request(site=site, action='expandtemplates', text=template).submit()['expandtemplates']['*']

    append = []
    if otrs:
        append.append('OTRS')
    if checkuser:
        append.append('di Check User')
    if len(append) > 0:
        template = template.replace('</small>', '</small> - \'\'\'sysop con funzioni {}\'\'\''.format(' e '.join(append)), 1)

    procedura.text = template
    procedura.save(comment=u'[[Wikipedia:Bot|Bot]]: creazione procedura di riconferma annuale', botflag=True)
    return (num, procedura, datainizio, orainizio, datafine)


def avvisaAdmin(utente, num, anno):
    talk = utente.getUserTalkPage()
    template = u'\n\n== Riconferma {anno} ==\n\n{{{{Avviso riconferma{num}}}}} --~~~~'.format(anno=anno, num=('|' + str(num) if num > 0 else ''))
    text = talk.get(force=True)
    talk.text += template
    pywikibot.showDiff(text, talk.text)
    talk.save(comment=u'[[Wikipedia:Bot|Bot]]: avviso riconferma {}'.format(anno), minor=False, botflag=True)


def data(template, param):
    if template.has(param):
        param = unicode(template.get(param).value)
        if param.isdigit() and len(param) == 8:
            try:
                pywikibot.Timestamp.fromtimestampformat(param + '000000')
                return param
            except:
                return


def localtime(typ):
    return pywikibot.data.api.Request(site=site, action='expandtemplates', text=u'{{#timel:' + typ + '}}').submit()['expandtemplates']['*']


def unannodopo(ts):
    return localtime('Ymd|' + ts + '+1 year')


def main(quorum):
    page = pywikibot.Page(site, 'Amministratori/Lista#Lista degli amministratori', ns=4)
    text = page.get(force=True)
    anno = localtime('Y')
    oggi = localtime('Ymd')
    utenti = []
    for template in mwparserfromhell.parse(text).ifilter_templates():
        if template.name[0].upper() + template.name[1:] == u'Amministratore/riga':
            if template.has('1') and template.has('4'):
                utente = pywikibot.User(site, unicode(template.get('1').value))
                elezione = data(template, '4')
                if elezione:
                    riconferma = data(template, '5')
                    if (riconferma is None and unannodopo(elezione) == oggi) or (riconferma and unannodopo(riconferma) == oggi):
                        pywikibot.output(utente)
                        numero, procedura, datainizio, orainizio, datafine = creaProcedura(utente, elezione, quorum, isOTRS(utente), isCU(utente))
                        aggiungiInElenco(utente, procedura)
                        aggiungiInVotazioni(utente, procedura, datafine, orainizio)
                        avvisaAdmin(utente, numero, anno)
                        oldtmp = unicode(template)
                        template.add('5', oggi, showkey=False, before='4')
                        page.text = page.text.replace(oldtmp, unicode(template))
    if page.text != text:
        pywikibot.showDiff(text, page.text)
        # page.save(comment=u'[[Wikipedia:Bot|Bot]]: aggiornamento procedure di riconferma', minor=False, botflag=True)

if __name__ == "__main__":
    pywikibot.handleArgs()
    site.login()
    q = quorum()
    if q:
        main(q)

# -*- coding: utf-8  -*-

import re
import urllib2
import datetime
import pywikibot
import bs4

site = pywikibot.Site('it', 'wikipedia')

fulldate = pywikibot.data.api.Request(site=site, action='expandtemplates', text='{{#timel:j xg Y}}').submit()['expandtemplates']['*']

today = datetime.date.today()

season = [str(today.year)]
if today.month < 8:
    season.insert(0, str(today.year-1))
else:
    season.append(str(today.year+1))

pywikibot.output(u'\03{lightgreen}calcio.py\03{lightpurple} by Ricordisamoa\n\nseason:\t\t'+'-'.join(season))

title = u'Serie A {0[0]}-{0[1]}'.format(season)


def squadre():
    team_mapping = {
        'ChievoVerona': 'Chievo',
        'Hellas Verona': 'Verona'
    }

    baseurl = 'http://www.legaseriea.it/it/serie-a-tim/classifica-estesa/classifica'

    row_img = {
        1: '[[File:Scudetto.svg|15px|Campione d\'Italia]] '
    }
    row_img[2] = row_img[3] = '[[File:Coppacampioni.png|12px]] '
    row_img[1] += row_img[2]
    row_img[4] = row_img[5] = '[[File:UEFA Europa League logo.png|12px]] '
    # row_img[4] = row_img[5] = '[[File:Coppauefa.png|12px]] '
    row_img[18] = row_img[19] = row_img[20] = '[[File:1downarrow red.svg|12px]] '

    tbl_style = ' class="wikitable sortable" style="text-align: center; font-size: 90%;"'

    row_style = {}
    for x in range(1, 21):
        row_style[x] = ' align=center'
    row_style[1] += ' style="background:#99CBFF;"'
    row_style[2] += ' style="background:#AFEEEE;"'
    row_style[3] = row_style[2]
    row_style[4] += ' style="background:#B0FFB0;"'
    row_style[5] = row_style[4]
    row_style[18] += ' style="background:#FFCCCC;"'
    row_style[20] = row_style[19] = row_style[18]

    row_title_style = {}
    for x in range(1, 21):
        row_title_style[x] = 'style="text-align:left;"'

    teams = []
    content = urllib2.urlopen(baseurl).read()
    tabid = '_BDC_classifica_estesa_WAR_LegaCalcioBDC_classifica_estesa'
    content = ''.join(re.split(ur'(<table [^\<\>]*\s*id="'+tabid+'")', content.split('</table>')[0])[1:3])+'</table>'
    bs = bs4.BeautifulSoup(content)
    for index, tr in enumerate(bs.find('table', {'id': tabid}).find('tbody').findAll('tr')):
        td = tr.findAll('td')
        sq = td[0].text.strip()
        if sq in team_mapping:
            sq = team_mapping[sq]
        gf = td[15].text.strip()
        gs = td[16].text.strip()
        dr = int(gf)-int(gs)
        if dr > 0:
            dr = str('+'+str(dr))
        teams.append({
            'Pos.': index+1,
            'Squadra': sq,
            'Pt': td[2].text.strip(),
            'G': td[3].text.strip(),
            'V': td[4].text.strip(),
            'N': td[5].text.strip(),
            'P': td[6].text.strip(),
            'GF': gf,
            'GS': gs,
            'DR': dr
        })

    comm = [
        (7, 'Pos.', 'Posizione'),
        (27, 'Squadra'),
        (10, 'Pt', 'Punti'),
        (7, 'G', 'Giocate'),
        (7, 'V', 'Vinte'),
        (7, 'N', 'Nulle'),
        (7, 'P', 'Perse'),
        (7, 'GF', 'Gol fatti'),
        (7, 'GS', 'Gol subiti'),
        (7, 'DR', 'Differenza reti')
    ]
    tbl_head = ['!width=7%|']
    for c in comm:
        tbl_head.append(('!width={}%|'+(u'{{{{Descrizione comando|{}|{}}}}}' if len(c) > 2 else '{}')).format(*c))

    tbl = u'<small>\'\'Aggiornata al {fulldate}.\'\'<ref>{{{{cita web|url={baseurl}|titolo=Serie A - Classifica|editore=legaseriea.it|accesso={fulldate}}}}}</ref></small>'.format(baseurl=baseurl, fulldate=fulldate)
    tbl += '\n<center>\n{|'+tbl_style
    tbl += '\n'+'\n'.join(tbl_head)

    cell_sep = '||'
    cell_format = {
        'Pos.': u'{}.',
        'Pt': u'\'\'\'{}\'\'\'',
        'Squadra': {}
    }
    for x in range(1, 21):
        cell_format['Squadra'][x] = u'{{{{Calcio {}}}}}'
    for x in (1, 18, 19, 20):
        cell_format['Squadra'][x] = '\'\'\''+cell_format['Squadra'][x]+'\'\'\''

    for team in teams:
        p = team['Pos.']
        tbl += '\n|-'+(row_style[p] if p in row_style else '')+'\n| '+(row_img[p] if p in row_img else '')+cell_sep
        tbl += (cell_format['Pos.'] if 'Pos.' in cell_format else '{}').format(p)+cell_sep
        tbl += (row_title_style[p] if p in row_title_style else '')+'|'+((cell_format['Squadra'][p] if p in cell_format['Squadra'] else cell_format['Squadra'])
                                                                         if 'Squadra' in cell_format else '{}'
                                                                         ).format(team_mapping[team['Squadra']] if team['Squadra'] in team_mapping else team['Squadra'])+'\n'
        for c in comm[2:]:
            tbl += cell_sep+(cell_format[c[1]] if c[1] in cell_format else '{}').format(team[c[1]])
    tbl += '\n|}'
    return tbl


def squadra(giocatore):
    giocatore.get()
    sportivo = [t for t in pywikibot.textlib.extract_templates_and_params(giocatore.text) if t[0][0].upper()+t[0][1:] == 'Sportivo']
    if len(sportivo) == 1 and len(sportivo[0]) == 2 and 'Squadra' in sportivo[0][1]:
        return sportivo[0][1]['Squadra']


def giocatore(nome):
    nomi = re.sub(ur'^(?P<cognome>(D(i|el?) )?\S+) (?P<nome>.+)$', u'\g<nome> \g<cognome>', nome).split(' ')
    alt = [' '.join(nomi)]
    if len(nomi) > 2:
        alt.append(' '.join(nomi[1:]))
        alt.append(' '.join([nomi[0]]+nomi[2:]))
    alt.append(' '.join(nomi)+' (calciatore)')
    if len(nomi) > 3:
        alt.append(' '.join([nomi[1], nomi[3]]))
        alt.append(' '.join([nomi[0], nomi[2]]))
    for nome in alt:
        page = pywikibot.Page(site, nome)
        if page.exists():
            if page.isRedirectPage():
                if page.getRedirectTarget().exists():
                    return page.getRedirectTarget()
            elif not page.isDisambig():
                return page
        page = pywikibot.Page(pywikibot.Site('en', site.family.name), nome)
        if page.isRedirectPage():
            if page.getRedirectTarget().exists():
                page = page.getRedirectTarget()
            else:
                break
        for langlink in page.iterlanglinks():
            if langlink.site == site:
                page = pywikibot.Page(langlink)
                if page.exists() and not page.isRedirectPage() and not page.isDisambig():
                    return page
                break
    return None


def marcatori():
    baseurl = 'http://www.legaseriea.it/it/serie-a-tim/campionato-classifica/marcatori'
    content = urllib2.urlopen(baseurl).read()
    tabid = 'classifica'
    content = ''.join(re.split(ur'(<table [^\<\>]*\s*id="'+tabid+'")', content.split('</table>')[0])[1:3])+'</table>'
    tbl = u'<small>\'\'Aggiornata al {fulldate}.\'\'<ref>{{{{cita web|url={baseurl}|titolo=Serie A - Marcatori|editore=legaseriea.it|accesso={fulldate}}}}}</ref></small>'.format(baseurl=baseurl, fulldate=fulldate)
    tbl += u'\n{{Classifica marcatori/inizio|rigori=on}}'
    bs = bs4.BeautifulSoup(content)
    [comment.extract() for comment in bs.findAll(text=lambda text:isinstance(text, bs4.element.Comment))]
    for index, tr in enumerate(bs.find('table', {'id': tabid}).findAll('tr')[1:]):
        nome = tr.findAll('td')[2].text.strip().replace('\t', '').replace(u'\xa0', ' ').split('(')[0]
        pl = giocatore(nome)
        if not pl:
            print nome
            return
        print pl.title(), squadra(pl)
        # tbl += u'\n{{Classifica marcatori|reti=4|rigori=0|nazione=SVK|nome=[[Marek Hamšík]]|squadra= Napoli|testa=on}}'

# marcatori()
sezione_squadre = u'Classifica'
# sezione_marcatori = u'Classifica marcatori'
basepage = pywikibot.Page(site, title)
text = basepage.get(force=True)
basepage.text = ''.join(re.split(ur'(=+\s*'+sezione_squadre+'\s*=+\n)', basepage.text)[0:2]) + squadre() + ''.join(re.split(ur'(\n<\/center>\n+\{\{[Cc]olonne\}\})', basepage.text)[1:3])
# basepage.text = ''.join(re.split(ur'(=+\s*'+sezione_marcatori+'\s*=+\n)', basepage.text)[0:2]) + marcatori() + ''.join(re.split(ur'(\n<\/center>\n+\{\{[Cc]olonne\}\})', basepage.text)[1:3])

pywikibot.showDiff(text, basepage.text)
basepage.save(comment='[[Wikipedia:Bot|Bot]]: aggiornamento automatico [[#'+sezione_squadre+'|classifica]]', botflag=True)

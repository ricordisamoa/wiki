# -*- coding: utf-8  -*-

import re
import sys
import json
import urllib2
import datetime
import pywikibot
from references import references
from merge import del_msg

site = pywikibot.Site('wikidata', 'wikidata').data_repository()
site.login()

enwiki = pywikibot.ItemPage(site, 'Q'+str(references(site)['enwiki']))
enwiki.get()

lines = list(urllib2.urlopen('http://tools.wmflabs.org/magnustools/static_data/people.dates.tab'))

pywikibot.handleArgs()

pywikibot.output(u'{} items to process'.format(len(lines)))
if len(sys.argv) > 1:
    limits = (int(sys.argv[1].split('-')[0]), int(sys.argv[1].split('-')[1]))
    lines = lines[limits[0]:limits[1]]
    pywikibot.output(u'items limited from {0[0]} to {0[1]}'.format(limits))

regex = u'(?P<item>[Qq]\d+)\t(?P<label>[^\t]+)\t(?P<prop>[Pp]\d+)\t(?P<time>\+0{7}\d{4}\-\d\d\-\d\dT00\:00\:00Z)$'

for line in lines:
    match = re.match(regex, line)
    if not match:
        continue
    print line.strip()
    item = pywikibot.ItemPage(site, match.group('item'))
    if not item.exists():
        del_msg(item)
        continue
    item.get(force=True)
    prop = match.group('prop').upper()
    date = {
        'time': match.group('time'),
        'timezone': 0,
        'before': 0,
        'after': 0,
        'precision': 11,
        'calendarmodel': 'http://www.wikidata.org/entity/Q1985727'
    }
    summary = u'[[Special:MyLanguage/Wikidata:Bots|Bot]]: importing [[Property:{prop}]] from [[{site}]]'.format(prop=prop, site=enwiki.getID())
    if not prop in item.claims:
        params = {
            'action': 'wbcreateclaim',
            'entity': item.getID(),
            'baserevid': item.latestRevision(),
            'property': prop,
            'snaktype': 'value',
            'value': json.dumps(date),
            'bot': 1,
            'summary': summary,
            'token': site.token(item, 'edit')
        }
        pywikibot.data.api.Request(site=item.site, **params).submit()
        pywikibot.output(u'\03{{lightgreen}}{}: claim successfully added'.format(item))
        item.get(force=True)
    if prop in item.claims and len(item.claims[prop]) == 1:
        claim = item.claims[prop][0]
        if claim.getTarget() == date:
            source = pywikibot.Claim(site, 'P143')
            source.setTarget(enwiki)
            try:
                claim.addSource(source, bot=1, summary=summary)
                pywikibot.output(u'\03{{lightgreen}}{qid}: source "{source}" successfully added'.format(qid=item.getID(), source=enwiki.labels['en']))
            except Exception, e:
                print e

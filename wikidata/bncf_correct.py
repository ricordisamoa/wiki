# -*- coding: utf-8  -*-

import pywikibot

wd = pywikibot.Site('wikidata', 'wikidata').data_repository()
wd.login(sysop=True)

propid = 508
rep_from = 'BNFC'
rep_into = 'BNCF'

prop = pywikibot.PropertyPage(wd, 'Property:P'+str(propid))
labels = {}
descriptions = {}
prop.get(force=True)
args = (rep_from, rep_into)
for lang in prop.labels.keys():
    labels[lang] = {'language': lang, 'value': prop.labels[lang].replace(*args)}
for lang in prop.descriptions.keys():
    descriptions[lang] = {'language': lang, 'value': prop.descriptions[lang].replace(*args)}
prop.editEntity({'labels': labels, 'descriptions': descriptions}, summary=u'{} \u2192 {}'.format(*args))

# -*- coding: utf-8  -*-

import pywikibot


def references(repo):
    sites = {}
    page = pywikibot.Page(repo, u'List of wikis/python', ns=4)
    for name, family in json.loads(page.get()).iteritems():
        for lang in family:
            dbName = pywikibot.Site(lang, name).dbName()
            sites[dbName] = pywikibot.ItemPage(repo, family[lang])
    return sites

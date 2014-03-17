# -*- coding: utf-8  -*-

import re
import pywikibot

cat = {
    'en': u'Lists of minor planets by number',
    'fy': u'List fan planetoïden',
    'nl': u'Planetoïdenlijst'
}
fmt = {
    'en': u'List of minor planets/{}–{}',
    'fy': u'List fan planetoïden {}-{}',
    'nl': u'Lijst van planetoïden {}-{}'
}


def main(site1=pywikibot.Site('fy', 'wikipedia'), site2=pywikibot.Site('nl', 'wikipedia')):
    site1.data_repository().login()
    regex = re.escape(fmt[site1.lang]).replace('\{', '{').replace('\}', '}').format('(\d+)', '(\d+)')
    for page1 in pywikibot.Category(site1, cat[site1.lang]).articles():
        match = re.match(regex, page1.title())
        if not match:
            continue
        print page1.title()
        print match.group(1), match.group(2)
        page2 = pywikibot.Page(site2, fmt[site2.lang].format(match.group(1), match.group(2)))
        print page2.title()
        if not page2.exists():
            continue
        item1 = pywikibot.ItemPage.fromPage(page1)
        item2 = pywikibot.ItemPage.fromPage(page2)
        if not item2.exists():
            continue
        if item1.exists() and item1 != item2:
            pywikibot.output(u'\03{{lightyellow}}{} and {} should be merged\03{{default}}'.format(item1.getID(), item2.getID()))
            continue
            # TODO: call merge.py
        item2.get(force=True)
        newdata = {}
        if not item1.exists():
            newdata['sitelinks'] = {}
            newdata['sitelinks'][site1.dbName()] = {'site': site1.dbName(), 'title': page1.title()}
            if not site1.lang in item2.labels:
                newdata['labels'] = {}
                newdata['labels'][site1.lang] = {'language': site1.lang, 'value': page1.title()}
        for dbname in item2.sitelinks:
            s = pywikibot.Site(dbname.replace('wiki', '').replace('_', '-'), 'wikipedia')  # hack
            if not s.lang in item2.labels:
                if not 'labels' in newdata:
                    newdata['labels'] = {}
                newdata['labels'][s.lang] = {'language': s.lang, 'value': item2.sitelinks[dbname]}
        if len(newdata) > 0:
            try:
                item2.editEntity(newdata)
                pywikibot.output(u'\03{lightgreen}editEntity successful\03{default}')
            except:
                pywikibot.output(u'\03{lightred}editEntity failed\03{default}')

if __name__ == "__main__":
    pywikibot.handleArgs()
    main()

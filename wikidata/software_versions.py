# -*- coding: utf-8  -*-

import re
import urllib2
import pywikibot
from bs4 import BeautifulSoup
from distutils.version import StrictVersion, LooseVersion

pywikibot.handleArgs()

site = pywikibot.Site().data_repository()
site.login()

items = {
    'Q119931': {
        'P348': (
            'http://www.stellarium.org',
            lambda x: re.match('latest version (\d+\.\d+(\.\d+)?)$', x.find('div', {'id': 'latestversion'}).find('a').text).group(1),
            StrictVersion
        )
    },
    'Q6410733': {
        'P348': (
            'http://kineticjs.com',
            lambda x: re.match('^(\d+\.\d+\.\d+)$', x.find('div', {'id': 'downloadContainer'}).find('a', {'class': 'download'}).find('span').text).group(1),
            StrictVersion
        )
    }
}

for qid in items:
    item = pywikibot.ItemPage(site, qid)
    if not item.exists():
        pywikibot.output(u'\03{{lightyellow}}Warning: item {} does not exist'.format(item))
        continue
    item.get(force=True)
    for prop in items[qid]:
        propname = pywikibot.PropertyPage(site, prop)
        propname.get()
        propname = propname.labels['en']
        new = items[qid][prop][1](BeautifulSoup(urllib2.urlopen(items[qid][prop][0]).read()))
        pywikibot.output(u'{prop} for "{program}" according to "{url}": {new}'.format(prop=propname, program=item.labels['en'], url=items[qid][prop][0], new=new))
        if prop in item.claims:
            if len(item.claims[prop]) == 1:
                old = item.claims[prop][0].getTarget()
                comp = items[qid][prop][2]
                if comp(new) > comp(old):
                    pywikibot.output(u'\03{{lightblue}}{program} has an out-of-date claim for {prop}: "{old}" instead of "{new}"'.format(program=item.labels['en'], prop=propname, old=old, new=new))
                    item.claims[prop][0].changeTarget(new, summary=u'updating {prop} from {url}'.format(prop=propname, url=items[qid][prop][0]))
                    pywikibot.output(u'\03{{lightgreen}}claim updated in {program} for {prop} with value "{val}"'.format(program=item.labels['en'], prop=propname, val=new))
                elif comp(new) == comp(old):
                    pywikibot.output(u'\03{{lightblue}}{program} has an up-to-date claim for {prop}: "{old}" == "{new}"'.format(program=item.labels['en'], prop=propname, old=old, new=new))
                else:
                    pywikibot.output(u'\03{{lightyellow}}Warning: {program} has a greater claim for {prop}: "{old}" > "{new}"'.format(program=item.labels['en'], prop=propname, old=old, new=new))
            else:
                pywikibot.output(u'\03{{lightyellow}}Warning: {item} contains {num} claims for {prop}'.format(item=item, num=len(item.claims[prop]), prop=propname))
        else:
            pywikibot.output(u'\03{{lightgreen}}{program} does not contain any claim for {prop}'.format(program=item.labels['en'], prop=propname))
            claim = pywikibot.Claim(site, prop)
            claim.setTarget(new)
            item.addClaim(claim, summary=u'importing {prop} from {url}'.format(prop=propname, url=items[qid][prop][0]))
            pywikibot.output(u'\03{{lightgreen}}claim added to {program} for {prop} with value "{val}"'.format(item.labels['en'], prop=propname, val=new))

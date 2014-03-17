# -*- coding: utf-8  -*-

import re
import urllib2
import pywikibot

viaf = 'P214'
baseurl = 'https://viaf.org/viaf/{}'
regex = ur'(https?\:)?\/\/viaf\.org\/viaf\/(\d+)\/?'
regex2 = ur'^\*\s*\[\[(?P<item>[Qq]\d+)\]\]\:\s*\['+regex+'\s+\d+\](\,\s*\['+regex+'\s+\d+\])+(\n|$)'
site = pywikibot.Site().data_repository()

viols = pywikibot.Page(site,
                       'Database reports/Constraint violations/'+viaf,
                       ns=4).get(force=True)
for match in re.finditer(regex2, viols, flags=re.MULTILINE):
    item = pywikibot.ItemPage(site, match.group('item'))
    item.get(force=True)
    if viaf in item.claims and len(item.claims[viaf]) > 1:
        removable = []
        values = [c.getTarget() for c in item.claims[viaf]]
        for claim in item.claims[viaf]:
            prev = claim.getTarget()
            url = baseurl.format(prev)
            try:
                got = re.match(regex+'$', urllib2.urlopen(url).geturl()).group(2)
                if got != prev:
                    pywikibot.output(
                        u'\03{{lightblue}}searched VIAF for {prev} but got redirected to {got}'.format(prev=prev, got=got))
                    if got in values:
                        pywikibot.output(u'\03{{lightgreen}}claim pertaining to VIAF {prev} is eligible for removal'.format(prev=prev))
                        removable.append(claim)
                    else:
                        pywikibot.output(u'\03{{lightyellow}}VIAF {got} was not found in existing claims, so {prev} cannot be removed'.format(prev=prev, got=got))
            except Exception, e:
                print e
        if len(removable) > 0:
            s = ('' if len(removable) == 1 else 's')
            item.removeClaims(removable, summary='remove redirected VIAF id{s}'.format(s=s))
            pywikibot.output(u'\03{{lightgreen}}{num} claim{s} removed from {item}'.format(num=len(removable), s=s, item=item))
        else:
            pywikibot.output(u'\03{{lightyellow}}no removable VIAF ids found on {item}'.format(item=item))

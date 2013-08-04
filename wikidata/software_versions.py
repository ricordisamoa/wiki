# -*- coding: utf-8  -*-

import re
import urllib2
import pywikibot
from bs4 import BeautifulSoup
from distutils.version import StrictVersion,LooseVersion

pywikibot.handleArgs()

site = pywikibot.Site().data_repository()
site.login()

items = {
	'Q119931':{
		'p348':(
			'http://www.stellarium.org',
			lambda x: re.match('latest version (\d+\.\d+(\.\d+)?)$',x.find('div',{'id':'latestversion'}).find('a').text).group(1),
			StrictVersion
		)
	}
}

for qid in items:
	item = pywikibot.ItemPage(site,qid)
	if not item.exists():
		pywikibot.output('\03{{lightyellow}}Warning: item {item} does not exist\03{{default}}'.format(item=item))
		continue
	item.get(force=True)
	for prop in items[qid]:
		new = items[qid][prop][1](BeautifulSoup(urllib2.urlopen(items[qid][prop][0]).read()))
		pywikibot.output('latest version for "{program}" according to "{site}": {new}'.format(program=item.labels['en'],site=items[qid][prop][0],new=new))
		if prop in item.claims:
			if len(item.claims[prop])==1:
				old = item.claims[prop][0].getTarget()
				comp = items[qid][prop][2]
				if comp(new) > comp(old):
					pywikibot.output('\03{{lightblue}}{item} has an out-of-date claim for {prop}: "{old}" instead of "{new}"\03{{default}}'.format(item=item,prop=prop,old=old,new=new))
					item.claims[prop][0].changeTarget(new)
					pywikibot.output('\03{{lightgreen}}claim updated in {item} for {prop} with value "{val}"\03{{default}}'.format(item=item,prop=prop,val=new))
				elif comp(new) == comp(old):
					pywikibot.output('\03{{lightblue}}{item} has an updated claim for {prop}: "{old}" == "{new}"\03{{default}}'.format(item=item,prop=prop,old=old,new=new))
				else:
					pywikibot.output('\03{{lightyellow}}Warning: {item} has a greater claim for {prop}: "{old}" > "{new}" \03{{default}}'.format(item=item,prop=prop,old=old,new=new))
			else:
				pywikibot.output('\03{{lightyellow}}Warning: {item} contains {num} claims for {prop}\03{{default}}'.format(item=item,num=len(item.claims[prop]),prop=prop))
		else:
			pywikibot.output('\03{{lightgreen}}{item} does not contain any claim for {prop}\03{{default}}'.format(item=item,prop=prop))
			claim = pywikibot.Claim(site,prop)
			claim.setTarget(new)
			item.addClaim(claim)
			pywikibot.output('\03{{lightgreen}}claim added to {item} for {prop} with value "{val}"\03{{default}}'.format(item=item,prop=prop,val=new))

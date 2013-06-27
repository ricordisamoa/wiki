# -*- coding: utf-8  -*-

import pywikibot

site=pywikibot.Site('it','wikipedia')

for image in site.allimages(prefix='Stub ',total=None):
	data=pywikibot.data.api.Request(site=site,action='query',titles=image.title(),prop='duplicatefiles').submit()['query']['pages']
	for info in data:
		if 'duplicatefiles' in data[info]:
			for df in data[info]['duplicatefiles']:
				if 'shared' in df:
					pywikibot.output(u'\03{{lightyellow}}shared duplicate found for {local}: {shared}\03{{default}}'.format(local=image.title(),shared=df['name']))
		else:
			pywikibot.output(u'\03{{lightblue}}no duplicate found for {local}\03{{default}}'.format(local=image.title()))

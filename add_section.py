# -*- coding: utf-8  -*-

import pywikibot

def insert(site=pywikibot.Site('it','wikipedia'),title='Wikipedia:Vandalismi in corso'):
	header=pywikibot.data.api.Request(site=site,action='expandtemplates',text='{{#timel:d xg}}').submit()['expandtemplates']['*']
	page=pywikibot.Page(site,title)
	text=page.get(force=True)
	if pywikibot.textlib.does_text_contain_section(text,header):
		pywikibot.output(u'\03{{lightyellow}}{page} already contains the header for "{header}"\03{{default}}'.format(page=page,header=header))
		return
	page.text+=u'\n\n== {header} =='.format(header=header)
	pywikibot.showDiff(text,page.text)
	page.save(comment='[['+site.namespace(4)+':Bot|Bot]]: inserimento della sezione giornaliera',minor=True,botflag=True)

if __name__=='__main__':
	pywikibot.handleArgs()
	insert()

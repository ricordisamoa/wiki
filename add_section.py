# -*- coding: utf-8  -*-

import pywikibot

pages={
	'wikipedia':{
		'it':[
			{
				'title':'Wikipedia:Vandalismi in corso',
				'level':3
			}
		]
	}
}

def main():
	for family in pages:
		for lang in pages[family]:
			for page in pages[family][lang]:
				kwargs=page
				kwargs['page']=pywikibot.Page(pywikibot.Site(lang,family),kwargs['title'])
				del kwargs['title']
				insert(**kwargs)

def insert(page,level=2,space=True,zero_padded=False,minorEdit=True):
	header=pywikibot.data.api.Request(site=page.site,action='expandtemplates',text='{{#timel:%s xg}}'%('d' if zero_padded else 'j')).submit()['expandtemplates']['*']
	text=page.get(force=True)
	if pywikibot.textlib.does_text_contain_section(text,header):
		pywikibot.output(u'\03{{lightyellow}}{page} already contains the header for "{header}"\03{{default}}'.format(page=page,header=header))
		return
	if isinstance(level,int):
		level='='*level
	if isinstance(space,bool):
		space=(' ' if space==True else '')
	page.text+=u'\n\n{level}{space}{header}{space}{level}'.format(header=header,level=level,space=space)
	pywikibot.showDiff(text,page.text)
	page.save(comment='[['+page.site.namespace(4)+':Bot|Bot]]: inserimento della sezione giornaliera',minor=minorEdit,botflag=True)

if __name__=='__main__':
	pywikibot.handleArgs()
	main()

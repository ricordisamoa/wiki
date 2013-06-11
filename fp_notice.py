# -*- coding: utf-8  -*-

import pywikibot

def usingPages(image):
	return image.site.imageusage(image,namespaces=0,filterredir=False)

def log(enpage,itpage,immagine):
	it=itpage.site
	logpage=pywikibot.User(it,it.user()).getUserPage(subpage='FP')
	add='{{/segnalazione|it=%(it)s|en=%(en)s|immagine=%(immagine)s}}'%{'it':itpage.title(),'en':enpage.title(),'immagine':immagine.title(withNamespace=False)}
	logpage.get(force=True)
	if add in logpage.text:
		pywikibot.output('\03{lightgreen}already logged\03{default}')
		return
	logpage.text+='\n\n'+add
	logpage.save(comment='[['+it.namespace(4)+':Bot|Bot]]: nuova segnalazione',minor=False,botflag=True)

def main(family,total):
	en=pywikibot.Site('en',family)
	it=pywikibot.Site('it',family)
	if not it.logged_in():
		it.login()
	commons=pywikibot.Site('commons','commons')
	for image in pywikibot.Category(commons,'Featured pictures on Wikimedia Commons').articles(namespaces=6,total=70):
		image_en=pywikibot.ImagePage(en,image.title())
		using_en=usingPages(image_en)
		if len(list(using_en))==0:
			pywikibot.output(u'no pages using "{image}" on {site}'.format(image=image.title(),site=en.dbName()))
			continue
		image_it=pywikibot.ImagePage(it,image.title())
		using_it=usingPages(image_it)
		for page in using_en:
			langlink=[linked for linked in page.langlinks() if linked.site==it]
			if len(langlink)==1:
				langlink=pywikibot.Page(langlink[0])
				pywikibot.output('\03{'+(u'lightgreen}}{en} and {it} have "{image}"' if langlink in list(using_it) else 'lightred}}{en} has {image} but {it} has not').format(en=page,image=image.title(),it=langlink)+'\03{default}')
				if not langlink in list(using_it):
					log(page,langlink,image)
			elif len(langlink)==0:
				pywikibot.output(u'\03{lightyellow}'+u'{en} has "{image}" but no {langlink} langlink is present'.format(en=page,image=image.title(),langlink=it)+'\03{default}')

if __name__ == '__main__':
	total=None
	family='wikipedia'
	for arg in pywikibot.handleArgs():
		if arg.startswith('-total:'):
			total=int(total[7:])
		elif arg.startswith('-family:'):
			family=total[8:]
	main(family,total)

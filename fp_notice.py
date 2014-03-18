# -*- coding: utf-8  -*-

import pywikibot


def usingPages(image, namespaces=[0]):
    return image.site.imageusage(image, namespaces=namespaces, filterredir=False)


def log(enpage, localpage, image):
    local = localpage.site
    logpage = pywikibot.User(local, local.user()).getUserPage(subpage='FP')
    logpage.get(force=True)
    add = u'{{{{/segnalazione|it={localpage}|en={enpage}|immagine={image}}}}}'.format({'local': localpage.title(),
                                                                                       'en': enpage.title(),
                                                                                       'image': image.title(withNamespace=False)
                                                                                       })
    if add in logpage.text:
        pywikibot.output(u'\03{lightgreen}already logged')
    else:
        logpage.text += u'\n\n' + add
        logpage.save(comment=u'[['+local.namespace(4)+u':Bot|Bot]]: nuova segnalazione', minor=False, botflag=True)


def main(local, total):
    en = pywikibot.Site('en', local.family.name)
    if not local.logged_in():
        local.login()
    commons = pywikibot.Site('commons', 'commons')
    for image in pywikibot.Category(commons, 'Featured pictures on Wikimedia Commons').articles(namespaces=6, total=total):
        image_en = pywikibot.ImagePage(en, image.title())
        using_en = usingPages(image_en)
        if len(list(using_en)) == 0:
            pywikibot.output(u'no pages using "{image}" on {site}'.format(image=image.title(), site=en))
            continue
        image_local = pywikibot.ImagePage(local, image.title())
        using_local = usingPages(image_local)
        for enpage in using_en:
            try:
                langlinks = [linked for linked in enpage.langlinks() if linked.site == local]
                if len(langlinks) == 1:
                    localpage = pywikibot.Page(langlinks[0])
                    kwargs = dict(enpage=enpage, localpage=localpage, image=image)
                    if langlink in list(using_local):
                        pywikibot.output(u'\03{{lightgreen}}{enpage} and {localpage} have {image}'.format(**kwargs))
                    else:
                        pywikibot.output(u'\03{{lightred}}{enpage} has {image} but {localpage} has not'.format(**kwargs))
                        log(**kwargs)
                elif len(langlink) == 0:
                    pywikibot.output(u'\03{{lightyellow}}{enpage} has {image} but no langlinks to {local} have been found'.format(en=page, image=image, local=local))
            except:
                pass

if __name__ == "__main__":
    total = None
    for arg in pywikibot.handleArgs():
        if arg.startswith('-total:'):
            total = int(arg[7:])
    main(pywikibot.Site(), total)

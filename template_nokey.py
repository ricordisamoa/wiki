# -*- coding: utf-8  -*-

import re
import pywikibot


def main(site=None, save=True, autosave=False, forcecat=False, forcelen=False):
    if site is None:
        site = pywikibot.Site()
    c = site.namespace(14)
    y = '[['+c+':\g<cat>]]'
    z = ur'\[\[\s*([Cc]ategory|['+re.escape(c[0].upper()+c[0].lower())+']'+re.escape(c[1:])+')\:(?P<cat>'
    if forcecat:
        pages = pywikibot.Category(site, forcecat).articles(namespaces=10)
        z += ur'['+re.escape(forcecat[0].upper()+forcecat[0].lower())+']'+re.escape(forcecat[1:])
    else:
        pages = site.allpages(namespace=10, filterredir=False)
        z += ur'[^\|\[\]]*[Tt]emplate[^\|\[\]]+'
    z += ur')\s*\|('
    pages = [page for page in pages if (not forcelen or len(page.title(withNamespace=False)) == forcelen) and page.canBeEdited()]
    for page in pages:
        text = page.get(force=True)
        page.text = re.sub(z+re.escape(page.title(withNamespace=False))+'|\{\{PAGENAME\}\})\s*\]\]', y, page.text)
        if text != page.text:
            pywikibot.showDiff(text, page.text)
            if save and (autosave or pywikibot.inputChoice(page.title(), ['Yes', 'No'], ['Y', 'N'], 'N').strip().lower() in ['yes', 'y']):
                try:
                    page.save(comment=u'[['+site.namespace(4)+':Bot|Bot]]: rimozione chiave di categorizzazione non necessaria',
                              minor=True, botflag=True)
                except pywikibot.LockedPage:
                    pywikibot.output(u'\03{lightyellow}page is locked')

if __name__ == "__main__":
    pywikibot.handleArgs()
    main()

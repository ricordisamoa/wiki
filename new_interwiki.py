# -*- coding: utf-8  -*-

import re
import pywikibot
from pywikibot import output, pagegenerators, textlib
from pywikibot.i18n import translate
from wikidata_summary import summary as wikidata_summary

import_summary = {
    'en': u'import %(sitelinks)s sitelink{{PLURAL:%(count)d||s}} from %(source)s'
}


class InterwikiBot:
    def __init__(self, generator):
        self.generator = generator

    def run(self):
        for page in self.generator:
            treat(page)


def treat(page):
    text = page.get(force=True)
    toImport = []
    toRemove = []
    importInto = pywikibot.ItemPage.fromPage(page)
    if not importInto.exists():
        items = {}
    else:
        items = None
        importInto.get(force=True)
    langlinks = textlib.getLanguageLinks(page.text, insite=page.site)
    for site, langlink in enumerate(langlinks):
        langlinkItem = pywikibot.ItemPage.fromPage(langlink)
        print langlink, langlinkItem
        if items is not None and langlinkItem.exists():
            if langlinkItem.getID() in items:
                items[langlinkItem.getID()] += 1
            else:
                items[langlinkItem.getID()] = 1
        if importInto.exists():
            if not site.dbName() in importInto.sitelinks:
                toImport.append(langlink)
            elif importInto.sitelinks[site.dbName()] == langlink.title():
                toRemove.append(langlink)
            else:
                output(u'\03{lightred}interwiki conflict!')
                return
        elif not page in toImport:
            toImport.append(page)
    if items is not None:
        if len(items) > 0:
            items = list(sorted(items.keys(), key=items.__getitem__))
            importInto = pywikibot.ItemPage(page.site.data_repository(), items[-1])
        else:
            importInto = None
    print items, importInto, toRemove, toImport
    if len(toImport) > 0:
        if importInto and importInto.exists():
            toImport = [sitelink for sitelink in toImport if canImport(importInto, sitelink)]
            print toImport
            if len(toImport) > 0:
                dbNames = [p.site.dbName() for p in toImport]
                summary = translate(importInto.site, import_summary,
                                    {'sitelinks': u', '.join(dbNames[:-2] + [u' and '.join(dbNames[-2:])]),
                                     'count': len(dbNames),
                                     'source': page.site.dbName()
                                     })
                importInto.setSitelinks(toImport, summary=summary)
                treat(page)
        return
    if len(toRemove) > 0:
        counter = 0
        for langlink in toRemove:
            temp = removeLanglink(text, langlink)
            if temp != text:
                counter += 1
                text = temp
        if counter == len(toRemove) and text != page.text:
            pywikibot.showDiff(page.text, text)
            page.text = text
            comment = translate(page.site, wikidata_summary[0],
                                {'counter': counter,
                                 'id': importInto.getID(),
                                 'user': page.site.user()
                                 })
            page.save(comment=comment, botflag=True, minor=True)
        else:
            output(u'\03{{lightred}}{} interwikis were to be removed but '
                   u'only {} were removed'.format(len(toRemove), counter))


def canImport(item, sitelink):
    item.get()
    if sitelink.site.dbName() in item.sitelinks:
        return False
    # prevents connecting a disambiguation page to a non-disambiguation item
    # and viceversa
    if isDisambig(item) != sitelink.isDisambig():
        return False
    # articles to galleries
    # project pages, templates, help pages and categories to self
    # https://www.wikidata.org/wiki/Wikidata:Requests_for_comment/Commons_links
    if sitelink.site.dbName() == 'commonswiki':
        if sitelink.namespace() in [0, 4, 10, 12, 14]:
            for page in item.iterlinks():
                if page.namespace() != sitelink.namespace():
                    return False
        elif sitelink.namespace() != 100 or not isPerson(item):  # creator
            return False
    return True


def allcase(string):
    return ''.join([ur'[' + re.escape(c.upper()) + re.escape(c.lower()) + ur']' for c in string])


def capitalized(string):
    return allcase(string[0]) + re.escape(string[1:])


def interwikiRegex(page):
    regex = ur'\[\[\s*%s\s*\:\s*%s\s*\]\]\s*' % (allcase(page.site.code),
                                                 capitalized(page.title()))
    regex = ur'(\s*\<noinclude\>[\s\n]*' + regex + ur'[\s\n]*\<\/\s*noinclude\>\s*|' + regex + ur')'
    return regex


def removeLanglink(text, langlink):
    regex = interwikiRegex(langlink)
    print regex
    exceptions = ['nowiki', 'comment', 'math', 'pre', 'source']
    text = textlib.replaceExcept(text, regex, '', exceptions)
    return text


def isInstanceOf(item, value):
    if 'P31' in item.claims:
        for claim in item.claims['P31']:
            try:
                if claim.getTarget().getID() == value:
                    return True
            except:
                pass
    return False


def isPerson(item):
    return isInstanceOf(item, 'Q5')


def isDisambig(item):
    if isInstanceOf(item, 'Q4167410'):
        return True
    for page in item.iterlinks():
        if page.isDisambig():
            return True
    return False


def main():
    genFactory = pagegenerators.GeneratorFactory()

    for arg in pywikibot.handleArgs():
        genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()
    if generator:
        bot = InterwikiBot(generator)
        bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

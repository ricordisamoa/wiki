# -*- coding: utf-8  -*-

import re
from operator import itemgetter
import pywikibot
from pywikibot import output, pagegenerators, textlib
from pywikibot.i18n import translate
from wikidata_summary import summary as wikidata_summary

import_summary = {
    'en': u'import %(sitelinks)s sitelink{{PLURAL:%(count)d||s}} from %(source)s'
}


class InterwikiBot:
    def __init__(self, generator, linked=False, comment=None):
        self.generator = generator
        self.linked = linked
        self.comment = comment

    def run(self):
        for page in self.generator:
            treat(page, comment=self.comment)
            if self.linked:
                treated = [page]
                for ll in [pywikibot.Page(ll) for ll in page.langlinks()]:
                    if ll.site.username() and ll not in treated:
                        treat(ll, comment=self.comment)
                        treated.append(ll)


def intelLabel(item, page):
    priority = ('wikipedia', 'wikivoyage', 'wikisource', 'commons')
    l = []
    for sl in item.iterlinks():
        if sl.site.lang == page.site.lang and sl.site.family.name in priority:
            l.append((priority.index(sl.site.family.name), sl.title()))
    l.append((priority.index(page.site.family.name) if page.site.family.name in priority else (len(priority) + 1), page.title()))
    l = sorted(l, key=itemgetter(0))
    return l[0][1]


def treat(page, comment):
    pywikibot.output(u'\n\n>>> \03{{lightpurple}}{}\03{{default}} <<<'.format(page.title(asLink=True)))
    try:
        text = page.get(force=True)
    except Exception, e:
        pywikibot.output(e)
        return
    toImport = []
    toRemove = []
    importInto = pywikibot.ItemPage.fromPage(page)
    if not importInto.exists():
        items = {}
    else:
        items = None
        importInto.get(force=True)
    langlinks = textlib.getLanguageLinks(page.text, insite=page.site)
    for site, langlink in langlinks.iteritems():
        langlinkItem = pywikibot.ItemPage.fromPage(langlink)
        if items is not None and langlinkItem.exists():
            if langlinkItem.getID() in items:
                items[langlinkItem.getID()] += 1
            else:
                items[langlinkItem.getID()] = 1
        if importInto.exists():
            if not site.dbName() in importInto.sitelinks:
                toImport.append(langlink)
            elif langlink.site.sametitle(importInto.sitelinks[site.dbName()], langlink.title()) or \
            (langlink.exists() and langlink.isRedirectPage() and langlink.getRedirectTarget() == pywikibot.Page(site, importInto.sitelinks[site.dbName()])):
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
    if len(toImport) > 0:
        if importInto and importInto.exists():
            toImport = [sitelink for sitelink in toImport if canImport(importInto, sitelink)]
            if len(toImport) > 0:
                dbNames = [p.site.dbName() for p in toImport]
                data = {'sitelinks': [], 'labels': []}
                for p in toImport:
                    data['sitelinks'].append({'site': p.site.dbName(), 'title': p.title()})
                    if not p.site.lang in importInto.labels:
                        data['labels'].append({'language': p.site.lang, 'value': intelLabel(importInto, p)})
                summary = translate(importInto.site, import_summary,
                                    {'sitelinks': u', '.join(dbNames[:-2] + [u' and '.join(dbNames[-2:])]),
                                     'count': len(dbNames),
                                     'source': page.site.dbName()
                                     })
                importInto.editEntity(data, summary=summary)
                treat(page=page, comment=comment)
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
            if comment is None:
                try:
                    comment = translate(page.site, wikidata_summary[0],
                                        {'counter': counter,
                                         'id': importInto.getID(),
                                         'user': page.site.user()
                                         })
                except IndexError:
                    try:
                        comment = translate(page.site, wikidata_summary[0],
                                            {'counter': counter,
                                             'id': importInto.getID()
                                             })
                    except Exception, e:
                        pywikibot.output(e)
                        return
            page.save(comment=comment, botflag=True, minor=True)
        else:
            output(u'\03{{lightred}}{} interwikis were to be removed but '
                   u'only {} were removed'.format(len(toRemove), counter))


def canImport(item, sitelink):
    item.get()
    if not sitelink.exists():
        return False
    if sitelink.isTalkPage():
        return False
    if sitelink.section() is not None:
        return False
    if sitelink.site.dbName() in item.sitelinks:
        return False
    if pywikibot.ItemPage.fromPage(sitelink).exists():
        return False
    # prevents connecting a disambiguation page to a non-disambiguation item
    # and viceversa
    if isDisambig(item) != sitelink.isDisambig():
        return False
    if sitelink.site.family.name not in ['wikipedia', 'wikiquote'] and isPerson(item) != isPerson(sitelink):
        return False
    # articles to galleries
    # project pages, templates, help pages and categories to self
    # https://www.wikidata.org/wiki/Wikidata:Requests_for_comment/Commons_links
    if sitelink.site.dbName() == 'commonswiki':
        if sitelink.namespace() in [0, 4, 10, 12, 14]:
            if isPerson(item):
                return False
            for page in item.iterlinks():
                if page.namespace() != sitelink.namespace():
                    return False
        elif not isPerson(sitelink):
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


def isPerson(arg):
    if isinstance(arg, pywikibot.page.ItemPage):
        return isInstanceOf(arg, 'Q5')
    elif isinstance(arg, pywikibot.page.Page):
        if arg.site.family.name == 'wikisource':
            ns = arg.site.family.authornamespaces
            if arg.namespace() in (ns[arg.site.code] or ns['_default']):
                return True
        elif arg.site.dbName() == 'commonswiki':
            return arg.namespace() == 100  # creator
    return False


def isDisambig(item):
    if isInstanceOf(item, 'Q4167410'):
        return True
    for page in item.iterlinks():
        if page.isDisambig():
            return True
    return False


def main():
    linked = False
    comment = None
    genFactory = pagegenerators.GeneratorFactory()
    for arg in pywikibot.handleArgs():
        if arg.startswith('-comment'):
            if len(arg) == 8:
                self.comment = pywikibot.input(u'What comment do you want to use?')
            else:
                comment = arg[9:]
        elif arg.startswith('-linked'):
            linked = True
        else:
            genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()
    if generator:
        bot = InterwikiBot(generator, linked=linked, comment=comment)
        bot.run()

if __name__ == "__main__":
    try:
        main()
    finally:
        pywikibot.stopme()

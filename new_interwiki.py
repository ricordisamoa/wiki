# -*- coding: utf-8  -*-

import re
from operator import itemgetter
import pywikibot
from pywikibot import pagegenerators, textlib
import mwparserfromhell
from wikidata_summary import summary as wikidata_summary

import_summary = {
    'en': u'import %(sitelinks)s sitelink{{PLURAL:%(count)d||s}} from %(source)s'
}

# language codes for which the WMF version differs from the correct one
labels = {
    'no': 'nb',
    'als': 'gsw',
    'fiu-vro': 'vro',
    'bat-smg': 'sgs',
    'be-x-old': 'be-tarask',
    'roa-rup': 'rup',
    'zh-classical': 'lzh',
    'zh-min-nan': 'nan',
    'zh-yue': 'yue',
    'crh': 'crh-latn'
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
                try:
                    for ll in [pywikibot.Page(ll) for ll in page.langlinks() if ll.site.username()]:
                        treat(ll, comment=self.comment)
                except Exception, e:
                    pywikibot.warning(e)


def interProjectLinks(page):
    config = {
        'itwiki': {
            'prefixes': ['q', 's', 'voy'],
            'remove': ['q', 's', 'voy']
        },
        'itwikiquote': {
            'prefixes': ['w', 's', 'voy']
        }
    }
    if page.site.dbName() in config:
        for template in mwparserfromhell.parse(page.text).ifilter_templates():
            if template.name[0].upper() + template.name[1:] in [u'Ip', u'Interprogetto']:
                prefixes = config[page.site.dbName()]['prefixes']
                for param in template.params:
                    if unicode(param.value).strip() != '':
                        if unicode(param.name).isnumeric():
                            if unicode(param.value) in prefixes:
                                yield pywikibot.Page(page.site, unicode(param.value) + ':' + page.title())
                        elif unicode(param.name) in prefixes:
                            lang = (unicode(template.get(unicode(param.name) + '_site').value) + ':') if template.has(unicode(param.name) + '_site') else ''
                            yield pywikibot.Page(page.site, unicode(param.name) + ':' + lang + unicode(param.value))


def lang(page):
    l = page.site.lang
    if l in labels:
        l = labels[l]
    return l


def intelLabel(item, page):
    # set of sites to get the label from
    priority = ('wikipedia', 'wikivoyage', 'wikiquote', 'wikisource', 'commons')
    l = []
    for sl in item.iterlinks():
        if lang(sl) == lang(page) and sl.site.family.name in priority:
            l.append((priority.index(sl.site.family.name), sl.title()))
    l.append((priority.index(page.site.family.name) if page.site.family.name in priority else (len(priority) + 1), page.title()))
    l = sorted(l, key=itemgetter(0))
    return l[0][1]


def treat(page, comment):
    pywikibot.output(u'\n\n>>> \03{{lightpurple}}{}\03{{default}} <<<'.format(page.title(asLink=True)))
    if page.isRedirectPage():
        treat(page.getRedirectTarget(), comment)
        return
    try:
        text = page.get(force=True)
    except Exception, e:
        pywikibot.warning(e)
        return

    toRemove = []
    importInto = pywikibot.ItemPage.fromPage(page)
    items = None
    if importInto.exists():
        importInto.get(force=True)
    else:
        # possible targets of link import
        items = {}

    # import interlanguage links
    langlinks = textlib.getLanguageLinks(page.text, insite=page.site)
    toImport = langlinks.copy()
    toImport[page.site] = page

    # import interproject links
    iws = list(set(interProjectLinks(page)))
    for iw in iws:
        if True not in [iw != i and i.site == iw.site for i in iws]:
            toImport[iw.site] = iw

    for site, link in toImport.iteritems():
        if link.isRedirectPage():
            toImport[site] = link.getRedirectTarget()

    if items is not None:
        for site, link in toImport.iteritems():
            linkItem = pywikibot.ItemPage.fromPage(link)
            if linkItem.exists():
                if linkItem.getID() in items:
                    items[linkItem.getID()] += 1
                else:
                    items[linkItem.getID()] = 1
        if len(items) > 0:
            # select the most appropriate item
            items = list(sorted(items.keys(), key=items.__getitem__))
            importInto = pywikibot.ItemPage(page.site.data_repository(), items[-1])
            importInto.get(force=True)
    if importInto is None or not importInto.exists():
        pywikibot.warning(u'no data item to import sitelinks into')
        return
    for site, langlink in langlinks.iteritems():
        if site.dbName() in importInto.sitelinks:
            try:
                if langlink.site.sametitle(importInto.sitelinks[site.dbName()], langlink.title()) or (
                   langlink.exists() and langlink.isRedirectPage() and langlink.getRedirectTarget().exists() and langlink.getRedirectTarget() == pywikibot.Page(site, importInto.sitelinks[site.dbName()])):
                    toRemove.append(langlink)
                else:
                    pywikibot.error(u'interwiki conflict: {} != {}'.format(langlink.title(), importInto.sitelinks[site.dbName()]))
                    return
            except Exception, e:
                pywikibot.warning(e)
    toImport = [sitelink for site, sitelink in toImport.iteritems() if sitelink.site.dbName() not in importInto.sitelinks or importInto.sitelinks[sitelink.site.dbName()] != sitelink.title()]
    if len(toImport) > 0:
        toImport = [sitelink for sitelink in toImport if canImport(importInto, sitelink)]
        if len(toImport) > 0:
            dbNames = [p.site.dbName() for p in toImport]
            data = {'sitelinks': [], 'labels': []}
            for p in toImport:
                data['sitelinks'].append({'site': p.site.dbName(), 'title': p.title()})
                lng = lang(p)
                if lng not in importInto.labels:
                    data['labels'].append({'language': lng, 'value': intelLabel(importInto, p)})
            summary = pywikibot.i18n.translate(importInto.site, import_summary,
                                               {'sitelinks': u', '.join(dbNames[:-2] + [u' and '.join(dbNames[-2:])]),
                                                'count': len(dbNames),
                                                'source': page.site.dbName()
                                                })
            try:
                importInto.editEntity(data, summary=summary)
                pywikibot.output(u'\03{{lightgreen}}successfully imported {} sitelinks and {} labels'.format(len(data['sitelinks']), len(data['labels'])))
            except Exception, e:
                pywikibot.warning(e)
                return
            treat(page=page, comment=comment)
        return
    toRemove = [link for link in toRemove if link.site.family == page.site.family]
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
                    comment = pywikibot.i18n.translate(page.site, wikidata_summary[0],
                                                       {'counter': counter,
                                                        'id': importInto.getID(),
                                                        'user': page.site.user()
                                                        })
                except IndexError:
                    try:
                        comment = pywikibot.i18n.translate(page.site, wikidata_summary[0],
                                                           {'counter': counter,
                                                            'id': importInto.getID()
                                                            })
                    except Exception, e:
                        pywikibot.warning(e)
                        return
            try:
                page.save(comment=comment, botflag=True, minor=True)
            except Exception, e:
                pywikibot.warning(e)
        else:
            pywikibot.error(u'{} interwikis were to be removed but only {} were removed'.format(len(toRemove), counter))


def canImport(item, sitelink):
    item.get()
    try:
        # otherwise it will throw an API error
        if not sitelink.exists():
            return False
        if sitelink.isTalkPage():
            return False
        # interwikis containing section links cannot be imported
        # and are often source of conflicts
        if sitelink.section() is not None:
            return False
        if sitelink.site.dbName() in item.sitelinks:
            return False
        if pywikibot.ItemPage.fromPage(sitelink).exists():
            return False
        # prevents connecting a disambiguation page to a non-disambiguation item
        if isDisambig(item) != sitelink.isDisambig():
            return False
        # a category to a non-category
        if isCategory(item) != sitelink.isCategory():
            return False
        # a template to a non-template
        if isTemplate(item) != isTemplate(sitelink):
            return False
        # a project page to a non-project page
        if isProjectPage(item) != isProjectPage(sitelink):
            return False
        # a person to a non-person
        if sitelink.site.family.name not in ['wikipedia', 'wikiquote'] and isPerson(item) != isPerson(sitelink):
            return False
        # special cases for Commons:
        # articles to galleries;
        # project pages, templates, help pages and categories to self:
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
    except Exception, e:
        pywikibot.warning(e)
        return False


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


def isCategory(item):
    return isInstanceOf(item, 'Q4167836')


def isTemplate(arg):
    if isinstance(arg, pywikibot.page.ItemPage):
        return isInstanceOf(arg, 'Q11266439')
    elif isinstance(arg, pywikibot.page.Page):
        return arg.namespace() == 10
    return False


def isProjectPage(arg):
    if isinstance(arg, pywikibot.page.ItemPage):
        return isInstanceOf(arg, 'Q14204246')
    elif isinstance(arg, pywikibot.page.Page):
        return arg.namespace() == 4
    return False


def main():
    linked = False
    comment = None
    genFactory = pagegenerators.GeneratorFactory()
    for arg in pywikibot.handleArgs():
        if arg.startswith('-comment'):
            if len(arg) == 8:
                comment = pywikibot.input(u'What comment do you want to use?')
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

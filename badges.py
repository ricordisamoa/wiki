# -*- coding: utf-8  -*-
"""
Script to remove {{Link FA}} and similar templates in favor of Wikibase badges.

Such templates were used on various Wikimedia sites to show a star besides
interlanguage links in the sidebar. Since Wikidata supports badges, they are
no longer needed.
The mwparserfromhell library is required for the bot to work.

------------------------------------------------------------------------------

Usage:

python badges.py [pagegenerators] [options]

You can use any typical pagegenerator to provide with a list of pages.

------------------------------------------------------------------------------

This script understands the following command-line arguments:

-summary:<summary>  Use <summary> instead of the default one.

-tmp:<template>     Add {{<template>}} at the end of the page.

-force              Do not check that the old templates are correct,
                    just remove them.

"""

import pywikibot
from pywikibot import i18n, pagegenerators, Bot
import mwparserfromhell


class BadgesBot(Bot):

    """Bot to remove star templates when corresponding badges are present."""

    templates = {
        ('Link V', 'Link FA', 'Link AdQ', 'Link FL'): 'Q17437796',
        ('Link VdQ', 'Link GA'): 'Q17437798'
    }

    summary = {
        'en': u'%(templates)s from Wikidata',
        'it': u'%(templates)s non più necessari grazie a Wikidata',
    }

    def __init__(self, **kwargs):
        """Initialize and configure the bot object."""
        self.availableOptions.update({
            'force': False,
            'tmp': None,
            'summary': None,
        })
        super(BadgesBot, self).__init__(**kwargs)

    def remove_element(self, wikicode, el):
        """
        Remove a node and the surrounding space from its parent.

        @param wikicode: the parent from which to remove the element
        @type wikicode: mwparserfromhell.wikicode.Wikicode
        @param el: the element to remove
        @type el: mwparserfromhell.nodes.Node
        """
        index = wikicode.index(el)
        try:
            before = wikicode.get(index - 1)
            if isinstance(before, mwparserfromhell.nodes.text.Text) and \
               before.rstrip(' ').endswith('\n'):
                wikicode.replace(before, before.rstrip(' '))
        except IndexError:
            pass
        try:
            after = wikicode.get(index + 1)
            if isinstance(after, mwparserfromhell.nodes.text.Text):
                lstripped = after.lstrip(' ')
                if lstripped.startswith('\n\n'):
                    wikicode.replace(after, lstripped[2:])
                elif lstripped.startswith('\n'):
                    wikicode.replace(after, lstripped[1:])
        except IndexError:
            pass
        wikicode.remove(el)

    def treat(self, page):
        """
        Load the given page, make the required changes, and save it.

        @param page: the page to treat
        @type page: pywikibot.Page
        """
        try:
            item = pywikibot.ItemPage.fromPage(page)
        except pywikibot.NoPage:
            return
        item.get()
        page.get()
        wikicode = mwparserfromhell.parse(page.text)
        tmps = set()
        for tmp in wikicode.ifilter_templates():
            tname = tmp.name.strip()
            if page.site.namespaces[10].case == 'first-letter':
                tname = tname[0].upper() + tname[1:]
            if self.getOption('tmp') and tname == self.getOption('tmp'):
                self.remove_element(wikicode, tmp)
                break
            for templates, badge_id in self.templates.items():
                if tname in templates:
                    if len(tmp.params) != 1 or not tmp.has('1'):
                        pywikibot.warning(u'invalid template "{tmp}" on {page}'.format(tmp=tname, page=page))
                        return
                    if not self.getOption('force'):
                        iwsite = pywikibot.Site(tmp.get('1').value.strip(), page.site.family.name)
                        if iwsite in item.sitelinks:
                            badges = [badge.getID() for badge in item.sitelinks[iwsite].badges]
                            if badges != [badge_id]:
                                pywikibot.warning(u'expected {badge_id} instead of {badges}'.format(badge_id=badge_id, badges=badges))
                                return
                        else:
                            pywikibot.warning(u'{site} sitelink not found'.format(site=iwsite.dbName()))
                            return
                    self.remove_element(wikicode, tmp)
                    tmps.add(tname)
                    break
        newtext = unicode(wikicode)
        if self.getOption('tmp'):
            newtext = u'%s\n\n{{%s}}' % (newtext.rstrip(), self.getOption('tmp'))
        summary = self.getOption('summary')
        if not summary:
            tmps = ['{{[[Template:%(tmp)s|%(tmp)s]]}}' % {'tmp': tmp}
                    for tmp in sorted(tmps)]
            summary = i18n.translate(page.site,
                                     self.summary,
                                     {'templates': page.site.list_to_text(tmps)},
                                     fallback=True)
        self.userPut(page, page.text, newtext, comment=summary)


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    options = {}
    local_args = pywikibot.handle_args(args)
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if genFactory.handleArg(arg):
            continue
        if arg.startswith('-summary:'):
            options['summary'] = arg[9:]
        elif arg.startswith('-tmp:'):
            options['tmp'] = arg[5:]
        elif arg == '-force':
            options['force'] = True
        elif arg == '-always':
            options['always'] = True

    gen = genFactory.getCombinedGenerator()
    if gen:
        bot = BadgesBot(generator=gen, **options)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == '__main__':
    main()

# -*- coding: utf-8  -*-
"""
This script can merge several rugby statistics templates into one, mainly on
the Italian Wikipedia.
It requires the mwparserfromhell library.

------------------------------------------------------------------------------

Usage:

python rugby.py [pagegenerators]

You can use any typical pagegenerator to provide with a list of pages.

"""

from operator import attrgetter
import pywikibot
from pywikibot import i18n, pagegenerators, Bot
import mwparserfromhell


def tmp_link(site, name):
    return pywikibot.Page(site, name, ns=10).title(asLink=True, insite=site)


unified = 'Link statistiche rugbisti a 15'
tmps = {
    'Statistiche Barbarians':          ['Barbarians'],
    'Scheda All Blacks':               ['All Blacks'],
    'Statistiche British Lions':       ['British Lions'],
    'Statistiche Barbarian francesi':  ['Barbarian francesi'],
    'Statistiche Pro12':               ['Pro12'],
    'Statistiche Celtic League':       ['Pro12'],
    'ErcRugby':                        ['ErcRugby'],
    'Scheda ItsRugby':                 ['ItsRugby'],
    'Statistiche English Premiership': [None, 'P861'],
    'Scrum':                           [None, 'P858'],
}
weblinks = ((2,), 'Collegamenti esterni')
reason = u'{} - [[Special:Permalink/67070342#Sostituzione template collegamenti esterni e ' \
         u'importazione valori parametri|richiesta]]'


class RugbyBot(Bot):
    def __init__(self, generator, **kwargs):
        super(RugbyBot, self).__init__(**kwargs)
        self.generator = generator

    def run(self):
        for page in self.generator:
            self.treat(page)

    def treat(self, page):
        code = mwparserfromhell.parse(page.text)
        sections = code.get_sections(levels=weblinks[0], flat=True, include_lead=False,
                                     include_headings=True)
        removed = []
        section_found = False
        for section in sections:
            headings = section.filter_headings()
            if len(headings) == 0:
                # a non-lead section must have a heading
                return
            first_tmp = None
            if weblinks[1] in [heading.title.strip() for heading in headings]:
                if section_found:
                    pywikibot.warning(u'multiple sections are named "{}"'.format(weblinks[1]))
                    return
                section_found = True
                for template in section.ifilter_templates():
                    tname = template.name.strip()
                    tname = tname[0].upper() + tname[1:]
                    if tname == unified:
                        first_tmp = template
                        break  # unified template already present
                for template in section.ifilter_templates():
                    tname = template.name.strip()
                    tname = tname[0].upper() + tname[1:]
                    if tname in tmps:
                        if len(template.params) == 2 and template.has('2') and \
                           page.title().startswith(template.get('2').strip()):
                            template.remove('2', keep_field=False)
                        if len(tmps[tname]) > 1 and tmps[tname][1] is not None:
                            prop = tmps[tname][1]
                            item = pywikibot.ItemPage.fromPage(page)
                            if not item.exists():
                                pywikibot.warning(u'no item found for {}'.format(page))
                                return
                            item.get()
                            if template.has('1'):
                                if prop not in item.claims:
                                    pywikibot.warning(u'no claims found for {}'.format(prop))
                                    return
                                if len(item.claims[prop]) != 1 or \
                                   item.claims[prop][0].getTarget() != template.get('1').strip():
                                    pywikibot.warning(u'the {} claim does not match the parameter'.format(prop))
                                    return
                        elif len(template.params) != 1 or not template.has('1'):
                            pywikibot.warning(u'invalid parameter(s) found in {}'.format(tname))
                            return
                        if len(tmps[tname]) > 1 and tmps[tname][0] is None:
                            equiv = None
                        else:
                            equiv = [' ' + tmps[tname][0] + ' ', template.get('1').strip()]
                        if template.has('1'):
                            template.remove('1', keep_field=False)
                        removed.append(template.name)
                        if first_tmp is None:
                            template.name = unified + '\n '
                            first_tmp = template
                        else:
                            while True:
                                before = code.get(code.index(template) - 1)
                                if '\n' in before:
                                    if not before.rstrip(' ').endswith('\n'):
                                        pywikibot.warning(u'unexpected character(s) before template: "{}"'.format(before))
                                        return
                                    break
                                if before.strip() in ('', '*'):
                                    code.remove(before)
                                else:
                                    pywikibot.warning(u'unexpected character(s) before template: "{}"'.format(before))
                                    return
                            try:
                                after = code.get(code.index(template) + 1)
                                if isinstance(after, mwparserfromhell.nodes.text.Text) and \
                                   unicode(after).startswith('\n'):
                                    code.replace(after, unicode(after)[1:])
                                else:
                                    pywikibot.warning(u'unexpected character(s) after template: "{}"'.format(after))
                                    return
                            except IndexError:
                                pass
                            code.remove(template)
                        if equiv:
                            first_tmp.add(*equiv, preserve_spacing=False)

                if first_tmp:
                    if len(first_tmp.params) == 0:
                        first_tmp.name = first_tmp.name.strip()
                    first_tmp.params.sort(key=attrgetter('name'))  # sort params by name
                    for index, param in enumerate(first_tmp.params):
                        # enforce spacing conventions
                        param.value = ' ' + param.value.strip() + '\n' + \
                                      ('' if index == len(first_tmp.params) - 1 else ' ')
        removed = [tmp_link(page.site, name) for name in set(removed)]
        new = unicode(code)
        comment = i18n.translate(page.site.lang,
                                 {'it': u'unione di %(templates)s in %(into)s'},
                                 {'templates': page.site.list_to_text(removed),
                                  'into': tmp_link(page.site, unified)})
        # comment = reason.format(comment)
        self.userPut(page, page.text, new, comment=comment)


if __name__ == "__main__":
    local_args = pywikibot.handleArgs()
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        genFactory.handleArg(arg)

    gen = genFactory.getCombinedGenerator()
    if gen:
        gen = pagegenerators.PreloadingGenerator(gen)
        bot = RugbyBot(gen)
        bot.run()
    else:
        pywikibot.showHelp()

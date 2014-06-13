# -*- coding: utf-8  -*-

import re
import pywikibot
from pywikibot import i18n, pagegenerators, Bot
import mwparserfromhell
from wikidata_summary import summary as wikidata_summary


class ItWsBot(Bot):

    params = {
        'wp': 'Nome della pagina su Wikipedia',
        'wq': 'Nome della pagina su Wikiquote',
        'cc': 'Nome della pagina su Commons',
    }

    def __init__(self, generator, **kwargs):
        super(ItWsBot, self).__init__(**kwargs)
        self.generator = generator

    def run(self):
        for page in self.generator:
            self.treat(page)

    def handle_wp(self, val, item):
        return ('itwiki' in item.sitelinks and item.sitelinks['itwiki'] == val)

    def handle_wq(self, val, item):
        return ('itwikiquote' in item.sitelinks and item.sitelinks['itwikiquote'] == val)

    def handle_cc(self, val, item):
        return (val.startswith('Category:') and 'P373' in item.claims and
                len(item.claims['P373']) == 1 and item.claims['P373'][0].getTarget() == val[9:])

    def treat(self, page):
        pywikibot.output(u'parsing {}'.format(page))
        item = pywikibot.ItemPage.fromPage(page)
        if not item.exists():
            pywikibot.warning(u'item not found for {}'.format(page))
            return
        text = page.text
        code = mwparserfromhell.parse(page.text)
        removed = []

        for template in code.ifilter_templates():
            if template.name.strip().title() != 'Autore':
                continue
            for pcode, pname in self.params.items():
                if template.has(pname, False):
                    val = template.get(pname).value.strip()
                    if val == '' or getattr(self, 'handle_' + pcode)(val, item) is True:
                        template.remove(pname, keep_field=False)
                        removed.append(pname)

        sections = {}
        sbeg = None
        elements = code.filter()
        for el in code.ifilter_tags():
            if el.tag == 'section' and el.self_closing is True:
                if el.has('begin'):
                    sbeg = el
                elif sbeg and el.has('end'):
                    sname = unicode(sbeg.get('begin').value)
                    if unicode(el.get('end').value) == sname:
                        start = elements.index(sbeg) + 2 + len(sbeg.attributes) * 2
                        sections[sname] = [sbeg] + elements[start:elements.index(el) + 1]
        for scode, sname in self.params.items():
            if sname in sections:
                val = ''.join(map(unicode, sections[sname][1:-1])).strip()
                if val == '' or getattr(self, 'handle_' + scode)(val, item) is True:
                    for el in sections[sname]:
                        code.remove(el)
                    removed.append(sname)

        if len(removed) == 6:
            remset = list(set(removed))
            if len(remset) != 3:
                return
            removed = list(remset)
            text = unicode(code)
            text = re.sub('(?<=\/\>)(\n\s*)+(?=\n\<)', '', text)
            comment = i18n.translate(page.site, wikidata_summary[1],
                                     {'counter': len(removed),
                                      'params': page.site.list_to_text(removed),
                                      'id': item.getID()
                                      })
            try:
                self.userPut(page, page.text, text, comment=comment, minor=True, botflag=True)
            except Exception as e:
                pywikibot.exception(e)


if __name__ == "__main__":
    options = {}

    local_args = pywikibot.handleArgs()
    genFactory = pagegenerators.GeneratorFactory()
    for arg in local_args:
        if arg == '-always':
            options['always'] = True
        else:
            genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()
    if generator:
        bot = ItWsBot(generator, **options)
        bot.run()

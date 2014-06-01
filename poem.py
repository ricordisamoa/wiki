# -*- coding: utf-8  -*-
"""
This script can remove old templates for line numbers embedded in <poem> tags,
auto-detecting the appropriate numbering scheme for each poetry block.
It requires the mwparserfromhell library.

------------------------------------------------------------------------------

Usage:

python poem.py [pagegenerators] [options]

You can use any typical pagegenerator to provide with a list of pages.

------------------------------------------------------------------------------

This script understands the following command-line arguments:

-preferred:tagname  The bot will replace <poem> tags with <tagname>.
                    Useful for setting tagname to 'lines'.

"""

import pywikibot
from pywikibot import i18n, pagegenerators, Bot
import mwparserfromhell


class PoemBot(Bot):
    def __init__(self, generator, **kwargs):
        self.availableOptions.update({
            'tags':  ['poem'],
            'preferred': None,
            'summary': None,
        })

        super(PoemBot, self).__init__(**kwargs)
        self.generator = generator

        pref = self.getOption('preferred')
        if pref and pref not in self.getOption('tags'):
            self.getOption('tags').append(pref)

        self.line_tmps = {
            'wikisource': {
                'it': ('R')
            }
        }

        self.summary = {
            'en': u'automatic line numbering in <poem> tag',
            'it': u'numerazione versi automatica in tag <poem>',
        }

    def run(self):
        for page in self.generator:
            self.treat(page)

    def detect_numbering(self, nums):
        """
        Tries to detect the line numbering scheme from the given markers.
        """
        if len(set(nums)) != len(nums):
            return
        mode = None
        for i, num in enumerate(nums[1:]):
            current = num - nums[i]
            if mode:
                if current != mode:
                    return
            else:
                mode = current
        return {'number-step': mode}

    def process_lines(self, page, lines):
        ln = 0
        numbering = []
        lines = lines.split('\n')
        for i, line in enumerate(lines):
            if line.strip() != '':
                ln += 1
                code = mwparserfromhell.parse(line)
                for tmp in code.ifilter_templates():
                    if tmp.name.strip() not in i18n.translate(page.site, self.line_tmps, fallback=False):
                        pywikibot.warning(u'unexpected template: "{}"'.format(tmp.name))
                        continue
                    if ln in numbering:
                        pywikibot.warning(u'exceeding template: "{}"'.format(tmp.name))
                        return
                    params = [param for param in tmp.params if tmp.has(param.name, True)]
                    if len(params) == 0:
                        pywikibot.warning(u'no parameters found in "{}"'.format(tmp.name))
                        return
                    if len(params) > 1:
                        pywikibot.warning(u'multiple parameters found in "{}"'.format(tmp.name))
                        return
                    if params[0].name.strip() != '1':
                        pywikibot.warning(u'unexpected parameter: "{}" in "{}"'.format(params[0].name, tmp.name))
                        return
                    if params[0].value.strip() != unicode(ln):
                        pywikibot.warning(u'unexpected line marker: "{}" in "{}"'.format(params[0].value, tmp.name))
                        return
                    if params[0].value.strip() != unicode(ln):
                        pywikibot.warning(u'unexpected line marker: "{}" in "{}"'.format(params[0].value, tmp.name))
                        return
                    if line.rstrip()[-len(unicode(tmp)):] != unicode(tmp):
                        pywikibot.warning(u'the "{}" template is not at the end of the line'.format(tmp.name))
                        return
                    line = line.rstrip()[:-len(unicode(tmp))]
                    line = line.rstrip()  # possibly breaking change
                    lines[i] = line
                    numbering.append(ln)
        return '\n'.join(lines), numbering

    def treat(self, page):
        """
        Loads the given page, makes the required changes, and saves it.
        """
        page.get()
        wikicode = mwparserfromhell.parse(page.text)
        for el in wikicode.ifilter_tags():
            if el.tag in self.getOption('tags'):
                result = self.process_lines(page, el.contents)
                if result:
                    lines, numbering = result
                    if lines != el.contents:
                        scheme = self.detect_numbering(numbering)
                        if scheme:
                            el.contents = lines
                            for attr, val in scheme.items():
                                el.add(attr, val)
                            if self.getOption('preferred'):
                                # change the tag name to the preferred form
                                el.tag = self.getOption('preferred')
                        else:
                            pywikibot.warning(u'a reliable line numbering scheme could not be obtained')
        newtext = unicode(wikicode)
        summary = self.getOption('summary')
        if not summary:
            summary = i18n.translate(page.site, self.summary, fallback=True)
        self.userPut(page, page.text, newtext, comment=summary)


if __name__ == "__main__":
    options = {}
    local_args = pywikibot.handleArgs()
    genFactory = pagegenerators.GeneratorFactory()

    for arg in local_args:
        if genFactory.handleArg(arg):
            continue
        if arg.startswith('-'):
            if ':' in arg:
                options[arg[1:].split(':', 1)[0].lower()] = arg[1:].split(':', 1)[1]
            else:
                options[arg[1:].lower()] = True

    gen = genFactory.getCombinedGenerator()
    if gen:
        bot = PoemBot(gen, **options)
        bot.run()
    else:
        pywikibot.showHelp()

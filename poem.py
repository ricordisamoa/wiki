# -*- coding: utf-8  -*-
"""
Script to convert old line numbering templates to attributes of <poem> tags.

It can auto-detect the appropriate numbering scheme for each <poem> block
and remove templates that were used to achieve the same effect.
The mwparserfromhell library is required.

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


class PoemError(pywikibot.Error):

    """Basic class for PoemBot-specific errors."""

    def __init__(self, message, *args, **kwargs):
        """
        Constructor.

        @param message: message for the exception
        @type message: basestring
        """
        self.message = message.format(*args, **kwargs)
        super(PoemError, self).__init__(self.message)


class PoemBot(Bot):

    """Bot to migrate old line templates to the new format."""

    line_tmps = {
        'wikisource': {
            'it': ('R',)
        }
    }

    summary = {
        'en': u'automatic line numbering in <poem> tag',
        'it': u'numerazione versi automatica in tag <poem>',
    }

    def __init__(self, generator, **kwargs):
        """Initialize and configure the bot object."""
        self.availableOptions.update({
            'tags':  set(['poem']),
            'preferred': None,
            'summary': None,
        })

        super(PoemBot, self).__init__(**kwargs)
        self.generator = generator

        pref = self.getOption('preferred')
        if pref:
            self.getOption('tags').add(pref)

    @staticmethod
    def detect_numbering(nums, lines_count):
        """
        Try to detect the line numbering scheme from the given markers.

        @param nums: markers
        @type nums: int[]
        @param lines_count: total number of lines in the poem block
        @type lines_count: int
        """
        if len(set(nums)) != len(nums):
            return
        step = None
        for i, num in enumerate(nums[1:]):
            current_step = num - nums[i]
            if step:
                if current_step != step:
                    return
            else:
                step = current_step
        if step:
            data = {'number-step': step}
            if nums[0] != 1:
                data['number-start'] = nums[0]
            if lines_count - nums[-1] > step:
                data['number-end'] = nums[-1]
            return data

    def process_lines(self, lines):
        """
        Remove old templates from lines and obtain line numbers.

        @param lines: the lines to clean up
        @type lines: unicode
        @return: cleaned-up lines and line numbers
        @rtype: tuple containing a unicode and a list of ints
        """
        ln = 0
        numbering = []
        lines = lines.split('\n')
        tmps = i18n.translate(self.current_page.site, self.line_tmps, fallback=False)
        for i, line in enumerate(lines):
            if line.strip() != '':
                ln += 1
                code = mwparserfromhell.parse(line)
                for tmp in code.ifilter_templates():
                    if tmp.name.strip() not in tmps:
                        pywikibot.warning(u'unexpected template: "{}"'.format(tmp.name))
                        continue
                    if ln in numbering:
                        raise PoemError(u'exceeding template: "{}"', tmp.name)
                    params = [param for param in tmp.params if tmp.has(param.name, True)]
                    if len(params) == 0:
                        raise PoemError(u'no parameters found in "{}"', tmp.name)
                    if len(params) > 1:
                        raise PoemError(u'multiple parameters found in "{}"', tmp.name)
                    if params[0].name.strip() != '1':
                        raise PoemError(u'unexpected parameter: "{}" in "{}"', params[0].name, tmp.name)
                    if params[0].value.strip() != unicode(ln):
                        raise PoemError(u'unexpected line marker: "{}" in "{}"', params[0].value, tmp.name)
                    if line.rstrip()[-len(unicode(tmp)):] != unicode(tmp):
                        raise PoemError(u'the "{}" template is not at the end of the line', tmp.name)
                    line = line.rstrip()[:-len(unicode(tmp))]
                    line = line.rstrip()  # possibly breaking change
                    lines[i] = line
                    numbering.append(ln)
        return '\n'.join(lines), numbering, len(lines)

    def treat(self, page):
        """
        Load the given page, make the required changes, and save it.

        @param page: the page to treat
        @type page: pywikibot.Page
        """
        self.current_page = page
        page.get()
        wikicode = mwparserfromhell.parse(page.text)
        for el in wikicode.ifilter_tags():
            if el.tag in self.getOption('tags'):
                try:
                    result = self.process_lines(el.contents)
                except PoemError as e:
                    pywikibot.warning(e)
                    continue
                if result:
                    lines, numbering, lines_count = result
                    if lines != el.contents:
                        scheme = self.detect_numbering(numbering, lines_count)
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
        if arg.startswith('-preferred:'):
            options['preferred'] = arg[11:]
        elif arg.startswith('-summary:'):
            options['summary'] = arg[9:]
        elif arg == '-always':
            options['always'] = True

    gen = genFactory.getCombinedGenerator()
    if gen:
        bot = PoemBot(gen, **options)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == '__main__':
    main()

# -*- coding: utf-8  -*-

import pywikibot
from pywikibot.data.api import Request

pages = {
    'wikipedia': {
        'it': [
            {
                'title': 'Wikipedia:Vandalismi in corso',
                'level': 3
            }
        ]
    }
}


def main():
    for family in pages:
        for lang in pages[family]:
            for page in pages[family][lang]:
                kwargs = page
                kwargs['page'] = pywikibot.Page(pywikibot.Site(lang, family),
                                                kwargs['title'])
                del kwargs['title']
                insert(**kwargs)


def insert(page, level=2, space=True, zero_padded=False,
           minorEdit=True, autolink=True):
    header = Request(site=page.site, action='expandtemplates',
                     text='{{#timel:%s xg}}' % ('d' if zero_padded else 'j')
                     ).submit()['expandtemplates']['*']
    text = page.get(force=True)
    if pywikibot.textlib.does_text_contain_section(text, header):
        pywikibot.output(u'\03{{lightyellow}}{} already contains'
                         u'the header for "{}"'.format(page, header))
        return
    if isinstance(level, int):
        level = '='*level
    if isinstance(space, bool):
        space = (' ' if space is True else '')
    fmt = u'\n\n{level}{space}{header}{space}{level}'
    page.text += fmt.format(header=header, level=level, space=space)
    pywikibot.showDiff(text, page.text)
    summary = u'[['+page.site.namespace(4)+':Bot|Bot]]: ' \
              u'inserimento della sezione giornaliera'
    if autolink:
        summary = u'/* {} */ {}'.format(header, summary)
    page.save(comment=summary, minor=minorEdit, botflag=True)

if __name__ == "__main__":
    pywikibot.handleArgs()
    main()

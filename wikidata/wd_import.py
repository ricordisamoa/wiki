# -*- coding: utf-8  -*-

import re
import pywikibot
from pywikibot import i18n, pagegenerators, WikidataBot
import mwparserfromhell
from wd_mappings import mappings
from wikidata_summary import summary as wikidata_summary


class DataImportBot(WikidataBot):
    def __init__(self, generator, **kwargs):
        self.availableOptions.update({
            'import_data': True,
            'remove': False,
            'remove_all_only': False,
        })

        super(DataImportBot, self).__init__(**kwargs)
        self.generator = generator
        self.cacheSources()

    @staticmethod
    def format_param(param, rawvalue):
        value = rawvalue
        for filtr in param.get('filters', []):
            if callable(filtr):
                value = filtr(value)
            else:
                match = re.search(filtr, value)
                if match:
                    value = match.group(0)
                else:
                    pywikibot.warning(u'value {value!r} skipped by filter'.format(
                        value=value))
                    continue
        if 'map' in param:
            new = param['map'].get(value)
            if new is None:
                pywikibot.warning(u'value {value!r} skipped by mapping'.format(
                    value=value))
            value = new
        return value

    def treat(self, page, item):
        self.current_page = page
        text = page.get(force=True)
        code = mwparserfromhell.parse(text)
        imported = []
        self.removed = []
        for template in code.ifilter_templates():
            tname = template.name.strip()
            for harv in mappings:
                if any(page.site.sametitle(tname, name) for name in harv['names']):
                    if 'sites' in harv and page.site.dbName() not in harv['sites']:
                        pywikibot.warning(u'{} template was found but skipped because site is not whitelisted'.format(tname))
                        continue
                    for param in harv['params']:
                        self.can_remove = False
                        if 'remove' in param and \
                           (param['remove'] is True or page.site.dbName() in param['remove']):
                            self.can_remove = True
                        for pname in param['names']:
                            if template.has(pname, ignore_empty=True):
                                rawvalue = unicode(template.get(pname).value)
                                pywikibot.output(u'{pname} parameter found in {tname}: {rawvalue!r}'.format(
                                    pname=pname, tname=tname, rawvalue=rawvalue))
                                value = self.format_param(param, rawvalue)
                                if value is None:
                                    continue
                                if value != rawvalue:
                                    pywikibot.output(u'{pname} parameter formatted from {rawvalue!r} to {value!r}'.format(
                                        pname=pname, rawvalue=rawvalue, value=value))
                                if self.getOption('import_data'):
                                    for prop in (param['claims'] if isinstance(param['claims'], list) else [param['claims']]):
                                        if isinstance(self.getOption('import_data'), list) and prop not in self.getOption('import_data'):
                                            pywikibot.warning(u'{} claim was to be added but was skipped because it is not whitelisted'.format(prop))
                                        else:
                                            claim = pywikibot.Claim(item.site, prop)
                                            claim.setTarget(value)
                                            source = self.getSource(page.site)
                                            if prop not in item.claims:
                                                item.addClaim(claim, summary=u'import [[Property:{prop}]] from {site}'.format(prop=prop, site=page.site.dbName()))
                                                pywikibot.output(u'\03{{lightgreen}}{qid}: claim successfully added'.format(qid=item.getID()))
                                                if source:
                                                    claim.addSource(source, bot=True, summary=u'import [[Property:{prop}]] from {site}'.format(prop=prop, site=page.site.dbName()))
                                                    pywikibot.output(u'\03{{lightgreen}}{qid}: source "{source}" successfully added'.format(qid=item.getID(), source=source.getTarget().getID()))
                                                item.get(force=True)
                                                imported.append(prop)
                                            elif source and prop in item.claims and len(item.claims[prop]) == 1 and item.claims[prop][0].getTarget() == claim.getTarget():
                                                try:
                                                    item.claims[prop][0].addSource(source, bot=True, summary=u'import a source for [[Property:{prop}]] from {site}'.format(prop=prop, site=page.site.dbName()))
                                                    item.get(force=True)
                                                    imported.append(prop)
                                                except:
                                                    pass
                                if self.can_remove and self.getOption('remove'):
                                    prop = param['claims']
                                    if prop in item.claims and len(item.claims[prop]) == 1:
                                        self.remove_if(template, param, pname, item.claims[prop][0].getTarget())
                                    elif self.getOption('remove_all_only'):
                                        self.can_remove = False
                                break
                            elif self.can_remove and template.has(pname, ignore_empty=False):
                                self.remove_if(template, param, pname)
                    break
        if self.getOption('remove') and len(self.removed) > 0:
            comment = i18n.translate(page.site, wikidata_summary[1],
                                     {'counter': len(self.removed),
                                      'params': page.site.list_to_text(self.removed),
                                      'id': item.getID()
                                      })
            self.userPut(page, text, page.text, comment=comment, minor=True,
                         botflag=True, ignore_save_related_errors=True)

    def remove_if(self, template, param, pname, expected_val=None):
        displayed = param.get('displayed', pname)
        conflict = True
        if template.has(pname, ignore_empty=False):
            value = unicode(template.get(pname).value)
            if expected_val is not None:
                value = self.format_param(param, value)
            if value.strip() == '' or value == expected_val:
                template_text = unicode(template)
                template.remove(pname, keep_field=False)
                pywikibot.output(u'\03{{lightgreen}}field {pname} {typ}: removed'.format(
                    pname=pname, typ=('as expected' if value == expected_val else 'empty')))
                conflict = False
                self.removed.append(displayed)
                self.current_page.text = self.current_page.text.replace(template_text, unicode(template))
            else:
                pywikibot.warning(u'field {pname} does not match: cannot be removed'.format(pname=pname))
        else:
            pywikibot.warning(u'field {pname} not found in template'.format(pname=pname))
        if conflict and self.getOption('remove_all_only'):
            self.can_remove = False


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
        if arg == '-noimport':
            options['import_data'] = False
        elif arg.startswith('-import:'):
            options['import_data'] = list(set(arg[8:].split(',')))
        elif arg == '-remove':
            options['remove'] = True
        elif arg == '-remove-all-only':
            options['remove'] = True
            options['remove_all_only'] = True
        elif arg == '-always':
            options['always'] = True
        else:
            genFactory.handleArg(arg)

    generator = genFactory.getCombinedGenerator()
    if generator:
        bot = DataImportBot(generator, **options)
        bot.run()
    else:
        pywikibot.showHelp()


if __name__ == '__main__':
    main()

# -*- coding: utf-8  -*-

import pywikibot
import mwparserfromhell


def main(commands=None):
    yellow = u'\03{lightyellow}%s'
    site = pywikibot.Site().data_repository()
    if not site.logged_in():
        site.login()
    if commands is None:
        commands = pywikibot.User(site, site.user()).getUserPage(subpage='Delinker/commands')
    text = commands.get(force=True)
    code = mwparserfromhell.parse(text)
    for template in code.ifilter_templates():
        if unicode(template.name).replace(commands.title(), '').lower().strip() == '/row':
            if template.has_param('status'):
                pywikibot.output(yellow % '"status" field already set')
                continue
            if template.has_param('items'):
                pywikibot.output(yellow % '"items" field already set')
                continue
            if not template.has_param('from'):
                pywikibot.output(yellow % '"from" field not set')
                continue
            if not template.has_param('to'):
                pywikibot.output(yellow % '"to" field not set')
                continue
            if not template.has_param('reason'):
                pywikibot.output(yellow % 'no reason stated')
                continue
            if not template.has_param('by'):
                pywikibot.output(yellow % 'no assignee specified')
                continue
            if template.has_param('prop'):
                prop_only = unicode(template.get('prop').value).upper().replace('P', '').split('-')
                pywikibot.output(u'\03{{lightpurple}}restricting claim replacing to the following properties: {props}'.format(props=', '.join(prop_only)))
            else:
                prop_only = None
            itemfrom = pywikibot.ItemPage(site, 'Q'+unicode(template.get('from').value))
            itemto = pywikibot.ItemPage(site, 'Q'+unicode(template.get('to').value))
            summary = u'[[User:SamoaBot/Delinker|SamoaBot Delinker]]: migrating [[{itemfrom}]] to [[{itemto}]] as ordered by [[User:{by}|{by}]] {reason}'
            summary = summary.format(itemfrom=itemfrom.getID().upper(),
                                     itemto=itemto.getID().upper(),
                                     by=unicode(template.get('by').value),
                                     reason=unicode(template.get('reason').value))
            count = 0
            refs = list(itemfrom.getReferences(namespaces=[0]))
            if len(refs) == 0:
                pywikibot.output(yellow % (u'{} has no references'.format(itemfrom)))
                template.add('status', 'nothingtodo')
            else:
                count = 0
                for page in refs:
                    item = pywikibot.ItemPage(site, page.title())
                    item.get(force=True)
                    for prop in item.claims:
                        if prop_only and (not prop.replace('P', '') in prop_only):
                            continue
                        for claim in item.claims[prop]:
                            if claim.getTarget() == itemfrom:
                                claim.changeTarget(itemto, summary=summary)
                                item.get(force=True)
                                pywikibot.output(u'\03{{lightgreen}}{item}: changed claim target'.format(item=item))
                                count += 1
                if prop_only or (count and count == len(refs) and len(list(itemfrom.getReferences(namespaces=[0]))) == 0):
                    pywikibot.output(u'\03{{lightgreen}}delinking successful for {}'.format(itemfrom))
                    template.add('status', 'done')
                    template.add('items', str(count))
                else:
                    pywikibot.output('\03{{lightred}}delinking unsuccessful for {}'.format(itemfrom))
                    template.add('status', 'error')
    newtext = unicode(code)
    if newtext != text:
        commands.text = newtext
        pywikibot.showDiff(text, commands.text)
        commands.save(comment='[[Wikidata:Bots|Bot]]: updating delinker status', botflag=True)

if __name__ == "__main__":
    pywikibot.handleArgs()
    main()

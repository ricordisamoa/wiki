# -*- coding: utf-8  -*-

import re
import string
import pywikibot
import mwparserfromhell
from references import references

pywikibot.handleArgs()
site = pywikibot.Site()
repo = site.data_repository()


def format_lccn(prev):
    prev = re.sub(r'^http:\/\/lccn\.loc\.gov\/(.+)$', '\g<1>', prev)
    prev = prev.strip().replace(u'\u200f', '').replace(' ', '').replace('-', '').replace('.', '')
    try:
        prev = re.sub(r'(\w\/\d+)', '\g<1>' + ('0' * (6 - len(re.search(r'\w\/\d+\/(\d+)', prev).group(1)))), prev, count=1)
    except:
        pass
    prev = re.sub(r'\/', '', prev)
    try:
        prev = re.sub(r'(?<=\d{2})', '0' * (8 - len(re.search(r'\d+', prev).group(0))), prev, count=1)
    except:
        pass
    if re.match(ur'^\w+\d+$', prev):
        return prev
    return False

harvesting = [
    {
        'name': ['authority control', 'normdaten', u'controllo di autorità', u'autorité'],
        'params': [
            {
                'name': 'VIAF',
                'claims': 'P214',
                'remove': ['itwiki'],
                'filter': [string.strip, '^\d+$']
            }, {
                'name': 'GND',
                'claims': 'P227',
                'filter': [string.strip, '^(1|10)\d{7}[0-9X]|[47]\d{6}-\d|[1-9]\d{0,7}-[0-9X]|3\d{7}[0-9X]$'],
                'remove': ['itwiki']
            }, {
                'name': 'LCCN',
                'claims': 'P244',
                'filter': format_lccn,
                'remove': ['itwiki']
            }
        ]
    },
    {
        'name': ['bio'],
        'sites': ['itwiki'],
        'params': [
            {
                'name': ['Sesso', 'sesso'],
                'claims': 'P21',
                'filter': [string.strip, string.upper],
                'map': {
                    'M': pywikibot.ItemPage(repo, 'Q6581097'),
                    'F': pywikibot.ItemPage(repo, 'Q6581072')
                }
            }
        ]
    },
    {
        'name': ['botanici', 'botanist'],
        'sites': ['itwiki', 'enwiki'],
        'params': [
            {
                'name': '1',
                'displayed': 'Botanici',
                'claims': 'P428',
                'filter': ur'^[\w\.\s]+$',
                'remove': ['itwiki']
            }
        ]
    },
    {
        'name': ['Divisione amministrativa'],
        'sites': ['itwiki'],
        'params': [
            {
                'name': 'Codice statistico',
                'claims': 'P635',
                'filter': ur'^\d{6}$'
            }, {
                'name': 'Codice catastale',
                'claims': 'P806',
                'filter': ur'^\w\d{3}$'
            }
        ]
    },
    {
        'name': ['Wdpa'],
        'sites': ['frwiki'],
        'params': [
            {
                'name': '1',
                'displayed': 'WDPA',
                'claims': 'P809',
                'filter': [string.strip, ur'^\d+$']
            }
        ]
    },
    {
        'name': [u'Infobox Aire protégée'],
        'sites': ['frwiki'],
        'params': [
            {
                'name': 'wdpa',
                'displayed': 'WDPA',
                'claims': 'P809',
                'filter': [string.strip, ur'^\d+$']
            }
        ]
    },
    {
        'name': [u'WTA'],
        'sites': ['itwiki'],
        'params': [
            {
                'name': ['id', '1'],
                'displayed': 'WTA',
                'claims': 'P597',
                'filter': [string.strip, ur'^\d+$'],
                'remove': ['itwiki']
            }
        ]
    },
    {
        'name': [u'Scrum'],
        'sites': ['itwiki'],
        'params': [
            {
                'name': ['1'],
                'displayed': 'Scrum',
                'claims': 'P858',
                'filter': [string.strip, ur'^\d+$'],
                'remove': ['itwiki']
            }
        ]
    },
    {
        'name': [u'Infobox Métier'],
        'sites': ['frwiki'],
        'params': [
            {
                'name': ['code ROME'],
                'displayed': 'ROME',
                'claims': 'P867',
                'filter': [string.strip, ur'^\w\d{4}$']
            }
        ]
    },
    {
        'name': [u'Base Sycomore'],
        'sites': ['frwiki'],
        'params': [
            {
                'name': ['1'],
                'displayed': 'Sycomore',
                'claims': 'P1045',
                'filter': [string.strip, ur'^\d{1,5}$']
            }
        ]
    }
]

field_removal_summary = {
    'it': u'[[Wikipedia:Bot|Bot]]: rimozione camp{{PLURAL:%(fields_num)d|o|i}} %(fields)s migrat{{PLURAL:%(fields_num)d|o|i}} a [[d:|Wikidata]]: [[d:%(qid)s]]'
}


def listToText(site, args):
    args = [unicode(e) for e in args]
    return site.mediawiki_message('comma-separator').join(args[:-2] + [(site.mediawiki_message('word-separator') + site.mediawiki_message('and') + site.mediawiki_message('word-separator')).join(args[-2:])])


def remove_if(removed, template, field, value, text, displayed=None):
    if not displayed:
        displayed = field
    template_text = unicode(template)
    if not template.has_param(field, False) and template.has_param(field.upper(), False):
        field = field.upper()
    conflict = True
    if template.has_param(field, False):
        try:
            if unicode(template.get(field).value).strip() == value or (field == 'LCCN' and format_lccn(unicode(template.get(field).value).strip()) == value):
                template.remove(field, force_no_field=True)
                pywikibot.output(u'\03{{lightgreen}}field {} matches: removed'.format(field))
                conflict = False
                removed.append(displayed)
            elif unicode(template.get(field).value).strip() == '':
                template.remove(field, force_no_field=True)
                pywikibot.output(u'\03{{lightgreen}}field {} empty: removed'.format(field))
                conflict = False
                removed.append(displayed)
            else:
                pywikibot.output(u'\03{{lightyellow}}field {} does not match: cannot be removed'.format(field))
        except:
            pass
    else:
        pywikibot.output(u'\03{{lightyellow}}field {} not found in template'.format(field))
    return text.replace(template_text, unicode(template)), removed, conflict


def from_page(page, import_data=True, remove=False, remove_all_only=True, autosave=False):
    pywikibot.output(u'parsing {page}'.format(page=page))
    item = pywikibot.ItemPage.fromPage(page)
    if not item.exists():
        pywikibot.output(u'\03{{lightyellow}}item not found for {}'.format(page))
        return False
    text = page.get(force=True)
    code = mwparserfromhell.parse(text)
    imported = []
    removed = []
    for template in code.ifilter_templates():
        tname = template.name.strip()
        for harv in harvesting:
            if tname == harv['name'] or tname in harv['name'] or tname.lower() == harv['name'] or tname.lower() in harv['name']:
                if 'sites' in harv and (not page.site.dbName() in harv['sites']):
                    pywikibot.output(u'\03{{lightyellow}}{} template was found but skipped because site is not whitelisted'.format(template.name))
                    continue
                for param in harv['params']:
                    can_remove = False
                    if 'remove' in param and (param['remove'] is True or param['remove'] == page.site.dbName() or page.site.dbName() in param['remove']):
                        can_remove = True
                    for pname in ([param['name']] if isinstance(param['name'], basestring) else param['name']):
                        if template.has_param(pname):
                            rawvalue = unicode(template.get(pname).value)
                            value = rawvalue
                            pywikibot.output(u'\03{{lightgreen}}{} parameter found in {}: {}'.format(pname, tname, value))
                            if 'filter' in param:
                                for filtr in (param['filter'] if isinstance(param['filter'], list) else [param['filter']]):
                                    if callable(filtr):
                                        value = filtr(value)
                                    else:
                                        match = re.search(filtr, value)
                                        if match:
                                            value = match.group(0)
                                        else:
                                            pywikibot.output(u'\03{{lightyellow}}{} value was skipped because it is excluded by filter'.format(value))
                                            continue
                            if 'map' in param:
                                if value in param['map']:
                                    value = param['map'][value]
                                else:
                                    pywikibot.output(u'\03{{lightyellow}}{} value was skipped because it is not mapped'.format(value))
                                    continue
                            if value != rawvalue:
                                pywikibot.output(u'{pname} parameter formatted from {frm} to {to}'.format(pname=pname, frm=rawvalue, to=value))
                            if import_data:
                                for prop in (param['claims'] if isinstance(param['claims'], list) else [param['claims']]):
                                    if isinstance(import_data, list) and prop not in import_data:
                                        pywikibot.output(u'\03{{lightyellow}}{} claim was to be added but was skipped because it is not whitelisted'.format(prop))
                                    else:
                                        claim = pywikibot.Claim(repo, prop)
                                        claim.setTarget(value)
                                        reference = pywikibot.Claim(repo, 'P143')
                                        reference.setTarget(reference_sites[pag-e.site.dbName()])
                                        reference.getTarget().get()
                                        if prop not in item.claims:
                                            item.addClaim(claim, summary=u'import [[Property:{prop}]] from {site}'.format(prop=prop, site=page.site.dbName()))
                                            pywikibot.output(u'\03{{lightgreen}}{qid}: claim successfully added'.format(qid=item.getID()))
                                            claim.addSource(reference, bot=1, summary=u'import [[Property:{prop}]] from {site}'.format(prop=prop, site=page.site.dbName()))
                                            pywikibot.output(u'\03{{lightgreen}}{qid}: source "{source}" successfully added'.format(qid=item.getID(), source=reference.getTarget().labels['en']))
                                            item.get(force=True)
                                            imported.append(prop)
                                        elif prop in item.claims and len(item.claims[prop]) == 1 and item.claims[prop][0].getTarget() == claim.getTarget():
                                            try:
                                                item.claims[prop][0].addSource(reference, bot=1, summary=u'import a source for [[Property:{prop}]] from {site}'.format(prop=prop, site=page.site.dbName()))
                                                pywikibot.output(u'\03{{lightgreen}}{qid}: source "{source}" successfully added'.format(qid=item.getID(), source=reference.getTarget().labels['en']))
                                                item.get(force=True)
                                                imported.append(prop)
                                            except:
                                                pass
                            if can_remove and remove and (isinstance(param['claims'], basestring) or len(param['claims']) == 1):
                                prop = (param['claims'] if isinstance(param['claims'], basestring) else param['claims'][0])
                                if prop in item.claims and len(item.claims[prop]) == 1:
                                    page.text, removed, conflict = remove_if(removed, template, pname, item.claims[prop][0].getTarget(), page.text, displayed=(param['displayed'] if 'displayed' in param else pname))
                                    if conflict and remove_all_only:
                                        remove = False
                                elif remove_all_only:
                                    remove = False
                            break
                        elif can_remove and template.has_param(pname, False):
                            page.text, removed, conflict = remove_if(removed, template, pname, '', page.text, displayed=(param['displayed'] if 'displayed' in param else pname))
                            if conflict and remove_all_only:
                                remove = False
                break
    if remove and removed:
        pywikibot.showDiff(text, page.text)
        comment = pywikibot.i18n.translate(page.site, field_removal_summary, {'fields_num': len(removed), 'fields': listToText(page.site, removed), 'qid': item.getID()})
        if autosave or pywikibot.inputChoice(page.title() + ' @ ' + comment, ['Yes', 'No'], ['Y', 'N'], 'N').strip().lower() in ['yes', 'y']:
            try:
                page.save(comment=comment, minor=True, botflag=True)
            except Exception, e:
                print e
    return (imported, removed)

if __name__ == "__main__":
    total = None
    import_data = True
    remove = False
    autosave = False
    cat = None
    recurse = None
    template = None
    start = None
    titles = []
    for arg in pywikibot.handleArgs():
        if arg.startswith('-total:'):
            total = int(arg[7:])
        elif arg.startswith('-noimport'):
            import_data = False
        elif arg.startswith('-import:'):
            import_data = (list(set(import_data+[arg[8:]])) if isinstance(import_data, list) and len(import_data) > 0 else [arg[8:]])
        elif arg.startswith('-remove'):
            remove = True
        elif arg.startswith('-autosave'):
            autosave = True
        elif arg.startswith('-cat:'):
            cat = arg[5:]
        elif arg.startswith('-category:'):
            cat = arg[10:]
        elif arg.startswith('-recurse:'):
            recurse = int(arg[9:])
        elif arg.startswith('-template:'):
            template = arg[10:]
        elif arg.startswith('-start:'):
            start = arg[7:]
        elif arg.startswith('-page:'):
            titles.append(arg[6:])
    global site
    site = pywikibot.Site()
    global repo
    repo = site.data_repository()
    global reference_sites
    reference_sites = references(repo)
    pages = [pywikibot.Page(site, title) for title in titles]
    if template:
        pages += list(pywikibot.Page(site, template, ns=10).getReferences(namespaces=0, onlyTemplateInclusion=True, total=total))
    if cat:
        pages += list(pywikibot.Category(site, cat).articles(namespaces=0, startsort=start, total=total, recurse=recurse))
    for page in sorted([page for page in list(set(pages)) if page.title() >= start]):
        from_page(page, import_data=import_data, remove=remove, autosave=autosave)

# -*- coding: utf-8  -*-

import re
import json
import pywikibot
from wd_import import listToText

site = pywikibot.Site().data_repository()


def del_msg(item):
    try:
        pywikibot.output(u'{item} was deleted by {sysop}'.format(item=item, sysop=list(site.logevents(logtype='delete', page=item, total=1))[0].user()))
    except:
        pywikibot.output(u'{} does not exist'.format(item))


def dump(xdict):
    lines = []
    maxlen = max([len(key) for key in xdict.keys()])
    for key in xdict:
        if len(xdict[key]) == 0:
            continue
        mlen = max([len(f) for f in xdict[key].keys()])
        for k in xdict[key]:
            lines.append(key+' '*(maxlen+1-len(key))+k+' '*(mlen+1-len(k))+' : '+unicode(xdict[key][k]))
    return '\n'.join(lines)


def empty(xdict):
    for key in xdict.keys():
        if isinstance(xdict[key], list):
            xdict[key] = [u'']*len(xdict[key])
        else:
            xdict[key] = u''
    return xdict


def compare(item1, item2, dictname=None):
    if dictname is None:
        dictname = 'dicts'
        dict1 = item1
        dict2 = item2
        item1 = 'item1'
        item2 = 'item2'
    else:
        dict1 = getattr(item1, dictname)
        dict2 = getattr(item2, dictname)
    for key in dict1:
        if key in dict2 and dict2[key] != dict1[key]:
            pywikibot.output(u'\03{{lightred}}{key} conflicting in {dictname}: {val1} in {item1} but {val2} in {item2}'.format(key=key, dictname=dictname, item1=item1, item2=item2, val1=dict1[key], val2=dict2[key]))
            return False
    return True


def clean_data(xdict):
    for site in xdict['sitelinks'].keys():
        xdict['sitelinks'][site] = {'site': site, 'title': xdict['sitelinks'][site]}
    for language in xdict['labels'].keys():
        xdict['labels'][language] = {'language': language, 'value': xdict['labels'][language]}
    for language in xdict['descriptions'].keys():
        xdict['descriptions'][language] = {'language': language, 'value': xdict['descriptions'][language]}
    for language in xdict['aliases'].keys():
        for index, item in enumerate(xdict['aliases'][language]):
            xdict['aliases'][language][index] = {'language': language, 'value': item}
    for key in xdict.keys():
        if len(xdict[key]) == 0:
            del xdict[key]
    return xdict


def fromDBName(dbname):
    s = pywikibot.site.APISite.fromDBName(dbname)
    return pywikibot.Site(s.code, s.family.name)


def user_link(user):
    page = pywikibot.Page(user.site, 'Contributions/'+user.name(), ns=-1)
    if (not user.isAnonymous()) and user.getUserPage().exists():
        page = user.getUserPage()
    return u'[[{}|{}]]'.format(page.title(), user.name())


def check_deletable(item, safe=True, askip=False):
    if not item.exists():
        del_msg(item)
        return
    item.get(force=True)
    if len(item.sitelinks) > 0:
        pywikibot.output(u'\03{{lightyellow}}{item} has {num} sitelinks, skipping'.format(item=item, num=len(item.sitelinks)))
        return
    if len(item.claims) > 0:
        pywikibot.output(u'\03{{lightyellow}}{item} has {num} claims, skipping'.format(item=item, num=len(item.claims)))
        return
    refs = len(list(item.getReferences(namespaces=0)))
    if refs > 0:
        pywikibot.output(u'\03{{lightyellow}}{item} has {num} references in the main namespace, skipping'.format(item=item, num=refs))
        return
    history = list(item.fullVersionHistory())
    if len(history) > 2:
        for entry in list(history[1:len(history)-1]):
            if 'bot' in pywikibot.User(item.site, entry[2]).groups():
                pywikibot.output(u'{item}: removed {bot} from history'.format(item=item, bot=entry[2]))
                del history[history.index(entry)]
    if len(history) == 1:
        pywikibot.output(u'{item} has been created empty by {user}'.format(item=item, user=history[0][2]))
    elif len(history) == 2:
        prev = json.loads(history[1][3])
        cur = json.loads(history[0][3])
        if 'links' in prev and len(prev['links']) == 1 and (len(cur['links']) == 0 or 'links' not in cur):
            removed_link = pywikibot.Link(prev['links'][prev['links'].keys()[0]]['name'], fromDBName(prev['links'].keys()[0]))
            removed_page = pywikibot.Page(removed_link)
            moved_into = pywikibot.ItemPage.fromPage(removed_page)
            if moved_into.exists():
                user = pywikibot.User(item.site, history[0][2])
                try:
                    msg = u'{user} moved {link} into [[{qid}]]'.format(link=removed_link.astext(onsite=item.site), qid=moved_into.getID(), user=user_link(user))
                except Exception, e:
                    print e
                    return False
                if safe is False or 'autoconfirmed' in user.groups() or (askip and pywikibot.inputChoice(u'delete item: %s?' % msg, ['Yes', 'No'], ['Y', 'N'], 'N').strip().lower() in ['yes', 'y']):
                    # safety check: only delete the item if the last editor is autoconfirmed
                    delete_item(item, moved_into, msg=msg, askmerge=askip)
                else:
                    pywikibot.output(u'\03{{lightyellow}}Skipped: {msg}'.format(msg=msg))
            else:
                pywikibot.output(u'\03{{lightyellow}}{page} does NOT have an associated item, skipping'.format(page=removed_page))
    elif len(history) > 2:
        pywikibot.output(u'\03{{lightyellow}}{item}\'s history has {num} entries, skipping'.format(item=item, num=len(history)))


def duplicates(tupl, force_lower=True):
    if force_lower:
        tupl = sort_items(tupl)
    sl = {}
    for item in tupl:
        if not item.exists():
            del_msg(item)
            return
        item.get(force=True)
        if len(item.claims) > 0:
            pywikibot.output(u'\03{{lightyellow}}{item} has {num} claims'.format(item=item, num=len(item.claims)))
            return
        if 'es' in item.descriptions and item.descriptions['es'] == u'categoría de Wikipedia':
            del item.descriptions['es']
        if 'fr' in item.descriptions and item.descriptions['fr'] == u'page de catégorie de Wikipédia':
            del item.descriptions['fr']
        if len(item.descriptions) > 0 and len(item.descriptions) > 1:
            pywikibot.output(u'\03{{lightyellow}}{item} has {num} descriptions'.format(item=item, num=len(item.descriptions)))
            return
        if len(item.aliases) > 0:
            pywikibot.output(u'\03{{lightyellow}}{item} has {num} aliases'.format(item=item, num=len(item.aliases)))
            return
        if compare(sl, item.sitelinks) is False:
            return
        sl.update(item.sitelinks)
    if len(sl) == 1:
        pywikibot.output(u'\03{{lightpurple}}{items} have the same "{sl}" sitelink, no claims, no descriptions, and no aliases: preparing deletion'.format(items=obj_join(tupl), sl=sl))
        kept = tupl[0]
        deletable = tupl[1:]
        shared = [(sl.keys()[0], sl[sl.keys()[0]])]
    else:
        deletable = list(tupl)
        shared = list(set.intersection(*[set([(key, i.sitelinks[key]) for key in i.sitelinks]) for i in tupl]))
        if len(shared) == 0:
            pywikibot.output(u'\03{{lightred}}{items} have no shared sitelinks'.format(items=obj_join(tupl)))
            return False
        kept = [item for item in tupl if item.sitelinks == sl]
        if len(kept) == 0:
            pywikibot.output(u'\03{{lightred}}Conflict detected for {items}'.format(items=obj_join(tupl), sl=sl))
            return False
        kept = kept[0]
        deletable.remove(kept)
        pywikibot.output(u'\03{{lightpurple}}{items} have {shared} shared sitelinks, no claims, no descriptions, and no aliases: preparing deletion'.format(items=obj_join(tupl), shared=len(shared)))
    shared = obj_join([pywikibot.Link.fromPage(pywikibot.Page(fromDBName(g[0]), g[1])).astext(onsite=item.site.data_repository()) for g in shared])
    for item in deletable:
        if False == delete_item(item, kept, msg=u'[[{proj}:True duplicates|True duplicate]] of [[{kept}]] by {shared}'.format(proj=item.site.namespace(4), kept=kept.getID(), shared=shared), allow_sitelinks=True):
            return False
    kept.purge(forcelinkupdate=True)
    return True


def sort_items(tupl):
    return sorted(tupl, key=lambda j: int(j.getID().replace('Q', '')))


def obj_join(args):
    return listToText(site, args)


def merge_items(tupl, force_lower=True, taxon_mode=True, api=False):
    item1, item2 = tupl
    if force_lower:
        item1, item2 = sort_items((item1, item2))
    if not item1.exists():
        del_msg(item1)
        return
    if not item2.exists():
        del_msg(item2)
        return
    pywikibot.output(u'merging {item1} with {item2}'.format(item1=item1, item2=item2))
    item1.get(force=True)
    item2.get(force=True)
    if compare(item1, item2, 'sitelinks') is False or compare(item1, item2, 'labels') is False or compare(item1, item2, 'descriptions') is False:
        return False
    if taxon_mode:
        dup_sl = item1.sitelinks
        dup_sl.update(item2.sitelinks)
        dup_pg = []
        for dbname in dup_sl:
            pg = pywikibot.Page(fromDBName(dbname), dup_sl[dbname])
            dup_pg.append((pg.title(withNamespace=False), pg.namespace()))
        if len(list(set(dup_pg))) != 1:
            pywikibot.output(u'\03{lightyellow}'+str(dup_pg))
            return
    else:
        pywikibot.output(u'\03{lightyellow}Warning: taxon mode disabled')
    if api:
        item2.mergeInto(item1)
    else:
        new_data = {
            'sitelinks': item1.sitelinks,
            'labels': item1.labels,
            'aliases': item1.aliases,
            'descriptions': item1.descriptions
        }
        old_dump = dump(new_data)
        new_data['sitelinks'].update(item2.sitelinks)
        new_data['labels'].update(item2.labels)
        new_data['descriptions'].update(item2.descriptions)
        for language in item2.aliases:
            if language in new_data['aliases']:
                new_data['aliases'][language] = list(set(new_data['aliases'][language]+item2.aliases[language]))
            else:
                new_data['aliases'][language] = item2.aliases[language]
        pywikibot.output(u'\03{lightblue}diff for new_data:\03{lightblue}')
        pywikibot.showDiff(old_dump, dump(new_data))
        new_data = clean_data(new_data)
        empty_data = {
            'sitelinks': item2.sitelinks,
            'labels': item2.labels,
            'aliases': item2.aliases,
            'descriptions': item2.descriptions
        }
        old_dump = dump(empty_data)
        for key in empty_data.keys():
            empty_data[key] = empty(empty_data[key])
        pywikibot.output(u'\03{lightblue}diff for empty_data:')
        pywikibot.showDiff(old_dump, dump(empty_data))
        empty_data = clean_data(empty_data)
        item2.editEntity(empty_data, summary=u'moving to [[{item1}]]'.format(item1=item1.getID()))
        pywikibot.output(u'\03{{lightgreen}}{qid} successfully emptied'.format(qid=item2.getID()))
        item1.editEntity(new_data, summary='moved from [[{item2}]]'.format(item2=item2.getID()))
        pywikibot.output(u'\03{{lightgreen}}{qid} successfully filled'.format(qid=item1.getID()))
        item1.get(force=True)
        item2.get(force=True)
        for prop in item2.claims:
            for claim2 in item2.claims[prop]:
                if prop in item1.claims:
                    for claim1 in item1.claims[prop]:
                        if claim1.getTarget() == claim2.getTarget():
                            for source in claim2.sources:
                                try:
                                    claim1.addSource(source, bot=1)
                                    pywikibot.output(u'\03{{lightgreen}}imported a source for {propid} into {qid}'.format(propid=prop, qid=item1.getID()))
                                    item1.get(force=True)
                                except:
                                    pass
                else:
                    claim = pywikibot.Claim(claim2.site, prop)
                    claim.setTarget(claim2.getTarget())
                    item1.addClaim(claim)
                    pywikibot.output(u'\03{{lightgreen}}imported a claim for {propid} into {qid}'.format(propid=prop, qid=item1.getID()))
                    for source in claim2.sources:
                        try:
                            claim.addSource(source, bot=1)
                            pywikibot.output(u'\03{{lightgreen}}imported a source for {propid} into {qid}'.format(propid=prop, qid=item1.getID()))
                            item1.get(force=True)
                        except:
                            pass
    delete_item(item2, item1)


def error_merge_msg(item1, item2):
    pywikibot.output(u'\03{{lightred}}error while merging {item1} and {item2}'.format(item1=item1.getID(), item2=item2.getID()))


def delete_item(item, other, msg=None, by=site.user(), rfd=False, allow_sitelinks=False, askmerge=False):
    item.get(force=True)
    other.get(force=True)
    if allow_sitelinks is not True and len(item.sitelinks) > 0:
        error_merge_msg(item, other)
        return False
    if compare(item, other, 'sitelinks') is False or compare(item, other, 'labels') is False or compare(item, other, 'descriptions') is False:
        if askmerge and pywikibot.inputChoice(u'force merging?', ['Yes', 'No'], ['Y', 'N'], 'N').strip().lower() in ['yes', 'y']:
            merge_items((other, item), force_lower=False, taxon_mode=False)
        return False
    if by is None:
        by = item.site.data_repository().user()
    for key in item.aliases:
        for alias in item.aliases[key]:
            if alias.strip() != '' and ((key not in other.aliases) or (alias not in other.aliases[key])):
                error_merge_msg(item, other)
                return False
    for prop in item.claims:
        if (prop not in other.claims) or len(list(set([claim.getTarget() for claim in item.claims[prop]])-set([claim.getTarget() for claim in other.claims[prop]]))):
            error_merge_msg(item, other)
            return False
    if rfd:
        rfd_page = pywikibot.Page(site, 'Requests for deletions', ns=4)
        rfd_page.get(force=True)
        if msg is None:
            msg = u'Merged with {other}{by}'.format(other=other.getID(), by=(u' by [[User:{0}|{0}]]'.format(by) if by != site.user() else ''))
        rfd_page.text += u'\n\n{{{{subst:Request for deletion|itemid={qid}|reason={msg}}}}} --~~~~'.format(qid=item.getID(), msg=msg)
        page.save(comment=u'[[Wikidata:Bots|Bot]]: nominating [[{qid}]] for deletion'.format(qid=item.getID()), minor=False, botflag=True)
        pywikibot.output(u'\03{{lightgreen}}{item} successfully nominated for deletion'.format(item=item))
        return True
    else:
        item.delete(reason=(msg if msg else u'Merged with [[{qid}]] by [[User:{by}|{by}]]'.format(qid=other.getID(), by=by)))
        pywikibot.output(u'\03{{lightgreen}}{item} successfully deleted'.format(item=item))
        return True


def matchmerge(iterable, **kwargs):
    for match in iterable:
        merge_items((pywikibot.ItemPage(site, match.group('item1')), pywikibot.ItemPage(site, match.group('item2'))), **kwargs)

if __name__ == "__main__":
    cat = None
    lang2 = None
    recurse = None
    total = None
    bulk = None
    mode = None
    api = False
    unflood = False
    ids = []
    for arg in pywikibot.handleArgs():
        if arg.startswith('-cat:'):
            cat = arg[5:]
        elif arg.startswith('-lang2:'):
            lang2 = arg[7:]
        elif arg.startswith('-recurse:'):
            recurse = int(arg[9:])
        elif arg.startswith('-id:'):
            ids.append(arg[4:])
        elif arg.startswith('-total:'):
            total = int(arg[7:])
        elif arg.startswith('-bulk:'):
            bulk = arg[6:]
        elif arg.startswith('-bulk'):
            bulk = True
        elif arg.startswith('-mode:'):
            mode = arg[6:]
        elif arg.startswith('-api'):
            api = True
        elif arg.startswith('-unflood'):
            unflood = True
    site.login()
    if cat and lang2:
        site1 = pywikibot.Site()
        site2 = pywikibot.Site(lang2, site1.family.name)
        suid = (site1.dbName() == 'suwiki' and site2.dbName() == 'idwiki')
        for page1 in pywikibot.Category(site1, cat).articles(recurse=recurse, total=total):
            t = page1.title()
            if suid:
                t = t.replace(u'é', u'e')
            page2 = pywikibot.Page(site2, t)
            if page2.exists():
                item1 = pywikibot.ItemPage.fromPage(page1)
                item2 = pywikibot.ItemPage.fromPage(page2)
                if item1.exists() and item2.exists() and item1 != item2:
                    merge_items((item1, item2), taxon_mode=(False if suid else True), api=api)
    elif len(ids) == 2:
        merge_items((pywikibot.ItemPage(site, ids[0]), pywikibot.ItemPage(site, ids[1])), api=api)
    elif len(ids) == 1:
        check_deletable(pywikibot.ItemPage(site, ids[0]), askip=True)
    elif bulk:
        # text = pywikibot.Page(site, u'Requests for deletions/Bulk'+('' if bulk is True else '/'+bulk), ns=4).get(force=True)
        text = pywikibot.Page(site, u'Requests for deletions#Bulk deletion request', ns=4).get(force=True)
        regex = re.compile('\|\s*(?P<item>[Qq]\d+)')
        for match in regex.finditer(text):
            check_deletable(pywikibot.ItemPage(site, match.group('item')), askip=True)
    elif mode == 'truedups':  # True duplicates
        text = pywikibot.Page(site, 'Byrial/Duplicates', ns=2).get(force=True)
        regex = re.compile('\*\s*\[\[(?P<item1>[Qq]\d+)\]\] \(\d links\, 0 statements\)\, \[\[(?P<item2>[Qq]\d+)\]\] \(\d links\, 0 statements\)\, duplicate link')
        for match in regex.finditer(text):
            duplicates((pywikibot.ItemPage(site, match.group('item1')), pywikibot.ItemPage(site, match.group('item2'))))
    elif mode == 'catitems':  # should be all done
        text = pywikibot.Page(site, 'Byrial/Category+name merge/ceb-war-Animalia', ns=2).get(force=True)
        regex = re.compile('^\*\s*\d+\:([Aa]rticle|[Cc]ategory)\:[\w\s]+\:\s+\[\[\:?(?P<item1>[Qq]\d+)\]\] \[\[\:?(?P<item2>[Qq]\d+)\]\](\n|$)', flags=re.MULTILINE)
        matchmerge(regex.finditer(text), api=api)
    elif mode == 'shortpages':  # ShortPages are often deletable ones
        gen = pywikibot.pagegenerators.ShortPagesPageGenerator(site=site, number=total)
        for page in pywikibot.pagegenerators.NamespaceFilterPageGenerator(gen, namespaces=[0]):
            check_deletable(pywikibot.ItemPage(page.site, page.title()))
    elif mode == 'rfd':
        rfd = pywikibot.Page(site, 'Requests for deletions', ns=4).get(force=True)
        for match in list(re.finditer(ur'\n\=+\s*\[\[(?P<item>[Qq]\d+)\]\]\s*\=+\n', rfd))[::-1]:
            check_deletable(pywikibot.ItemPage(site, match.group('item')))
    elif mode == 'request':  # temporary
        text = pywikibot.Page(site, u'Bot requests#Merge multiple items', ns=4).get(force=True)
        regex = re.compile('^\s*\*\s*\[http\:\/\/nssdc\.gsfc\.nasa\.gov\/nmc\/spacecraftDisplay\.do\?id\=[\w\d\-\s]+\]\: \{\{[Qq]\|(?P<item1>\d+)\}\}\, \{\{[Qq]\|(?P<item2>\d+)\}\}', flags=re.MULTILINE)
        for match in regex.finditer(text):
            merge_items((pywikibot.ItemPage(site, 'Q'+match.group('item1')), pywikibot.ItemPage(site, 'Q'+match.group('item2'))), taxon_mode=False, api=api)
    else:  # 'standard' mode
        text = pywikibot.Page(site, 'Soulkeeper/dups', ns=2).get(force=True)
        regex = re.compile('^\*\s*\w+[\w\s]*\[\[\:?(?P<item1>[Qq]\d+)\]\] \[\[\:?(?P<item2>[Qq]\d+)\]\](\n|$)', flags=re.MULTILINE)
        matchmerge(regex.finditer(text), api=api)
    if unflood:
        site.login(sysop=True)
        rightstoken = pywikibot.data.api.Request(site=site, action='query', list='users', ususers=site.user(), ustoken='userrights').submit()
        rightstoken = rightstoken['query']['users'][0]
        if rightstoken['name'] == site.user():
            rightstoken = rightstoken['userrightstoken']
            pywikibot.data.api.Request(site=site, action='userrights', user=site.user(), token=rightstoken, remove='flood', reason=u'the current mass-deletion task has been completed').submit()
            pywikibot.output(u'\03{lightgreen}The flood flag has been removed successfully from the current user')

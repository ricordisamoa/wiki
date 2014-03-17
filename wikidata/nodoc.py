# -*- coding: utf-8  -*-

import re
import pywikibot
from merge import fromDBName


def do_item(item):
    if not item.exists():
        pywikibot.output(u'\03{{lightblue}}{} does not exist'.format(item))
        return True
    item.get(force=True)
    nd = {'sitelinks': {}, 'labels': {}}
    removed_from = []
    for dbname in item.sitelinks:
        s = fromDBName(dbname)
        t = item.sitelinks[dbname]
        b = pywikibot.Page(s, t)
        o = '('+re.escape(s.mediawiki_message('scribunto-doc-page-name').replace(s.namespace(828)+':', s.namespace(10)+':').replace('Module:', s.namespace(10)+':')).replace('\$1', '.+)')+'$'
        m = re.match(o, t)
        if m:
            f = pywikibot.Page(s, m.group(1))
            if f.exists():
                i = pywikibot.ItemPage.fromPage(f)
                if i.exists():
                    pywikibot.output(u'\03{{lightred}}Conflict detected: {item1} has {page1} and {item2} has {page2}'.format(item1=i, page1=f, item2=item, page2=b))
                    return False
                elif f.isRedirectPage():
                    target = f.getRedirectTarget()
                    i = pywikibot.ItemPage.fromPage(target)
                    if i.exists():
                        pywikibot.output(u'\03{{lightred}}Conflict detected: {item1} has {page1} (which redirects to {target}) and {item2} has {page2}'.format(item1=i, page1=f, target=target, item2=item, page2=b))
                        return False
                    pywikibot.output(u'\03{{lightyellow}}Warning: {page1} redirects to {target}, which does not have a linked item'.format(page1=f, target=target))
                else:
                    nd['sitelinks'][dbname] = {'site': dbname, 'title': f.title()}
                    if not 'sitelinks' in removed_from:
                        removed_from.append('sitelinks')
                    if (not s.lang in item.labels) or item.labels[s.lang] == t or item.labels[s.lang] == b.title():
                        nd['labels'][s.lang] = {'language': s.lang, 'value': f.title()}
                        if s.lang in item.labels and (not 'labels' in removed_from):
                            removed_from.append('labels')
        elif not s.lang in item.labels:
            nd['labels'][s.lang] = {'language': s.lang, 'value': b.title()}
    if len(nd['sitelinks']) == 0 and len(nd['labels']) == 0:
        pywikibot.output(u'\03{{lightblue}}{}: nothing to update'.format(item))
        return None
    summary = u'[['+site.namespace(4)+':Bots|Bot]]: [['+site.namespace(4)+':Requests for permissions/Bot/SamoaBot 37|removing /doc suffix from '+' and '.join(removed_from)+']]'
    if len(nd['sitelinks']) == 1 and len(nd['labels']) == 0:
        nd = nd['sitelinks'][nd['sitelinks'].keys()[0]]
        pywikibot.data.api.Request(action='wbsetsitelink', id=item.getID(), linksite=nd['site'], linktitle=nd['title'], summary=summary, bot=1, token=site.data_repository().token(item, 'edit'), site=item.site.data_repository()).submit()
    else:
        item.editEntity(nd, summary=summary)
    pywikibot.output(u'\03{{lightgreen}}{} updated!'.format(item))
    item.get(force=True)
    return do_item(item) is None

if __name__ == "__main__":
    ids = []
    lang = None
    for arg in pywikibot.handleArgs():
        if arg.startswith('-id:'):
            ids.append(arg[4:])
        elif arg.startswith('-language:'):
            lang = arg[10:]
    site = pywikibot.Site().data_repository()
    if len(ids) > 0:
        for qid in ids:
            do_item(pywikibot.ItemPage(site, qid))
    else:
        p = pywikibot.Page(site, 'Yamaha5/incorrect template interwiki'+('-'+lang if lang and lang != 'en' else ''), ns=2)
        text = p.get(force=True)
        for match in re.finditer(ur'^\#\[\[\:?(\w+)\:([^\[\]]+)\]\]\n', text, flags=re.MULTILINE):
            g = do_item(pywikibot.ItemPage.fromPage(pywikibot.Page(pywikibot.Site(match.group(1), 'wikipedia'), match.group(2))))
            if g is True:
                text = text.replace(match.group(), '')
                pywikibot.showDiff(p.text, text)
                p.text = text
        p.save(comment=u'[['+site.namespace(4)+':Bots|Bot]]: removing processed items', botflag=True)

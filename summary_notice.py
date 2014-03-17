# -*- coding: utf-8  -*-

import pywikibot
from pywikibot.data.api import Request
from pywikibot.i18n import translate

msg = {
    'notice': {
        'it': u'{{{{Oggetto|{titles[0]}}}}}'
    },
    'header': {
        'it': u'Avviso'
    },
    'comment': {
        'en': u'%s: report low frequency of edit summary',
        'it': u'%s: bassa frequenza di sommario delle modifiche'
    }
}


def bot_link(site):
    group = site.mediawiki_message('group-bot')
    group = pywikibot.Page(site, group, ns=4).title()
    member = translate(site,
                       site.mediawiki_message('group-bot-member'),
                       site.user())
    return u'[[{}|{}]]'.format(group, member)


def log(user, pages):
    talk = user.getUserTalkPage()
    titles = [page.title() for page in pages]
    notice = translate(talk.site, msg['notice']).format(titles=titles)
    text = talk.get(force=True)
    if notice in talk.text:
        pywikibot.output(u'\03{lightgreen}already logged')
        return
    header = translate()
    talk.text += u'\n\n== {} ==\n\n{} --~~~~'.format(header, notice)
    pywikibot.showDiff(text, talk.text)
    comment = translate(talk.site, msg['comment'], [bot_link(user.site)])
    talk.save(comment=comment, minor=False, botflag=True)


def summary_check(summary):
    if summary != '':
        pywikibot.output(u'\03{{lightyellow}}not-empty edit summary: "{}"'.format(summary))
        return True
    return False


def main(site, total=50, min_edits=5, namespaces=[0], groups=None, allow_blocked=False, **kwargs):
    site.login()
    users = []
    for change in site.recentchanges(namespaces=namespaces, changetype='edit', showBot=False, total=total, **kwargs):
        user = change['user']
        if user in users:
            pywikibot.output(u'\03{{lightyellow}}user has already been checked: {}'.format(user))
            continue
        users.append(user)
        if summary_check(change['comment']):
            continue
        user = pywikibot.User(site, user)
        if groups and len(list(set(groups)-set(user.groups()))) == len(list(set(groups))):
            pywikibot.output(u'\03{{lightyellow}}{} is not in {}'.format(user.name(), groups))
            continue
        if user.isBlocked() and not allow_blocked:
            pywikibot.output(u'\03{{lightyellow}}{} is blocked'.format(user.name()))
            continue
        pywikibot.output(u'fetching contributions for {}'.format(user.name()))
        contribs = site.usercontribs(user=user.username,
                                     namespaces=namespaces, total=min_edits)
        if True in [summary_check(contrib['comment']) for contrib in contribs]:
            continue
        pywikibot.output(u'\03{{lightblue}}{user} has {num} edits with no edit summary'.format(user=user.name(), num=min_edits))
        log(user, [pywikibot.Page(site, rev['title']) for rev in contribs])

if __name__ == "__main__":
    groups = None
    total = None
    for arg in pywikibot.handleArgs():
        if arg.startswith('-groups:'):
            groups = arg[8:].split(',')
        elif arg.startswith('-total:'):
            total = int(arg[7:])
    main(site=pywikibot.Site(), total=total, groups=groups)

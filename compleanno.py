# -*- coding: utf-8  -*-

import re
import datetime
import pywikibot
from pywikibot import Bot, NoPage, IsRedirectPage


class CompleannoBot(Bot):

    """Bot to wish users a happy birthday."""

    pages = {
        'wikipedia': {
            'it': 'Wikipedia:Wikipediani/Per giorno di nascita'
        },
        'wikinews': {
            'it': 'Wikinotizie:Wikinotiziani/Compleanno'
        }
    }

    message = u'\n\n== Auguri{post} ==\nBuon compleanno! <small class="{tag}">' \
              u'&nbsp;&nbsp;&ndash; Messaggio automatico ([[{source}|fonte]] | ' \
              u'[[{{{{subst:ns:3}}}}:{{{{subst:REVISIONUSER}}}}|è sbagliato?]]) di</small> ~~~~'

    def __init__(self, site, **kwargs):
        """Initialize and configure the bot object."""
        self.availableOptions.update({
            'basedate': datetime.date.today(),
            'page': None,
            'back': 0,
            'forward': 0,
        })
        super(CompleannoBot, self).__init__(**kwargs)
        self.site = site
        if not self.getOption('page'):
            self.options['page'] = self.pages[self.site.family.name][self.site.lang]
        self.comment = u'[[{ns}:Bot|Bot]]: auguri di compleanno{{post}}'.format(
            ns=self.site.namespace(4))
        user_namespaces = [u'[' + re.escape(ns[0].upper() + ns[0].lower()) + u']' +
                           re.escape(ns[1:])
                           for ns in self.site.namespaces[2]]
        self.regex = re.compile(u'\[\[\s*(' + u'|'.join(user_namespaces) +
                                u')\:(?P<nome>[^\|\{\}\[\]]+)(\]\]|\|[^\]]+\]\])')

    @staticmethod
    def format_user(user):
        return u'\03{{lightblue}}{name}\03{{default}}'.format(
            name=user.name())

    def run(self):
        """Wish a happy birthday to every user that was born within the selected range."""
        if not self.site.logged_in():
            self.site.login()
        for date in [self.getOption('basedate') + datetime.timedelta(days=num)
                     for num in range(-self.getOption('back'), self.getOption('forward') + 1)]:
            if date > datetime.date.today():
                post = ' in anticipo'
            elif date < datetime.date.today():
                post = ' in ritardo'
            else:
                post = ''
            mese = self.site.months_names[date.month - 1][0]
            tag = u'bot-compleanno-auguri-{anno}'.format(anno=date.year)
            compleanni = pywikibot.Page(self.site, '%s#%s%s' % (self.getOption('page'), mese[0].upper(), mese[1:]))
            giorno = u'{giorno} {mese}'.format(giorno=date.day, mese=mese)
            pywikibot.output(u'Sto cercando gli utenti di {sito} nati il giorno {giorno}'.format(
                sito=self.site, giorno=giorno))
            utenti = re.search(ur"\*\s*'*\[\[" + giorno + "\]\]'*\s*(\:|\-)\s*(?P<utenti>[^\n]+)\n", compleanni.get())
            if not utenti:
                pywikibot.warning('sezione giornaliera "{giorno}" non trovata'.format(giorno=giorno))
                continue
            utenti = list(set(pywikibot.User(self.site, link.group('nome'))
                              for link in self.regex.finditer(utenti.group('utenti'))))
            if len(utenti) == 0:
                pywikibot.output('non ci sono utenti con i criteri cercati')
                continue
            nomi = [self.format_user(utente) for utente in utenti]
            pywikibot.output(u'Invierò gli auguri a {nomi}'.format(nomi=self.site.list_to_text(nomi)))
            for utente in utenti:
                fmt = u'{utente}: %s'.format(utente=self.format_user(utente))
                if not utente.isRegistered():
                    pywikibot.warning(fmt % 'il nome utente non risulta registrato')
                    continue
                if utente.isBlocked(force=True):
                    pywikibot.warning(fmt % 'l\'utente risulta bloccato')
                    continue
                if not utente.getUserPage().exists():
                    pywikibot.warning(fmt % 'la pagina utente non esiste')
                    continue
                if utente.getUserPage().isRedirectPage():
                    pywikibot.warning(fmt % 'la pagina utente è un redirect')
                    continue
                discussione = utente.getUserTalkPage()
                try:
                    disc = discussione.get(force=True)
                except (NoPage, IsRedirectPage) as e:
                    pywikibot.warning(e)
                    continue
                if disc.find(tag) != -1:
                    pywikibot.output(fmt % u'\03{lightgreen}gli auguri sono già stati inviati')
                    continue
                discussione.text += self.message.format(post=post, tag=tag, source=compleanni.title())
                self.userPut(discussione, disc, discussione.text,
                             minor=False,  # trigger the 'new message' flag
                             comment=self.comment.format(post=post))
        pywikibot.output(u'\03{lightgreen}completato')


def main(*args):
    """
    Process command line arguments and invoke bot.

    If args is an empty list, sys.argv is used.

    @param args: command line arguments
    @type args: list of unicode
    """
    today = datetime.date.today()
    day = today.day
    month = today.month
    year = today.year
    options = {}
    for arg in pywikibot.handle_args(args):
        if arg.startswith('-day:'):
            day = int(arg[5:])
        elif arg.startswith('-month:'):
            month = int(arg[7:])
        elif arg.startswith('-page:'):
            options['page'] = arg[6:]
        elif arg.startswith('-back:'):
            options['back'] = int(arg[6:])
        elif arg.startswith('-forward:'):
            options['forward'] = int(arg[9:])
    options['basedate'] = datetime.date(year, month, day)
    bot = CompleannoBot(site=pywikibot.Site(), **options)
    bot.run()


if __name__ == '__main__':
    main()

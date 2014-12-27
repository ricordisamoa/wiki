# -*- coding: utf-8  -*-

import re


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
    return None


mappings = [
    {
        'names': ['authority control', 'normdaten', u'controllo di autorità', u'autorité'],
        'params': [
            {
                'names': ['VIAF'],
                'claims': 'P214',
                'filters': [unicode.strip, '^\d+$'],
                'remove': ['itwiki']
            }, {
                'names': ['GND'],
                'claims': 'P227',
                'filters': [unicode.strip, '^(1|10)\d{7}[0-9X]|[47]\d{6}-\d|[1-9]\d{0,7}-[0-9X]|3\d{7}[0-9X]$'],
                'remove': ['itwiki']
            }, {
                'names': ['LCCN'],
                'claims': 'P244',
                'filters': [format_lccn],
                'remove': ['itwiki']
            }
        ]
    },
    {
        'names': ['bio'],
        'sites': ['itwiki'],
        'params': [
            {
                'names': ['Sesso', 'sesso'],
                'claims': 'P21',
                'filters': [unicode.strip, unicode.upper],
                'map': {
                    'M': None,  # pywikibot.ItemPage(repo, 'Q6581097'),
                    'F': None,  # pywikibot.ItemPage(repo, 'Q6581072')
                }
            }
        ]
    },
    {
        'names': ['botanici', 'botanist'],
        'sites': ['itwiki', 'enwiki'],
        'params': [
            {
                'names': ['1'],
                'displayed': 'Botanici',
                'claims': 'P428',
                'filters': [ur'^[\w\.\s]+$'],
                'remove': ['itwiki']
            }
        ]
    },
    {
        'names': ['Divisione amministrativa'],
        'sites': ['itwiki'],
        'params': [
            {
                'names': ['Codice statistico'],
                'claims': 'P635',
                'filters': [ur'^\d{6}$']
            }, {
                'names': ['Codice catastale'],
                'claims': 'P806',
                'filters': [ur'^\w\d{3}$']
            }
        ]
    },
    {
        'names': ['Wdpa'],
        'sites': ['frwiki'],
        'params': [
            {
                'names': ['1'],
                'displayed': 'WDPA',
                'claims': 'P809',
                'filters': [unicode.strip, ur'^\d+$']
            }
        ]
    },
    {
        'names': [u'Infobox Aire protégée'],
        'sites': ['frwiki'],
        'params': [
            {
                'names': ['wdpa'],
                'displayed': 'WDPA',
                'claims': 'P809',
                'filters': [unicode.strip, ur'^\d+$']
            }
        ]
    },
    {
        'names': [u'WTA'],
        'sites': ['itwiki'],
        'params': [
            {
                'names': ['id', '1'],
                'displayed': 'WTA',
                'claims': 'P597',
                'filters': [unicode.strip, ur'^\d+$'],
                'remove': ['itwiki']
            }
        ]
    },
    {
        'names': [u'Scrum'],
        'sites': ['itwiki'],
        'params': [
            {
                'names': ['1'],
                'displayed': 'Scrum',
                'claims': 'P858',
                'filters': [unicode.strip, ur'^\d+$'],
                'remove': ['itwiki']
            }
        ]
    },
    {
        'names': [u'Infobox Métier'],
        'sites': ['frwiki'],
        'params': [
            {
                'names': ['code ROME'],
                'displayed': 'ROME',
                'claims': 'P867',
                'filters': [unicode.strip, ur'^\w\d{4}$']
            }
        ]
    },
    {
        'names': [u'Base Sycomore'],
        'sites': ['frwiki'],
        'params': [
            {
                'names': ['1'],
                'displayed': 'Sycomore',
                'claims': 'P1045',
                'filters': [unicode.strip, ur'^\d{1,5}$']
            }
        ]
    }
]

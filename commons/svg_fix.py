# -*- coding: utf-8  -*-

import re
import urllib2
import pywikibot

pywikibot.config.put_throttle=12

site=pywikibot.Site('commons','commons')
site.login()

#   __          __        _      _____         _____
#   \ \        / /       | |    |_   _|       |  __ \
#    \ \  /\  / ___  _ __| | __   | |  _ __   | |__) _ __ ___   __ _ _ __ ___ ___ ___
#     \ \/  \/ / _ \| '__| |/ /   | | | '_ \  |  ___| '__/ _ \ / _` | '__/ _ / __/ __|
#      \  /\  | (_) | |  |   <   _| |_| | | | | |   | | | (_) | (_| | | |  __\__ \__ \
#       \/  \/ \___/|_|  |_|\_\ |_____|_| |_| |_|   |_|  \___/ \__, |_|  \___|___|___/
#                                                               __/ |
#                                                              |___/

def fix_image(svg):
	print ''.join(list(urllib2.urlopen(svg.fileUrl())))

fix_image(pywikibot.ImagePage(site,'2NOGCMOS.svg'))

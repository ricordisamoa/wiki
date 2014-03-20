# wiki

[![Build Status](https://api.travis-ci.org/ricordisamoa/wiki.png?branch=master)](https://travis-ci.org/ricordisamoa/wiki)

A collection of scripts assisting with several tasks on Wikimedia Foundation projects.

Most of them require the latest [core branch](//git.wikimedia.org/summary/pywikibot/core.git) of the [Pywikibot](//www.mediawiki.org/wiki/Manual:Pywikibot) framework.

### add_section.py
It loops onto a predefined set of `pages` and, if absent, inserts the daily section header with the specified options. Used at the moment in [it:Wikipedia:Vandalismi in corso](//it.wikipedia.org/wiki/Wikipedia:Vandalismi_in_corso) only.

### calcio.py
It can update [Serie A 2013-2014#Classifica](//it.wikipedia.org/wiki/Serie_A_2013-2014#Classifica) from http://www.legaseriea.it/it/serie-a-tim/classifica-estesa/classifica

### compleanno.py
Written in Italian for the [Italian Wikipedia](//it.wikipedia.org), it searches for users born in the current day (from [this page](//it.wikipedia.org/wiki/Wikipedia:Wikipediani/Per_giorno_di_nascita)) and wishes them a happy birthday with a predefined message.

### fp_notice.py
From an [idea](//it.wikipedia.org/wiki/Discussioni_progetto:Coordinamento/Immagini#Migliorare_la_qualit.C3.A0_delle_immagini_presenti_nelle_voci_usando_quelle_gi.C3.A0_selezionate_da_Commons) of [Marcok](//it.wikipedia.org/wiki/Utente:Marcok), it checks for Wikimedia Commons [Featured Pictures](//commons.wikimedia.org/wiki/COM:FP) that are used in English articles but not in their Italian versions, and logs them in a user subpage.

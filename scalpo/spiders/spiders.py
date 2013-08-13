# -*- coding: utf-8 -*-

from scrapy.spider import BaseSpider
from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scalpo.items import ScalpoItem
from scrapy.http import Request
from scrapy import log
from itertools import groupby
from urlparse import urljoin

class RemacleSpider(CrawlSpider):
    'This is a very simple spider to crawl http://remacle.org entirely'

    name = 'remacle'
    allowed_domains = ['remacle.org']
    start_urls = ['http://remacle.org/']

    # Just crawl ANY link
    rules = [Rule(SgmlLinkExtractor(), 'parse_item', follow=True)]

    def parse_item(self, response):
        '''
        We extract ALL the text from the page in a single blob.
        Then we try to extract some metainformation from the url.
        '''
        hxs = HtmlXPathSelector(response)
        item = ScalpoItem()
        item['url'] = response.url
        item['title'] = ''.join(hxs.select('//title/text()').extract()[:1])
        item['text'] = ''.join(n.extract() for n in hxs.select('//body//text()'))

        # Some meta-information we can deduce from the urls
        _, _, path = response.url.partition('/bloodwolf/')
        if path:
            path = path.split('/')
            if len(path) == 2 and path[0] == 'orateurs':
                item['category'] = path[0]
                item['author'] = 'ciceron'
                item['work'] = path[1].replace('htm', '')
            elif len(path) >= 2:
                item['category'] = path[0]
                item['author'] = path[1]
                item['work'] = '/'.join(path[2:]).replace('.htm', '')

        return item


class UCLSpider(BaseSpider):
    '''
    This spider crawls the two hypertext databases "Itinera
    electronica" and "Oδoι ελεκτρoνικαι" hosted by UCL. It leverages
    their fairly regular structure to extract metadata.
    '''

    name = 'ucl'
    # agoraclass: server for itinera 
    # mercure: server for oδoι
    # pot-pourri: server for non hypertext
    allowed_domains = [server + '.fltr.ucl.ac.be' 
                       for server in ('agoraclass', 'mercure', 'pot-pourri')]

    def start_requests(self):
        'The two start pages'
        return [
            Request('http://agoraclass.fltr.ucl.ac.be/concordances/intro.htm',
                    meta={'category': 'itinera'}, callback=self.parse_intro,
                    errback=self.errback),
            Request('http://mercure.fltr.ucl.ac.be/Hodoi/concordances/intro.htm',
                    meta={'category': 'hodoi'}, callback=self.parse_intro,
                    errback=self.errback)
            ]

    def stringify(self, x):
        'facility to convert XPath objexts to strings'
        t = x.extract()
        return ' '.join(x.strip(' \r\n\t') for x in t)

    def urlgen(self, base, url=None):
        'facility to generate and correct urls'
        base = base.strip()
        # join paths
        if url is not None:
            url = url.strip()
            # fix paths which are directory names
            if not (base[-1] == '/'
                    or base[-4] == '.'):
                base += '/'
            url = urljoin(base, url)
        else:
            url = base

        # broken url fixes

        broken = {
            'http://agoraclass.fltr.ucl.ac.be/concordances/varron_de_agricultura_03/lecture/7htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/varron_de_agricultura_03/lecture/7.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/quintilianus_instit_lv04/lecture/11,htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/quintilianus_instit_lv04/lecture/11.htm',
            'http://mercure.fltr.ucl.ac.be/Hodoi/concordances/plutarque_opinions_phil_04/lecture/default.htm':
                'http://mercure.fltr.ucl.ac.be/Hodoi/concordances/plutarque_opinions_phil_04%20-%20Copie/lecture/default.htm',
            'http://mercure.fltr.ucl.ac.be/Hodoi/concordances/platon_republique_1/lecture/default.htm':
                'http://mercure.fltr.ucl.ac.be/Hodoi/concordances/platon_republique_01/lecture/default.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/commodien_instruc_01/lecture/89.htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/commodien_instruc_01/lecture/29.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/cicero_de_inuentione_02/lecture/89.htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/cicero_de_inuentione_02/lecture/29.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/cicero_de_inuentione_01/lecture/89.htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/cicero_de_inuentione_01/lecture/29.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/cassiodore_var_01_20&25/lecture/default.htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/cassiodore_var_01_20_25/lecture/default.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/augustin_serrmons_150/lecture/default.htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/augustin_sermons_150/lecture/default.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/augustin_serrmons_136/lecture/default.htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/augustin_sermons_136/lecture/default.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/augustin_civ_dei_16/lecture/89.htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/augustin_civ_dei_16/lecture/29.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/augustin_civ_dei_18/lecture/89.htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/augustin_civ_dei_18/lecture/29.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/augustin_civ_dei_20/lecture/89.htm':
                'http://agoraclass.fltr.ucl.ac.be/concordances/augustin_civ_dei_20/lecture/29.htm',
            'http://agoraclass.fltr.ucl.ac.be/concordances/pot-pourri.fltr.ucl.ac.be/files/Aclassftp/textes/BACON/bacon_de_sap_vet_10.txt':
                'http://pot-pourri.fltr.ucl.ac.be/files/Aclassftp/textes/BACON/de_sap_vet_10.txt',
            'http://agoraclass.fltr.ucl.ac.be/concordances/pot-pourri.fltr.ucl.ac.be/files/Aclassftp/textes/BACON/bacon_de_sap_vet_10_fr.txt':
                'http://pot-pourri.fltr.ucl.ac.be/files/Aclassftp/textes/BACON/de_sap_vet_10_fr.txt',
            'http://agoraclass.fltr.ucl.ac.be/concordances/pot-pourri.fltr.ucl.ac.be/files/Aclassftp/textes/BACON/bacon_de_sap_vet_27.txt':
                'http://pot-pourri.fltr.ucl.ac.be/files/Aclassftp/textes/BACON/de_sap_vet_27.txt',
            'http://agoraclass.fltr.ucl.ac.be/concordances/pot-pourri.fltr.ucl.ac.be/files/Aclassftp/textes/BACON/bacon_de_sap_vet_27_fr.txt':
                'http://pot-pourri.fltr.ucl.ac.be/files/Aclassftp/textes/BACON/de_sap_vet_27_fr.txt',
            }

        if url in broken:
            url = broken[url]

        return url

    def errin(self, url, meta):
        'Error reporting utility function'
        return ("%s in\n  %s, %s, %s" %
                ((url,) + 
                 tuple(meta[m] for m in ('author', 'work', 'section'))))

    def errback(self, err):
        'error callback used by all requests'
        if hasattr(err.value, 'response'):
            self.log('HTTP error %d %s' % (err.value.response.status,
                      self.errin(err.value.response.url, err.value.response.meta)),
                     log.ERROR)
        else:
            self.log(err.getErrorMessage(), log.ERROR)

    def parse_intro(self, response):
        '''
        This is the most difficult part: make sense of the list of all
        informatized texts in the two start pages.
        '''
        hxs = HtmlXPathSelector(response)
        # Select tables which have 4 columns (Aristoteles sometimes gets 5!)
        tables = hxs.select('//table')
        authors = [t for t in tables
                   if (t.select('tr') 
                       and all(len(r.select('td')) in (4, 5)
                               for r in t.select('tr')))]

        # Read the tables row by row
        for a in authors:
            # Columns have this format
            #   date | author | work | [subwork] | link(s) to chapter
            for r in a.select('tr'):
                c = r.select('td')
                auth = self.stringify(c[1].select('.//text()'))
                work = self.stringify(c[2:len(c)-1].select('.//text()'))

                # Sometimes links are broken over multiple words and
                # we want to aggregate them, sometimes there really
                # are multiple links in the same row.
                for url, g in groupby(((a.select('@href').extract()[0], a)
                                       for a in c[-1].select('.//a')),
                                      key=lambda (url, _): url):
                    chap = ' '.join(self.stringify(a.select('.//text()'))
                                    for (_, a) in g)

                    # Notify if some metadata could not be extracted
                    if not all([auth, work, chap]):
                        self.log('Cannot extract metadata from ' + self.stringify(r), log.WARNING)

                    # strip off some uninformative metadata
                    if chap.lower() in ('texte complet',
                                        u'oeuvre complète',
                                        u'poème', u'poèmes'):
                        chap = ''

                    # select the appropriate callback and url,
                    # depending on the server
                    url = self.urlgen(response.url, url)
                    if url.startswith('http://pot'):
                        cb = self.parse_txt
                        enc = 'txt'
                    else:
                        cb = self.parse_itinera
                        enc = 'html'
                        url = self.urlgen(url, 'lecture/default.htm')

                    req = response.request.replace(url=url, callback=cb)
                    req.meta.update({
                            'author' : auth,
                            'work'   : work,
                            'section': chap,
                            'enc'    : enc
                            })

                    yield req

    def parse_itinera(self, response):
        'Parse TOCs on itinera and oδoι'

        hxs = HtmlXPathSelector(response)
        # Get all links
        links = hxs.select('//a')
        try:
            # Find the beginning of the footer, and extract source link
            hrefs = links.select('@href').extract()
            try:
                bottom = hrefs.index('../consult.cfm')
            except ValueError:
                bottom = hrefs.index(
                    'http://mercure.fltr.ucl.ac.be/Hodoi/concordances/recherche/default.htm')
            source = links[bottom + hrefs[bottom:].index('../default.htm') + 1].select('@href').extract()[0]
        except ValueError, IndexError:
            self.log('Cannot parse footer at ' 
                     + self.errin(response.url, response.meta),
                     log.ERROR)
        else:
            # Crawl all links before the footer
            for a in links[:bottom]:
                url = a.select('@href').extract()
                if url:
                    url = self.urlgen(response.url, url[0])
                    # Only follow links to itinera and oδoι
                    # (Suetonius' De Vita Cæsarum deserves special treatement...)
                    if (url.startswith('http://agoraclass')
                        or url.startswith('http://mercure')
                        or url.startswith('http://bcs.fltr.ucl.ac.be/SUET/')):
                        req = response.request.replace(url=url, callback=self.parse_txt)
                        req.meta['section'] += ', '*bool(req.meta['section']) + self.stringify(a.select('.//text()'))
                        req.meta['source'] = source
                        yield req
                    else:
                        self.log('Not following '
                                 + self.errin(url, response.meta),
                                 log.INFO)

    def parse_txt(self, response):
        'Parse texts and hypertexts'

        # gather metadata
        item = ScalpoItem()
        item['url'] = response.url
        meta = [(x, response.meta[x]) for x in ('category', 'author', 'work', 'section')]
        item.update(meta)
        item['title'] = ', '.join(map(lambda (_,x) : x, meta[1:]))

        # scrap text, depending on file format
        if response.meta['enc'] == 'txt':
            item['text'] = response.body_as_unicode()
            item['source'] = 'http://bcs.fltr.ucl.ac.be/'
        else:
            item['source'] = response.meta['source']
            hxs = HtmlXPathSelector(response)
            # Suetonius deserves special treatement, we just grab everything
            if response.url.startswith('http://bcs.fltr.ucl.ac.be/SUET/'):
                text = hxs.select('//body')
            # For all the others, we have a rather precise idea of the
            # page structure
            else:
                text = hxs.select('//body/center')
                if len(text) != 2:
                    self.log('Found odd structure at '
                             + self.errin(response.url, response.meta),
                             log.WARNING)
            item['text'] = self.stringify(text.select('.//text()'))
        return item



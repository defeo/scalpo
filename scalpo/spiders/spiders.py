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
    their (seemingly?) machine-generated structure to extract
    metadata.
    '''

    name = 'ucl'
    # agoraclass: server for itinera 
    # mercure: server for oδoι
    # pot-pourri: server for non hypertext
    allowed_domains = [server + '.fltr.ucl.ac.be' 
                       for server in ('agoraclass', 'mercure', 'pot-pourri')]

    def stringify(self, x):
        t = x.extract()
        if isinstance(t, list):
            t = ' '.join(t)
        return t.strip(' \r\n\t')

    def start_requests(self):
        return [
            Request('http://agoraclass.fltr.ucl.ac.be/concordances/intro.htm',
                    meta={'category': 'itinera'}, callback=self.parse_intro),
            Request('http://mercure.fltr.ucl.ac.be/Hodoi/concordances/intro.htm',
                    meta={'category': 'hodoi'}, callback=self.parse_intro)]

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

        requests = []
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

                    # correct some erroneous links
                    if url.startswith('pot-pourri'):
                        url = 'http://' + url

                    # select the appropriate callback, depending on
                    # the server
                    req = response.request.replace(url=urljoin(response.url, url),
                                                   callback=(self.parse_txt 
                                                             if url.startswith('http://pot')
                                                             else self.parse_itinera))
                    req.meta.update({
                            'author' : auth,
                            'work'   : work,
                            'section': chap
                            })
                    requests.append(req)

        return requests

    def parse_txt(self, response):
        'Parse txt files found on pot-pourri'
        item = ScalpoItem()
        item['url'] = response.url
        meta = [(x, response.meta[x]) for x in ('category', 'author', 'work', 'section')]
        item.update(meta)
        item['title'] = ', '.join(map(lambda (_,x) : x, meta[1:]))
        item['text'] = response.body_as_unicode()
        return item

    def parse_itinera(self, response):
        'Parse per-section pages on itinera and oδoι'
        pass

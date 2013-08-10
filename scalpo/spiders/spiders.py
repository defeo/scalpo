# -*- coding: utf-8 -*-

from scrapy.contrib.spiders import CrawlSpider, Rule
from scrapy.contrib.linkextractors.sgml import SgmlLinkExtractor
from scrapy.selector import HtmlXPathSelector
from scalpo.items import ScalpoItem

class RemacleSpider(CrawlSpider):
    name = 'remacle'
    allowed_domains = ['remacle.org']
    start_urls = ['http://remacle.org/']
    rules = [Rule(SgmlLinkExtractor(), 'parse_item', follow=True)]

    def parse_item(self, response):
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

class UCLSpider(CrawlSpider):
    name = 'ucl'
    allowed_domains = ['fltr.ucl.ac.be']
    start_urls = ['http://bcs.fltr.ucl.ac.be/']
    rules = [
#        Rule(SgmlLinkExtractor(allow=['bcs.fltr.ucl.ac.be/']), 'parse_bcs'),  # BCS
        Rule(SgmlLinkExtractor(allow=['fltr.ucl.ac.be/concordances/.*/lecture/.*',
                                      'fltr.ucl.ac.be/Hodoi/concordances/.*/lecture/.*']),
             'parse_itinera'),  # Itinera Electronica
#        Rule(SgmlLinkExtractor(allow=['fltr.ucl.ac.be/files/AClassFTP/Textes/']), 'parse_txt'), # txt files
        Rule(SgmlLinkExtractor(allow=[], deny=['\?']))  # avoid queries
        ]

    def parse_itinera(self, response):
        hxs = HtmlXPathSelector(response)
        item = ScalpoItem()
        item['url'] = response.url
        item['title'] = ''.join(hxs.select('//title/text()').extract()[:1])
        item['text'] = ''.join(n.extract() for n in hxs.select('//body//text()'))

        return item


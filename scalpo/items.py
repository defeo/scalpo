# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/topics/items.html

from scrapy.item import Item, Field

class ScalpoItem(Item):
    url = Field()
    title = Field()
    text = Field()
    author = Field()
    work = Field()
    category = Field()
    section = Field()
    source = Field()

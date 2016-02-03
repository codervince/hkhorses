# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy


class HkhorsesItem(scrapy.Item):
    # define the fields for your item here like:
    # name = scrapy.Field()
    horsecode= scrapy.Field()
    horsename= scrapy.Field()
    yob= scrapy.Field()
    countryoforigin= scrapy.Field()
    importtype= scrapy.Field()
    owner= scrapy.Field()
    sirename= scrapy.Field()
    damname= scrapy.Field()
    damsirename= scrapy.Field()
    samesirecodes=scrapy.Field()
    twurl=scrapy.Field()
    veturl =scrapy.Field()
    pedigreeurl=scrapy.Field()
    pastraceindexes=scrapy.Field()
    pastracedates=scrapy.Field()
    pastraceconfigs=scrapy.Field()
    pastdistances=scrapy.Field()

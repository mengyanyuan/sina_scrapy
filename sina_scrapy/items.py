# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.loader.processors import TakeFirst


class SinaUserItem(scrapy.Item):
    # 微博用户唯一标识
    user_id = scrapy.Field(output_processor=TakeFirst())
    # 用户昵称
    username = scrapy.Field(output_processor=TakeFirst())
    # 微博数量
    webo_num = scrapy.Field(output_processor=TakeFirst())
    # 关注人数
    follow_num = scrapy.Field(output_processor=TakeFirst())
    # 粉丝人数
    fans_num = scrapy.Field(output_processor=TakeFirst())
    # 性别
    gender = scrapy.Field(output_processor=TakeFirst())
    # 地区
    district = scrapy.Field(output_processor=TakeFirst())
    # 省份
    province = scrapy.Field(output_processor=TakeFirst())
    # 地市
    city = scrapy.Field(output_processor=TakeFirst())
    # 生日
    birthday = scrapy.Field(output_processor=TakeFirst())
    # 简介
    brief_intro = scrapy.Field(output_processor=TakeFirst())
    # 认证
    identify = scrapy.Field(output_processor=TakeFirst())
    # 头像 URL
    head_img = scrapy.Field(output_processor=TakeFirst())
    # 爬取时间
    crawl_time = scrapy.Field(output_processor=TakeFirst())

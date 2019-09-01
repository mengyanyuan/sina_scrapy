# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html

from pymongo import MongoClient
from scrapy.conf import settings

host = settings.get('MONGODB_HOST')
port = settings.get('MONGODB_PORT')
dbname = settings.get('MONGODB_DBNAME')
collection_name = settings.get('MONGODB_COLLECTION')
db = MongoClient(host=host, port=port).get_database(dbname).get_collection(collection_name)


class SaveUserInfoPipeline(object):
    """
    保存爬取的数据\n
    """

    def __init__(self):
        print('要保存的 Collenction：%s' % collection_name)

    def process_item(self, item, spider):
        data = dict(item)
        print("最终入库数据：%s" % item)
        # 记录不存在则插入，否则更新数据
        db.update_one({'weibo_id': data.get('weibo_id')}, {"$set": data}, True)
        return item

# -*-* encoding:UTF-8 -*-
# author            : mengy
# date              : 2019/5/21
# python-version    : Python 3.7.0
# description       : Redis 缓存相关操作

import redis

# Redis 主机地址
CACHE_HOST = '127.0.0.1'
# Redis 端口
CACHE_PORT = '6379'
# 设置写入的键值对中的value为str类型
CACHE_DECODE_RESPONSES = True


class Cache(object):
    __pool = redis.ConnectionPool(host=CACHE_HOST, port=CACHE_PORT, decode_responses=CACHE_DECODE_RESPONSES)

    def __init__(self):
        self.__redis = redis.Redis(connection_pool=self.__pool)

    def delete(self, *names):
        """
        根据name删除redis中的任意数据类型\n
        :param names: key或者命名空间
        :return:
        """
        self.__redis.delete(*names)

    def exists(self, name):
        """
        检测redis的name是否存在\n
        :param name: key或者命名空间
        :return:
        """
        return self.__redis.exists(name)

    def keys(self, pattern='*'):
        """
        根据* ？等通配符匹配获取redis的name\n
        :param pattern: 通配符
        :return:
        """
        return self.__redis.keys(pattern)

    def expire(self, name, time):
        """
        为某个name设置超时时间\n
        :param name: key或者命名空间\n
        :param time: 超时时间（s）
        :return:
        """
        if not self.exists(name):
            raise Exception(name + ' 不存在')
        self.__redis.expire(name, time)

    def type(self, name):
        """
         获取name对应值的类型\n
        :param name: key或者命名空间\n
        :return:
        """
        return self.__redis.type(name)

    def rename(self, src, dst):
        """
        重命名key或者命名空间\n\n
        :param src: 原key或者命名空间\n
        :param dst: 修改后的key或者命名空间\n
        :return:
        """
        if self.exists(dst):
            raise Exception(dst + ' 已存在')
        if not self.exists(src):
            raise Exception(src + ' 不存在')
        self.__redis.rename(src, dst)

    # ------------------------字符串-----------------------------

    def get(self, key):
        """
        获取指定字符串值\n
        :param key:单个键\n
        :return:
        """
        return self.__redis.get(key)

    def mget(self, *keys):
        """
        批量获取指定字符串值\n
        :param keys:多个键\n
        :return:
        """
        return self.__redis.mget(keys)

    def set(self, key, value, px=None):
        """
        字符串设置值 \n
        :param key:键\n
        :param value:值\n
        :param px:过期时间(ms)\n
        :return:
        """
        self.__redis.set(name=key, value=value, px=px)

    def mset(self, **map):
        """
        字符串批量设置值\n
        :param map:批量设置的键值字典\n
        :return:
        """
        self.__redis.mset(mapping=map)

    # -------------------------Hash-----------------------------

    def hget(self, name, key):
        """
        在name对应的hash中根据key获取value \n
        :param name: 命名空间
        :param key: 命名空间下对应的键
        :return:
        """
        return self.__redis.hget(name=name, key=key)

    def hmget(self, name, *keys):
        """
        在name对应的hash中获取多个key的值\n
        :param name: 命名空间\n
        :param keys: 命名空间下的多个键
        :return:
        """
        return self.__redis.hmget(name=name, keys=keys)

    def hgetall(self, name):
        """
        获取name对应hash的所有键值 \n
        :param name:命名空间 \n
        :return:
        """
        return self.__redis.hgetall(name=name)

    def hset(self, name, key, value):
        """
        name对应的hash中设置一个键值对（不存在，则创建，否则，修改）\n
        :param name: 命名空间
        :param key: 命名空间下对应的键
        :param value: 命名空间下对应的值
        :return:
        """
        self.__redis.hset(name=name, key=key, value=value)

    def hmset(self, name, **map):
        """
        在name对应的hash中批量设置键值对\n
        :param name:命名空间\n
        :param map:键值对\n
        :return:
        """
        self.__redis.hmset(name=name, mapping=map)

    def hexists(self, name, key):
        """
        检查name对应的hash是否存在当前传入的key\n
        :param name: 命名空间\n
        :param key: 命名空间下对应的键
        :return:
        """
        return self.__redis.hexists(name=name, key=key)

    def hdel(self, name, keys):
        """
        批量删除指定name对应的key所在的键值对\n
        :param name:命名空间\n
        :param keys:要删除的键\n
        :return:
        """
        self.__redis.hdel(name, keys)

    # -------------------------List-----------------------------

    def lpush(self, name, *values, left=True):
        """
        在name对应的list中添加元素，每个新的元素都添加到列表的最左边\n
        :param name: 命名空间
        :param values: 值
        :param left: 是否添加到列表的最左边，True：最左边，False：最右边，默认为True
        :return:
        """
        if left:
            self.__redis.lpush(name, *values)
        else:
            self.__redis.rpush(name, *values)

    def lset(self, name, index, value):
        """
        对list中的某一个索引位置重新赋值\n
        :param name: 命名空间
        :param index: 索引位置
        :param value: 要插入的值
        :return:
        """
        self.__redis.lset(name=name, index=index, value=value)

    def lrem(self, name, count, value):
        """
        删除name对应的list中的指定值\n
        :param name:命名空间\n
        :param count:num=0 删除列表中所有的指定值；num=2 从前到后，删除2个；num=-2 从后向前，删除2个
        :param value:要删除的值
        :return:
        """
        self.__redis.lrem(name=name, count=count, value=value)

    def lpop(self, name):
        """
        移除列表的左侧第一个元素，返回值则是第一个元素\n
        :param name: 命名空间\n
        :return: 第一个元素
        """
        return self.__redis.lpop(name=name)

    def lindex(self, name, index):
        """
        根据索引获取列表内元素\n
        :param name: 命名空间\n
        :param index: 索引位置
        :return:
        """
        return self.__redis.lindex(name=name, index=index)

    def lrange(self, name, start, end):
        """
        获取指定范围内的元素\n
        :param name: 命名空间\n
        :param start: 起始位置
        :param end: 结束位置
        :return:
        """
        return self.__redis.lrange(name=name, start=start, end=end)

    def ltrim(self, name, start, end):
        """
        移除列表内没有在该索引之内的值\n
        :param name: 命名空间\n
        :param start: 起始位置
        :param end: 结束位置
        :return:
        """
        self.__redis.ltrim(name=name, start=start, end=end)

    # -------------------------Set-----------------------------

    def sadd(self, name, *values):
        """
        给name对应的集合中添加元素\n
        :param name:命名空间\n
        :param values:集合
        :return:
        """
        self.__redis.sadd(name, *values)

    def smembers(self, name):
        """
        获取name对应的集合的所有成员\n
        :param name: 命名空间\n
        :return:
        """
        return self.__redis.smembers(name=name)

    def sdiff(self, name, *others):
        """
        在第一个name对应的集合中且不在其他name对应的集合的元素集合，即，name集合对于其他集合的差集\n
        :param name:主集合\n
        :param others:其他集合\n
        :return:
        """
        # print(*others)
        return self.__redis.sdiff(name, *others)

    def sinter(self, name, *names):
        """
        获取多个name对应集合的交集\n
        :param name: 主集合\n
        :param names: 其他集合\n
        :return:
        """
        return self.__redis.sinter(name, *names)

    def sunion(self, name, *names):
        """
        获取多个name对应集合的并集\n
        :param name: 主集合\n
        :param names: 其他集合\n
        :return:
        """
        return self.__redis.sunion(name, *names)

    def sismember(self, name, value):
        """
        检查value是否是name对应的集合内的元素\n
        :param name:命名空间\n
        :param value:待检查的值\n
        :return:
        """
        return self.__redis.sismember(name=name, value=value)

    def smove(self, src, dst, value):
        """
        将某个元素从一个集合中移动到另外一个集合\n
        :param src: 原集合\n
        :param dst: 目标集合\n
        :param value: 待移动的值
        :return:
        """
        self.__redis.smove(src=src, dst=dst, value=value)

    def spop(self, name):
        """
        从集合的右侧移除一个元素，并将其返回\n
        :param name: 命名空间\n
        :return:
        """
        return self.__redis.spop(name=name)

    def srem(self, name, *values):
        """
        删除name对应的集合中的某些值\n
        :param name: 命名空间\n
        :param values: 要删除的值
        :return:
        """
        self.__redis.srem(name, *values)

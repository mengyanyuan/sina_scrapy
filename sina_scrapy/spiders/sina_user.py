# -*- coding: utf-8 -*-
import scrapy, time, re
from scrapy.loader import ItemLoader
from sina_scrapy.items import SinaUserItem


class SinaUserSpider(scrapy.Spider):
    # 爬虫的名字，唯一标识
    name = 'sina_user'
    # 允许爬取的域名范围
    allowed_domains = ['weibo.cn']
    # 爬虫的起始页面url
    start_urls = ['https://weibo.cn/u/1809054937']

    def __init__(self):
        self.headers = {
            'Referer': 'https://weibo.cn/u/1809054937',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
        }

        self.cookies = {
            'SCF': 'Al6oYEOIHG6uNyht6TbHJp7SLcrD339k-BxY3pGt5lGPZyZ3AzUo06ViWBPnaNv0KmkdfjZM2l-Om8g7ID6QdLQ.',
            'SUB': '_2A25wERk0DeRhGeVG7FcZ9yvPzT-IHXVT_ad8rDV6PUJbkdAKLRbSkW1NT5gs2CiaURmtMaZbhWzmdEvfYno07yQM',
            'SUHB': '0JvgjOCg8alBIo',
            '_T_WM': 80799919764
        }

    def start_requests(self):
        """
        构造最初 request 函数\n
        :return:
        """
        for url in self.start_urls:
            yield scrapy.Request(url=url, callback=self.base_info_parse, headers=self.headers, cookies=self.cookies)

    def base_info_parse(self, response):
        """
        微博用户基本信息解析函数\n
        :param response:
        :return:
        """
        # 加载器（Loader）
        load = ItemLoader(item=SinaUserItem(), response=response)
        selector = scrapy.Selector(response)
        # 解析微博用户 id
        re_url = selector.xpath('///a[contains(@href,"uid")]/@href').re('uid=(\d{10})')
        user_id = re_url[0] if re_url else ''
        load.add_value('user_id', user_id)

        follows_url = 'https://weibo.cn/%s/follow' % user_id
        fans_url = 'https://weibo.cn/%s/fans' % user_id
        for url in (follows_url, fans_url):
            yield scrapy.Request(url=url, callback=self.follow_fans_parse, headers=self.headers,
                                 cookies=self.cookies, meta={'user_id': user_id})

        # 微博数
        webo_num_re = selector.xpath('//div[@class="tip2"]').re(u'微博\[(\d+)\]')
        webo_num = int(webo_num_re[0]) if webo_num_re else 0
        load.add_value('webo_num', webo_num)
        # 关注人数
        follow_num_re = selector.xpath('//div[@class="tip2"]').re(u'关注\[(\d+)\]')
        follow_num = int(follow_num_re[0]) if follow_num_re else 0
        load.add_value('follow_num', follow_num)
        # 粉丝人数
        fans_num_re = selector.xpath('//div[@class="tip2"]').re(u'粉丝\[(\d+)\]')
        fans_num = int(fans_num_re[0]) if fans_num_re else 0
        load.add_value('fans_num', fans_num)
        # 记录爬取时间
        load.add_value('crawl_time', time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time())))

        yield scrapy.Request(url='https://weibo.cn/%s/info' % user_id, callback=self.detail_info_parse,
                             headers=self.headers, cookies=self.cookies, meta={'item': load.load_item()})

    def detail_info_parse(self, response):
        """
        用户资料解析函数\n
        :param response:
        :return:
        """
        # 获取上一个函数的解析结果
        item = response.meta['item']
        user_id = item.get('user_id')
        # 利用上一个函数的解析结果构造加载器（Loader）
        load = ItemLoader(item=item, response=response)
        selector = scrapy.Selector(response)
        # 如果 user_id 为空，在用户资料页面，再次提取 user_id
        if not user_id:
            ids = selector.xpath('//a[contains(@href,"uid")]/@href').re('uid=(\d{10})')
            ids = list(set(ids))
            user_id = ids[0]
            load.add_value('user_id', user_id)
        nick_name, gender, district, birthday, brief_intro, identify, head_img = '', '', '', '', '', '', ''
        for info in selector.xpath('//div[@class="c"][3]/text()'):
            # 提取个人资料
            nick_name = info.re(u'昵称:(.*)')[0] if info.re(u'昵称:(.*)') else nick_name
            identify = info.re(u'认证:(.*)')[0] if info.re(u'认证:(.*)') else identify
            gender = info.re(u'性别:(.*)')[0] if info.re(u'性别:(.*)') else gender
            district = info.re(u'地区:(.*)')[0] if info.re(u'地区:(.*)') else district
            birthday = info.re(u'生日:(.*)')[0] if info.re(u'生日:(.*)') else birthday
            brief_intro = info.re(u'简介:(.*)')[0] if info.re(u'简介:(.*)') else brief_intro
        # 根据用户填写的地区信息拆分成 省份 和 城市
        province, city = '', ''
        if district:
            extract = district.split(' ')
            province = extract[0] if extract else ''
            city = extract[1] if extract and len(extract) > 1 else ''
        # 合并用户基本信息和详细资料
        load.add_value('province', province)
        load.add_value('city', city)
        load.add_xpath('head_img', '//div[@class="c"]/img[@alt="头像"]/@src')
        load.add_value('username', nick_name)
        load.add_value('identify', identify)
        load.add_value('gender', gender)
        load.add_value('district', district)
        load.add_value('birthday', birthday)
        load.add_value('brief_intro', brief_intro)
        yield load.load_item()

    def follow_fans_parse(self, response):
        """
        获取关注用户/粉丝用户\n
        :param response:
        :return:
        """
        user_id = response.meta.get('user_id')
        if not user_id:
            user_id = re.compile('https://weibo.cn/(\d{10})/.*').findall(response.url)
            user_id = user_id[0] if user_id else ''
        selector = scrapy.Selector(response)
        # 判断用户数是否超过配置的最大用户数
        type_str = '关注' if str(response.url).find('follow') > 0 else '粉丝'
        self.logger.info('开始构造 [%s] %s爬取请求...' % (user_id, type_str))
        # 解析页面中所有的 URL，并提取 用户 id
        accounts = selector.xpath('//a[starts-with(@href,"https://weibo.cn/u/")]/@href').re(
            u'https://weibo.cn/u/(\d{10})')
        # 去重
        accounts = list(set(accounts))
        # 使用用户 id 构造个人资料、用户主页、关注列表以及粉丝列表的 URL
        urls = []
        [urls.extend(('https://weibo.cn/u/%s' % acc, 'https://weibo.cn/%s/fans' % acc,
                      'https://weibo.cn/%s/follow' % acc)) for acc in accounts]

        # 使用生成的 URL 构造 request
        for url in urls:
            if str(url).find('follow') > 0 or str(url).find('fan') > 0:
                yield scrapy.Request(url=url, callback=self.follow_fans_parse, headers=self.headers,
                                     cookies=self.cookies, meta={'user_id': user_id})
            else:
                yield scrapy.Request(url=url, callback=self.base_info_parse, headers=self.headers, cookies=self.cookies)

        # 下一页
        nextLink = selector.xpath('//div[@class="pa"]/form/div/a/@href').extract()
        if nextLink:
            url = 'https://weibo.cn' + nextLink[0]
            self.logger.info('[%s] %s下一页：%s' % (user_id, type_str, url))
            yield scrapy.Request(url=url, callback=self.follow_fans_parse, headers=self.headers, cookies=self.cookies,
                                 meta={'user_id': user_id})
        else:
            self.logger.info(u'[%s] %s已爬取完毕！' % (user_id, type_str))

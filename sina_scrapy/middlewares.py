# -*- coding: utf-8 -*-

# Define here the models for your spider middleware
#
# See documentation in:
# https://doc.scrapy.org/en/latest/topics/spider-middleware.html
import json
import random
import re

from scrapy import signals
from scrapy.exceptions import CloseSpider
from scrapy.http.headers import Headers
from scrapy.downloadermiddlewares.useragent import UserAgentMiddleware

from scrapy.conf import settings
from sina_scrapy.utils import crawl_proxy, simulate_login


class SinaScrapySpiderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the spider middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        # Called for each response that goes through the spider
        # middleware and into the spider.

        # Should return None or raise an exception.
        return None

    def process_spider_output(self, response, result, spider):
        # Called with the results returned from the Spider, after
        # it has processed the response.

        # Must return an iterable of Request, dict or Item objects.
        for i in result:
            yield i

    def process_spider_exception(self, response, exception, spider):
        # Called when a spider or process_spider_input() method
        # (from other spider middleware) raises an exception.

        # Should return either None or an iterable of Response, dict
        # or Item objects.
        pass

    def process_start_requests(self, start_requests, spider):
        # Called with the start requests of the spider, and works
        # similarly to the process_spider_output() method, except
        # that it doesn’t have a response associated.

        # Must return only requests (not items).
        for r in start_requests:
            yield r

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class SinaScrapyDownloaderMiddleware(object):
    # Not all methods need to be defined. If a method is not defined,
    # scrapy acts as if the downloader middleware does not modify the
    # passed objects.

    @classmethod
    def from_crawler(cls, crawler):
        # This method is used by Scrapy to create your spiders.
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_request(self, request, spider):
        # Called for each request that goes through the downloader
        # middleware.

        # Must either:
        # - return None: continue processing this request
        # - or return a Response object
        # - or return a Request object
        # - or raise IgnoreRequest: process_exception() methods of
        #   installed downloader middleware will be called
        return None

    def process_response(self, request, response, spider):
        # Called with the response returned from the downloader.

        # Must either;
        # - return a Response object
        # - return a Request object
        # - or raise IgnoreRequest
        return response

    def process_exception(self, request, exception, spider):
        # Called when a download handler or a process_request()
        # (from other downloader middleware) raises an exception.

        # Must either:
        # - return None: continue processing this exception
        # - return a Response object: stops process_exception() chain
        # - return a Request object: stops process_exception() chain
        pass

    def spider_opened(self, spider):
        spider.logger.info('Spider opened: %s' % spider.name)


class RandomUserAgentMiddleware(UserAgentMiddleware):
    """
    随机选取 代理（User-Agent）
    """

    def __init__(self, user_agent):
        self.user_agent = user_agent
        self.headers = Headers()

    @classmethod
    def from_crawler(cls, crawler):
        """
        开始构造请求前执行的方法\n
        :param crawler:整个爬虫的全局对象\n
        :return:
        """
        # 从配置里获取 用户代理（User-Agent） 列表
        return cls(user_agent=crawler.settings.get('USER_AGENT_LIST'))

    def process_request(self, request, spider):
        """
        发送请求前执行的方法\n
        :param request:请求\n
        :param spider:爬虫应用\n
        :return:
        """
        # 从 代理 列表中随机选取一个 代理
        agent = random.choice(self.user_agent)
        print('当前 User-Agent ：', agent)
        self.headers['User-Agent'] = agent
        request.headers = self.headers


class IPProxyMiddleware(object):
    """
    IP 代理池中间件
    """

    def __init__(self):
        # 爬取有效 ip
        self.ip_list = crawl_proxy.get_ips(pages=3)
        # 请求已经失败的次数
        self.retry_time = 0
        self.index = random.randint(0, len(self.ip_list) - 1)

    def process_request(self, request, spider):
        """
        处理将要请求的 Request
        :param request:
        :param spider:
        :return:
        """
        # 失败重试次数
        self.retry_time = 0
        #
        # if len(self.ip_list) < 5:
        #     self.ip_list.extend(crawl_proxy.get_ips(refresh=True))
        # 随机选取 ip
        proxy = json.loads(self.ip_list[self.index])
        print('选取的 ip：' + proxy.get('url'))
        # 设置代理
        request.meta['Proxy'] = proxy.get('url')

    def process_spider_input(self, response, spider):
        if str(response.url).find('https://passport.weibo.cn/signin/login') > 0:
            return CloseSpider('Cookies 异常，需要重新登录！')

    def process_response(self, request, response, spider):
        """
        处理返回的 Response
        :param request:
        :param response:
        :param spider:
        :return:
        """
        # 针对4**、和5** 响应码，重新选取 ip
        if re.findall('[45]\d+', str(response.status)):
            print(u'[%s] 响应状态码：%s' % (response.url, response.status))
            if self.retry_time > settings.get('MAX_RETRY', 5):
                return response
            if response.status == 418:
                # 出现 418 重新获取 cookies
                request.cookies = simulate_login.LoginBase(settings.get('SINA_ACCOUNT'),
                                                           settings.get('SINA_PASSWD')).get_cookies('.weibo.cn')
                sec = random.randrange(30, 35)
                print(u'休眠 %s 秒后重试' % sec)
                # time.sleep(sec)
            self.retry_time += 1
            proxy = json.loads(random.choice(self.ip_list))
            print('失败 %s 次后，重新选取的 ip：%s' % (self.retry_time, proxy.get('url')))
            request.meta['Proxy'] = proxy.get('url')
            return request
        return response


class CookiesMiddleware(object):
    """
    登录 Cookies 中间件
    """

    def __init__(self):
        self.cookies = simulate_login.LoginBase(settings.get('SINA_ACCOUNT'), settings.get('SINA_PASSWD')).get_cookies()

    def process_request(self, request, spider):
        cookies = self.cookies.get('.weibo.cn')
        request.cookies = cookies

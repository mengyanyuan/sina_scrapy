# -*-* encoding:UTF-8 -*-
# author            : mengy
# date              : 2019/6/26
# python-version    : Python 3.7.0
# description       : 模拟登录新浪微博

import base64
import urllib
import rsa
import binascii
import json
import re
import http.cookiejar
import urllib.request
from sina_scrapy.utils.cache_utils import Cache

# cookies 在缓存中的有效期（s）
COOKIES_EXPIRES = 3 * 24 * 60 * 60


def urlopen(url, callback=None, data=None, timeout=5):
    """
    重写 urllib 的 urlopen 方法，该方法能够将 cookies 作为参数传给回调函数\n
    :param url:请求的地址或者 url.request.Request() 对象\n
    :param callback:回调函数\n
    :param data:请求数据\n
    :param timeout:超时时间（s），默认为 5s\n
    :return:
    """
    cookie = http.cookiejar.CookieJar()
    handler = urllib.request.HTTPCookieProcessor(cookie)
    opener = urllib.request.build_opener(handler)
    response = opener.open(url, data=data, timeout=timeout)
    if callback:
        callback(cookie)
    return response


class LoginBase(object):
    """
    微博模拟登录基类，实现了新浪移动微博网页版（https://weibo.cn/）的模拟登录\n
    """
    # 缓存工具
    __cache = Cache()

    # 移动网页版 cookies 在缓存中的命名
    COOKIES_NAMESPACE = 'MOBILE_WEB_POOL_COOKIES'

    def __init__(self, username, password):
        # 微博账号
        self.__username = username
        # 微博密码
        self.__password = password
        # 记录 cookies，按照 domain 分组
        self.cookies = {}

    @property
    def username(self) -> str:
        return self.__username

    @property
    def password(self) -> str:
        return self.__password

    def save_cookies(self, cookie: http.cookiejar.CookieJar):
        """
        保存 Cookies\n
        :param cookie:
        :return:
        """
        # 按照 domain 分组记录所访问过 url 的 cookies
        for item in cookie:
            tmp = self.cookies.get(item.domain)
            if tmp:
                tmp.update({item.name: item.value})
            else:
                self.cookies.update({item.domain: {item.name: item.value}})

    def login(self):
        """
        微博移动网页版模拟登录（https://weibo.cn/），代码实现逻辑根据网页版 js，有一定的时效性\n
        :return:
        """
        print(u'微博移动网页版模拟登录（https://weibo.cn/）开始...')
        # 登录地址
        url = 'https://passport.weibo.cn/sso/login'
        # 默认 Headers
        headers = {
            'Referer': 'https://passport.weibo.cn/signin/login?entry=mweibo&r=https%3A%2F%2Fweibo.cn&page=9.com&uid=1260427471&_T_WM=c6e864f47316ecbaf8607a214d4bb3fa',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/537.36'
        }
        # 构造模拟登录请求的表单数据
        data = {
            'username': self.__username,
            'password': self.__password,
            'savestate': 1,
            'r': 'https://weibo.cn',
            'ec': 0,
            'pagerefer': '',
            'entry': 'mweibo',
            'wentry': '',
            'loginfrom': '',
            'client_id': '',
            'code': '',
            'qq': '',
            'mainpageflag': 1,
            'hff': '',
            'hfp': ''
        }
        try:
            # 格式化 请求数据
            post_data = urllib.parse.urlencode(data).encode('gbk')
            # 构造请求
            req = urllib.request.Request(url=url, data=post_data, headers=headers, method='POST')
            # 使用自定义的请求方法，保存请求的 cookies
            response = urlopen(url=req, callback=self.save_cookies, timeout=10)
            # 将返回的数据转化成 dict
            result = json.loads(response.read().decode('gbk'))
            if result.get('retcode') == 20000000:
                print(u'登录成功！')
                # 登录成功后返回的 url
                crossdomainlist = result.get('data').get('crossdomainlist')
                # 依次访问 url，获取 cookies 并保存
                if crossdomainlist:
                    for item in dict(crossdomainlist).values():
                        urlopen(item, self.save_cookies)
            else:
                print(u'登录失败！')
            # 将 cookies 放入缓存 redis
            self.push_cache()
            return True
        except Exception as e:
            print(u'解析失败', e)
            return False

    def push_cache(self):
        assert self.cookies, u'请先模拟登录'
        # self.__cache.lpush(self.COOKIES_NAMESPACE, json.dumps(self.cookies))
        self.__cache.hset(self.COOKIES_NAMESPACE, self.username, json.dumps(self.cookies))
        # 设置 cookies 的有效时间（三天）
        self.__cache.expire(self.COOKIES_NAMESPACE, COOKIES_EXPIRES)

    def get_cookies(self, domain=None, is_force_login=False):
        """
        获取 cookies\n
        :param domain:域名
        :param is_force_login:是否强制登录（默认为 False）\n
        :return:
        """
        # 从 redis 获取 cookies
        # data = self.__cache.lrange(namespace, 0, 1)
        data = self.__cache.hget(self.COOKIES_NAMESPACE, self.username)
        if is_force_login or not data:
            # 如果 redis 中没有 cookies，则模拟登录，重新获取 cookies
            if self.login():
                cookies = self.cookies
            else:
                raise Exception(u'获取 Cookies 失败！')
        else:
            print(u'从缓存中获取 cookies')
            cookies = json.loads(data)
        if domain:
            return cookies.get(domain)
        return cookies


class LoginForSinaCom(LoginBase):
    """
    模拟新浪微博 PC 网页版（https://weibo.com）登录，登录后，将 cookies 保存到 redis 缓存中，并提供获取 cookies 的方法
    """

    # PC 网页版 cookies 在缓存中的命名
    COOKIES_NAMESPACE = 'PC_WEB_POOL_COOKIES'

    def __init__(self, username, password):
        LoginBase.__init__(self, username, password)

    def encrypt_name(self) -> str:
        """
        用 base64 加密用户名 \n
        :return:
        """
        return base64.encodebytes(bytes(urllib.request.quote(self.username), 'utf-8'))[:-1].decode('utf-8')

    def encrypt_passwd(self, **kwargs) -> str:
        """
         使用 rsa 加密密码\n
        :param kwargs:
        :return:
        """
        try:
            # 拼接明文
            message = str(kwargs['servertime']) + '\t' + str(kwargs['nonce']) + '\n' + str(self.password)
            # 10001 为 js 加密文件中的加密因子，16进制
            key = rsa.PublicKey(int(kwargs['pubkey'], 16), 0x10001)
            # 使用 rsa 加密拼接后的密码
            encrypt_pwd = rsa.encrypt(message.encode('utf-8'), key)
            # 将加密后的密文转化成 AscII 码
            final_pwd = binascii.b2a_hex(encrypt_pwd)
            return final_pwd
        except Exception as e:
            print(e)
            return None

    def pre_login(self) -> dict:
        """
        预登录，请求 prelogin_url 链接地址 获取 servertime，nonce，pubkey 和 rsakv \n
        :return:
        """
        # 预登录地址
        pre_login_url = 'http://login.sina.com.cn/sso/prelogin.php?entry=sso&callback=sinaSSOController.preloginCallBack&su=%s&rsakt=mod&client=ssologin.js(v1.4.19)' % self.encrypt_name()
        try:
            response = urlopen(pre_login_url, callback=self.save_cookies, timeout=5)
            # 提取响应结果
            preloginCallBack = re.compile('\((.*)\)').search(str(response.read(), 'UTF-8'))
            if preloginCallBack:
                result = json.loads(preloginCallBack.group(1))
            else:
                raise Exception(u'解析响应结果失败！')
            return result
        except Exception as e:
            print(e)
            return None

    def login(self):
        """
        登录新浪微博 PC 网页版（https://weibo.com）\n
        :return:
        """
        print(u'新浪微博 PC 网页版（https://weibo.com）登录开始...')
        # 预登录
        result = self.pre_login()
        # 加密用户账号
        encodedUserName = self.encrypt_name()
        serverTime = result.get('servicetime')
        nonce = result.get('nonce')
        rsakv = result.get('rsakv')
        # 加密密码
        encodedPassWord = self.encrypt_passwd(**result)
        # 构造请求数据
        post_data = {
            "entry": "weibo",
            "gateway": "1",
            "from": "",
            "savestate": "7",
            "qrcode_flag": 'false',
            "useticket": "1",
            "pagerefer": "https://login.sina.com.cn/crossdomain2.php?action=logout&r=https%3A%2F%2Fweibo.com%2Flogout.php%3Fbackurl%3D%252F",
            "vsnf": "1",
            "su": encodedUserName,
            "service": "miniblog",
            "servertime": serverTime,
            "nonce": nonce,
            "pwencode": "rsa2",
            "rsakv": rsakv,
            "sp": encodedPassWord,
            "sr": "1680*1050",
            "encoding": "UTF-8",
            "prelt": "194",
            "url": "https://weibo.com/ajaxlogin.php?framelogin=1&callback=parent.sinaSSOController.feedBackUrlCallBack",
            "returntype": "META"
        }
        # 登录地址
        url = 'https://login.sina.com.cn/sso/login.php?client=ssologin.js(v1.4.19)'
        # 打包请求数据
        data = urllib.parse.urlencode(post_data).encode('GBK')
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36'
        }
        try:
            # 请求登录
            req = urllib.request.Request(url=url, data=data, headers=headers)
            response = urlopen(req, callback=self.save_cookies)
            text = response.read().decode('GBK')
        except Exception as e:
            print(e)
        try:
            # 获取第一次重定向地址
            login_url = re.compile('location\.replace\("(.*)"\)').search(text).group(1)
            # 第一次重定向
            response = urlopen(login_url, callback=self.save_cookies)
            data = response.read().decode('GBK')
            # 获取第二次重定向地址
            jump_url = re.compile("location\.replace\('(.*)'\)").search(data).group(1)
            # 第二次重定向
            response = urlopen(jump_url, callback=self.save_cookies)
            data = response.read().decode('utf-8')
            # 获取服务器返回的加密的 用户名
            name = re.compile('"userdomain":"(.*)"').search(data).group(1)
            index = 'http://weibo.com/' + name
            # 第三次跳转到首页
            urlopen(index, callback=self.save_cookies)
            print(u'登录成功！')
            # 将 cookies 放入缓存 redis
            self.push_cache()
            return True
        except Exception as e:
            print(u'登录失败！，异常：', e)
            return False


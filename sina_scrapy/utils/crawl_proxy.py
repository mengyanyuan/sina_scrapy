# -*-* encoding:UTF-8 -*-
# author            : mengy
# date              : 2019/9/1
# python-version    : Python 3.7.0
# description       : 

import re, subprocess as sp, time, json

from urllib import request
from bs4 import BeautifulSoup
from sina_scrapy.utils.cache_utils import Cache
from sina_scrapy.utils.thread_pool import ThreadPool

executor = ThreadPool()

cache = Cache()

# 西刺代理 URL
PROXY_IP_XICI_URL = 'https://www.xicidaili.com/nn/%s'
# 快代理 URL
PROXY_IP_QUICK_URL = 'https://www.kuaidaili.com/free/inha/%s/'
# 模拟请求头
PROXY_IP_XICI_HEADERS = {
    'Host': 'www.xicidaili.com',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3',
    'Connection': 'keep-alive',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.157 Safari/537.36',
    'Accept - Encoding': 'gzip, deflate, br',
    'Accept - Language': 'zh - CN, zh;q = 0.9, en;q = 0.8',
    'Cookie': '_free_proxy_session = BAh7B0kiD3Nlc3Npb25faWQGOgZFVEkiJTBhMGNlZjVlYjdjNDU5NjY3ZDNlOGU0YmQ4NTU0OTBhBjsAVEkiEF9jc3JmX3Rva2VuBjsARkkiMVZpMzIrOVV3aFp5cnJXR3hTVUtFRy9ud0MxMGtyY2R3WjJzMjltSFNSeEE9BjsARg % 3D % 3D - -55779e702f4e95b04fa84eafbb70ccb4006cd839;Hm_lvt_0cf76c77469e965d2957f0553e6ecf59 = 1558427855, 1558427893, 1558427898, 1558427901;Hm_lpvt_0cf76c77469e965d2957f0553e6ecf59 = 1558428119'
}
PROXY_IP_QUICK_HEADERS = {
    'Host': 'www.kuaidaili.com',
    'Connection': ' keep-alive',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.36',
    'Cookie': 'channelid=bdtg_a10_a10a1; sid=1559283308913843; _ga=GA1.2.594886518.1559283655; _gid=GA1.2.578719903.1559283655; Hm_lvt_7ed65b1cc4b810e9fd37959c9bb51b31=1559283656; Hm_lpvt_7ed65b1cc4b810e9fd37959c9bb51b31=1559283719'
}
# 代理ip列表在缓存中的命名
PROXY_IP_NAMESPACE = 'POOL_PROXY_IPS'
# 缓存中代理 ip 失效时间（s）
PROXY_IP_EXPIRE = 15 * 60

# ping ip 最高丢包率（%）
MAX_LOST = 75
# ping ip 最大延迟时间（ms）
MAX_TIMEOUT = 1000


def get_ips(pages=1, refresh=False):
    """
    获取代理ip，优先从缓存取，如果缓存为空，则爬取新的代理 ip，并更新缓存\n
    :param refresh: 是否强制爬取\n
    :return:
    """
    if refresh:
        return crawl_quick(pages)
    else:
        # 从缓存中查询代理ip
        data = cache.lrange(name=PROXY_IP_NAMESPACE, start=0, end=100)
        if not data:
            print(u'缓存数据为空！开始爬取高匿代理ip')
            return crawl_quick(pages)
        else:
            return data


def sub_thread(ip_info):
    """
    校验 ip 是否连通\n
    :param ip_info:
    :return:
    """
    if check_ip(ip_info.get('ip')):
        # 将可用的 ip 放入缓存
        cache.lpush(PROXY_IP_NAMESPACE, json.dumps(ip_info))
        # 如果 ip 可用，则返回 ip 的信息
        return json.dumps(ip_info)
    else:
        return None

def crawl_quick(page=1):
    """
     请求 快代理 爬取高匿代理 ip\n
    :param page:
    :return:
    """
    print(u'请求 快代理 爬取高匿代理 ip')
    assert 1 <= page <= 10, '页数有效范围为（1 - 10）'
    validate_ips = []
    for i in range(page):
        req = request.Request(url=PROXY_IP_QUICK_URL % str(i + 1), headers=PROXY_IP_QUICK_HEADERS)
        response = request.urlopen(req)
        if response.status == 200:
            # 解析页面元素
            soap = BeautifulSoup(str(response.read(), encoding='utf-8'), 'lxml')
            ip_table = soap.select('#list > table > tbody > tr')
            ips = []
            # 获取当前页的所有 ip 信息
            for data in ip_table:
                item = data.text.split('\n')
                info = {}
                ip, port, area, proxy_type, protocol, alive_time, check_time = item[1], item[2], item[5], item[3], item[
                    4], '', item[7]
                url = str.lower(protocol) + "://" + ip + ":" + port
                # 将 ip 信息封装成字典
                info.update(ip=ip, port=port, area=area, type=proxy_type, protocol=protocol, alive_time=alive_time,
                            check_time=check_time, url=url, add_time=int(time.time()))
                ips.append(info)
            # 遍历爬取的 ip 信息，校验 ip 是否连通
            tasks = [executor.submit(sub_thread, (ip_info)) for ip_info in ips]

            # 轮询所有完成的线程，查询线程的执行结果
            for task in executor.completed_tasks(tasks):
                data = task.result()
                if data:
                    # 将线程执行结果返回
                    validate_ips.append(data)
            # 降低爬取频率
            time.sleep(2.5)
    # 当还没有子线程返回可用的 ip 时，再次查询缓存
    if not validate_ips:
        validate_ips = cache.lrange(name=PROXY_IP_NAMESPACE, start=0, end=100)
    # 设置缓存超时时间
    cache.expire(name=PROXY_IP_NAMESPACE, time=PROXY_IP_EXPIRE)
    print(u'本次爬取 ip ：%d 条，有效：%d 条' % (15 * page, len(validate_ips)))
    return validate_ips


def check_ip(ip):
    """
    通过 ping ip 来验证 ip 是否有效\n
    :param ip: 待 ping 的 ip
    :return:
    """
    assert ip, 'ip 不能为空！'
    # CMD 命令（windows）
    cmd = 'ping -n 4 -w 4 %s' % ip
    # 参数 shell 设为 true，程序将通过 shell 来执行,subprocess.PIPE 可以初始化 stdin , stdout 或 stderr 参数。表示与子进程通信的标准流
    p = sp.Popen(cmd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.PIPE, shell=True)
    out = p.stdout.read().decode('gbk')
    # 丢失率
    lost_ratio = re.compile(u'(\d+)% 丢失', re.IGNORECASE).findall(out)
    # 平均耗时
    avg_time = re.compile(u'平均 = (\d+)', re.IGNORECASE).findall(out)
    # 如果失败率高于最高丢包率则丢弃
    if lost_ratio[0] and int(lost_ratio[0]) > MAX_LOST:
        print('%s 失败率过高！丢弃' % ip)
        return False
    # 如果响应时间高于最大延迟时间则丢弃
    if avg_time and int(avg_time[0]) > MAX_TIMEOUT:
        print('%s 响应时间过长，网络不稳定，丢弃' % ip)
        return False
    return True

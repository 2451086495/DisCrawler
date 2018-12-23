#encoding=utf-8
import pickle
from bs4 import BeautifulSoup
import re
import socket, fcntl, struct
import threading
import sys
import uuid
sys.path.append('../common')
from scripy import CrawlerHandler
from Common import Common
from master_LogCmd import master_LogCmd
from slaver_WordAnalysisCmd import slaver_WordAnalysisCmd
from DataStore import RedisList, RedisHash
from Parase import Parser

'''
    网页抓任务
'''
class slaver_ScripyCmd():
    para = {'phone' : 0, 'UA' : 1, 'url' : 2}
    Parser = None
    handleCnt = None
    FrameInfo = None
    redisList = None
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    LocalIp = socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', 'eth0'[:15]))[20:24])

    @classmethod
    def Init(cls, config):
        cls.Parser = Parser(config)
        cls.handleCnt = 'handleCnt'
        cls.FrameInfo = RedisHash('FrameInfo', redishost=config.get('redis', 'redis'))       #记录爬虫状态，hash结构，如正在抓取url的redis
        cls.redisList = RedisList(cls.Name(),  redishost=config.get('redis', 'redis'))
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        cls.mac = uuid.UUID(int = uuid.getnode()).hex[-12:].upper()
        master_LogCmd.Init(config)
        slaver_WordAnalysisCmd.Init(config)

    @classmethod
    def Name(cls):
        return cls.__name__

    #优先级，值越低优先级越大
    @staticmethod
    def Priority():
        return 10

    @classmethod
    def WriteTaskData(cls, url):
        cls.redisList.rpush(pickle.dumps(url))

    @classmethod
    def ReadTaskData(cls):
        data = cls.redisList.lpop()
        if data != None:
            data = pickle.loads(data)
        return data

    @classmethod
    def IOStage(cls, url):
        #在redis中记录当前抓取的线程id
        key = "%s_%d" % (cls.mac, threading.currentThread().ident)
        cls.FrameInfo.hset(key, url)

        # 抓取数据
        contenttype, content = Common.GetContentByUrl(url)

        #在redis更新抓取网页统计值
        urlHandleCnt = int(cls.FrameInfo.hget(cls.handleCnt)) + 1
        cls.FrameInfo.hset(cls.handleCnt, urlHandleCnt)
        cls.FrameInfo.hdel(key)

        #抓取异常判断
        if content == None or contenttype == None or content == '':
            master_LogCmd.WriteTaskData("Failed : %s" % url)
            return None

        #对于网页内容，则触发“基于文本分析不良网页的任务”
        if contenttype.find("text/html") != -1:  #是网页资源
            slaver_WordAnalysisCmd.WriteTaskData(content, url)

        return None

    @classmethod
    def CPUStage(cls, data):
        pass
#encoding=utf-8  
import pickle
from bs4 import BeautifulSoup
import re
import socket, fcntl, struct
import threading
import sys
import os
import random
sys.path.append('../common')
from Common import Common
from master_LogCmd import master_LogCmd
from DataStore import RedisList
from Parase import Parser
import pickle

'''
    基于图片分析不良网页的任务
'''
class slaver_PicAnalysisCmd():
    Parser = None
    picFmt = None
    unhealthrate = None
    redisList = None

    @classmethod
    def Init(cls, config):
        cls.Parser = Parser(config)
        cls.picFmt = config.get('spider', 'PicFormat')
        cls.unhealthrate = config.get("spider", "unhealthrate")
        cls.redisList = RedisList(cls.Name(),  redishost=config.get('redis', 'redis'))
        master_LogCmd.Init(config)
        print 'finish init %s' % cls.Name()

    @classmethod
    def Name(cls):
        return cls.__name__

    #优先级，值越低优先级越大
    @staticmethod
    def Priority():
        return 8

    @classmethod
    def WriteTaskData(cls, content, url):
        cls.redisList.rpush(pickle.dumps((content, url)))

    @classmethod
    def ReadTaskData(cls):
        data = cls.redisList.lpop()
        if data != None:
            data = pickle.loads(data)
        return data

    @classmethod
    def IOStage(cls, data):
        return data

    @classmethod
    def CPUStage(cls, data):
        content = data[0]
        url = data[1]
        print "%s get url : %s" % (cls.Name(), url)
        imgSet = cls.GetImgUrls(url, content, cls.picFmt)  #提取网页中图片的url
        maxUnhealImgCnt = len(imgSet) * float(cls.unhealthrate)   #根据设定的不良图片比例，计算出网页中不良图片的数量
        unHealthImgCnt = 0

        for imgurl in imgSet:
            imgtype, content = Common.GetContentByUrl(imgurl)  #抓取图片
            if content != None and cls.Parser.IsInvalidImg(content, imgtype, imgurl):  #分析是否为不良图片
                unHealthImgCnt += 1
                if unHealthImgCnt >= maxUnhealImgCnt:   #网页中不良图片数量超过阈值maxUnhealImgCnt
                    picName = str(random.randint(0, 10000000)) + '.jpg'
                    master_LogCmd.WriteTaskData("!!!! found invalid html by %s: url: %s, picname:%s" % (cls.Name(), url, picName))
                    os.popen('phantomjs snapshot.js %s %s' % (url, picName))  #网页截图
                    break

    '''
        通过正则表达式从网页中提取指定格式的图片
    '''
    @classmethod
    def GetImgUrls(cls, url, content, picFormat):
        imgurls = set()
        #soup = BeautifulSoup(content, "html.parser", from_encoding="utf-8")
        #soup.encode('utf-8')
        #[imgurls.add(Common.UrlJoin(url, img['src'])) for img in soup.findAll("img", attrs={"src": True}) if img['src'] != '']
        pattern = re.compile(r'https?://.+?\.%s' % picFormat)
        for imgurl in re.findall(pattern, content):
            pos = imgurl.rfind('http://')
            if pos != -1:
                imgurl = imgurl[pos:]
            else:
                pos = imgurl.rfind('https://')
                if pos not in [-1, 0]:
                    imgurl = imgurl[pos:]
            try:
                absUrl = Common.UrlJoin(url, imgurl)
            except Exception as e:
                master_LogCmd.WriteTaskData('UrlJoin failed, url ; %s, imgurl : %s' % (url, imgurl))
                continue
            imgurls.add(absUrl)
        return imgurls

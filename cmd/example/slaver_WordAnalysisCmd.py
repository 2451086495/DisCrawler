#encoding=utf-8
import pickle
import sys
from master_LogCmd import master_LogCmd
from slaver_PicAnalysisCmd import slaver_PicAnalysisCmd
import random
import os

sys.path.append('../common')
from DataStore import RedisList, RedisHash
from Parase import Parser

'''
    基于文本分析不良网页的任务
'''
class slaver_WordAnalysisCmd():
    Parser = None
    redisList = None

    @classmethod
    def Init(cls, config):
        cls.Parser = Parser(config)
        cls.redisList = RedisList(cls.Name(), redishost=config.get('redis', 'redis'))
        slaver_PicAnalysisCmd.Init(config)
        print 'finish init %s' % cls.Name()

    @classmethod
    def Name(cls):
        return cls.__name__

    #优先级，值越低优先级越大
    @staticmethod
    def Priority():
        return 9

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
        if cls.Parser.IsInvalidPage(content):  # 判断是否含有非法文字信息
            picName = str(random.randint(0, 10000000)) + '.jpg'
            os.popen('phantomjs snapshot.js %s %s' % (url, picName))  #通过phantomjs对网页截图
            master_LogCmd.WriteTaskData("!!!! found invalid html by %s: url: %s, picname:%s" % (cls.Name(), url, picName))
        else:    #通过将网页内容写入到redis中“基于图片分析不良网页的任务”队列，触发该任务的执行
            slaver_PicAnalysisCmd.WriteTaskData(content, url)


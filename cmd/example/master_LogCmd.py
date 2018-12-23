# encoding=utf-8
import sys
import logging
import logging.handlers
sys.path.append('../common')
from DataStore import RedisList

'''
    日志管理任务：对其他节点上的任务提供写日志接口，本任务接收其他任务的日志内容并写文件
'''
class master_LogCmd():
    logger = None
    redisList = None

    @classmethod
    def Init(cls, config):
        redisIp = config.get('redis', 'redis')
        logfileName = config.get('spider', 'logfile')
        handler = logging.handlers.RotatingFileHandler(logfileName)  # 实例化handler
        formatter = logging.Formatter('%(asctime)s - %(message)s')  # 实例化formatter
        handler.setFormatter(formatter)  # 为handler添加formatte
        cls.logger = logging.getLogger('tst')  #  #日志文件,获取名为tst的logger
        cls.logger.addHandler(handler)  # 为logger添加handler
        cls.logger.setLevel(logging.DEBUG)
        cls.redisList = RedisList(cls.Name(), redishost=redisIp) # redis队列
        print 'finish init %s' % cls.Name()

    @classmethod
    def Name(cls):
        return cls.__name__

    @staticmethod
    def Priority():
        return 10

    '''
        写日志文件
    '''
    @classmethod
    def IOStage(cls, data):
        #print "%s: %s" % (cls, data)
        master_LogCmd.logger.debug(data)

    @classmethod
    def CPUStage(cls, data):
        pass

    @classmethod
    def WriteTaskData(cls, data):
        cls.redisList.rpush(data)

    @classmethod
    def ReadTaskData(cls):
        return cls.redisList.lpop()
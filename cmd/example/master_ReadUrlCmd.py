#encoding=utf-8
import sys
import time
import os
from slaver_ScripyCmd import slaver_ScripyCmd
sys.path.append('../common')
from DataStore import RedisHash, RedisList

'''
    管理待抓取url任务：从本地文件读入待抓取url，写入redis中“url抓取任务”的队列
'''
class master_ReadUrlCmd():
    FrameInfo = None
    RunTime = None
    DataPath = None
    redisList = None
    StartTime = time.time()
    slaverScripyCmd = None

    @classmethod
    def Init(cls, config):
        redisIp = config.get('redis', 'redis')
        master_ReadUrlCmd.FrameInfo = RedisHash('FrameInfo', redishost = redisIp)
        master_ReadUrlCmd.RunTime   = 'RunTime'
        master_ReadUrlCmd.DataPath  = config.get("spider", "DataSrc").strip()
        master_ReadUrlCmd.redisList = RedisList(master_ReadUrlCmd.Name(), redishost=redisIp)
        slaver_ScripyCmd.Init(config)
        #触发任务
        master_ReadUrlCmd.WriteTaskData(' ')
        print 'finish init %s' % cls.Name()

    @classmethod
    def Name(cls):
        return cls.__name__

    @staticmethod
    def Priority():
        return 10

    @classmethod
    def IOStage(cls, data):
        for file in os.listdir(master_ReadUrlCmd.DataPath):
            path = os.path.join(master_ReadUrlCmd.DataPath, file)
            with open(path, 'r') as f:
                for url in f.readlines():
                    if not url.startswith('http://'):
                        url = 'http://' + url
                    url = url.strip()
                    print url
                    slaver_ScripyCmd.WriteTaskData(url)

                    #抓取队列中大于1000个url则休眠，防止redis内存过大
                    while slaver_ScripyCmd.redisList.llen() >= 1000:
                        master_ReadUrlCmd.FrameInfo.hset(master_ReadUrlCmd.RunTime, (time.time() - master_ReadUrlCmd.StartTime) / 60)
                        time.sleep(2)

        master_ReadUrlCmd.FrameInfo.hset(master_ReadUrlCmd.RunTime, (time.time() - master_ReadUrlCmd.StartTime) / 60)
        #再次触发任务
        #master_ReadUrlCmd.WriteTaskData(' ')

        return None

    @classmethod
    def CPUStage(cls, data):
        return ''

    @classmethod
    def WriteTaskData(cls, data):
        cls.redisList.rpush(data)

    @classmethod
    def ReadTaskData(cls):
        return cls.redisList.lpop()
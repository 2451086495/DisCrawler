#encoding=utf-8
import sys
import time
import signal
import os
import socket
import ConfigParser

sys.path.append('common')
from ScheTaskManager import TaskLoad
from IniFile import IniFile
from DataStore import RedisList, RedisHash, FlushRedis
from Framework import StartCrawlerFramework

SOCKET = None

#接收ctrl+c信号以优雅的退出进程
bRunning = True

def CtrlCHandle(sig, frame):
    print 'exit'
    global bRunning
    bRunning = False

#入参解析
def ParaseArgs():
    if len(sys.argv) != 5:
        print "Usage: %s [master|slaver] scripyProcCnt scripythreadCnt parseStorePoc" % sys.argv[0]
        sys.exit()

    if sys.argv[1] != 'master' and sys.argv[1] != 'slaver':
        print 'parameter 1 should be [master] or [slaver]'
        sys.exit()

    if not str(sys.argv[2]).isdigit():
        print 'parameter scripyProcCnt should be digital'
        sys.exit()

    if not str(sys.argv[3]).isdigit():
        print 'parameter scripythreadCnt should be digital'
        sys.exit()

    if not str(sys.argv[4]).isdigit():
        print 'parameter parsePoc should be digital'
        sys.exit()

    return sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])

def InitMaster(config):
    #通过端口bind保证master脚本单例运行
    try:
        global SOCKET
        SOCKET = socket.socket()
        SOCKET.bind((socket.gethostname(), 60123))
    except:
        print "instance is running..."
        sys.exit(0)

    redisIp = config.get('redis', 'redis')
    FlushRedis(redisIp)

    #初始化redis中管理爬虫状态的hash
    FrameInfo = RedisHash('FrameInfo', redishost=redisIp)
    FrameInfo.hset('handleCnt', '0')


if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf-8')

    # 注册中断信号处理函数，响应Ctrl + C
    signal.signal(signal.SIGTERM, CtrlCHandle)
    signal.signal(signal.SIGINT, CtrlCHandle)

    #解析入参
    role, IOProcCnt, IOThreadCnt, CPUProcCnt = ParaseArgs()

    #启动主框架
    childProcPid = StartCrawlerFramework(IOProcCnt, IOThreadCnt, CPUProcCnt)

    #读入配置文件
    config = ConfigParser.ConfigParser()
    config.read('./spider.ini')

    #根绝启动的角色加载相应任务
    print '----Start %s----' % role
    if role == 'master':
        InitMaster(config)
    TaskLoad(role, config)

    #休眠，
    while bRunning:
        time.sleep(10)

    #杀死各个进程，退出
    for pid in childProcPid:
        os.popen('kill -9 %d' % pid)
    print 'exit'

#encoding=utf-8
import multiprocessing
import threading
import os
import time
from ScheTaskManager import TaskManager

'''
    处理IO密集型任务的线程
'''
class ScripThread(threading.Thread):
    def __init__(self, OutPutProcQue, Name):
        threading.Thread.__init__(self)
        self.OutputProcQue = OutPutProcQue
        self.Scripying = False
        self.Name = Name

    '''
        从任务调度管理器中提取任务和数据并执行，如果成功则将任务和数据放入到CPU密集型进程中执行
    '''
    def run(self):
        #print 'start ScripyThread %s' % (self.Name)
        while True:
            for (data, task) in TaskManager.GetTask():
                self.Scripying = True
                data = task.IOStage(data)
                if data != None:
                    self.OutputProcQue.put((data, task))
                self.Scripying = False
            time.sleep(0.08)

    def IsScripying(self):
        return self.Scripying

'''
    处理CPU密集型任务的进程
'''
class ParaseStoreProc(multiprocessing.Process):
    def __init__(self, OutPutProcQue, Name):
        multiprocessing.Process.__init__(self)
        self.OutPutProcQue = OutPutProcQue
        self.Name = Name
        self.Status = False

    def run(self):
        print 'start ParaseStoreProc %s, pid %d' % (self.Name, os.getpid())
        while True:
            (data, task) = self.OutPutProcQue.get()
            self.Status = True
            task.CPUStage(data)
            self.Status = False

    def IsRuning(self):
        return self.Status

def ScrayWorker(scrapyThreadCnt, que):
    for i in range(scrapyThreadCnt):
        thread = ScripThread(que, str(i))
        thread.start()
    while True:
        time.sleep(10)

'''
    功能：启动主框架
    参数：
        IOProcCnt：指定处理IO密集型任务的进程数
        IOThreadCnt：指定每个IO密集型进程下的线程数量
        CPUProcCnt：指定处理CPU密集型任务的进程数
'''
def StartCrawlerFramework(IOProcCnt = 1, IOThreadCnt = 1, CPUProcCnt = 1):
    que = multiprocessing.Queue()
    childProcPid = []
    for i in range(IOProcCnt):
        p = multiprocessing.Process(target=ScrayWorker, args=(IOThreadCnt,que))
        p.start()
        childProcPid.append(p.pid)

    for i in range(CPUProcCnt):
        p = ParaseStoreProc(que, str(i))
        p.start()
        childProcPid.append(p.pid)

    childProcPid.append(os.getpid())
    return childProcPid

#Scripyer('a')
'''
if __name__ == '__main__':
    multiprocessing.freeze_support()
    redisname = 'test'
    #CrawlerHandler.RegistScrip('300', Domainsrc.Scripy, Domainsrc.Parse, Domainsrc.Store)
    r, scripyThreads, parseStoreProcs = Scripyer(redisname)
    r.lpush('300|http://beian.links.cn/beiansitemap/0_1.html')
    while True:
        time.sleep(2)
'''
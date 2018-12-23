#encoding=utf-8
import os
import pyinotify
from multiprocessing import Manager
import sys
import threading
import json

class TaskManager(object):
    '''
        任务调度管理器，字典数据结构，value: List(Task)，任务的List； key: 任务队列的优先级
    '''
    ScheduleTaskDict = dict()

    '''
        任务必须定义的方法，缺一不可，各接口说明如下：
    '''
    TaskMethod = ['Init',          #类方法，入参：配置文件对象，功能：初始化任务；在redis中为本任务创建FIFO队列
                  'Name',          #类方法，入参：无；  出参：任务名称字符串； 功能：唯一标识任务名称，以及任务在redis中的List名称
                  'Priority',      #类静态方法，入参：无；  出参：整型优先级值；  功能：设定任务优先级，值越低优先级越大
                  'IOStage',       #类方法，入参：任务框架第一阶段执行必要的数据，各任务自定义； 出参：失败返回None，成功返回第二阶段必要的数据；
                                            #功能：处理网络IO密集型任务，在爬虫场景主要实现网络抓取
                  'CPUStage',      #类方法，入参：任务框架第二阶段执行必要的数据，各任务自定义； 出参：无；
                                            #功能：处理CPU密集型任务，目前主要基于caffe分析不良图片
                  'WriteTaskData',  #类方法，入参：任务执行必要的数据；  出参：无；   功能：通过往任务队列放入数据来触发任务
                  'ReadTaskData'    #类方法，入参：无；  出参：任务执行必须的数据；   功能：从任务队列读出数据，为后续任务调度提供数据
                  ]

    def __getitem__(self, method):
        if method in self.TaskMethod:
            return self.__getattribute__(method)
        print 'Not Support Method %s' % method
        return None

    '''
        功能：在任务调度管理器中移除任务task
    '''
    @classmethod
    def RemoveTask(cls, task):
        for (priority, taskList) in cls.ScheduleTaskDict.items():
            if not task in taskList:
                continue

            taskList.remove(task)
            if len(cls.ScheduleTaskDict[task.Priority()]) == 0:
                del cls.ScheduleTaskDict[task.Priority()]
            print 'remove Task %s' % task.Name()
            return

    '''
        功能：在任务调度管理器中添加任务task
    '''
    @classmethod
    def AddTask(cls, task):
        cls.RemoveTask(task)
        if not cls.ScheduleTaskDict.has_key(task.Priority()):
            cls.ScheduleTaskDict[task.Priority()] = []
        cls.ScheduleTaskDict[task.Priority()].append(task)
        print 'Add Task %s\n' % task.Name()

    '''
        功能：解析任务文件，加入任务调度管理器
        参数：
            role：角色（master/slaver）
            TaskFile：任务文件名
            config：配置文件对象        
    '''
    @classmethod
    def TaskFile2Task(cls, role, TaskFile, config):
        if not TaskFile.endswith('Cmd.py') or not TaskFile.startswith(role):
            return

        pluginName = os.path.splitext(TaskFile)[0]
        print 'pluginName:%s' % pluginName
        plugin = __import__("%s" % pluginName, fromlist=[pluginName])  # 相当于import dir.modle
        cmdCls = getattr(plugin, pluginName)  # getattr 用于从plugin模块下获得pluginName成员

        for method in cls.TaskMethod:
            if not cmdCls.__dict__.has_key(method):
                print 'laod failed: %s should compele %s' % (cmdCls.__name__, method)
                return

        cmdCls.Init(config)
        cls.AddTask(cmdCls)

    '''
        功能：按照任务优先级从高到低，在redis中遍历队列，提取队列数据，返回任务和数据的元祖
    '''
    @classmethod
    def GetTask(cls):
        tasts = []
        for (priority, tastList) in cls.ScheduleTaskDict.items():
            for task in tastList:
                data = task.ReadTaskData()
                if data != None:
                    tasts.append((data, task))
            if len(tasts) != 0:
                break
        return tasts

'''
    实现对任务文件的增、删、改进行监控，一旦任务文件有变动则重新加载任务
'''
class TaskNotify(pyinotify.ProcessEvent):
    def __init__(self, role, config):
        self.role = role
        self.config = config

    '''
        新增任务回调函数
    '''
    def process_IN_CREATE(self, event):
        print "CREATE Task:", event.pathname
        TaskManager.TaskFile2Task(self.role, event.pathname.split('/')[-1], self.config)

    '''
        删除任务回调函数
    '''
    def process_IN_DELETE(self, event):
        print "DELETE Task:", event.pathname
        TaskManager.TaskFile2Task(self.role, event.pathname.split('/')[-1], self.config)

    '''
        修改任务回调函数
    '''
    def process_IN_MODIFY(self, event):
        print "MODIFY Task:", event.pathname
        TaskManager.TaskFile2Task(self.role, event.pathname.split('/')[-1], self.config)

    '''
        功能：注册一个监控任务
        参数：
            dir：被监控目录
    '''
    @staticmethod
    def RegisterNotify(dir, role, config):
        # watch manager
        print dir
        wm = pyinotify.WatchManager()
        wm.add_watch(dir, pyinotify.IN_DELETE | pyinotify.IN_CREATE | pyinotify.IN_MODIFY, auto_add=True, rec=True)

        # notifier
        notifier = pyinotify.Notifier(wm, TaskNotify(role, config))
        #notifier.loop()
        while True:
            try:
                notifier.process_events()
                if notifier.check_events():
                    notifier.read_events()
            except KeyboardInterrupt:
                notifier.stop()
                break

'''
    功能：根绝启动的角色（mater/slaver）在cmd目录下加载相应的任务
    参数：
        role:角色（master/slaver）
        config:配置文件对象，供任务初始化使用
'''
def TaskLoad(role, config):
    cmdPath = 'cmd'
    sys.path.append(cmdPath)

    for fileName in os.listdir(cmdPath):
        TaskManager.TaskFile2Task(role, fileName, config)

    t = threading.Thread(target=TaskNotify.RegisterNotify, args=('./cmd', role, config, ))
    t.start()
    return t


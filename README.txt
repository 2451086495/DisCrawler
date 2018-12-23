一、功能：
	python实现的分布式任务调度系统，以redis作为broker，以redis中的任务数据驱动任务调度。
	本系统将任务分为IO密集型任务和CPU密集型任务，对于IO密集型任务放在多线程执行，对于CPU密集型任务放在多进程中执行。以规避python的GIL锁带来的性能限制
	
	
二、目录：
	cmd: 实现任务（cmd/example 为任务样文件）
	common：框架文件
	DisCrawler.py ： 启动文件

	
三、任务类实现：
	在cmd下实现，任务分为两类，master类和slaver类
	文件名：master类为master_xxx.py，slaver类为slaver_xxx.py
	任务接口：
	
		from DataStore import RedisList
		class master_xxx():
			''' 
					说明：任务初始化接口
					入参：
					config : 解析完spider.ini配置文件后的ConfigParser对象
			'''
			@classmethod
    	def Init(cls, config):
    			cls.redisList = RedisList(cls.Name(), redishost=redisIp) # redis队列
					pass
			
			'''
					说明：配置任务名称接口
					返回值：任务名称
			'''
			@classmethod
   	  def Name(cls):
          return cls.__name__
			
			'''
					说明：配置优先级接口，值越低优先级越高。对于redis中存在多种任务的数据中，根据优先级高低取数据执行。
					返回值：任务优先级，整形
			'''
      @staticmethod
      def Priority():
          pass
          
      '''
         说明：IO接口，在多线程中执行
         入参：
         		data:从redis中取出的数据
         返回值：None表示处理完成
         				 非None表示进一步到CPU接口中执行的数据         
	    '''
	    @classmethod
	    def IOStage(cls, data):
	        #print "%s: %s" % (cls, data)
	        master_LogCmd.logger.debug(data)
	    
	    '''
	    	 说明：CPU接口，在多进程中执行
	    	 入参；
	    	 		data：从IO接口中得到的数据
	    '''
	  	@classmethod
    	def CPUStage(cls, data):
        	pass
        	
      '''
      	 说明：将data写入到redis队列中，触发其他任务的执行
      '''
		  @classmethod
      def WriteTaskData(cls, data):
          cls.redisList.rpush(data)

			'''
				 说明：从redis中读取本任务的数据，接下里准备调IOStage
			'''
	    @classmethod
	    def ReadTaskData(cls):
	        return cls.redisList.lpop() 
	        
四、启动：
 启动master类任务：	python  DisCrawler.py  master 执行IO接口的进程数  IO进程下的线程数  执行CPU接口的进程数 
 启动slaver类任务： python  DisCrawler.py  slaver 执行IO接口的进程数  IO进程下的线程数  执行CPU接口的进程数
 slaver可在多个逻辑节点上执行
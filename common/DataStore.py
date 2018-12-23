#encoding=utf-8
import sqlite3
import multiprocessing
import redis
import pg

class Singleton(object):
    def __new__(cls,*args,**kwargs):
        if not hasattr(cls,'_inst'):
            cls._inst=super(Singleton,cls).__new__(cls,*args,**kwargs)
        return cls._inst

def FlushRedis(redishost='localhost', redisport=6379, redisdb=0):
    r = redis.Redis(host=redishost, port=redisport, db=redisdb)
    r.flushdb()

# 封装redis的list数据结构
class RedisList():
    def __init__(self, redisname, redishost='localhost', redisport=6379, redisdb=0):
        self.r = redis.Redis(host=redishost, port=redisport, db=redisdb)
        self.name = redisname

    def lpush(self, data):
        self.r.lpush(self.name, data)

    def rpush(self, data):
        self.r.rpush(self.name, data)

    def rpop(self):
        return self.r.rpop(self.name)

    def lpop(self):
        return self.r.lpop(self.name)

    def llen(self):
        return self.r.llen(self.name)

    def delete(self):
        self.r.delete(self.name)


#封装redis的hash数据结构
class RedisHash():
    def __init__(self, redisname, redishost = 'localhost', redisport = 6379, redisdb = 0):
        self.r = redis.Redis(host = redishost, port = redisport, db = redisdb)
        self.name = redisname

    def hset(self, key, val):
        self.r.hset(self.name, key, val)

    def hmset(self, dicts): #将字典数据dicts批量写入hash
        self.r.hmset(self.name, dicts)

    def hget(self, key):
        return self.r.hget(self.name, key)

    def hkeys(self): #以list返回hash中所有key
        return self.r.hkeys(self.name)

    def hvals(self): #以list返回hash中所有val
        return self.r.hvals(self.name)

    def hgetall(self): #以dict返回hash中所有（key, val）
        return self.r.hgetall(self.name)

    def hexists(self, key):
        return self.r.hexists(self.name, key)

    def hlen(self):
        return self.r.hlen(self.name)

    def hdel(self, key):
        self.r.hdel(self.name, key)

    def delete(self):
        self.r.delete(self.name)

#封装redis的set数据结构
class RedisSet():
    def __init__(self, redisname, redishost = 'localhost', redisport = 6379, redisdb = 0):
        self.r = redis.Redis(host = redishost, port = redisport, db = redisdb)
        self.name = redisname

    def sadd(self, data):  #返回添加成功的数量
        return self.r.sadd(self.name, data)

    def scard(self):  #返回集合中元素的数量
        return self.r.scard(self.name)

    def sismember(self, data): #判断data是否为集合的成员
        return self.r.sismember(self.name, data)

    def srem(self, data): #删除指定元素
        self.r.srem(self.name, data)

    def spop(self): #移除并返回集合中的一个随机元素
        return self.r.spop(self.name)

    def delete(self):
        self.r.delete(self.name)

class Sqlite():
    def __init__(self, dbname, lock = multiprocessing.Lock()):
        self.conn = sqlite3.connect(dbname, check_same_thread=False)
        self.conn
        self.conn.text_factory = str
        self.sqlite3Cmd = self.conn.cursor()
        self.Lock = lock

    def __del__(self):
        self.conn.close()

    def RunCmd(self, CmdList):
        if self.Lock.acquire():
            for Cmd in CmdList:
                try:
                    self.sqlite3Cmd.execute(str(Cmd).encode('utf8'))
                except BaseException, e:
                        pass
            self.conn.commit()
            self.Lock.release()

    def RunSelect(self, Cmd):
        RetList = []
        if self.Lock.acquire():
            for Ret in self.sqlite3Cmd.execute(Cmd):
                RetList.append(Ret)
            self.Lock.release()
            return RetList

class GP():
    def __init__(self, db, host, user, pwd):
        # 连接数据库
        try:
            self.pgdb_conn = pg.connect(dbname=db, host=host, user=user, passwd=pwd)
        except Exception, e:
            print "conntect postgre database failed, ret = %s" % e.args[0]
            return

    def WriteCmd(self, sql_desc):
        try:
            self.pgdb_conn.query(sql_desc)
        except Exception, e:
            print "run %s failed, ret = %s" % (sql_desc, e.args[0])
            return False
        return True

    def ReadCmd(self, sql_desc):
        try:
            dictresult = pgdb_conn.query(sql_desc).dictresult()
        except Exception, e:
            print "run %s failed, ret = %s" % (sql_desc, e.args[0])
            dictresult = None
        return dictresult


from GBaseConnector import connect, GBaseError
class GBASE():
    # 连接
    def GBaseConnect(self, ip, db='zxvmax', user='gbase', pwd='ZXvmax_2017', port=5258, connect_timeout=600):
        cfg = {'host': ip, 'port': port, 'database': db, 'user': user, 'passwd': pwd, 'connect_timeout':connect_timeout}
        self.conn = connect()
        self.conn.connect(**cfg)
        self.cur = self.conn.cursor()
        self.row = 0
        self.col = 0

    #读入sql文件执行
    def GBaseCmdFromeFile(self, filePath):
        with open(filePath, 'r') as f:
            content = f.read()
            for sql in content.split(';')[:-1]:
                sql = sql + ';'
                self.GBaseCmd(sql)

    # zhixing
    def GBaseSelect(self, cmd, catchErr=0):
        cmd = cmd.encode('utf-8')
        if catchErr:
            try:
                self.cur.execute(cmd)
                row = self.cur.fetchone()
                self.col = len(row)
                rows = []
                while row != None:
                    rows.append(row)
                    row = self.cur.fetchone()
                self.row = len(rows)
            except BaseException as e:
                print e
                return []
        else:
            self.cur.execute(cmd)
            row = self.cur.fetchone()
            self.col = len(row)
            rows = []
            while row != None:
                rows.append(row)
                row = self.cur.fetchone()
            self.row = len(rows)
        return rows

    def GBaseCmd(self, cmd, catchErr=0):
        cmd = cmd.encode('utf-8')
        if catchErr:
            try:
                self.cur.execute(cmd)
            except BaseException as e:
                print e
        else:
            self.cur.execute(cmd)

    def GBaseGetRowCnt(self):
        if hasattr(self, 'row'):
            return self.row
        else:
            return 0

    def GBaseGetColCnt(self):
        if hasattr(self, 'col'):
            return self.col
        else:
            return 0

    def GBaseClose(self):
        self.cur.close()
        self.conn.close()


'''
#测试代码

test = Sqlite('test.db', threading.Lock())
cmd = ['drop table if exists COMPANY',
       'CREATE TABLE if not exists COMPANY (ID INT PRIMARY KEY NOT NULL,  NAME TEXT NOT NULL,  AGE INT NOT NULL, ADDRESS CHAR(50), SALARY REAL);',
       "INSERT INTO COMPANY (ID,NAME,AGE,ADDRESS,SALARY) VALUES (1, '%s', 32, 'California', 20000.00 )" % ('你好'),
       "INSERT INTO COMPANY (ID,NAME,AGE,ADDRESS,SALARY) VALUES (2, '好', 25, 'Texas', 15000.00 )"]
print type('你好'.decode('utf8'))
print cmd[2]
test.RunCmd(cmd)
cursor = test.RunSelect("SELECT id, name, address, salary  from COMPANY")
for row in cursor:
   print "ID = ", row[0]
   print "NAME = ", row[1]
   print "ADDRESS = ", row[2]
   print "SALARY = ", row[3], "\n"
test.Close()
'''
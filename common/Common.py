# coding: utf-8
import os
import shutil
from urlparse import urljoin
from urlparse import urlunparse
from posixpath import normpath
from urlparse import urlparse
import requests
import re
import StringIO
import random
#from requests.packages.urllib3.exceptions import InsecureRequestWarning
import subprocess
from multiprocessing import Process,Lock
import multiprocessing
import sys
import chardet

# 禁用安全请求警告
#requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

class Singleton(object):
    def __new__(cls,*args,**kwargs):
        if not hasattr(cls,'_inst'):
            cls._inst=super(Singleton,cls).__new__(cls,*args,**kwargs)
        return cls._inst

class Common(Singleton):
    @staticmethod
    def Post(url, data, headers):
        contenttype = None
        dwLen = 0
        for key, val in data.items():
            dwLen += len(key) + len(val)
        dwLen += 2 * len(data) - 1
        headers['Content-Length'] = str(dwLen)

        try:
            r = requests.post(url, data=data, headers=headers)
            r.raise_for_status()  # 如果响应状态码不是 200，就主动抛出异常
        except requests.RequestException as e:
            print e
            return ""

        if "Content-Type" in r.headers.keys():
            contenttype = r.headers["Content-Type"]
        elif "content-type" in r.headers.keys():
            contenttype = r.headers["content-type"]

        content = r.content
        if contenttype.find("text/html") != -1:
            content = r.content.decode(r.encoding, 'ignore').encode('utf8', 'ignore')

        return content

    @staticmethod
    def is_uchar(text):
        for uchar in text:
            # is chinese
            if uchar >= u'\u4e00' and uchar <= u'\u9fa5':
                return True
            # is digital
            if uchar >= u'\u0030' and uchar <= u'\u0039':
                return True
            # ia alphabat
            if (uchar >= u'\u0041' and uchar <= u'\u005a') or (uchar >= u'\u0061' and uchar <= u'\u007a'):
                return True
            # is puncate
            if uchar in ('-', ',', '.', '>', '?', '<', '/', ':', ';', '\'', '\"', ']', '[', '}', '{', '+', '=', '-', '_',')', '(', '*','&', '^', '%', '$', '#', '@', '!', '~', '`'):
                return True
        return False

    @staticmethod
    def GetContentByUrl(url, useragent = 'Mozilla / 5.0(Windows NT 6.1; WOW64) AppleWebKit / 537.36(KHTML, like Gecko) Chrome / 53.0.2785.104 Safari / 537.36    Core / 1.53.3226 .400 QQBrowser / 9.6 .11681.400', headers = None):
        if headers == None:
            headers = {'User-Agent': useragent}

        contenttype = None
        try:
            r = requests.get(url, headers=headers, verify=False, timeout=90)
            r.raise_for_status()  # 如果响应状态码不是 200，就主动抛出异常
        except requests.RequestException as e:
            print "GetUrlFaild: %s\n" % str(e)
            return None, None

        if "Content-Type" in r.headers.keys():
            contenttype = r.headers["Content-Type"]
        elif "content-type" in r.headers.keys():
            contenttype = r.headers["content-type"]

        content = r.content
        if contenttype and contenttype.find("text/html") != -1:
            if len(requests.utils.get_encodings_from_content(r.content)) != 0:
                encoding = requests.utils.get_encodings_from_content(r.content)[0]
            else:
                encoding = r.encoding
            content = r.content.decode(encoding, 'ignore').encode('utf8', 'ignore')

        r.close()
        return contenttype, content

    @staticmethod
    def RmDir(Path):
        if os.path.exists(Path):
            shutil.rmtree(Path)

    @staticmethod
    def MkDir(Path):
        if not os.path.exists(Path):
            os.makedirs(Path)

    @staticmethod
    def UrlJoin(base, url):
        url1 = urljoin(base, url)
        arr = urlparse(url1)
        path = normpath(arr[2])
        return urlunparse((arr.scheme, arr.netloc, path, arr.params, arr.query, arr.fragment))

    @staticmethod
    def Copy(SrcPath, DstPath):
        if not os.path.exists(SrcPath):
            return
        if not os.path.exists(DstPath):
            os.makedirs(DstPath)
        shutil.copy(SrcPath, DstPath)

    @staticmethod
    def SaveContent(Content, Path, mode = 'w+'):
        FileObj = open(Path, mode)
        try:
            FileObj.write(Content)
        finally:
            FileObj.close()

    @staticmethod
    def ConvWebp2JPEG(raw_img):
        name = random.randint(0, 10000000)
        SrcName = str(name) + '.webp'
        DstName = str(name) + '.png'
        FileObj = open(SrcName, 'w+')
        FileObj.write(raw_img)
        FileObj.close()
        cmd = 'dwebp %s -o %s' % (SrcName, DstName)
        out = subprocess.Popen(cmd, shell=True, stderr=subprocess.PIPE)
        if 'failed' in out.stderr.read():
            os.remove(SrcName)
            return ''
        FileObj = open(DstName, 'r')
        raw_img = FileObj.read()
        FileObj.close()
        os.remove(DstName)
        os.remove(SrcName)
        return raw_img

    '''将当前进程fork为一个守护进程
       注意：如果你的守护进程是由inetd启动的，不要这样做！inetd完成了
       所有需要做的事情，包括重定向标准文件描述符，需要做的事情只有chdir()和umask()了
    '''
    @staticmethod
    def daemonize(stdin='/dev/null', stdout='/dev/null', stderr='/dev/null'):
        # 重定向标准文件描述符（默认情况下定向到/dev/null）
        try:
            pid = os.fork()
            # 父进程(会话组头领进程)退出，这意味着一个非会话组头领进程永远不能重新获得控制终端。
            if pid > 0:
                print 'parent'
                sys.exit(0)  # 父进程退出
        except OSError, e:
            sys.stderr.write("fork #1 failed: (%d) %s\n" % (e.errno, e.strerror))
            sys.exit(1)
        # 从母体环境脱离
        #os.chdir("/")  # chdir确认进程不保持任何目录于使用状态，否则不能umount一个文件系统。也可以改变到对于守护程序运行重要的文件所在目录
        os.umask(0)  # 调用umask(0)以便拥有对于写的任何东西的完全控制，因为有时不知道继承了什么样的umask。
        os.setsid()  # setsid调用成功后，进程成为新的会话组长和新的进程组长，并与原来的登录会话和进程组脱离。

        # 执行第二次fork
        try:
            pid = os.fork()
            if pid > 0:
                sys.exit(0)  # 第二个父进程退出
        except OSError, e:
            sys.stderr.write("fork #2 failed: (%d) %s\n" % (e.errno, e.strerror))
            sys.exit(1)

        # 进程已经是守护进程了，重定向标准文件描述符
        for f in sys.stdout, sys.stderr: f.flush()
        si = open(stdin, 'r')
        so = open(stdout, 'a+')
        se = open(stderr, 'a+', 0)
        '''
        os.dup2(si.fileno(), sys.stdin.fileno())  # dup2函数原子化关闭和复制文件描述符
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        '''
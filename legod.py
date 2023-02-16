

###############
# @Author: 6yy66yy
# @Date: 2021-07-26 16:44:05
# @LastEditors: 6yy66yy
# @LastEditTime: 2023-01-20 01:30:42
# @FilePath: \legod-auto-pause\legod.py
# @Description: 雷神加速器时长自动暂停，暂停程序，可以独立运行。
###############
from concurrent.futures import ThreadPoolExecutor
import requests
import json
import os
import configparser
# from hyper.contrib import HTTP20Adapter
import win32com.client
import time
# import logging #log记录组件，目前没啥用
import hashlib #md5 加密
from sys import gettrace

class legod(object):
    def __init__(self,first,filedir='None'):
        print('''
***************************************************\n
*                                                 *\n
*                                                 *\n
*              雷神加速器自动暂停工具v2.2         *\n
*                     正在运行                    *\n
*                   作者:6yy66yy                  *\n
*                                                 *\n
***************************************************\n
''')
        self.url='https://webapi.leigod.com/api/user/pause'
        self.header = {
                # ':authority': 'webapi.nn.com',
                # ':method':'POST',
                # ':path':'/api/user/pause',
                # ':scheme': 'https',
                'User-Agent':'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.96 Safari/537.36 Edg/88.0.705.53',
                'Content-Type': "application/x-www-form-urlencoded; charset=UTF-8",
                'Connection':"keep-alive",
                'Accept': "application/json, text/javascript, */*; q=0.01",
                'Accept-Encoding': "gzip, deflate, br",
                'Accept-Language': "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
                'DNT': "1",
                'Referer': 'https://www.legod.com/',
                'Sec-Fetch-Dest': 'empty',
                'Sec-Fetch-Mode': 'cors',
                'Sec-Fetch-Site': 'same-site'
                        }
        self.Dir=filedir
        self.stopp=False
        self.conf=self.load()

    def genearteMD5(self,str):
        '''
        创建md5对象
        '''
        if isDebug:#debug模式下，在config中填入md5加密后的密码。todo:接下来考虑如何加密存储密码，保证数据安全。目前想法:输入后自动替换md5
            return str
        hl = hashlib.md5()
        # Tips
        # 此处必须声明encode
        # 否则报错为：hl.update(str)    Unicode-objects must be encoded before hashing
        hl.update(str.encode(encoding='utf-8'))
        return hl.hexdigest()

    def login(self,uname,password):
        '''
        登录函数，当token无效的时候调用登录函数获取新的token

        Return:
            成功:True+新的token
            失败:False+错误信息
        '''
        if(uname=="" or password==""):
            return False
        token=""
        body={
            'username':uname,
            'password':self.genearteMD5(password),
            'user_type':'0',
            'src_channel':'guanwang',
            'country_code':86,
            'lang':'zh_CN',
            'region_code':1,
            'account_token':'null'}
        r = requests.post("https://webapi.leigod.com/api/auth/login",data=body,headers = self.header)
        msg=json.loads(r.text)
        if(msg['code']==0):
            token=msg['data']['login_info']['account_token']
            return True,token
        else:
            print(msg['msg'])
            return False,msg['msg']

    def check_exsit(self):
        '''
        查询进程中是否存在游戏列表中的进程
        '''
        WMI = win32com.client.GetObject('winmgmts:')
        for i in self.applist:
            processCodeCov = WMI.ExecQuery('select * from Win32_Process where Name like "%{}%"'.format(i+'.exe'))
            if len(processCodeCov) > 0:
                return '检测到{}'.format(i)
        return False

    def pause(self):
        '''
        暂停加速,调用官网api

        Returns:
            官网返回的信息
        '''
        payload={
            "account_token":self.conf.get("config","account_token"),
            "lang":"zh_CN"}
        # sessions=requests.session()
        # sessions.mount('https://webapi.nn.com', HTTP20Adapter())
        # r =sessions.post(url,data=payload,headers = header)
        i=0
        token=''
        tmp_msg=''
        while(i<3):
            i+=1
            if(self.uname=="" or self.password=="" and self.conf.get("config","account_token") == ""):
                print("没填用户名密码或者是token无效,请填写后重启工具")
                tmp_msg="没填用户名密码或者是token无效,请填写后重启工具"
                break
            r = requests.post(self.url,data=payload,headers = self.header)
            if r.status_code==403:
                try:
                    token = self.login(self.uname,self.password)
                except:
                    print("未知错误，可能是请求频繁或者是网址更新")
                    tmp_msg="未知错误，可能是请求频繁或者是网址更新"
                continue
            msg=json.loads(r.text)
            print("暂停结果：",msg['msg'])
            if(msg['code']!=400006):
                tmp_msg=msg['msg']
                return tmp_msg
            else:
                suces,token = self.login(self.uname,self.password)
                if suces:
                    self.conf.set('config','account_token',token)
                    self.conf.write(open(self.configPath,'w',encoding='utf_8'))
                    print("原token失效,已写入新的token")
                    tmp_msg="原token失效,已写入新的token"
                    payload['account_token']=token
                else:
                    tmp_msg=token
                    break
        return tmp_msg
    def load(self):
        '''
        加载配置文件

            文件名:configfile(在文件头定义,默认为config.ini)

        Returns:
            conf元组
        '''
        # 当前文件路径
        if __name__ == '__main__':
            proDir = os.path.dirname(sys.argv[0])
        elif self.Dir != 'None':
            proDir = self.Dir
        else:
            e=Exception('调用此函数需要导入主函数所在路径')
            raise e
        # global appname,sec,uname,password,update,account_token,configPath,lepath,conf # 大概没用注释一下
        if isDebug:     # 在当前文件路径下查找.ini文件
            print("debug模式开启,密码不加密传输")
            print("当前加载配置为"+configfile)
        self.configPath = os.path.join(proDir, configfile)
        self.conf = configparser.ConfigParser()

        # 读取.ini文件
        self.conf.read(self.configPath,encoding='UTF-8-sig')
        # 捕获异常并打印错误信息
        try:
            # get()函数读取section里的参数值
            appname = self.conf.get('config','games').replace("，",",") # 先对字符串中的中文逗号进行替换
            self.sec = int(self.conf.get('config','looptime'))          # 允许游戏关闭的时间（在此时间内切换游戏不会关闭加速器）单位：秒
            self.uname=self.conf.get("config","uname")                  # 用户名/手机号
            self.password=self.conf.get("config","password")            # 密码
            self.update=int(self.conf.get("config","update"))           # 检测时间，多少秒检测一次程序
            self.lepath=self.conf.get("config","path").strip('"')       # 雷神路径,替换掉外部的\"

            self.applist = appname.split(',')                           # 英文逗号分割成列表
            print("目前检测游戏列表:{}".format(appname))

            # account_token=login(self.uname,self.password)
            account_token = self.conf.get("config","account_token")
            return self.conf
        except Exception as e:
            print("文件加载地址为"+self.configPath)
            print("配置文件加载失败,请检查配置文件是否正确")
            print(e)
    def detection(self):
        sw=1
        while 1==1:
            game=self.check_exsit()
            if(game):
                if(sw==1):
                    print(game)
                    sw=0
            elif(sw==0):
                for i in range(1,self.sec):
                    game=self.check_exsit()
                    time.sleep(1)
                if game is False:
                    self.pause()
                sw=1
            time.sleep(self.update)
# 常量定义区
## 是否为debug模式
isDebug = True if gettrace() else False
## 配置config文件名
configfile="config.ini" if not isDebug else "config-dev.ini"

## 配置日志
# logging.basicConfig(filename='log.log')

if __name__ == '__main__': 
    t=legod(True)
    t.detection()
    
    


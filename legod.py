

###############
# @Author: 6yy66yy
# @Date: 2021-07-26 16:44:05
# @LastEditors: 6yy66yy
# @LastEditTime: 2023-03-05 19:35:49
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
import sys

class legod(object):
    def __init__(self,first,filedir='None'):
        self.version = "v2.2.1"
        self.pause_url='https://webapi.leigod.com/api/user/pause'
        self.info_url = 'https://webapi.leigod.com/api/user/info'
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
        print('''
***************************************************
*                                                 *
*                                                 *
*              雷神加速器自动暂停工具             *
*                     正在运行                    *
*                   作者:6yy66yy                  *
*                                                 *
*************************************************** 当前版本：%s'''%self.version)

    def genearteMD5(self,password):
        '''
        创建md5对象
        '''
        # 已经md5加密过的密码
        if self.md5 == '1':
            print("密码已加密,无需再次加密")
            return password
        hl = hashlib.md5()
        # Tips
        # 此处必须声明encode
        # 否则报错为：hl.update(str)    Unicode-objects must be encoded before hashing
        hl.update(password.encode(encoding='utf-8'))
        password = hl.hexdigest()
        self.conf.set('config','md5','1')
        self.conf.set('config','password',password)
        self.conf.write(open(self.configPath,'w',encoding='utf_8'))
        print("原密码已加密,已写入新的密码")
        return password

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
    
    def get_token(self,payload) -> tuple:
        '''获取并写入token到config.ini
        Returns
        --------
        :class:`bool`
           True 登录成功 False  登录失败
        :class:`str`
            登录成功返回成功msg，登录失败返回错误msg
        '''
        tmp_msg = ''
        result = self.login(self.uname,self.password)
        token = result[1]
        if result[0]:
            self.conf.set('config','account_token',token)
            self.conf.write(open(self.configPath,'w',encoding='utf_8'))
            print("原token失效,已写入新的token")
            tmp_msg="原token失效,已写入新的token"
            payload['account_token']=token
            return True,tmp_msg
        else:
            tmp_msg=token
            return False,tmp_msg
  
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
    
    def get_account_info(self) -> tuple:
        '''
        获取账号信息
        Returns
        --------
        :class:`tuple`
            (True,账号信息) or (False,错误信息)
        '''
        payload={ "account_token":self.conf.get("config","account_token"),
                "lang":"zh_CN"}
        for i in range(2):
            r = requests.post(self.info_url,data=payload,headers = self.header)
            msg=json.loads(r.text)
            # code:400006  msg: '账号未登录'说明token失效，需要重新登录获取token
            if msg['code']==400006:
                result = self.get_token(payload)
            elif(msg['code']==0):
                return True,msg['data']
                break
            else:
                return False,msg['msg']
                break
    
    def check_stop_status(self) -> bool:
        '''
        通过账号信息判断是否暂停
        0:正常,1:暂停
        '''
        status=self.get_account_info()[1]['pause_status_id']
        if(status == 1):
            return True
        else:
            return False
        
    def pause(self):
        '''
        暂停加速,调用官网api

        Returns:
            官网返回的信息
        '''
        # sessions=requests.session()
        # sessions.mount('https://webapi.nn.com', HTTP20Adapter())
        # r =sessions.post(url,data=payload,headers = header)
        i=0
        token=''
        tmp_msg=''
        while(i<3):
            i+=1
            if(self.uname=="" or self.password=="" and self.conf.get("config","account_token") == ""):
                print("没填用户名密码或者是token无效,请填写后再试")
                tmp_msg="没填用户名密码或者是token无效,请填写再试"
                break
            # 检查是否暂停，如果暂停则不再暂停
            if(self.check_stop_status()):
                tmp_msg="已经暂停"
                print(tmp_msg)
                break
            # 请求暂停
            payload={
            "account_token":self.conf.get("config","account_token"),
            "lang":"zh_CN"}
            response = requests.post(self.pause_url,data=payload,headers = self.header)
            if response.status_code==403:
                try:
                    token = self.login(self.uname,self.password)
                except:
                    print("未知错误，可能是请求频繁或者是网址更新")
                    tmp_msg="未知错误，可能是请求频繁或者是网址更新"
                continue
            msg=json.loads(response.text)
            print("暂停结果：",msg['msg'])
            if(msg['code']!=400006):
                tmp_msg=msg['msg']
                return tmp_msg
            else:
                result = self.get_token(payload)
                result,tmp_msg=result[0],result[1]
                # 获取token失败直接退出
                if not result:
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
            # print("debug模式开启,密码不加密传输")
            print("debug模式开启")
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
            self.md5 = self.conf.get("config","md5")                    # 密码是否已经md5加密
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
    
    




###############
# @Author: 6yy66yy
# @Date: 2021-07-26 16:44:05
# @LastEditors: 6yy66yy
# @LastEditTime: 2021-08-31 01:08:53
# @FilePath: \undefinedh:\资料备份\源码\Python\雷神\legod.py
# @Description: 雷神加速器时长自动暂停
###############
import requests
import json
import os
import configparser
# from hyper.contrib import HTTP20Adapter
import win32com.client
import time
import traceback
import logging
import hashlib #md5 加密

logging.basicConfig(filename='log.log')
def genearteMD5(str):
    # 创建md5对象
    hl = hashlib.md5()

    # Tips
    # 此处必须声明encode
    # 否则报错为：hl.update(str)    Unicode-objects must be encoded before hashing
    hl.update(str.encode(encoding='utf-8'))
    return hl.hexdigest()
url='https://webapi.nn.com/api/user/pause'
header = {
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
        'Referer': 'https://vip-jiasu.nn.com/',
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'same-site'
                }

def login(uname,password):
    if(uname=="" or password==""):
        return False
    token=""
    body={
        'username':uname,
        'password':genearteMD5(password),
        'user_type':'0',
        'src_channel':'guanwang',
        'country_code':86,
        'lang':'zh_CN',
        'region_code':1,
        'account_token':'null'}
    r = requests.post("https://webapi.nn.com/api/auth/login",data=body,headers = header)
    msg=json.loads(r.text)
    if(msg['code']==0):
        token=msg['data']['login_info']['account_token']
        return token
    else:
        print(msg['msg'])
        return False

def check_exsit(process_name):
    ls=process_name.split(',')
    WMI = win32com.client.GetObject('winmgmts:')
    for i in ls:
        processCodeCov = WMI.ExecQuery('select * from Win32_Process where Name like "%{}%"'.format(i+'.exe'))
        if len(processCodeCov) > 0:
            return '检测到{}'.format(i)
    return False

def pause(account_token,header):
    payload={
        "account_token":account_token,
        "lang":"zh_CN"}
    # sessions=requests.session()
    # sessions.mount('https://webapi.nn.com', HTTP20Adapter())
    # r =sessions.post(url,data=payload,headers = header)
    i=0
    token=''
    while(i<3):
        r = requests.post(url,data=payload,headers = header)
        msg=json.loads(r.text)
        if(msg['code']!=400006):
            print(msg['msg'])
            return True
        else:
            token = login(uname,password)
            if token:
                conf.set('config','account_token',token)
                conf.write(open(configPath,'w'))
                print("原token失效,已写入新的token")
                payload['account_token']=token
# 当前文件路径
proDir = os.path.split(os.path.realpath(__file__))[0]

# 在当前文件路径下查找.ini文件
configPath = os.path.join(proDir, "config.ini")
conf = configparser.ConfigParser()

# 读取.ini文件
conf.read(configPath,encoding='UTF-8')

# get()函数读取section里的参数值

appname = conf.get('config','games')
sec = int(conf.get('config','looptime'))
uname=conf.get("config","uname")
password=conf.get("config","password")
update=int(conf.get("config","update"))

print('''
        ***************************************************\n
        *                                                 *\n
        *                                                 *\n
        *              雷神加速器自动暂停工具v1.0         *\n
        *                     正在运行                     *\n
        *                    作者：6yy66yy                 *\n
        *                                                 *\n
        ***************************************************\n
        ''')
print("目前检测游戏列表:{}".format(appname))

# account_token=login(uname,password)
account_token = conf.get("config","account_token")

sw=1
while 1==1:
    game=check_exsit(appname)
    if(game):
        if(sw==1):
            print(game)
            sw=0
    elif(sw==0):
        for i in range(1,sec):
            game=check_exsit(appname)
            time.sleep(1)
        if game is False:
            try:
                pause(account_token,header)
            except:
                s = traceback.format_exc()
                logging.error(s)
        sw=1
    time.sleep(update)


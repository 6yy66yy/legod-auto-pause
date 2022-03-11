###############
# @Author: 6yy66yy
# @Date: 2022-03-11 14:13:00
# @LastEditors: 6yy66yy
# @LastEditTime: 2022-03-11 20:10:37
# @FilePath: \legod-auto-pause\run.py
# @Description: 这里写文件描述
###############

import legod
import TrayIcon
import multiprocessing
import win32gui 
from multiprocessing import Pipe
def gui(conn2):
    # print(os.getpid())
    t = TrayIcon.TrayIcon()
    win32gui.PumpMessages()
    conn2.send('A') #发送标志将后台程序关闭
def houtai(conn1):
    # print(os.getpid())
    legod.detection(conn1)
if __name__=='__main__':
    multiprocessing.freeze_support()
    conn1, conn2 = Pipe(duplex=True)  # 开启双向管道，管道两端都能存取数据。默认开启
    pool = multiprocessing.Pool(processes=2)
    pool.apply_async(houtai,(conn1,))
    pool.apply_async(gui,(conn2,))
    
    pool.close()
    pool.join()
    print ("所有进程结束")
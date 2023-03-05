
###############
# @Author: 6yy66yy
# @Date: 2022-03-11 14:13:00
# @LastEditors: 6yy66yy
# @LastEditTime: 2023-03-05 19:00:49
# @FilePath: \legod-auto-pause\TrayIcon.py
# @Description: 托盘控制程序，依赖legod.py运行
###############

from asyncio.windows_events import NULL
from ctypes import WinError
import win32con, win32gui, win32api, win32event
import winerror, pywintypes
import os
import legod
from time import sleep
from threading import Thread
import pythoncom
import logging
from logging.handlers import RotatingFileHandler
import sys

#设置日志输出格式
logLevel = logging.DEBUG if legod.isDebug else logging.ERROR

logging.basicConfig(level=logLevel 
                    #log日志输出的文件位置和文件名
                    #RotatingFileHandler循环写入日志，文件按maxBytes=1MB分割最多backupCount份
                    ,handlers=[RotatingFileHandler(filename="./demo.log",maxBytes=1 * 1024 * 1024, backupCount=2, encoding='utf-8')]
                    ,format="%(asctime)s - %(levelname)-8s - %(filename)-8s : %(lineno)s line - %(message)s" #日志输出的格式
                    # -8表示占位符，让输出左对齐，输出长度都为8位
                    ,datefmt="%Y-%m-%d %H:%M:%S" #时间输出的格式
                    )


class TrayIcon(object):
    def __init__(self):
        # 检查是否已经运行
        self.mutex = None
        self.mutex_name = "legodpause"
        check_result = self.check_already_running()
        if check_result:
            logging.error("程序已经运行")
            os._exit(1)
        msg_TaskbarRestart = win32gui.RegisterWindowMessage("Legod自动暂停")
        message_map = {
            msg_TaskbarRestart: self.OnRestart,
            win32con.WM_DESTROY: self.OnDestroy,
            win32con.WM_COMMAND: self.OnCommand,
            win32con.WM_USER + 20: self.OnTaskbarNotify,
        }
        # 注册窗口类
        wndclass = win32gui.WNDCLASS()
        hinst = wndclass.hInstance = win32api.GetModuleHandle(None)
        wndclass.lpszClassName = "Legod自动暂停"
        wndclass.style = win32con.CS_VREDRAW | win32con.CS_HREDRAW
        wndclass.hCursor = win32api.LoadCursor(0, win32con.IDC_ARROW)
        wndclass.hbrBackground = win32con.COLOR_WINDOW
        wndclass.lpfnWndProc = message_map
        try:
            classAtom = win32gui.RegisterClass(wndclass)
        except win32gui.error as err_info:
            if err_info.winerror != WinError.ERROR_CLASS_ALREADY_EXISTS:
                logging.error("窗口注册失败%s"%err_info)
                raise
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(wndclass.lpszClassName, 'Legod自动暂停', style, 0, 0,
                                          win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, hinst, None)
        win32gui.UpdateWindow(self.hwnd)
        Dir=os.path.dirname(sys.argv[0])
        self._createIcon()
        self.legod=legod.legod(True,Dir);
        self.stopflag=False
        t1 = Thread(target=self.detection, args=())
        t1.start()
        self.taskbar_msg("自动暂停工具运行成功",'游戏列表:%s'%",".join(self.legod.applist))

    def check_already_running(self) -> bool:
        ''' 检查是否已经运行
        Returns
        --------
        :class:`bool`
           True 已经运行 False 未运行
        '''
        # 创建互斥量
        # prevent the PyHANDLE from going out of scope, ints are fine
        mutex = win32event.CreateMutex(None, False, self.mutex_name)
        self.mutex = int(mutex)
        mutex.Detach()
        # 判断是否已经存在
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            win32api.CloseHandle(mutex)
            self.mutex = None
            return True
        return False

    def _createIcon(self):
        hinst = win32api.GetModuleHandle(None)
        iconPathName = "legod.ico"
        if os.path.isfile(iconPathName):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst, iconPathName, win32con.IMAGE_ICON, 0, 0, icon_flags)
        else:
            print('未找到icon文件,使用默认')
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "自动暂停工具")
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
            self.nid=nid
        except win32gui.error:
            logging.error("创建icon失败")
            print("Failed to add the taskbar icon - is explorer running?")

    def OnRestart(self, hwnd, msg, wparam, lparam):
        self._createIcon()

    def OnDestroy(self, hwnd, msg, wparam, lparam):
        nid = (self.hwnd, 0)
        win32gui.Shell_NotifyIcon(win32gui.NIM_DELETE, nid)
        win32gui.PostQuitMessage(0)  # Terminate the app.

    def OnTaskbarNotify(self, hwnd, msg, wparam, lparam):
        # if lparam == win32con.WM_LBUTTONUP:
        #     print("左键单击")
        # elif lparam == win32con.WM_LBUTTONDBLCLK:
        #     print("You double-clicked me - goodbye")
        #     win32gui.DestroyWindow(self.hwnd)
        if lparam == win32con.WM_RBUTTONUP:
            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1023, "打开雷神加速器")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1024, "暂停时长")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1025, "设置")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1026, "退出并暂停时长")
            win32gui.AppendMenu(menu, win32con.MF_DISABLED, 0, "自动暂停工具%s"%self.legod.version)
            win32gui.AppendMenu(menu, win32con.MF_DISABLED, 0, "Author: 6yy66yy")
            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        return 1

    def OnCommand(self, hwnd, msg, wparam, lparam):
        id = win32api.LOWORD(wparam)
        if id == 1023:
            logging.debug("尝试打开雷神")
            if(self.legod.lepath!=""):
                os.system('start "" "'+self.legod.lepath+'"')
            else:
                print("没填雷神路径")
                self.taskbar_msg("没填雷神路径","尝试设置一下\n自动暂停工具v2.0")
                logging.info("没填雷神路径")
        elif id == 1024:
            logging.debug("尝试暂停时长")
            msg = self.legod.pause()
            self.taskbar_msg("暂停时长结果",msg)
            logging.info("暂停结果:%s"%msg)
            print ("暂停时长")
        elif id == 1025:
            print("打开设置")
            self.taskbar_msg("打开设置","保存并关闭窗口以更新设置")
            os.system(legod.configfile)
            self.legod.load()
            self.taskbar_msg("设置更新",'新的游戏列表为:%s'%",".join(self.legod.applist))
            logging.info("更新ini文件")
        elif id == 1026:
            print ("退出并暂停时长")
            self.stopflag=True
            msg=self.legod.pause()
            self.taskbar_msg("退出并暂停时长结果",msg)
            sleep(2)
            win32gui.DestroyWindow(self.hwnd)
            # 结束进程回收资源
            win32event.ReleaseMutex(self.mutex)
            os._exit(0)
        else:
            print ("Unknown command -", id)
    def taskbar_msg(self,title,msg):
        # Taskbar icon
        nid =self.nid[4]
        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY,
        (self.hwnd, 0, win32gui.NIF_INFO,
        win32con.WM_USER + 20,
        nid, "Balloon Tooltip", msg,1,title))
        # update windows
        win32gui.UpdateWindow(self.hwnd)
        # win32gui.DestroyWindow(self.hwnd)
        # win32gui.UnregisterClass(self.wc.lpszClassName, None)
    def detection(self):
        sw=1
        print("开始检测")
        pythoncom.CoInitialize()
        while 1==1:
            game=self.legod.check_exsit()
            if(game):
                if(sw==1):
                    print(game)
                    nid = (self.nid[0],self.nid[1],self.nid[2],self.nid[3],self.nid[4],game)
                    win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)
                    sw=0
            elif(sw==0):
                for i in range(1,self.legod.sec):
                    game=self.legod.check_exsit()
                    sleep(1)
                if game is False:
                    try:
                        msg=self.legod.pause()
                        self.taskbar_msg("暂停结果：",msg)
                        nid = (self.nid[0],self.nid[1],self.nid[2],self.nid[3],self.nid[4],"检测中...")
                        win32gui.Shell_NotifyIcon(win32gui.NIM_MODIFY, nid)
                    except:
                        self.taskbar_msg("出错了","未知错误")
                sw=1
            sleep(self.legod.update)
            if(self.stopflag):
                print("线程结束")
                pythoncom.CoUninitialize()
                break
if __name__ == '__main__':
    logging.debug("开始运行！")
    t = TrayIcon()
    win32gui.PumpMessages()
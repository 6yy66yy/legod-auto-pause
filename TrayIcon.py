
###############
# @Author: 6yy66yy
# @Date: 2022-03-11 14:13:00
# @LastEditors: 6yy66yy
# @LastEditTime: 2022-04-29 16:45:57
# @FilePath: \legod-auto-pause\TrayIcon.py
# @Description: 托盘控制程序，依赖legod.py运行
###############

from asyncio.windows_events import NULL
import win32con
import win32gui
import win32api
from ctypes import WinError
import os
import legod
from time import sleep
from threading import Thread
import pythoncom

class TrayIcon(object):
    def __init__(self):
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
                raise
        style = win32con.WS_OVERLAPPED | win32con.WS_SYSMENU
        self.hwnd = win32gui.CreateWindow(wndclass.lpszClassName, 'Legod自动暂停', style, 0, 0,
                                          win32con.CW_USEDEFAULT, win32con.CW_USEDEFAULT, 0, 0, hinst, None)
        win32gui.UpdateWindow(self.hwnd)
        self._createIcon()
        self.legod=legod.legod(True);
        self.stopflag=False
        t1 = Thread(target=self.detection, args=())
        t1.start()
        self.taskbar_msg("自动暂停工具运行成功",'游戏列表:%s'%self.legod.appname)

    def _createIcon(self):
        hinst = win32api.GetModuleHandle(None)
        iconPathName = "legod.ico"
        if os.path.isfile(iconPathName):
            icon_flags = win32con.LR_LOADFROMFILE | win32con.LR_DEFAULTSIZE
            hicon = win32gui.LoadImage(hinst, iconPathName, win32con.IMAGE_ICON, 0, 0, icon_flags)
        else:
            print('未找到icon文件，使用默认')
            hicon = win32gui.LoadIcon(0, win32con.IDI_APPLICATION)
        flags = win32gui.NIF_ICON | win32gui.NIF_MESSAGE | win32gui.NIF_TIP
        nid = (self.hwnd, 0, flags, win32con.WM_USER + 20, hicon, "LegodPause Service")
        try:
            win32gui.Shell_NotifyIcon(win32gui.NIM_ADD, nid)
            self.nid=nid
        except win32gui.error:
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
            # print("You right clicked me.")
            menu = win32gui.CreatePopupMenu()
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1023, "打开雷神加速器")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1024, "暂停时长")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1025, "设置")
            win32gui.AppendMenu(menu, win32con.MF_STRING, 1026, "退出并暂停时长")
            win32gui.AppendMenu(menu, win32con.MF_DISABLED, 0, "自动暂停工具v2.0")
            win32gui.AppendMenu(menu, win32con.MF_DISABLED, 0, "Author: 6yy66yy")
            pos = win32gui.GetCursorPos()
            win32gui.SetForegroundWindow(self.hwnd)
            win32gui.TrackPopupMenu(menu, win32con.TPM_LEFTALIGN, pos[0], pos[1], 0, self.hwnd, None)
            win32gui.PostMessage(self.hwnd, win32con.WM_NULL, 0, 0)
        return 1

    def OnCommand(self, hwnd, msg, wparam, lparam):
        id = win32api.LOWORD(wparam)
        if id == 1023:
            if(self.legod.lepath!=""):
                os.system('start '+self.legod.lepath)
            else:
                print("没填雷神路径")
                self.taskbar_msg("没填雷神路径","尝试设置一下\n自动暂停工具v2.0")
        elif id == 1024:
            self.taskbar_msg("暂停时长结果",self.legod.pause())
            print ("暂停时长")
        elif id == 1025:
            print("打开设置")
            os.system('start config.ini')
        elif id == 1026:
            print ("退出并暂停时长")
            self.stopflag=True
            msg=self.legod.pause()
            self.taskbar_msg("退出并暂停时长结果",msg)
            sleep(2)
            win32gui.DestroyWindow(self.hwnd)
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
                    sw=0
            elif(sw==0):
                for i in range(1,self.legod.sec):
                    game=self.legod.check_exsit()
                    sleep(1)
                if game is False:
                    try:
                        msg=self.legod.pause()
                        self.taskbar_msg("暂停结果：",msg)
                    except:
                        self.taskbar_msg("出错了")
                sw=1
            sleep(self.legod.update)
            if(self.stopflag):
                print("线程结束")
                pythoncom.CoUninitialize()
                break
if __name__ == '__main__':
    if __debug__:
        print("debug模式开启,密码不加密传输")
    t = TrayIcon()
    win32gui.PumpMessages()
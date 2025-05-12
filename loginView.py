
'''
Author: 6yy66yy
Date: 2025-04-23 15:21:19
LastEditors: wangqianqi
LastEditTime: 2025-05-12 17:04:30
FilePath: \legod-auto-pause\loginView.py
Description: 
'''
import webview
from threading import Timer
import webview.menu as wm

# 用于保存 token 的全局变量
result_token = None

def onload(window):
    print("loaded!!")
    # window.run_js('document.getElementsByClassName("login")[0].children[0].click()')

    # 开始检测 account_token
    Timer(2, detection, args=(window,)).start()

def detection(window):
    global result_token

    print("开始检测Token")
    try:
        result = window.evaluate_js('JSON.parse(localStorage.getItem("account_token"))')
        print(f"检测执行完成了: {result}")

        if result and 'account_token' in result:
            result_token = result['account_token']
            print(f"Account Token: {result_token}")
            print("Account token found and valid")

            # 成功获取 token 后关闭窗口
            window.destroy()
        else:
            print("Account token not found or invalid")
            Timer(2, detection, args=(window,)).start()
    except Exception as e:
        print(f"JS 执行错误: {e}")
        Timer(2, detection, args=(window,)).start()

# 设置 Edge 的手机版 User-Agent
user_agent = "Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Mobile Safari/537.36 EdgA/110.0.1587.63"

def get_account_token(url = 'https://www.leigod.com/m/mlogin.html?region_code=1&language=zh_CN&platform=2'):
    """对外暴露的方法，用于启动 GUI 并获取 token"""
    window = webview.create_window(
        '请进行登录操作'+url,
        url
    )
    window.events.loaded += onload
    # menu_items = [
    #     wm.Menu('Nothing Here', [wm.MenuAction('This will do nothing', do_nothing)]),
    # ]
    webview.start(user_agent=user_agent)

    return result_token

if __name__ == "__main__":
    # 单独运行时自动启动并输出 token 后退出
    token = get_account_token()
    print("【调试模式】获取到的 token 是:", token)
from selenium.webdriver import Chrome, ChromeOptions
import json
import time
import requests
import urllib
import hmac
import base64
from urllib import parse
import hashlib


def init_chrome(chrome, url_item):
    """初始化浏览器，确保已登录"""
    # chrome.set_window_position(x=0, y=0)
    chrome.maximize_window()
    chrome.get(url_item)
    chrome.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": """
        Object.defineProperty(navigator, 'webdriver', {
          get: () => undefined
        })
      """
    })


def launch_chrome():
    """启动浏览器，解决Webdriver指纹问题"""
    options = ChromeOptions()
    # 允许以root权限运行
    options.add_argument("--no-sandbox")
    # 禁止'正受到自动化软件控制'提示
    options.add_argument("--disable-infobars")
    options.binary_location = r'C:\Users\1\AppData\Local\Google\Chrome\Application\chrome.exe'
    options.add_experimental_option('excludeSwitches', ['enable-automation'])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("disable-blink-features=AutomationControlled")  # 就是这一行告诉chrome去掉了webdriver痕迹

    return Chrome(options=options)


def ding(title, options: dict):
    content = '\n'.join([f"+ **{k}**：{v}" for k, v in options.items()])
    secret = 'SEC789e87081fc800363b6520cd4d0dea9aeb151adf3ca22a83ab1ff67be8e408ba'
    token = '00c14a94c66e0223d71145811827f81468de45d22475b8f3c7e21c62c2c729b6'
    timestamp = int(time.time() * 1000)
    data = (str(timestamp) + '\n' + secret).encode('utf-8')
    hmac_code = hmac.new(secret.encode('utf-8'), data, digestmod=hashlib.sha256).digest()
    sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
    url = f'https://oapi.dingtalk.com/robot/send?access_token={token}&timestamp={timestamp}&sign={sign}'
    r = requests.post(url, json={
        "msgtype": "markdown",
        "markdown": {
            "title": title,
            "text": content,
        }
    })


def reset_key():
    headers = {
        "referer": "https://console.open.taobao.com/",
        "user-agen": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/72.0.3626.121 Safari/537.36",
        "cookie": ";".join(i for i in [k + '=' + v for k, v in cookies.items()])
    }
    url = f'https://console.open.taobao.com/handler/app/clearAccessCount.json?_bizId_=1&appkey=29441833&_tb_token_={cookies.get("_tb_token_")}&_ksTS={int(time.time() * 1000)}_364'
    rec = json.loads(requests.get(url, headers=headers).text)
    return rec

def main():
    try:
        global cookies
        chrome = launch_chrome()
        url = 'https://console.open.taobao.com/?#/app/23116944/app_app'
        init_chrome(chrome, url)
        time.sleep(1)
        chrome.find_element_by_xpath('/html/body/div/div[2]/div[3]/div/div/div/div[2]/div/form/div[1]/div[2]/input').send_keys('xxxx')

        time.sleep(1)
        chrome.find_element_by_xpath('/html/body/div/div[2]/div[3]/div/div/div/div[2]/div/form/div[2]/div[2]/input').send_keys('@xxxx......')
        time.sleep(1)
        # 登陆
        chrome.find_element_by_xpath('//*[@id="login-form"]/div[4]/button').click()
        time.sleep(2)
        # 获取cookie
        cookie = chrome.get_cookies()

        for i in range(1, 5):
            c = {i['name']: i['value'] for i in chrome.get_cookies()}
            if "cookie1" in c:
                print("登陆成功")
                break
            else:
                print("未登录")
                time.sleep(2)
        else:
            print("登陆失败")
            raise Exception("登陆失败")
        cookies = {c.get("name"): c.get("value") for c in cookie}
        result = reset_key()
        ding("重置key结果", result)
    except Exception as e:
        ding("重置key异常", {"message": e})
    finally:
        # time.sleep(600)
        chrome.close()


if __name__ == '__main__':
    main()

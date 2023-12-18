"""테스트"""
import time
import requests
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from tmp_watch import SeleWatch


while True:
    sele_watch = SeleWatch()
    sele_watch.create_selenium()
    # 닫기 버튼 클릭
    sele_watch.element_click_with_css("button.btnClose")

    # 로그인 과정
    sele_watch.login()
    user_list = sele_watch.get_user_list()
    save_list = requests.get(
        url="http://panda-manager.com:3000/user/tmp-user",
        timeout=5,
    ).json()
    print(save_list)
    for user in user_list:
        if user["name"] in save_list:
            continue
        else:
            sele_watch = SeleWatch()
            sele_watch.create_selenium()
            sele_watch.goto_url(
                f"https://www.pandalive.co.kr/live/search?text={user['name']}#bj"
            )
            # 닫기 버튼 클릭
            # sele_watch.element_click_with_css("button.btnClose")
            sele_watch.add_user(user["name"])
    print("one cycle clear")
    time.sleep(300)




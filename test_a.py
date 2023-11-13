"""테스트"""
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from tmp_watch import SeleWatch

sele_watch = SeleWatch()
sele_watch.create_selenium()
# 닫기 버튼 클릭
sele_watch.element_click_with_css("button.btnClose")

# 로그인 과정
sele_watch.login()
sele_watch.goto_url("https://www.pandalive.co.kr/pick#bookmark")
while True:
    time.sleep(5)
    # sele_watch.start()
    time.sleep(5)
print("hahaha")

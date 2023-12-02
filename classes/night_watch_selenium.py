"""테스트"""
import os
import time
import requests
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.common.by import By

from util.my_util import logging_debug

BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
PUBLIC_IP = os.getenv("PUBLIC_IP")


class SeleWatch:
    """PandaWrapper 클래스"""

    def __init__(self) -> None:
        self.driver = None
        self.bookmark_list = []
        self.delete_bookmark_list = []
        self.backend_url = BACKEND_URL
        self.backend_port = BACKEND_PORT
        self.bookmark_list_changed = False

    def create_selenium(self):
        """selenium 생성"""
        options = ChromeOptions()
        user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36"
        options.add_argument("user-agent=" + user_agent)
        options.add_argument("lang=ko_KR")
        options.add_argument("window-size=1080x680")
        options.add_argument("disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--headless")

        # 크롬 드라이버 최신 버전 설정
        service = ChromeService(executable_path="/usr/bin/chromedriver")

        # chrome driver
        self.driver = webdriver.Chrome(
            service=service, options=options
        )  # <- options로 변경
        self.driver.get("https://www.pandalive.co.kr/")
        self.driver.implicitly_wait(10)

    def goto_url(self, url):
        """url 이동"""
        self.driver.get(url)

    def login(self, manager_id="xptmxmdyd123", manager_pw="Adkflfkd1"):
        """로그인 함수"""
        self.element_click_with_css(".btn_login.btn_my_infor")
        self.element_click_with_css("div.profile_infor > a > span.name")
        self.element_click_with_css("ul.memTab > li > a")
        self.element_click_with_css("div.input_set > input#login-user-id")
        self.element_fill_with_css("div.input_set > input#login-user-id", manager_id)
        self.element_click_with_css("div.input_set > input#login-user-pw")
        self.element_fill_with_css("div.input_set > input#login-user-pw", manager_pw)
        self.element_click_with_css("div.btnList > span.btnBc > input[type=button]")
        self.element_click_with_css("div.profile_img")

    def find_element_with_css(self, css_selector):
        """css_selector로 element 찾기"""
        try:
            btn_close = self.driver.find_element(by=By.CSS_SELECTOR, value=css_selector)
            return btn_close
        except Exception as e:  # pylint: disable=W0703
            print(f"[find_element_with_css] - {css_selector}\n{e}")

    def element_click_with_css(self, css_selector):
        """css 엘리먼트 클릭"""
        self.find_element_with_css(css_selector).click()

    def element_fill_with_css(self, css_selector, value):
        """css 엘리먼트 입력"""
        self.find_element_with_css(css_selector).send_keys(value)

    def start(self):
        """NightWatch Loop 함수"""
        try:
            # print("[start night watch] - BookMark Start")
            for book_mark_id in self.delete_bookmark_list:
                self.set_book_mark(book_mark_id, False)
            for book_mark_id in self.bookmark_list:
                self.set_book_mark(book_mark_id, True)
            self.bookmark_list.clear()
            self.delete_bookmark_list.clear()
            idle_users, live_users = self.get_user_status()
            backend_live_users = requests.get(
                url=f"http://{self.backend_url}:{self.backend_port}/bj?mode=playing",
                timeout=5,
            ).json()
            backend_idle_users = requests.get(
                f"http://{self.backend_url}:{self.backend_port}/bj?mode=idle",
                timeout=5,
            ).json()
            print("[start night watch] - filter_dict_by_list")
            wanted_play_list = self.filter_dict_by_list(live_users, backend_idle_users)
            wanted_stop_list = self.filter_dict_by_list(idle_users, backend_live_users)
            print(f"watned play lsit = {wanted_play_list}")
            print(f"watend stop list = {wanted_stop_list}")
            # 이 부분 이후에 에러 발생 1
            if len(wanted_play_list) > 0:
                requests.post(
                    url=f"http://{self.backend_url}:{self.backend_port}/resource/task",
                    json={"panda_ids": wanted_play_list},
                    timeout=5,
                )
            if len(wanted_stop_list) > 0:
                requests.delete(
                    url=f"http://{self.backend_url}:{self.backend_port}/resource/task",
                    json={"panda_ids": wanted_stop_list},
                    timeout=5,
                )
        except Exception as e:  # pylint: disable=W0703
            print("what the fuck ?")
            print(e)

    def set_book_mark(self, panda_id: str, state: bool):
        """북마크 세팅. state상태로 세팅함"""
        self.goto_url(f"https://www.pandalive.co.kr/channel/{panda_id}/notice")
        time.sleep(1)
        book_mark = self.find_element_with_css("span.btn_bookmark")
        book_mark_class = book_mark.get_attribute("class")
        # 이미 북마크가 되어있다면
        if "on" in book_mark_class:
            if state is False:
                self.bookmark_list_changed = True
                book_mark.click()
        # 북마크가 되어있지 않다면
        else:
            if state is True:
                self.bookmark_list_changed = True
                book_mark.click()

    def get_user_status(self):
        """유저 상태를 가져옴"""
        self.driver.implicitly_wait(0)
        idle_users = {}
        live_users = {}
        if self.driver.current_url != "https://www.pandalive.co.kr/pick#bookmark":
            print("북마크 페이지가 아닙니다. 북마크 페이지로 이동합니다.")
            self.goto_url("https://www.pandalive.co.kr/pick#bookmark")
        # 유저 상태를 가져옴
        user_list = self.driver.find_elements(By.CSS_SELECTOR, "div.pickList > ul > li")
        for lists_li in user_list:
            photo = lists_li.find_element(By.CSS_SELECTOR, "div.photo")
            infor = lists_li.find_element(By.CSS_SELECTOR, "div.infor")
            nickname = infor.text.strip()
            nickname = nickname.replace(" ", "").replace("\n", "")
            try:
                photo.find_element(By.CSS_SELECTOR, "span")
                live_users[nickname] = True
            except:  # pylint: disable=W0702
                idle_users[nickname] = False
        self.driver.implicitly_wait(10)
        if self.bookmark_list_changed:
            self.bookmark_list_changed = False
            idle_user_keys = list(idle_users.keys())
            live_user_keys = list(live_users.keys())
            combined_keys = idle_user_keys + live_user_keys
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log/debug",
                json={
                    "panda_id": "NightWatch",
                    "description": "Current Regist User",
                    "data": combined_keys,
                },
                timeout=5,
            )
            requests.patch(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/nightwatch",
                json={"ip": PUBLIC_IP, "size": len(combined_keys)},
                timeout=5,
            )

        return idle_users, live_users

    def filter_dict_by_list(self, my_dict, my_list):
        """list중 dict안에 존재하는 요소만 반납"""
        ret_list = []
        for user in my_list:
            if user["nickname"] in my_dict:
                ret_list.append(user["panda_id"])
        return ret_list

    def add_book_mark_list(self, panda_id: str):
        """북마크 해야될 리스트에 추가"""
        self.bookmark_list.append(panda_id)

    def delete_book_mark_list(self, panda_id: str):
        """북마크 삭제해야될 리스트에 추가"""
        self.delete_bookmark_list.append(panda_id)

    def refresh(self):
        """새로고침"""
        self.driver.refresh()

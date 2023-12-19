"""playwright용 nightwatch"""
import asyncio
import os
from playwright.async_api import Page
from playwright.async_api import Browser
from playwright.async_api import BrowserContext
from playwright.async_api import async_playwright
import requests
from classes.book_mark_list_api_data import BookMarkListApiData

BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")
PUBLIC_IP = os.getenv("PUBLIC_IP")


class PlayWrightNightWatch:
    """playwright를 이용한 NightWatch 모듈"""

    def __init__(self):
        self.watch_id = "siveriness1"
        self.watch_pw = "Adkflfkd1"
        self.page: Page
        self.browser = Browser
        self.context = BrowserContext
        self.bookmark_list = []
        self.delete_bookmark_list = []
        self.backend_url = os.getenv("BACKEND_URL")
        self.backend_port = os.getenv("BACKEND_PORT")
        self.bookmark_list_changed = False
        self.bookmark_api_data = BookMarkListApiData()
        self.prev_list_length = 0

    async def set_interceptor(self):
        """인터셉터 설정"""
        await self.context.route(
            "https://api.pandalive.co.kr/v1/live/bookmark", self.intercept_bookmark_list
        )

    async def intercept_bookmark_list(self, route, request):
        """북마크 인터셉터"""
        if self.bookmark_api_data.is_need_list_headers():
            self.bookmark_api_data.set_list_headers(request.headers)
        await route.continue_()

    async def goto_url(self, url):
        """url 이동"""
        await self.page.goto(url)

    async def destroy(self):
        """free memory"""
        await self.browser.close()

    async def create_selenium(self):
        """playwright 객체 생성"""
        apw = await async_playwright().start()
        self.browser = await apw.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            viewport={"width": 1500, "height": 900},  # 원하는 해상도 크기를 지정하세요.
            locale="ko-KR",
        )
        self.page = await self.context.new_page()
        await self.page.goto("http://pandalive.co.kr")
        print(await self.page.title())
        return True

    async def element_click_with_css(self, css_selector):
        """css 엘리먼트가 있다면 클릭"""
        element = await self.page.query_selector(css_selector)
        if element:
            await element.click()

    async def element_fill_with_css(self, css_selector, value):
        """css 엘리먼트가 있다면 value를 입력"""
        element = await self.page.query_selector(css_selector)
        if element:
            await element.fill(value)

    async def login(self):
        """로그인"""
        await self.element_click_with_css(".btn_login.btn_my_infor")
        await self.element_click_with_css("div.profile_infor > a > span.name")
        await self.element_click_with_css("ul.memTab > li > a")
        await self.element_click_with_css("div.input_set > input#login-user-id")
        await self.element_fill_with_css(
            "div.input_set > input#login-user-id", self.watch_id
        )
        await self.element_click_with_css("div.input_set > input#login-user-pw")
        await self.element_fill_with_css(
            "div.input_set > input#login-user-pw", self.watch_pw
        )
        await self.element_click_with_css(
            "div.btnList > span.btnBc > input[type=button]"
        )
        await self.page.wait_for_selector("div.profile_img")
        await self.element_click_with_css("div.profile_img")

    async def start(self):
        """NightWatch Loop 함수"""
        try:
            # print("[start night watch] - BookMark Start")
            for book_mark_id in self.delete_bookmark_list:
                await self.set_book_mark(book_mark_id, False)
            for book_mark_id in self.bookmark_list:
                await self.set_book_mark(book_mark_id, True)
            self.bookmark_list.clear()
            self.delete_bookmark_list.clear()
            idle_users, live_users = await self.get_user_status()
            backend_live_users = requests.get(
                url=f"http://{self.backend_url}:{self.backend_port}/bj?mode=playing",
                timeout=5,
            ).json()
            backend_idle_users = requests.get(
                f"http://{self.backend_url}:{self.backend_port}/bj?mode=idle",
                timeout=5,
            ).json()
            print("[start night watch] - filter_dict_by_list")
            wanted_play_list = self.filter_wanted_play_list(
                live_users, backend_idle_users
            )
            wanted_stop_list = self.filter_wanted_stop_list(
                idle_users, backend_live_users
            )
            print(f"watned play lsit = {wanted_play_list}")
            print(f"watend stop list = {wanted_stop_list}")
            # 이 부분 이후에 에러 발생 1
            if len(wanted_play_list) > 0:
                requests.post(
                    url=f"http://{self.backend_url}:{self.backend_port}/log/info",
                    json={
                        "panda_id": "Night-Watch",
                        "description": "Detect - 방송시작",
                        "data": wanted_play_list,
                    },
                    timeout=5,
                )
                requests.post(
                    url=f"http://{self.backend_url}:{self.backend_port}/resource/task",
                    json={"panda_ids": wanted_play_list},
                    timeout=5,
                )
            if len(wanted_stop_list) > 0:
                requests.post(
                    url=f"http://{self.backend_url}:{self.backend_port}/log/info",
                    json={
                        "panda_id": "Night-Watch",
                        "description": "Detect - 방송종료",
                        "data": wanted_stop_list,
                    },
                    timeout=5,
                )
                requests.delete(
                    url=f"http://{self.backend_url}:{self.backend_port}/resource/task",
                    json={"panda_ids": wanted_stop_list},
                    timeout=5,
                )
        except Exception as e:  # pylint: disable=W0703
            print("what the fuck ?")
            print(e)

    async def set_book_mark(self, panda_id: str, state: bool):
        """북마크 세팅. state상태로 세팅함"""
        try:
            self.goto_url(f"https://www.pandalive.co.kr/channel/{panda_id}/notice")
            asyncio.sleep(1)
            self.bookmark_list_changed = True
            book_mark = self.page.locator("span.btn_bookmark")
            book_mark_class = book_mark.get_attribute("class")
            # 이미 북마크가 되어있다면
            if "on" in book_mark_class:
                if state is False:
                    book_mark.click()
            # 북마크가 되어있지 않다면
            else:
                if state is True:
                    book_mark.click()
        except Exception as e:  # pylint: disable=W0703
            print(e)

    async def get_user_status(self):
        """유저 상태를 가져옴"""
        if self.bookmark_api_data.book_mark_list_headers:
            user_datas = await self.bookmark_api_data.get_bookmark_list()
            if user_datas is not None:
                users_datas_json = user_datas.json()["list"]
                if self.prev_list_length != len(users_datas_json):
                    self.prev_list_length = len(users_datas_json)
                    self.bookmark_list_changed = True
                idle_users = [
                    user["userId"]
                    for user in users_datas_json
                    if user.get("media") is None
                ]
                live_users = [
                    user["userId"]
                    for user in users_datas_json
                    if user.get("media") is not None
                ]
        else:
            await self.goto_url("https://www.pandalive.co.kr/pick#bookmark")

        if self.bookmark_list_changed:
            self.bookmark_list_changed = False
            combined_keys = idle_users + live_users
            combined_keys.append(f"nightWatch length = {len(combined_keys)}")
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log/info",
                json={
                    "panda_id": "Night-Watch",
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

    def filter_wanted_play_list(self, current_live_list: list, backend_idle_list: list):
        """idle_list 중 current_live_list안에 있는 요소만 반납"""
        ret_list = []
        for user in current_live_list:
            for backend_data in backend_idle_list:
                if user == backend_data["panda_id"]:
                    ret_list.append(backend_data["panda_id"])
                    break
        return ret_list

    def filter_wanted_stop_list(self, current_live_list: list, backend_live_list: list):
        """live_list에서 dict안에 존재하는 요소만 반납"""
        ret_list = []
        for current_user in current_live_list:
            for backend_user in backend_live_list:
                if backend_user["panda_id"] == current_user:
                    ret_list.append(backend_user["panda_id"])
        return ret_list

    def add_book_mark_list(self, panda_id: str):
        """북마크 해야될 리스트에 추가"""
        self.bookmark_list.append(panda_id)

    def delete_book_mark_list(self, panda_id: str):
        """북마크 삭제해야될 리스트에 추가"""
        self.delete_bookmark_list.append(panda_id)

    async def refresh(self):
        """새로고침"""
        await self.page.reload()

import asyncio
import aiohttp
import requests
from playwright.async_api import async_playwright
from classes import playwright_watch as pm
from urllib.parse import quote


class ChannelApiData:
    """채널 요청에 관련된 Api에 필요한 데이터"""

    def __init__(self):
        self.headers = None
        self.channel = ""
        self.token = ""
        self.valid = False
        self.is_manager = False

    def is_valid(self):
        """현재 토큰이 올바른지 변수"""
        return self.headers

    def is_list_enabled(self):
        """직전 list요청이 성공했는지 여부"""
        return self.is_manager

    def set_data(self, headers, channel: str, token: str):
        """API에 필요한 데이터를 설정 하는 함수"""
        self.headers = headers
        self.channel = channel
        self.token = token
        self.valid = True

    async def send_channel_user_count(self):
        """채널의 유저 수를 요청하는 함수"""
        url = (
            "https://api.pandalive.co.kr/v1/chat/channel_user_count?"
            f"channel={self.channel}&token={self.token}"
        )
        # print(url)
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
        except:  # pylint: disable= W0702
            self.valid = False
        return response

    async def send_channel_user_list(self):
        """채널의 유저 수를 요청하는 함수"""
        url = (
            "https://api.pandalive.co.kr/v1/chat/channel_user_list?"
            f"channel={self.channel}&token={self.token}"
        )
        print(url)
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
        except:  # pylint: disable= W0702
            self.valid = False
        return response


class ChattingApiData:
    """채팅 요청에 관련된 Api에 필요한 데이터"""

    def __init__(self):
        self.message = ""
        self.roomid = None
        self.chatoken = None
        self.t = None
        self.channel = None
        self.token = None
        self.valid = False
        self.headers = None

    def set_data(
        self,
        message: str,
        roomid: str,
        chatoken: str,
        t: str,
        channel: str,
        token: str,
        headers,
    ):
        """API에 필요한 데이터를 설정 하는 함수"""
        self.message = message
        self.roomid = roomid
        self.chatoken = chatoken
        self.t = t
        self.channel = channel
        self.token = token
        self.headers = headers
        self.valid = True

    def set_mesage(self, message: str):
        """채팅 메시지 설정"""
        self.message = message

    async def send_chatting_message(self):
        """채널의 유저 수를 요청하는 함수"""
        url = "https://api.pandalive.co.kr/v1/chat/message"
        try:
            post_data = (
                "message="
                + self.message
                + "&roomid="
                + self.roomid
                + "&chaToken="
                + self.chatoken
                + "&t="
                + self.t
                + "&channel="
                + self.channel
                + "&token="
                + self.token
            )
            print(post_data)
            response = requests.post(
                url, headers=self.headers, data=post_data, timeout=1
            )
        except:  # pylint: disable= W0702
            self.valid = False
        return response


class BookMarkListApiData:
    """ "북마크 API 요청 데이터"""

    def __init__(self):
        self.offset = 0
        self.limit = 200
        self.is_live = ""
        self.hide_only = "N"
        self.book_mark_list_headers: dict = None

    def is_need_list_headers(self):
        """헤더정보가 있는지 체크"""
        if self.book_mark_list_headers is None:
            return True
        else:
            return False

    def set_list_headers(self, headers):
        """API에 필요한 데이터를 설정 하는 함수"""
        self.book_mark_list_headers = headers

    def set_book_mark_list_headers(self, headers):
        """API에 필요한 데이터를 설정 하는 함수"""
        self.book_mark_list_headers = headers

    async def get_bookmark_list(self):
        """북마크 리스트를 요청하는 함수"""
        if self.book_mark_list_headers is None:
            print("헤더가 없는 요청입니다")
            return None
        try:
            print(self.book_mark_list_headers)
            response = requests.post(
                url="https://api.pandalive.co.kr/v1/live/bookmark",
                headers=self.book_mark_list_headers,
                json={
                    "offset": self.offset,
                    "limit": self.limit,
                    "isLive": self.is_live,
                    "hideOnly": self.hide_only,
                },
                # f"offset={self.offset}&limit={self.limit}&isLive={self.is_live}&hideOnly={self.hide_only}",
                timeout=5,
            )
            return response
        except Exception as e:
            print("북마크 리스트 API 요청 실패", e)

    async def get_heart_user_list(self):
        """실험용 API"""
        if self.book_mark_list_headers is None:
            print("헤더가 없는 요청입니다")
            return None
        response = requests.get(
            url="https://api.pandalive.co.kr/v1/heart/use_list",
            headers=self.book_mark_list_headers,
            json={"offset": 0, "limit": 10},
            timeout=5,
        )
        print(response.json())
        return response


class SearchLiveBj:
    """실시간 방송중인 BJ 검색 클래스"""

    def __init__(self):
        self.headers: dict = None

    def set_list_headers(self, headers):
        """API에 필요한 데이터를 설정 하는 함수"""
        self.headers = headers

    async def search_live_bj(self, searchVal: str):
        """실시간 방송중인 BJ 검색"""
        if self.headers is None:
            print("헤더가 없는 요청입니다")
            return None
        try:
            print(self.headers)
            response = requests.post(
                url="https://api.pandalive.co.kr/v1/live",
                headers=self.headers,
                data=f"offset=0&limit=20&orderBy=user&searchVal={quote(searchVal)}",
                timeout=5,
            )
            print(response.json())
            return response
        except Exception as e:
            self.headers = None
            print("실시간 방송중인 BJ 검색 실패", e)


channel_api_data = ChannelApiData()
chatting_api_data = ChattingApiData()
bookmark_api_Data = BookMarkListApiData()
search_live_api_data = SearchLiveBj()


async def intercept_channel_user_count(route, request):
    """채널의 유저 수를 요청을 인터셉트 하는 함수"""
    if channel_api_data.headers:
        response = await channel_api_data.send_channel_user_count()

        if response.status_code == 200:
            print(response.json())
        else:
            print(response.status_code)
        await route.fulfill(
            status=response.status_code, headers=response.headers, body=response.text
        )
    else:
        query = request.url.split("?")[1].split("&")
        channel = query[0].split("=")[1]
        token = query[1].split("=")[1]
        channel_api_data.set_data(request.headers, channel=channel, token=token)
        await route.continue_()


async def intercept_bookmark_list(route, request):
    """북마크 인터셉터"""
    if bookmark_api_Data.is_need_list_headers():
        bookmark_api_Data.set_list_headers(request.headers)
        await route.continue_()
    else:
        response = await bookmark_api_Data.get_bookmark_list()
        response_json = response.json()
        print(len(response_json["list"]))
        if response.status_code == 200:
            print(response.json())
        else:
            print(response.status_code)
        await route.fulfill(
            status=response.status_code, headers=response.headers, body=response.text
        )


async def intercept_channel_user_list(route, request):
    """채널의 유저 리스트를 요청을 인터셉트하는 함수"""
    if channel_api_data.is_list_enabled():
        response = await channel_api_data.send_channel_user_list()
        if response.status_code == 200:
            print(response.json())
        else:
            print(response.status_code)
        await route.fulfill(
            status=response.status_code, headers=response.headers, body=response.text
        )
    else:
        query = request.url.split("?")[1].split("&")
        channel = query[0].split("=")[1]
        token = query[1].split("=")[1]
        channel_api_data.set_data(request.headers, channel=channel, token=token)
        await route.continue_()


async def intercept_chatting_message(route, request):
    """채팅 메시지를 요청을 인터셉트하는 함수"""
    # print(request.url)
    # await route.continue_()

    if chatting_api_data.valid:
        response = await chatting_api_data.send_chatting_message()
        if response.status_code == 200:
            print(response.json())
        else:
            print(response.status_code)
            response.status_code = 404
        await route.fulfill(
            status=response.status_code, headers=response.headers, body=response.text
        )
    else:
        query = request.post_data.split("&")
        message = query[0].split("=")[1]
        roomid = query[1].split("=")[1]
        chatoken = query[2].split("=")[1]
        t = query[3].split("=")[1]
        channel = query[4].split("=")[1]
        token = query[5].split("=")[1]
        chatting_api_data.set_data(
            message=message,
            roomid=roomid,
            chatoken=chatoken,
            t=t,
            channel=channel,
            token=token,
            headers=request.headers,
        )
        await route.continue_()


async def intercept_search_live_bj(route, request):
    """실시간 방송중인 BJ 검색 요청을 인터셉트하는 함수"""
    if search_live_api_data.headers is None:
        search_live_api_data.headers = request.headers
        await route.continue_()
    else:
        response = await search_live_api_data.search_live_bj("지애v")
        if response.status_code == 200:
            print(response.json())
        else:
            print(response.status_code)
        await route.fulfill(
            status=response.status_code, headers=response.headers, body=response.text
        )


async def main():
    """메인"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # WebSocket 요청을 인터셉트하는 함수를 등록
        await context.route(
            "https://api.pandalive.co.kr/v1/live", intercept_search_live_bj
        )
        # await context.route("**/channel_user_count*", intercept_channel_user_count)
        # await context.route(
        #     "https://api.pandalive.co.kr/v1/live/bookmark", intercept_bookmark_list
        # )

        # 새 페이지 열기
        page = await context.new_page()

        # WebSocket을 사용하는 작업 수행
        await page.goto("https://www.pandalive.co.kr/")

        while True:
            await page.wait_for_timeout(0)
            title = await page.query_selector("xpath=/html/body/div[3]/div/div[1]/h2")
            error_btn = await page.query_selector(
                "xpath=/html/body/div[3]/div/div[3]/button[1]"
            )
            if title:
                title_text = await title.inner_text()
                print(title_text)
                await error_btn.click()
                break
            await page.wait_for_timeout(5000)
            await asyncio.sleep(5)

        # 페이지 작업 완료 후 브라우저 종료
        await browser.close()


asyncio.run(main())

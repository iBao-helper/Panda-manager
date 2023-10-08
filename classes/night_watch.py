""" this is night wiath.py"""
import asyncio
from playwright.async_api import async_playwright
from playwright.async_api import Page
from playwright.async_api import Browser
import urllib.request  # pylint: disable=C0411
from stt import sample_recognize


class NightWatch:
    """PandaWrapper 클래스"""

    def __init__(self) -> None:
        self.page: Page
        self.browser = Browser
        self.wath_loop = False
        self.bookmark_list = []

    async def create_playwright(self):
        """playwright 객체 생성"""
        apw = await async_playwright().start()
        self.browser = await apw.chromium.launch(
            headless=False,
            # proxy={"server": "13.125.205.153:8888"}
            # headless=False
        )
        context = await self.browser.new_context(
            viewport={"width": 1500, "height": 900}  # 원하는 해상도 크기를 지정하세요.
        )
        self.page = await context.new_page()
        await self.page.goto("http://pandalive.co.kr")
        print(await self.page.title())
        # await self.page.get_by_role("button", name="닫기").click()
        return

    async def login(self, login_id: str = "xptmxmdyd123", login_pw: str = "Adkflfkd1"):
        """
        1. 팝업탭이 있는지 확인하고 팝업탭이 있다면 닫음
        2. 로그인 과정을 수행
        3. 로그인 과정을 수행한 뒤 로그인 프로필 이미지가 나타날때까지 대기
        4. bookmark 페이지로 이동
        """
        await self.page.get_by_role("button", name="닫기").click()
        await self.page.get_by_role("button", name="로그인 / 회원가입").click()
        await self.page.get_by_role("link", name="로그인 / 회원가입").click()
        await self.page.get_by_role("link", name="로그인").click()
        # await self.page.get_by_role("textbox").nth(1).fill("siveriness0")
        # await self.page.get_by_role("textbox").nth(2).fill("dkflfkd12#")
        await self.page.get_by_role("textbox").nth(1).fill(login_id)
        await self.page.get_by_role("textbox").nth(2).fill(login_pw)
        await asyncio.sleep(2)
        await self.page.get_by_role("button", name="로그인", exact=True).click()
        await asyncio.sleep(2)
        print("로그인 클릭")
        invalid_text_id = await self.page.get_by_text("존재하지 않는 사용자입니다.").is_visible()
        invalid_text_pw = await self.page.get_by_text(
            "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
        ).is_visible()
        if invalid_text_id or invalid_text_pw:
            print("Invalid Id or PW")
            # raise error
            return False
        invalid_label_id = await self.page.get_by_label("존재하지 않는 사용자입니다.").is_visible()
        invalid_label_pw = await self.page.get_by_label(
            "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
        ).is_visible()
        if invalid_label_id or invalid_label_pw:
            print("popup Invalid Id or PW")
            await self.page.get_by_role("button", name="확인").click()
            # raise error
            return False
        invalid_login_detect = await self.page.get_by_label(
            "비정상적인 로그인이 감지되었습니다.잠시 후 다시 시도해 주세요."
        ).is_visible()
        auto_detect = await self.page.get_by_label("자동접속방지 체크박스를 확인해주세요").is_visible()
        if invalid_login_detect or auto_detect:
            print("Invliad login popup")
            await self.page.get_by_role("button", name="확인").click()
            await asyncio.sleep(2)
            click_frame = None
            show_frame = None
            frames = self.page.frames
            for frame in frames:
                print(frame.name)
                if "/api2/bframe" in frame.url:
                    show_frame = self.page.frame_locator(f'iframe[name="{frame.name}"]')
                if "/api2/anchor" in frame.url:
                    click_frame = self.page.frame_locator(
                        f'iframe[name="{frame.name}"]'
                    )
            await click_frame.get_by_label("로봇이 아닙니다.").click()
            await show_frame.get_by_role("button", name="음성 보안문자 듣기").click()
            test = await show_frame.get_by_role(
                "link", name="또는 오디오를 MP3로 다운로드하세요."
            ).get_attribute("href")
            print(test)
            print(f"curl {test} --output stt/audio.mp3")
            await asyncio.sleep(1)
            urllib.request.urlretrieve(test, "stt/audio.mp3")
            response = sample_recognize("stt/audio.mp3")
            if response:
                print(response)
                await show_frame.get_by_label("들리는 대로 입력하세요.").fill(response)
                await show_frame.get_by_role("button", name="확인").click()
                await self.page.get_by_role("button", name="로그인", exact=True).click()
                await self.page.wait_for_selector("div.profile_img")
            else:
                print("stt 실패")
        else:
            print("로그인 성공")
            return True

    async def goto_url(self, url: str):
        """url 이동"""
        await self.page.goto(url)

    async def refresh(self):
        """refresh"""
        await self.page.reload()

    async def remove_video(self):
        """remove Video box"""
        await self.page.evaluate("document.querySelector('div.player-box').remove()")

    # async def chatting_example(self):
    #     """테스트용"""
    #     while True:
    #         cast_chat = self.page.locator(".castChat")
    #         chat_l_elements = await self.page.query_selector_all(".cht_l")
    #         for chat_l in chat_l_elements:
    #             userinner = await chat_l.query_selector(".nickname")
    #             chatinner = await chat_l.query_selector(".message")
    #             user = await userinner.inner_text()
    #             user = user.replace(":", "").strip()
    #             chat = await chatinner.inner_text()
    #             chat = chat.strip()
    #             print(user)
    #             print(chat)
    #             # if user == "크기가전부는아니자나여" or user == "24K™":
    #             #     await self.page.get_by_placeholder("채팅하기").fill(chat)
    #             #     await self.page.get_by_role("button", name="보내기").click()
    #             await chat_l.evaluate("(element) => element.remove()")
    #         await asyncio.sleep(0.1)
    #     return "haha"

    #######  night watch 관련 함수들 #######
    async def start_night_watch(self):
        """nightWatch 시작 함수"""
        self.wath_loop = True
        while self.wath_loop:
            for book_mark_id in self.bookmark_list:
                await self.set_book_mark(book_mark_id, True)
                asyncio.sleep(0.1)
            self.bookmark_list.clear()
            live_users = await self.get_user_status()
            print(live_users)
            await asyncio.sleep(10)

    async def get_user_status(self):
        """유저 상태"""
        ret_list = []
        if self.page.url != "https://www.pandalive.co.kr/pick#bookmark":
            print("북마크 페이지가 아닙니다. 북마크 페이지로 이동합니다.")
            await self.goto_url("https://www.pandalive.co.kr/pick#bookmark")
        tmp = self.page.locator("div.pickList ul")

        try:
            print(tmp)
            lists = await tmp.locator("li").element_handles()
            for lists_li in lists:
                photo = await lists_li.query_selector("div.photo")
                infor = await lists_li.query_selector("div.infor")
                live_span = await photo.query_selector("span")
                nickname = await infor.text_content()
                nickname = nickname.replace(" ", "").replace("\n", "")
                print(nickname)
                if live_span:
                    ret_list.append(nickname)
        except Exception as e:
            print("what the fuck")
            print(e)
        return ret_list

    async def set_book_mark(self, panda_id: str, state: bool):
        """북마크 세팅. state상태로 세팅함"""
        await self.goto_url(f"https://www.pandalive.co.kr/channel/{panda_id}/notice")
        asyncio.sleep(1)
        book_mark = await self.page.query_selector(".btn_bookmark")
        book_mark_class = await book_mark.get_attribute("class")
        # 이미 북마크가 되어있다면
        if "on" in book_mark_class:
            if state is False:
                await book_mark.click()
        # 북마크가 되어있지 않다면
        else:
            if state is True:
                await book_mark.click()

    async def add_book_mark_list(self, panda_id: str):
        """북마크 해야될 리스트에 추가"""
        self.bookmark_list.append(panda_id)

    async def stop(self):
        """awef"""
        self.wath_loop = False

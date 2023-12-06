""" this is night wiath.py"""
import asyncio
import os
import urllib.request
import emoji
from datetime import datetime
from playwright.async_api import async_playwright
from playwright.async_api import Page
from playwright.async_api import Browser
from playwright.async_api import BrowserContext
from pydantic import BaseModel  # pylint: disable=C0411
from dotenv import load_dotenv
from stt_v2 import sample_recognize

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
SERVER_KIND = os.getenv("SERVER_KIND")


class CreateManagerDto(BaseModel):
    """매니저 생성 DTO"""

    panda_id: str
    proxy_ip: str
    manager_id: str
    manager_pw: str
    resource_ip: str


class PandaManager:
    """PandaWrapper 클래스"""

    def __init__(self) -> None:
        self.page: Page
        self.browser = Browser
        self.context = BrowserContext

    async def create_playwright(self):
        """playwright 객체 생성"""
        try:
            apw = await async_playwright().start()
            if SERVER_KIND == "local":
                self.browser = await apw.chromium.launch(
                    headless=False,
                    # proxy={"server": f"{proxy_ip}:8888"}
                    # headless=HEADLESS,
                )
            else:
                self.browser = await apw.chromium.launch(headless=HEADLESS)
            self.context = await self.browser.new_context(
                viewport={"width": 1500, "height": 900},  # 원하는 해상도 크기를 지정하세요.
                locale="ko-KR",
            )
            self.page = await self.context.new_page()
            await self.page.goto("http://pandalive.co.kr")
            print(await self.page.title())
        except Exception as e:  # pylint: disable=W0703
            print(e)
        return True

    async def login(self, login_id: str = "xptmxmdyd123", login_pw: str = "Adkflfkd1"):
        """
        1. 팝업탭이 있는지 확인하고 팝업탭이 있다면 닫음
        2. 로그인 과정을 수행
        3. 로그인 과정을 수행한 뒤 로그인 프로필 이미지가 나타날때까지 대기
        4. bookmark 페이지로 이동
        """
        await self.page.get_by_role("button", name="닫기").click()
        await self.page.get_by_role("button", name="로그인 / 회원가입").click()
        await asyncio.sleep(0.3)
        await self.page.get_by_role("link", name="로그인 / 회원가입").click()
        await asyncio.sleep(0.3)
        await self.page.get_by_role("link", name="로그인").click()
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
        invalid_label_id = await self.page.get_by_label("존재하지 않는 사용자입니다.").is_visible()
        invalid_label_pw = await self.page.get_by_label(
            "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
        ).is_visible()
        if invalid_label_id or invalid_label_pw:
            print("popup Invalid Id or PW")
            await self.page.get_by_role("button", name="확인").click()
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
            await asyncio.sleep(1)
            # 리캡챠 떳는지 확인
            await show_frame.get_by_role("button", name="음성 보안문자 듣기").click()
            await asyncio.sleep(1)
            # 보안문자 떳는지 확인
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
                # 보안 문자 떳는지 확인
                await asyncio.sleep(1)
                await self.page.get_by_role("button", name="로그인", exact=True).click()
                await asyncio.sleep(1)
                await self.page.wait_for_selector("div.profile_img")
            else:
                print("STT Failed")
        else:
            print("로그인 성공")
            return True

    async def goto_url(self, url: str):
        """url 이동"""
        await self.page.goto(url)
        err_404 = await self.page.query_selector("div.err404")
        if err_404 is not None:
            await self.refresh()
            await asyncio.sleep(3)
            await self.goto_url(url)

    async def refresh(self):
        """refresh"""
        await self.page.reload()

    async def remove_elements(self):
        """remove other elements"""
        target = self.page.locator("#header")
        await target.evaluate("(element) => element.remove()")
        target = self.page.locator("#sideArea")
        await target.evaluate("(element) => element.remove()")
        target = self.page.locator(".live_left_area")
        await target.evaluate("(element) => element.remove()")

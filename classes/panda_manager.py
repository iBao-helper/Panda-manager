""" this is night wiath.py"""
import asyncio
import urllib.request
import emoji
from playwright.async_api import async_playwright
from playwright.async_api import Page
from playwright.async_api import Browser
from pydantic import BaseModel  # pylint: disable=C0411
import requests
from custom_exception import custom_exceptions as ex
from stt import sample_recognize
from util.my_util import getCommands


class CreateManagerDto(BaseModel):
    """매니저 생성 DTO"""

    proxy_ip: str
    nickname: str
    manager_id: str
    manager_pw: str
    resource_ip: str
    panda_id: str


class PandaManager:
    """PandaWrapper 클래스"""

    def __init__(self, body: CreateManagerDto) -> None:
        self.page: Page
        self.browser = Browser
        self.loop = False
        self.backend_url = "teemo-world.link"
        self.backend_port = "3000"
        self.data = body

    async def create_playwright(self, proxy_ip: str):
        """playwright 객체 생성"""
        try:
            apw = await async_playwright().start()
            self.browser = await apw.chromium.launch(
                headless=False, proxy={"server": f"{proxy_ip}:8888"}
            )
            context = await self.browser.new_context(
                viewport={"width": 1500, "height": 900}  # 원하는 해상도 크기를 지정하세요.
            )
            self.page = await context.new_page()
            await self.page.goto("http://pandalive.co.kr")
            print(await self.page.title())
        except Exception as e:
            raise ex.PlayWrightException(ex.PWEEnum.PD_CREATE_ERROR) from e
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
        await self.page.get_by_role("link", name="로그인 / 회원가입").click()
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
            raise ex.PlayWrightException(ex.PWEEnum.PD_LOGIN_INVALID_ID_OR_PW)
        invalid_label_id = await self.page.get_by_label("존재하지 않는 사용자입니다.").is_visible()
        invalid_label_pw = await self.page.get_by_label(
            "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
        ).is_visible()
        if invalid_label_id or invalid_label_pw:
            print("popup Invalid Id or PW")
            await self.page.get_by_role("button", name="확인").click()
            raise ex.PlayWrightException(ex.PWEEnum.PD_LOGIN_INVALID_ID_OR_PW)
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
            await asyncio.sleep(0.43)
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
                raise ex.PlayWrightException(ex.PWEEnum.PD_LOGIN_STT_FAILED)
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

    async def chatting_example(self, commands: list):
        """테스트용"""
        self.loop = True
        while self.loop:
            try:
                chat_l_elements = await self.page.query_selector_all(".cht_l")
                for chat_l in chat_l_elements:
                    userinner = await chat_l.query_selector(".nickname")
                    chatinner = await chat_l.query_selector(".message")
                    if userinner is None:
                        continue
                    user = await userinner.inner_text()
                    user = user.replace(":", "").strip()
                    chat = await chatinner.inner_text()
                    chat = chat.strip()
                    chat = emoji.demojize(chat)
                    print(user)
                    print(chat)
                    chat_split = chat.split(" ", 2)
                    if chat_split[0] == "!등록" and (
                        user is self.data.nickname or user == "크기가전부는아니자나여"
                    ):
                        response = requests.post(
                            url=f"http://{self.data.resource_ip}:3000/user/command",
                            json={
                                "pandaId": self.data.panda_id,
                                "key": chat_split[1],
                                "value": chat_split[2],
                            },
                            timeout=5,
                        )
                        print(response.text)
                        commands = await getCommands(self.data.panda_id)
                        await self.page.get_by_placeholder("채팅하기").fill(response.text)
                        await self.page.get_by_role("button", name="보내기").click()
                        await chat_l.evaluate("(element) => element.remove()")
                    elif chat_split[0] == "!삭제" and (
                        user is self.data.nickname or user == "크기가전부는아니자나여"
                    ):
                        response = requests.delete(
                            url=f"http://{self.data.resource_ip}:3000/user/command",
                            json={
                                "panda_id": self.data.panda_id,
                                "keyword": chat_split[1],
                            },
                            timeout=5,
                        )
                        print(response.text)
                        commands = await getCommands(self.data.panda_id)
                        await self.page.get_by_placeholder("채팅하기").fill(response.text)
                        await self.page.get_by_role("button", name="보내기").click()
                        await chat_l.evaluate("(element) => element.remove()")
                    for command in commands:
                        if command["keyword"] == chat:
                            await self.page.get_by_placeholder("채팅하기").fill(
                                emoji.emojize(command["response"])
                            )
                            await self.page.get_by_role("button", name="보내기").click()
                    await chat_l.evaluate("(element) => element.remove()")
                await asyncio.sleep(0.1)
            except Exception as e:  # pylint: disable=W0718
                print(e)

        return "haha"

    #######  manager 관련 유틸 함수들 #######
    def filter_dict_by_list(self, my_dict, my_list):
        """list중 dict안에 존재하는 요소만 반납"""
        ret_list = []
        for user in my_list:
            print(user["nickname"])
            if user["nickname"] in my_dict:
                ret_list.append(user["panda_id"])
        return ret_list

    async def stop(self):
        """awef"""
        self.loop = False

    async def destroy(self):
        """free memory"""
        self.loop = False
        await self.browser.close()

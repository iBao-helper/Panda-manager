""" this is night wiath.py"""
import asyncio
import os
import urllib.request
from datetime import datetime
import emoji
from playwright.async_api import async_playwright
from playwright.async_api import Page
from playwright.async_api import Browser
from playwright.async_api import ElementHandle
from playwright.async_api import BrowserContext
from playwright.async_api import FrameLocator
from pydantic import BaseModel  # pylint: disable=C0411

import requests
from dotenv import load_dotenv
from classes.channel_api_data import ChannelApiData

from custom_exception import custom_exceptions as ex
from stt_v2 import sample_recognize
from util.my_util import (
    User,
    error_in_chatting_room,
    get_commands,
    get_greet_message,
    get_greet_toggle,
    get_hart_message,
    get_hart_toggle,
    get_pr_message,
    get_pr_period,
    get_pr_toggle,
    get_rc_message,
    get_rc_toggle,
    logging_debug,
    logging_error,
)

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

    def __init__(self, body: CreateManagerDto) -> None:
        self.page: Page
        self.browser = Browser
        self.context = BrowserContext
        self.loop = False
        self.backend_url = BACKEND_URL
        self.backend_port = BACKEND_PORT
        self.user: User
        self.data = body
        self.commands = []
        self.song_list = []
        self.is_pr_message_sendable = False
        self.song_message_boolean = False
        self.command_executed = False
        self.command_list = [
            "!등록",
            "!삭제",
            "!사용법",
            "!추천",
            "!하트",
            "!써칭",
            "!합계",
            "!타이머",
            "!꺼",
            "!신청",
            "!리스트",
        ]
        self.timer_message_boolean = False
        self.timer_complete = False
        self.time = 0
        self.channel_api = ChannelApiData()
        self.new_users = []
        print(f"data = {self.data}")

    async def create_playwright(self, proxy_ip: str):
        """playwright 객체 생성"""
        try:
            apw = await async_playwright().start()
            if SERVER_KIND == "local":
                self.browser = await apw.chromium.launch(
                    headless=HEADLESS,
                    proxy={"server": f"{proxy_ip}:8888"}
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
            self.data.proxy_ip = proxy_ip
            raise ex.PlayWrightException(
                ex.PWEEnum.PD_CREATE_ERROR, message=f"[create_playwright] - {str(e)}"
            ) from e
        return True

    async def login(self, login_id: str = "xptmxmdyd123", login_pw: str = "Adkflfkd1"):
        """
        1. 팝업탭이 있는지 확인하고 팝업탭이 있다면 닫음
        2. 로그인 과정을 수행
        3. 로그인 과정을 수행한 뒤 로그인 프로필 이미지가 나타날때까지 대기
        4. bookmark 페이지로 이동
        """
        await self.page.get_by_role("button", name="닫기").click()
        await logging_debug(
            self.data.panda_id, "[login] - 닫기", {"debug_message": "닫기 성공"}
        )
        await self.page.get_by_role("button", name="로그인 / 회원가입").click()
        await logging_debug(
            self.data.panda_id, "[login] - 회원가입 버튼 클릭", {"debug_message": "로그인 / 회원가입"}
        )
        await asyncio.sleep(0.3)
        await self.page.get_by_role("link", name="로그인 / 회원가입").click()
        await logging_debug(
            self.data.panda_id,
            "[login] - 로그인 / 회원가입 링크 클릭",
            {"debug_message": "로그인 / 회원가입"},
        )
        await asyncio.sleep(0.3)
        await self.page.get_by_role("link", name="로그인").click()
        await logging_debug(
            self.data.panda_id, "[login] - 로그인 링크 클릭", {"debug_message": "로그인"}
        )
        await self.page.get_by_role("textbox").nth(1).fill(login_id)
        await self.page.get_by_role("textbox").nth(2).fill(login_pw)
        await asyncio.sleep(2)
        await self.page.get_by_role("button", name="로그인", exact=True).click()
        await logging_debug(
            self.data.panda_id, "[login] - 로그인 버튼 클릭", {"debug_message": "로그인"}
        )
        await asyncio.sleep(2)
        invalid_text_id = await self.page.get_by_text("존재하지 않는 사용자입니다.").is_visible()
        invalid_text_pw = await self.page.get_by_text(
            "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
        ).is_visible()
        await logging_debug(
            self.data.panda_id,
            "[invalid-visible check]",
            {"id": invalid_text_id, "pw": invalid_text_pw},
        )
        if invalid_text_id or invalid_text_pw:
            print("Invalid Id or PW")
            raise ex.PlayWrightException(
                ex.PWEEnum.PD_LOGIN_INVALID_ID_OR_PW,
                panda_id=self.data.panda_id,
                resource_ip=self.data.resource_ip,
                message="아디 비번 틀렸음",
            )
        invalid_label_id = await self.page.get_by_label("존재하지 않는 사용자입니다.").is_visible()
        invalid_label_pw = await self.page.get_by_label(
            "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
        ).is_visible()
        await logging_debug(
            self.data.panda_id,
            "[invalid-visible check]",
            {"id": invalid_text_id, "pw": invalid_text_pw},
        )
        if invalid_label_id or invalid_label_pw:
            print("popup Invalid Id or PW")
            await self.page.get_by_role("button", name="확인").click()
            raise ex.PlayWrightException(
                ex.PWEEnum.PD_LOGIN_INVALID_ID_OR_PW,
                panda_id=self.data.panda_id,
                resource_ip=self.data.resource_ip,
                message="아뒤 비번 틀렸음(팝업)",
            )
        invalid_login_detect = await self.page.get_by_label(
            "비정상적인 로그인이 감지되었습니다.잠시 후 다시 시도해 주세요."
        ).is_visible()
        auto_detect = await self.page.get_by_label("자동접속방지 체크박스를 확인해주세요").is_visible()
        await logging_debug(
            self.data.panda_id,
            "[invalid-login_detect check]",
            {"invalid_login_detect": invalid_login_detect, "auto_detect": auto_detect},
        )
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
            await logging_debug(
                self.data.panda_id, "[로봇이 아닙니다]", {"debug_message": "로봇이 아닙니다."}
            )
            await asyncio.sleep(1)
            # 리캡챠 떳는지 확인
            await self.check_popup_recaptcha_failed(show_frame)
            await show_frame.get_by_role("button", name="음성 보안문자 듣기").click()
            await logging_debug(
                self.data.panda_id, "[음성 보안문자 듣기]", {"debug_message": "음성 보안문자 듣기"}
            )
            await asyncio.sleep(1)
            # 보안문자 떳는지 확인
            await self.check_popup_recaptcha_failed(show_frame)
            test = await show_frame.get_by_role(
                "link", name="또는 오디오를 MP3로 다운로드하세요."
            ).get_attribute("href")
            await logging_debug(
                self.data.panda_id, "[음성 보안문자 듣기] - 다운로드 주소", {"debug_message": test}
            )
            await asyncio.sleep(1)
            urllib.request.urlretrieve(test, "stt/audio.mp3")
            response = sample_recognize("stt/audio.mp3")
            if response:
                print(response)
                await show_frame.get_by_label("들리는 대로 입력하세요.").fill(response)
                await show_frame.get_by_role("button", name="확인").click()
                await logging_debug(
                    self.data.panda_id,
                    "[들리는대로 입력하세요 확인]",
                    {"debug_message": "들리는대로 입력하세요 확인"},
                )
                # 보안 문자 떳는지 확인
                await asyncio.sleep(1)
                await self.check_popup_recaptcha_failed(show_frame)
                await self.page.get_by_role("button", name="로그인", exact=True).click()
                await logging_debug(
                    self.data.panda_id, "마지막 로그인", {"debug_message": "마지막 로그인"}
                )
                await asyncio.sleep(1)
                await self.check_popup_recaptcha_failed(show_frame)
                await self.page.wait_for_selector("div.profile_img")
            else:
                print("stt 실패")
                raise ex.PlayWrightException(
                    ex.PWEEnum.PD_LOGIN_STT_FAILED,
                    panda_id=self.data.panda_id,
                    resource_ip=self.data.resource_ip,
                    message="stt에 실패함",
                )
        else:
            print("로그인 성공")
            return True

    async def goto_url(self, url: str):
        """url 이동"""
        await self.page.goto(url)
        err_404 = await self.page.query_selector("div.err404")
        if err_404 is not None:
            await logging_error(self.data.panda_id, "404에러", {"debug_message": "404에러"})
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

    async def chat_command_register_delete(self, splited_chat: list):
        """채팅 매크로 등록/삭제 처리"""
        try:
            if splited_chat[0] == "!등록":
                if len(splited_chat) >= 3:
                    response = requests.post(
                        url=f"http://{self.backend_url}:{self.backend_port}/bj/command/{self.user.panda_id}",
                        json={
                            "key": splited_chat[1],
                            "value": splited_chat[2],
                        },
                        timeout=5,
                    )
                    self.commands = await get_commands(self.user.panda_id)
                    await self.chatting_send("등록되었습니다")
                    return True
                else:
                    await self.chatting_send("유효한 형태가 아닙니다/\n[!등록] [키워드] [응답]")
                    return True
            elif splited_chat[0] == "!삭제":
                if len(splited_chat) >= 2:
                    response = requests.delete(
                        url=f"http://{self.backend_url}:{self.backend_port}/bj/command/{self.user.panda_id}",
                        json={
                            "key": splited_chat[1],
                        },
                        timeout=5,
                    )
                    print(response.text)
                    response = response.text
                    self.commands = await get_commands(self.user.panda_id)
                    await self.chatting_send(response)
                    return True
                else:
                    await self.chatting_send("유효한 포멧이 아닙니다/\n[!삭제] [키워드]")
                    return True
        except Exception as e:  # pylint: disable=W0718
            print(e)
            return False

    async def handle_command(
        self,
        chat_user: str,
        chat: str,
        splited_chat: list,
        data: CreateManagerDto,
        chat_l: ElementHandle,
    ):
        """명령어를 처리하기 위한 로직"""
        try:
            if splited_chat[0] == "!사용법":
                await self.chatting_send(
                    "사용법은 아래와 같습니다.\n!등록 [키워드] [응답]\n!삭제 [키워드]\n!추천 [메세지]\n!하트 [메세지]\n!써칭 [닉네임]\n!합계 [닉네임]\n!타이머 [시간] [알림간격]"
                )
            elif (splited_chat[0] == "!등록" or splited_chat[0] == "!삭제") and (
                chat_user == data.nickname
                or chat_user == "크기가전부는아니자나여"
                or chat_user == "FS시혈_FUXK금붕어"
            ):
                response = await self.chat_command_register_delete(splited_chat)
                return response
            elif splited_chat[0] == "!추천" or splited_chat[0] == "!하트":
                if splited_chat[0] == "!추천":
                    recommand_message = " ".join(splited_chat[1:])
                    response = await self.regist_recommand_message(recommand_message)
                elif splited_chat[0] == "!하트":
                    recommand_message = " ".join(splited_chat[1:])
                    response = await self.regist_hart_message(recommand_message)
            elif splited_chat[0] == "!써칭" or splited_chat[0] == "!합계":
                response = await self.get_hart_history(splited_chat[0], splited_chat[1])
            elif splited_chat[0] == "!타이머":
                if len(splited_chat) == 3:
                    asyncio.create_task(
                        self.set_timer(int(splited_chat[1]), int(splited_chat[2]))
                    )
                elif len(splited_chat) == 2:
                    asyncio.create_task(self.set_timer(int(splited_chat[1])))

            elif splited_chat[0] == "!꺼":
                # 비동기 호출
                await self.stop_timer()
            elif splited_chat[0] == "!신청":
                await self.regist_song(" ".join(splited_chat[1:]))
            elif splited_chat[0] == "!리스트":
                await self.send_song_list(chat_user)
            return True

        except:  # pylint: disable=W0702
            return False

    def check_command(self, chat, user: bool):
        """
        채팅이 채팅메크로에 일치하는지 검사
        이전 명령어를 실행하여 flag가 True라면 채팅매크로를 실행하지 않음
        """
        # 위에서 커맨드를 실행했거나 매니저가 친 채팅이라면
        if user == self.user.manager_nick:
            return None
        for command in self.commands:
            if command["keyword"] == chat:
                return command["response"]
        return None

    async def chatting_handler(self):
        """채팅 핸들러"""
        try:
            chat_l_elements = await self.page.query_selector_all(".cht_l")
            for chat_l in chat_l_elements:
                userinner = await chat_l.query_selector(".nickname")
                chatinner = await chat_l.query_selector(".message")
                # 임시땜빵용 특정 큰손들같은 경우 셀렉터가 다름
                if userinner is None:
                    continue
                user = await userinner.inner_text()
                user = user.replace(":", "").strip()
                chat = await chatinner.inner_text()
                chat = chat.strip()
                chat = emoji.demojize(chat)
                chat_split = chat.split(" ", 2)
                # 명령어 리스트중에 있는지 검사하고
                if chat_split:
                    if chat_split[0] in self.command_list:
                        # 명령어가 있다면 명령어를 처리
                        self.command_executed = await self.handle_command(
                            user, chat, chat_split, self.user, chat_l
                        )
                        # 이후 진행을 할지 안할지 command_executed로 세팅
                        if self.command_executed is True:
                            await chat_l.evaluate("(element) => element.remove()")
                            continue
                    command_response = self.check_command(chat, user)
                    if command_response is not None:
                        self.command_executed = True
                        await self.chatting_send(command_response)
                    await chat_l.evaluate("(element) => element.remove()")
        except Exception as e:  # pylint: disable=W0718
            print("chatting handler")
            print(e)

    async def hart_handler(self):
        """하트 핸들러"""
        try:
            hart_elements = await self.page.query_selector_all(".cht_hart_new")
            for hart_box in hart_elements:
                hart_info = await hart_box.query_selector(".hart_info")
                hart_user_tag = await hart_info.query_selector("p")
                hart_user = (await hart_user_tag.inner_text()).strip().replace("님이", "")
                hart_count_tag = await hart_info.query_selector("b")
                hart_count = (
                    (await hart_count_tag.inner_text()).strip().replace("개", "")
                )
                await hart_box.evaluate("(element) => element.remove()")
                print(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), hart_user, hart_count
                )
                if self.user.hart_message != "":
                    response_recommand_message = self.user.hart_message.replace(
                        r"{hart_user}", hart_user
                    ).replace(r"{hart_count}", hart_count)
                    await self.chatting_send(response_recommand_message)
                requests.post(
                    url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/hart-history/{self.user.nickname}",
                    json={
                        "user_name": emoji.emojize(hart_user),
                        "count": hart_count,
                    },
                    timeout=5,
                )
        except Exception as e:  # pylint: disable=W0718
            print("hart handler")
            print(e)

    async def recommand_handler(self):
        """추천 핸들러"""
        try:
            recommand_elements = await self.page.query_selector_all(".cht_al.cht_al_1")
            for recommand_element in recommand_elements:
                recommand_message = await recommand_element.inner_text()
                if "매니저" in recommand_message:
                    continue
                if "채팅금지" in recommand_message:
                    continue
                user_name = recommand_message.split(" ")[0].replace("님께서", "")
                await recommand_element.evaluate("(element) => element.remove()")
                if self.user.rc_message != "":
                    response_recommand_message = self.user.rc_message.replace(
                        r"{user_name}", user_name
                    )
                    await self.chatting_send(response_recommand_message)
        except Exception as e:  # pylint: disable=W0718
            print("recommand handler")
            print(e)

    async def new_user_handler(self):
        """새로운 유저 핸들러"""
        if len(self.new_users) > 0:
            combined_str = ", ".join(self.new_users)
            self.new_users = []
            await self.chatting_send(f"'{combined_str}' 님 어서오세요~!")

    async def macro(self):
        """테스트용"""
        self.loop = True
        self.commands = await get_commands(self.user.panda_id)
        asyncio.create_task(self.pr_timer())
        print("[Receive default commands]", self.commands)
        while self.loop:
            self.command_executed = False
            try:
                await self.chatting_handler()
                if self.user.toggle_hart:
                    await self.hart_handler()
                if self.user.toggle_rc:
                    await self.recommand_handler()
                if self.user.toggle_pr:
                    await self.pr_handler()
                if self.user.toggle_greet:
                    await self.new_user_handler()
                await self.timer_handler()

                await asyncio.sleep(0.1)
            except Exception as e:  # pylint: disable=W0718
                print(e)
        return "haha"

    #######  manager 관련 유틸 함수들 #######
    async def check_popup_recaptcha_failed(self, show_frame: FrameLocator):
        """popup recaptcha failed"""
        retry_detect = await show_frame.get_by_text("나중에 다시 시도해 주세요").is_visible()
        print("retry_detect", retry_detect)
        if retry_detect:
            print("잦은 재시도 탐지에 걸림")
            await logging_error(
                self.data.panda_id, "잦은 재시도 탐지에 걸림", {"debug_message": "잦은 재시도 탐지에 걸림"}
            )
            raise ex.PlayWrightException(
                ex.PWEEnum.PD_LOGIN_STT_FAILED,
                panda_id=self.data.panda_id,
                message="잦은 재시도 탐지에 걸림",
            )

    async def find_element(self, selector: str, is_pass: bool):
        """
        특정 요소를 셀렉터로 찾습니다. is_pass가 true라면 존재하지 않아도 통과합니다.
        없다면 에러를 발생시킵니다.
        """

    async def regist_recommand_message(self, rc_message):
        """Request update recommand message"""
        try:
            response = requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/recommand-message/{self.user.panda_id}",
                json={"message": rc_message},
                timeout=5,
            )
            self.user.rc_message = response.text
            await self.chatting_send("추천 메세지가 등록되었습니다")
            return True
        except:  # pylint: disable=W0702
            return False

    async def regist_hart_message(self, rc_message):
        """Request update hart message"""
        try:
            response = requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/hart-message/{self.user.panda_id}",
                json={"message": rc_message},
                timeout=5,
            )
            self.user.hart_message = response.text
            await self.chatting_send("하트 메세지가 등록되었습니다")
            return True
        except:  # pylint: disable=W0702
            return False

    async def get_hart_history(self, command, user):
        """하드 내역 조회"""
        try:
            if command == "!써칭":
                response = requests.get(
                    f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/hart-history/{emoji.emojize(user)}?mode=search",
                    timeout=5,
                )
                json_data = response.json()
                print("써칭 리스폰스", json_data)
                message = ""
                if len(json_data) > 0:
                    for data in json_data:
                        message = (
                            message
                            + f"[{data['user_name']}] -> [{data['bj_name']}] ♥{data['count']}개\n"
                        )
                    await self.chatting_send(message)
                else:
                    await self.chatting_send(
                        f"{user}님의 하트 내역이 없습니다. 하트 내역은 매니저봇이 있는 방에서만 집계됩니다."
                    )
                return True
            elif command == "!합계":
                response = requests.get(
                    url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/hart-history/{emoji.emojize(user)}?mode=sum",
                    timeout=5,
                )
                print(response)
                message = f"{user} : {response.text}개"
                await self.chatting_send(message)
                return True
        except:  # pylint: disable=W0702
            return False  # pylint: disable=W0702

    async def timer_handler(self):
        """타이머 핸들러. 타이머메세지를 출력해야한다면 출력"""
        if self.timer_message_boolean and self.time > 0:
            time_min = self.time // 60
            time_sec = self.time % 60
            await self.chatting_send(f"{time_min}분 {time_sec}초 남았습니다")
            self.timer_message_boolean = False
        if self.timer_complete:
            self.timer_complete = False
            self.time = 0
            await self.chatting_send("타이머가 완료되었습니다")

    async def set_timer(self, time: int, time_period: int = 60):
        """타이머 설정"""
        if self.time > 0:
            return
        self.time = time
        time_min = self.time // 60
        time_sec = self.time % 60
        await self.chatting_send(
            f"{time_min}분 {time_sec}초 / {time_period}초 간격으로 알람이 설정되었습니다"
        )
        count = 0
        while self.time >= 1:
            count += 1
            self.time = self.time - 1
            if count == time_period:
                self.timer_message_boolean = True
                count = 0
            if self.time <= 5:
                self.timer_message_boolean = True
            print(self.time)
            await asyncio.sleep(1)
        self.timer_complete = True
        self.timer_message_boolean = True

    async def stop_timer(self):
        """타이머 정지"""
        self.time = 0

    async def stop(self):
        """awef"""
        self.loop = False

    async def destroy(self):
        """free memory"""
        self.loop = False
        self.time = 0
        await self.browser.close()

    def set_user(self, user):
        """사용된 user data 세팅"""
        self.user = user

    async def regist_song(self, song):
        """신청곡 추가"""
        if song in self.song_list:
            await self.chatting_send("이미 신청한 곡입니다.")
            return
        self.song_list.append(song)
        await self.chatting_send(f"'{song}' 신청되었습니다.")
        self.song_message_boolean = True

    async def send_song_list(self, chat_user):
        """신청곡 리스트 보내기"""
        message = "신청곡 리스트\n"
        for song in self.song_list:
            message += f"{song}\n"
        if len(self.song_list) > 0 and chat_user == self.user.nickname:
            self.song_list.remove(self.song_list[0])
        await self.chatting_send(message)

    async def pr_handler(self):
        """일정 주기마다 안내메시지 발송하는 핸들러"""
        if self.is_pr_message_sendable:
            await self.chatting_send(self.user.pr_message)
            self.is_pr_message_sendable = False

    async def update_commands(self):
        """커맨드 업데이트"""
        if self.user:
            self.commands = await get_commands(self.user.panda_id)

    async def update_recommend(self):
        """커맨드 업데이트"""
        if self.user:
            response = await get_rc_message(self.user.panda_id)
            self.user.rc_message = response.text
            print(self.user.rc_message)

    async def update_hart_message(self):
        """커맨드 업데이트"""
        if self.user:
            response = await get_hart_message(self.user.panda_id)
            self.user.hart_message = response.text
            print(self.user.hart_message)

    async def update_greet_message(self):
        """커맨드 업데이트"""
        if self.user:
            response = await get_greet_message(self.user.panda_id)
            self.user.greet_message = response.text
            print(self.user.hart_message)

    async def update_pr(self):
        """PR 업데이트"""
        if self.user:
            pr_message = await get_pr_message(self.user.panda_id)
            self.user.pr_message = pr_message.text
            print(self.user.pr_message)

            pr_period = await get_pr_period(self.user.panda_id)
            self.user.pr_period = int(pr_period.text)
            print(self.user.pr_period)

    async def toggle_rc(self):
        """RC 토글 업데이트"""
        if self.user:
            response = await get_rc_toggle(self.user.panda_id)
            self.user.toggle_rc = response.json()
            print(self.user.toggle_rc)

    async def toggle_hart(self):
        """Hart 토글 업데이트"""
        if self.user:
            response = await get_hart_toggle(self.user.panda_id)
            self.user.toggle_hart = response.json()
            print(self.user.toggle_hart)

    async def toggle_pr(self):
        """PR 토글 업데이트"""
        if self.user:
            response = await get_pr_toggle(self.user.panda_id)
            self.user.toggle_pr = response.json()
            print(self.user.toggle_pr)

    async def toggle_greet(self):
        """Greet 토글 업데이트"""
        if self.user:
            response = await get_greet_toggle(self.user.panda_id)
            self.user.toggle_greet = response.json()
            print(self.user.toggle_greet)

    async def pr_timer(self):
        """신청곡 타이머"""
        while True:
            time = self.user.pr_period
            while time > 0:
                time -= 1
                await asyncio.sleep(1)
            self.is_pr_message_sendable = True

    async def send_screenshot(self):
        """백엔드서버에 스크린샷 보냄"""
        await self.page.screenshot(path=self.data.panda_id + ".png")
        files = {
            "file": (
                self.data.panda_id + ".png",
                open(self.data.panda_id + ".png", "rb"),
                "image/png",
            )
        }
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log/upload",
            files=files,
            timeout=20,
        )

    async def chatting_send(self, message):
        """채팅 전송"""
        try:
            await self.page.get_by_placeholder("채팅하기").fill(emoji.emojize(message))
            await self.page.get_by_role("button", name="보내기").click()
        except Exception as e:  # pylint: disable=W0718, W0612
            await self.send_screenshot()
            await logging_error(
                self.data.panda_id,
                "채팅 보내기 실패",
                {"panda_id": self.data.panda_id},
            )
            await error_in_chatting_room(self.data.panda_id)

    async def set_interceptor(self):
        """인터셉터 설정"""
        await self.context.route(
            "**/channel_user_count*", self.intercept_channel_user_count
        )

    async def intercept_channel_user_count(self, route, request):
        """채널의 유저 수를 요청을 인터셉트 하는 함수"""
        if self.channel_api.is_list_enabled():
            response = await self.channel_api.send_channel_user_count()
            self.new_users = await self.channel_api.get_new_users()
            await route.fulfill(
                status=response.status_code,
                headers=response.headers,
                body=response.text,
            )
        else:
            query = request.url.split("?")[1].split("&")
            channel = query[0].split("=")[1]
            token = query[1].split("=")[1]
            self.channel_api.set_data(request.headers, channel=channel, token=token)
            await route.continue_()

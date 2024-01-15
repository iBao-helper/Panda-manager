"""팬더 매니저 V2"""
import asyncio
import json
import time
import websockets
from classes.api_client import APIClient
from classes.chatting_data import ChattingData
from util.my_util import (
    User,
    add_song_list,
    delete_normal_command,
    delete_song_list,
    get_bj_data,
    get_commands,
    get_hart_history_with_three,
    get_hart_history_with_total,
    get_song_list,
    logging_error,
    logging_info,
    regist_hart_message,
    regist_normal_command,
    regist_recommend_message,
    update_bj_nickname,
    update_manager_nickanme,
)


class PandaManager2:
    """팬더 매니저를 담당하는 클래스"""

    def __init__(
        self,
        panda_id: str,
        sess_key: str,
        user_idx: str,
        proxy_ip: str,
        manager_nick: str,
    ):
        self.api_client = APIClient(panda_id=panda_id, proxy_ip=proxy_ip)
        self.api_client.set_login_data(sess_key, user_idx)
        self.panda_id = panda_id
        self.manager_nick = manager_nick
        self.is_running = False
        self.websocket = None
        self.websocket_url = "wss://chat-ws.neolive.kr/connection/websocket"
        self.user_data = None
        self.normal_commands = []
        self.api_commands = {
            "!등록": self.regist_normal_command,
            "!삭제": self.delete_normal_command,
            "!추천": self.regist_recommend_message,
            "!하트": self.regist_hart_message,
            "!써칭": self.hart_search_by_three,
            "!합계": self.hart_search_by_total,
            "!신청": self.add_song_list,
            "!리스트": self.send_song_list,
            "!신청곡리셋": self.reset_song_list,
        }
        self.reserved_commands = [
            "!타이머",
            "!꺼",
        ]

    async def reset_song_list(self):
        """신청곡 초기화"""
        response = await delete_song_list(self.panda_id)
        if response.status_code == 200 or response.status_code == 201:
            await self.api_client.send_chatting("신청곡 리스트가 초기화 되었습니다")
        else:
            await self.api_client.send_chatting("백엔드 서버가 맛탱이가 갔습니다! 죄송합니당! 문의넣어주세욤!")

    async def send_song_list(self):
        """신청곡 리스트 보내기"""
        message = "신청곡 리스트\n"
        song_list = await get_song_list(self.panda_id)
        if song_list.status_code == 200 or song_list.status_code == 201:
            song_list = song_list.json()
            print(song_list)
            for song in song_list:
                message += f"{song}\n"
            await self.api_client.send_chatting(message)
        else:
            await self.api_client.send_chatting("백엔드 서버가 맛탱이가 갔습니다! 죄송합니당! 문의넣어주세욤!")

    async def add_song_list(self, user_nickname: str, song_name: str):
        """신청곡 추가"""
        response = await add_song_list(self.panda_id, user_nickname, song_name)
        if response.status_code == 200 or response.status_code == 201:
            await self.api_client.send_chatting(f"'{song_name}' 신청되었습니다.")
        else:
            await self.api_client.send_chatting("백엔드 서버가 맛탱이가 갔습니다! 죄송합니당! 문의넣어주세욤!")

    async def hart_search_by_total(self, user_nickname: str):
        """하트내역 모두 조회"""
        response = await get_hart_history_with_total(user_nickname)
        if response is not None:
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("하트내역 조회에 실패했습니다")

    async def hart_search_by_three(self, user_nickname: str):
        """최근 하트내역 3개 조회"""
        response = await get_hart_history_with_three(user_nickname)
        if response is not None:
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("하트내역 조회에 실패했습니다")

    async def delete_normal_command(self, splited: []):
        """일반 커맨드 삭제"""
        response = await delete_normal_command(self.panda_id, splited[0])
        if response is not None:
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("삭제에 실패했습니다")

    async def regist_normal_command(self, splited: []):
        """일반 커맨드 등록"""
        response = await regist_normal_command(self.panda_id, splited[0], splited[1])
        if response is not None:
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("등록에 실패했습니다")

    async def regist_hart_message(self, splited: []):
        """!하트 맵핑 핸들러"""
        response = await regist_hart_message(self.panda_id, splited.join(" "))
        if response is not None:
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("등록에 실패했습니다")

    async def regist_recommend_message(self, splited: []):
        """!하트 맵핑 핸들러"""
        response = await regist_recommend_message(self.panda_id, splited.join(" "))
        if response is not None:
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("등록에 실패했습니다")

    async def connect_webscoket(self):
        """웹소켓에 연결을 시도함"""
        await logging_info(self.panda_id, "웹소켓 연결 작업 시작", {})
        result = await self.api_client.play(self.panda_id)
        if result is None:
            return None
        message = {
            "id": 1,
            "params": {
                "name": "js",
                "token": self.api_client.jwt_token,  # 실제 토큰 값
            },
        }
        extra_headers = {
            "authority": "api.pandalive.co.kr",
            "method": "POST",
            "path": "/v1/member/login",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "accept-language": "ko",
            "content-length": "37",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.pandalive.co.kr",
            "referer": "https://www.pandalive.co.kr/",
            "sec-ch-ua": '"Not_A Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Device-Info": '{"t":"webPc","v":"1.0","ui":0}',
        }
        self.websocket = await websockets.connect(
            uri=self.websocket_url, extra_headers=extra_headers
        )
        if self.websocket:
            print("websocket = ", self.websocket)
            await logging_info(self.panda_id, "웹소켓 연결 성공", {})
            await self.websocket.send(json.dumps(message))
            response = await self.websocket.recv()
            print(f"서버로부터 메시지 수신: {response}")
            message = {
                "id": 2,
                "method": 1,
                "params": {"channel": str(self.api_client.channel)},
            }
            await self.websocket.send(json.dumps(message))
            response = await self.websocket.recv()
            print(f"서버로부터 메시지 수신: {response}")
        return self.websocket

    async def check_nickname_changed(self):
        """닉네임 변경시 반영하기 위한 로직"""
        bj_info = await self.api_client.search_bj(self.panda_id)
        self.user_data: User = await get_bj_data(panda_id=self.panda_id)
        if bj_info.nick != self.user_data.nickname:
            await update_bj_nickname(self.panda_id, bj_info.nick)
        if self.manager_nick != self.user_data.manager_nick:
            await update_manager_nickanme(self.panda_id, self.manager_nick)

    ## 조건 리턴 함수
    def is_self_chatting(self, chat: ChattingData):
        """매니저봇의 채팅인지 확인"""
        return chat.nickname == self.manager_nick

    def is_chatting(self, chat: ChattingData):
        """채팅인지 확인"""
        if chat.type == "bj" or chat.type == "chatter" or chat.type == "manager":
            return True
        return False

    def is_system_message(self, chat: ChattingData):
        """하트,추천,정보갱신 인지 확인"""
        if (
            chat.type == "SponCoin"
            or chat.type == "Recommend"
            or chat.type == "MediaUpdate"
        ):
            return True
        return False

    ## 핸들러 관련 함수
    async def chatting_handler(self, chat: ChattingData):
        """채팅일때의 처리"""
        # 여기다 다 때려박기에는........ 너무 드럽잖아.....
        # 근데 각 함수마다 원하는 인자 데이터가 달라...
        # dict로 만들어서 호출하기에도 무리고..

        return

    async def start(self):
        """팬더 매니저 시작"""
        # 닉네임이 변경된 게 있다면 업데이트
        await self.check_nickname_changed()
        # 명령어 관련 정보 가져옴
        self.normal_commands = await get_commands(self.panda_id)

        self.is_running = True
        while self.is_running:
            try:
                data = await self.websocket.recv()
                chat = ChattingData(data)
                if self.is_self_chatting(chat):
                    continue
                elif self.is_chatting(chat):
                    await self.chatting_handler(chat)
                    k = 9
                elif self.is_system_message(chat):
                    # system_handler
                    k = 9

                print(chat)
            except websockets.exceptions.ConnectionClosedOK:
                break

    async def stop(self):
        """팬더 매니저 종료"""
        try:
            message = {
                "id": 2,
                "method": 2,
                "params": {"channel": str(self.api_client.channel)},
            }
            await self.websocket.send(json.dumps(message))
            self.is_running = False
        except:  # pylint: disable=W0702
            pass
        await self.websocket.close()
        # 웹소켓에 나간다는 웹소켓 메세지 전송하고
        # self.is_runiing = false로 바꿈

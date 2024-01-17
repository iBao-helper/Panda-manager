"""팬더 매니저 V2"""
import asyncio
import json
import websockets
from classes.api_client import APIClient
from classes.chatting_data import ChattingData
from util.my_util import (
    User,
    add_room_user,
    add_song_list,
    delete_normal_command,
    delete_song_list,
    error_in_chatting_room,
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
    remove_room_user,
    send_hart_history,
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
        self.user: User = None

        # 현재 방 유저 갱신하기 위한 변수들
        self.user_list = []
        self.prev_user_list = []
        ###

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
        self.system_commands = {
            "SponCoin": self.spon_coin_handler,
            "Recommend": self.recommend_handler,
        }
        self.reserved_commands = {
            "!랭킹": self.get_ranking,
            # "!타이머",
            # "!꺼",
        }

    #####################
    # API 커맨드 함수들
    #####################
    async def reset_song_list(self, chat: ChattingData):  # pylint: disable=W0613
        """신청곡 초기화"""
        response = await delete_song_list(self.panda_id)
        if response.status_code == 200 or response.status_code == 201:
            await self.api_client.send_chatting("신청곡 리스트가 초기화 되었습니다")
        else:
            await self.api_client.send_chatting("백엔드 서버가 맛탱이가 갔습니다! 죄송합니당! 문의넣어주세욤!")

    async def send_song_list(self, chat: ChattingData):  # pylint: disable=W0613
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

    async def add_song_list(self, chat: ChattingData):
        """신청곡 추가"""
        splited = chat.message.split(" ")
        if len(splited) < 2:
            await self.api_client.send_chatting("ex)\n!신청 [곡명]")
            return
        response = await add_song_list(
            self.panda_id, chat.nickname, " ".join(splited[1:])
        )
        if response.status_code == 200 or response.status_code == 201:
            await self.api_client.send_chatting(f"{' '.join(splited[1:])}' 신청되었습니다.")
        else:
            await self.api_client.send_chatting("백엔드 서버가 맛탱이가 갔습니다! 죄송합니당! 문의넣어주세욤!")

    async def hart_search_by_total(self, chat: ChattingData):
        """하트내역 모두 조회"""
        response = await get_hart_history_with_total(chat.nickname)
        if response is not None:
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("하트내역 조회에 실패했습니다")

    async def hart_search_by_three(self, chat: ChattingData):
        """최근 하트내역 3개 조회"""
        response = await get_hart_history_with_three(chat.nickname)
        if response is not None:
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("하트내역 조회에 실패했습니다")

    async def delete_normal_command(self, chat: ChattingData):
        """일반 커맨드 삭제"""
        splited = chat.message.split(" ")
        if len(splited) < 2 and (
            chat.type in ("manager", "bj") or chat.nickname is "크기가전부는아니자나연"
        ):
            await self.api_client.send_chatting("ex)\n!삭제 [커맨드]")
            return
        response = await delete_normal_command(self.panda_id, splited[1])
        if response is not None:
            if splited[1] in self.normal_commands:
                del self.normal_commands[splited[1]]
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("삭제에 실패했습니다")

    async def regist_normal_command(self, chat: ChattingData):
        """일반 커맨드 등록"""
        splited = chat.message.split(" ")
        if len(splited) < 3 and (
            chat.type in ("manager", "bj") or chat.nickname is "크기가전부는아니자나연"
        ):
            await self.api_client.send_chatting("ex)\n!등록 [커맨드] [메세지]")
            return
        response = await regist_normal_command(
            self.panda_id, splited[1], " ".join(splited[2:])
        )
        if response is not None:
            if response != "이미 등록된 커맨드입니다":
                self.normal_commands[splited[1]] = " ".join(splited[2:])
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("등록에 실패했습니다")

    async def regist_hart_message(self, chat: ChattingData):
        """!하트 맵핑 핸들러"""
        splited = chat.message.split(" ")
        if len(splited) < 2 and (
            chat.type in ("manager", "bj") or chat.nickname is "크기가전부는아니자나연"
        ):
            await self.api_client.send_chatting("ex)\n!하트 {후원인}님 {후원개수}개 감사합니다~")
            return
        response = await regist_hart_message(self.panda_id, " ".join(splited[1:]))
        if response is not None:
            self.user.hart_message = " ".join(splited[1:])
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("등록에 실패했습니다")

    async def regist_recommend_message(self, chat: ChattingData):
        """!추천 맵핑 핸들러"""
        splited = chat.message.split(" ")
        if len(splited) < 2 and (
            chat.type in ("manager", "bj") or chat.nickname is "크기가전부는아니자나연"
        ):
            await self.api_client.send_chatting("ex)\n!추천 {추천인}님 추천 감사합니다~")
            return
        response = await regist_recommend_message(self.panda_id, " ".join(splited[1:]))
        if response is not None:
            self.user.rc_message = " ".join(splited[1:])
            await self.api_client.send_chatting(response)
        else:
            await self.api_client.send_chatting("등록에 실패했습니다")

    async def get_ranking(self, chat: ChattingData):  # pylint: disable=W0613
        """랭킹 조회 함수"""
        bj_info = await self.api_client.search_bj(self.panda_id)
        await self.api_client.send_chatting(f"현재 BJ랭킹은 {bj_info.rank}위 입니다")

    #######################
    # system handler 함수들
    #######################
    async def spon_coin_handler(self, message_class):
        """하트 후원 핸들러"""
        if self.user.toggle_hart is False:
            return
        chat_message = self.user.hart_message
        # if "rk" in message_class:
        #     if message_class["rk"] != 0:
        #         chat_message = f"팬 랭킹{message_class['rk']}위!\n" + chat_message
        if "nick" in message_class:
            chat_message = chat_message.replace("{후원인}", message_class["nick"])
        if "coin" in message_class:
            chat_message = chat_message.replace("{후원개수}", str(message_class["coin"]))
        await send_hart_history(
            bj_name=self.user.nickname,
            user_id=message_class["id"],
            nickname=message_class["nick"],
            hart_count=message_class["coin"],
        )
        await self.api_client.send_chatting(chat_message)
        print(chat_message)

    async def recommend_handler(self, message_class):
        """추천 핸들러"""
        if self.user.toggle_rc is False:
            return
        rc_message = self.user.rc_message
        if "nick" in message_class:
            rc_message = rc_message.replace("{추천인}", message_class["nick"])
        print(rc_message)
        await self.api_client.send_chatting(rc_message)

    # 웹 소켓 연결 함수
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

    # user정보 업데이트 및 닉네임 체크해서 갱신해주는 함수
    async def check_nickname_changed(self):
        """닉네임 변경시 반영하기 위한 로직"""
        bj_info = await self.api_client.search_bj(self.panda_id)
        self.user: User = await get_bj_data(panda_id=self.panda_id)
        if bj_info.nick != self.user.nickname:
            await update_bj_nickname(self.panda_id, bj_info.nick)
        if self.manager_nick != self.user.manager_nick:
            await update_manager_nickanme(self.panda_id, self.manager_nick)

    async def update_room_list(self):
        """방에 있는 유저를 갱신시키는 함수"""
        room_user_list = await self.api_client.get_current_room_user()
        if room_user_list is None:
            return [], []
        self.prev_user_list = self.user_list
        self.user_list = {
            user["nick"] for user in room_user_list if user["nick"] != "게스트"
        }
        # Set으로 구현하여 700명 풀방일 경우 49만번의 연산이 일어나는것을 방지
        new_users = {user for user in self.user_list if user not in self.prev_user_list}
        idle_users = {
            user for user in self.prev_user_list if user not in self.user_list
        }
        return new_users, idle_users

    ###############
    # 조건 리턴 함수
    ###############
    def is_self_chatting(self, chat: ChattingData):
        """매니저봇의 채팅인지 확인"""
        return chat.nickname == self.manager_nick

    def is_user_chatting(self, chat: ChattingData):
        """채팅인지 확인"""
        if chat.type == "bj" or chat.type == "chatter" or chat.type == "manager":
            return True
        return False

    def is_system_message(self, chat: ChattingData):
        """하트,추천,정보갱신 인지 확인"""
        if chat.type == "SponCoin" or chat.type == "Recommend":
            return True
        return False

    ## 핸들러 관련 함수
    async def chatting_handler(self, chat: ChattingData):
        """사용자 채팅일때의 처리"""
        splited = chat.message.split(" ")
        if splited[0] in self.api_commands:  # 명령어가 api를 호출하는 명령어일 경우
            await self.api_commands[splited[0]](chat)
        elif chat.message in self.normal_commands:  # 일반 key-value 명령어일 경우
            await self.api_client.send_chatting(self.normal_commands[chat.message])
        elif chat.message in self.reserved_commands:  # 그 외 기능적인 예약어일 경우
            await self.reserved_commands[chat.message](chat)
        return

    async def system_handler(self, chat: ChattingData):
        """추천,하트,정보갱신 등의 처리"""
        chat_message_class = json.loads(chat.message)
        await self.system_commands[chat.type](chat_message_class)

    async def update_room_user_timer(self):
        """방 유저 갱신 타이머"""
        while self.is_running:
            new_users, idle_users = await self.update_room_list()
            if len(new_users) > 0:
                await add_room_user(self.panda_id, new_users)
                if self.user.toggle_greet:
                    combined_str = ", ".join(new_users)
                    message = self.user.greet_message.replace(r"{list}", combined_str)
                    await self.api_client.send_chatting(message)
            if len(idle_users) > 0:
                await remove_room_user(self.panda_id, idle_users)
            await asyncio.sleep(2)

    async def update_jwt_refresh(self):
        """JWT 토큰 갱신"""
        await asyncio.sleep(60 * 25)
        while self.is_running:
            await self.api_client.refresh_token()
            message = {
                "id": 68,
                "method": 10,
                "params": {"token": self.api_client.jwt_token},
            }
            await self.websocket.send(json.dumps(message))
            await asyncio.sleep(60 * 25)

    async def pr_handler(self):
        """PR 핸들러"""
        await asyncio.sleep(self.user.pr_period)
        while self.is_running and self.user.toggle_pr:
            bj_info = await self.api_client.search_bj(self.panda_id)
            chat_message = (
                self.user.pr_message.replace("{추천}", str(bj_info.score_like))
                .replace("{즐찾}", str(bj_info.score_bookmark))
                .replace("{시청}", str(bj_info.score_watch))
                .replace("{총점}", str(bj_info.score_total))
                .replace("{팬}", str(bj_info.fan_cnt))
                .replace("{랭킹}", str(bj_info.rank))
                .replace("{월방송}", str(bj_info.play_time.month))
                .replace("{총방송}", str(bj_info.play_time.total))
            )
            print("PR메세지", chat_message)
            await self.api_client.send_chatting(chat_message)
            await asyncio.sleep(self.user.pr_period)

    async def update_commands(self):
        """커맨드 업데이트"""
        result = await get_commands(self.panda_id)
        if result is not None:
            self.normal_commands = result

    async def update_user(self):
        """유저 관련 데이터 업데이트"""
        result = await get_bj_data(self.panda_id)
        if result is not None:
            self.user = result

    async def start(self):
        """팬더 매니저 시작"""
        self.is_running = True
        # 닉네임이 변경된 게 있다면 업데이트
        await self.check_nickname_changed()
        # 명령어 관련 정보 가져옴
        await self.update_commands()
        print(self.normal_commands)
        if self.user.toggle_pr:
            asyncio.create_task(self.pr_handler())
        asyncio.create_task(self.update_room_user_timer())
        asyncio.create_task(self.update_jwt_refresh())
        while self.is_running:
            try:
                data = await self.websocket.recv()
                try:
                    chat = ChattingData(data)
                except Exception as e:  # pylint: disable=W0718
                    await logging_error(
                        panda_id=self.panda_id,
                        description="웹소켓 read Error",
                        data=str(e),
                    )
                    continue
                if chat.type is None:
                    continue
                elif self.is_self_chatting(chat):
                    continue
                elif self.is_user_chatting(chat):
                    await self.chatting_handler(chat)
                elif self.is_system_message(chat):
                    await self.system_handler(chat)
                elif chat.type == "personal":
                    await logging_error(self.panda_id, "다른기기에 접속하였습니다", {})
                    await error_in_chatting_room(self.panda_id)
            except websockets.exceptions.ConnectionClosedOK:
                break

    async def stop(self):
        """팬더 매니저 종료"""
        try:
            self.is_running = False
            message = {
                "id": 2,
                "method": 2,
                "params": {"channel": str(self.api_client.channel)},
            }
            await self.websocket.send(json.dumps(message))
        except:  # pylint: disable=W0702
            pass
        await self.websocket.close()
        # 웹소켓에 나간다는 웹소켓 메세지 전송하고
        # self.is_runiing = false로 바꿈

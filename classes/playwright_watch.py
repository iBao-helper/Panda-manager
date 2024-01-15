"""playwright용 nightwatch"""
import os

import requests
from classes.api_client import APIClient


class PlayWrightNightWatch:
    """playwright를 이용한 NightWatch 모듈"""

    def __init__(self, watch_id: str, watch_pw: str):
        self.watch_id = watch_id
        self.watch_pw = watch_pw
        self.sess_key = None  # 세션키를 저장할 변수
        self.user_idx = None  # panda서버의 유저 인덱스
        self.backend_url = os.getenv("BACKEND_URL")
        self.backend_port = os.getenv("BACKEND_PORT")
        self.public_ip = os.getenv("PUBLIC_IP")
        self.api_client = APIClient()

    async def login(self):
        """로그인"""
        await self.api_client.login(self.watch_id, self.watch_pw)

    async def start(self):
        """NightWatch Loop 함수"""
        try:
            # print("[start night watch] - BookMark Start")
            idle_users, live_users = await self.get_user_status()
            print(live_users)
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

    async def get_user_status(self):
        """유저 상태를 가져옴"""
        user_datas = await self.api_client.get_bookmark_list()
        idle_users = [
            user["userId"] for user in user_datas if user.get("media") is None
        ]
        live_users = [
            user["userId"]
            for user in user_datas
            if user.get("media") is not None
            and user["media"]["liveType"] != "rec"
            and user["media"]["isPw"] is False
        ]
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

    async def add_book_mark_list(self, panda_id: str):
        """북마크 해야될 리스트에 추가"""
        await self.api_client.add_book_mark(panda_id)

    async def delete_book_mark_list(self, panda_id: str):
        """북마크 삭제해야될 리스트에 추가"""
        await self.api_client.delete_book_mark(panda_id)

    async def refresh(self):
        """새로고침"""
        self.api_client = APIClient()
        await self.api_client.login(self.watch_id, self.watch_pw)
        # await self.page.reload()

    async def get_nickname_by_panda_id(self, panda_id: str):
        """panda_id로 팬더 백엔드 서버에 요청한 닉네임을 가져오기"""
        nickname = await self.api_client.get_nickname_by_panda_id(panda_id)
        return nickname

    async def get_bookmark_list_to_nickname(self):
        """북마크 리스트를 닉네임으로 가져오기"""
        return await self.api_client.get_bookmark_list_to_nickname()

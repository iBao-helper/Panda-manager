"""팬더백엔드 서버에 API를 호출하는 클래스"""

import time
from urllib.parse import quote
import emoji
import requests
from classes.bj_info import BjInfo
from fastapi import HTTPException

from util.my_util import (
    callback_login_failure,
    delete_bj_manager_by_panda_id,
    logging_error,
    logging_info,
)


class APIClient:
    """API를 호출하는 클래스"""

    def __init__(self, panda_id="로그인 전용 객체", proxy_ip=""):
        self.panda_id = panda_id
        self.default_header: dict = {
            "authority": "api.pandalive.co.kr",
            "method": "POST",
            "scheme": "https",
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate, br",
            "Accept-Language": "ko,ko-KR;q=0.9",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.pandalive.co.kr",
            "referer": "https://www.pandalive.co.kr/",
            "sec-ch-ua": '"Not_A Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "Windows",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Device-Info": '{"t":"webPc","v":"1.0","ui":24229319}',
        }
        self.sess_key = None
        self.user_idx = None
        self.chat_token = None
        self.jwt_token = None
        self.channel = None
        self.room_id = None
        self.is_manager = None
        self.proxy_ip = proxy_ip

    async def request_api_call(self, url, data, headers):
        """API 호출하는 함수"""
        if self.proxy_ip == "":
            response = requests.post(url=url, headers=headers, data=data, timeout=5)
        else:
            response = requests.post(
                url=url,
                headers=headers,
                data=data,
                timeout=30,
                proxies={
                    "http": f"http://{self.proxy_ip}:8888",
                    "https": f"http://{self.proxy_ip}:8888",
                },
            )
        if response.status_code == 200:
            return response.json()
        await logging_error(
            self.panda_id, "API 호출 실패", {"response": response.json()}
        )
        raise Exception(response.json()["message"])  # pylint: disable=W0719

    async def login(self, login_id, login_pw, panda_id):
        """
        팬더서버에 로그인 요청하는 함수, 결과값으로 매니저의 닉네임을 리턴함
        비밀번호가 변경되었을 경우 매니저 해제 요청 + 프록시 제거 요청을 보냄
        """
        login_url = "https://api.pandalive.co.kr/v1/member/login"
        dummy_header = self.default_header.copy()
        data = f"id={login_id}&pw={login_pw}&idSave=N"
        dummy_header["path"] = "/v1/member/login"
        dummy_header["content-length"] = str(len(data))
        try:
            result = await self.request_api_call(login_url, data, dummy_header)
        except Exception as e:  # pylint: disable=W0703
            await logging_error(
                self.panda_id,
                "[로그인 실패]",
                {"login_id": login_id, "login_pw": login_pw, "data": str(e)},
            )
            # 매니저의 비밀번호가 변경되었다면 여기서 등록됐던 manager 제거, 이후 None을 보고 Proxy 제거
            if "비밀번호" in str(e):
                await delete_bj_manager_by_panda_id(panda_id)
            await callback_login_failure(panda_id)
            return None  # pylint: disable=W0719 W0707
        login_info = result["loginInfo"]
        self.sess_key = login_info["sessKey"]
        self.user_idx = login_info["userInfo"]["idx"]
        print(self.sess_key, self.user_idx)
        return login_info["userInfo"]["nick"]

    async def get_login_data(self):
        """로그인 데이터를 얻는 함수"""
        if self.sess_key is not None and self.user_idx is not None:
            return self.sess_key, self.user_idx
        await logging_error(self.panda_id, "[로그인 데이터 없음]", {})
        raise Exception("로그인이 필요합니다")  # pylint: disable=W0719

    def set_login_data(self, sess_key, user_idx):
        """로그인 데이터를 설정하는 함수"""
        self.sess_key = sess_key
        self.user_idx = user_idx

    async def search_bj(self, panda_id: str) -> BjInfo:
        """BJ검색 API 호출"""
        if self.sess_key is None or self.user_idx is None:
            raise Exception("로그인이 필요합니다")  # pylint: disable=W0719
        search_bj_url = "https://api.pandalive.co.kr/v1/member/bj"
        dummy_header = self.default_header.copy()
        data = f"userId={panda_id}&info=media%20fanGrade%20bookmark"
        dummy_header["path"] = "/v1/member/bj"
        dummy_header["content-length"] = str(len(data))
        dummy_header["cookie"] = (
            f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        )
        try:
            result = await self.request_api_call(search_bj_url, data, dummy_header)
        except Exception as e:  # pylint: disable=W0703
            await logging_error(
                self.panda_id,
                "[BJ 검색 실패]",
                {"panda_id": panda_id, "data": str(e)},
            )
            return None  # pylint: disable=W0719 W0707
        bj_info = BjInfo(result["bjInfo"])
        return bj_info

    async def get_user_idx(self, panda_id):
        """search_bj를 호출하여 user_idx를 얻는 함수"""
        response = await self.search_bj(panda_id)
        return response.idx

    async def add_book_mark(self, panda_id):
        """panda_id를 북마크에 추가하는 함수"""
        user_idx = await self.get_user_idx(panda_id)
        add_bookmark_url = "https://api.pandalive.co.kr/v1/bookmark/add"
        dummy_header = self.default_header.copy()
        data = f"userIdx={user_idx}"
        dummy_header["path"] = "/v1/bookmark/add"
        dummy_header["content-length"] = str(len(data))
        dummy_header["cookie"] = (
            f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        )
        try:
            result = await self.request_api_call(add_bookmark_url, data, dummy_header)
        except Exception as e:  # pylint: disable=W0703
            await logging_error(
                self.panda_id,
                "[북마크 추가 실패]",
                {"panda_id": panda_id, "data": str(e)},
            )
            return None  # pylint: disable=W0719 W0707
        return result

    async def delete_book_mark(self, panda_id):
        """panda_id를 북마크에서 삭제하는 함수"""
        user_idx = await self.get_user_idx(panda_id)
        delete_bookmark_url = "https://api.pandalive.co.kr/v1/bookmark/delete"
        dummy_header = self.default_header.copy()
        data = f"userIdx%5B0%5D={user_idx}"
        dummy_header["path"] = "/v1/bookmark/delete"
        dummy_header["content-length"] = str(len(data))
        dummy_header["cookie"] = (
            f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        )
        try:
            result = await self.request_api_call(
                delete_bookmark_url,
                data,
                dummy_header,
            )
        except Exception as e:  # pylint: disable=W0703
            await logging_error(
                self.panda_id,
                "[북마크 제거 실패]",
                {"panda_id": panda_id, "data": str(e)},
            )
            return None  # pylint: disable=W0719 W0707
        return result

    async def get_nickname_by_panda_id(self, panda_id):
        """panda_id를 통해 닉네임을 얻는 함수"""
        response = await self.search_bj(panda_id)
        if response is None:
            return None
        print(response)
        return response.nick

    async def get_bookmark_list(self):
        """북마크 리스트를 얻는 함수"""
        if self.sess_key is None or self.user_idx is None:
            raise Exception("로그인이 필요합니다")  # pylint: disable=W0719
        book_mark_url = "https://api.pandalive.co.kr/v1/live/bookmark"
        dummy_header = self.default_header.copy()
        data = "offset=0&limit=200&isLive=&hideOnly=N"
        dummy_header["path"] = "/v1/live/bookmark"
        dummy_header["content-length"] = str(len(data))
        dummy_header["cookie"] = (
            f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        )
        try:
            result = await self.request_api_call(book_mark_url, data, dummy_header)
        except Exception as e:  # pylint: disable=W0703
            await logging_error(
                self.panda_id,
                "[북마크 리스트 호출 실패]",
                {"data": str(e)},
            )
            return None  # pylint: disable=W0719 W0707
        return result["list"]

    async def get_bookmark_list_to_nickname(self):
        """북마크 닉네임 리스트를 얻는 함수"""
        book_mark_list = await self.get_bookmark_list()
        if book_mark_list is None:
            return None
        filtered_list = [user["userNick"] for user in book_mark_list]
        return filtered_list

    async def play(self, panda_id):
        """방송 시청 API 호출, 아마 방송에 대한 정보를 받는 API일듯"""
        if self.sess_key is None or self.user_idx is None:
            await logging_error(
                panda_id=self.panda_id,
                description="로그인 정보가 필요합니다",
                data={"sess_key": self.sess_key, "user_idx": self.user_idx},
            )
            return None
        play_url = "https://api.pandalive.co.kr/v1/live/play"
        data = f"action=watch&userId={panda_id}&password=&shareLinkType="
        dummy_header = self.default_header.copy()
        dummy_header["path"] = "/v1/live/play"
        dummy_header["content-length"] = str(len(data))
        dummy_header["cookie"] = (
            f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        )
        try:
            result = await self.request_api_call(play_url, data, dummy_header)
        except Exception as e:  # pylint: disable=W0703
            await logging_error(
                self.panda_id,
                "[play API 호출 실패]",
                {"data": str(e)},
            )
            return None  # pylint: disable=W0719 W0707
        await logging_info(self.panda_id, "[play API 결과]", result)
        try:
            self.chat_token = result["chatServer"]["token"]
            self.jwt_token = result["token"]
            self.channel = result["media"]["userIdx"]
            self.room_id = result["media"]["code"]
            self.is_manager = result["fan"]["isManager"]
            return result
        except Exception as e:  # pylint: disable=W0703
            await logging_error(
                self.panda_id,
                "[play API 결과 파싱 실패]",
                {"error": str(e), "result": result},
            )
            return None

    async def get_current_room_user(self):
        """새로 들어온 유저를 반환하는 함수"""
        if self.is_manager is False:
            return None
        room_list_url = (
            "https://api.pandalive.co.kr/v1/chat/channel_user_list?"
            f"channel={self.channel}&token={self.jwt_token}"
        )
        dummy_header = self.default_header.copy()
        dummy_header["path"] = (
            f"/v1/chat/channel_user_list?channel={self.channel}&token={self.jwt_token}"
        )
        dummy_header["cookie"] = (
            f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        )
        try:
            response = requests.get(
                url=room_list_url, headers=self.default_header, timeout=5
            )
            tmp = response.json()["list"]
            return tmp
        except:  # pylint: disable= W0702
            return None

    async def refresh_token(self):
        """토큰 갱신하는 요청"""
        refresh_token_url = "https://api.pandalive.co.kr/v1/chat/refresh_token"
        data = f"channel={self.channel}&token={self.jwt_token}"
        dummy_header = self.default_header.copy()
        dummy_header["path"] = "/v1/chat/refresh_token"
        dummy_header["content-length"] = str(len(data))
        dummy_header["cookie"] = (
            f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        )
        try:
            result = await self.request_api_call(refresh_token_url, data, dummy_header)
            if "token" in result:
                print(result["token"])
                self.jwt_token = result["token"]
        except Exception as e:  # pylint: disable=W0703
            await logging_error(
                self.panda_id,
                "[refresh_token API 호출 실패]",
                {"data": str(e)},
            )
            return None  # pylint: disable=W0719 W0707
        return result

    async def send_chatting(self, message):
        """채팅을 보내는 함수"""
        if self.sess_key is None or self.user_idx is None:
            await logging_error(
                panda_id=self.panda_id,
                description="로그인 정보가 필요합니다",
                data={"sess_key": self.sess_key, "user_idx": self.user_idx},
            )
            return None
        if (
            self.chat_token is None
            or self.jwt_token is None
            or self.channel is None
            or self.room_id is None
        ):
            await logging_error(
                panda_id="정보없음",
                description="Play API를 호출했을때의 정보가 필요합니다",
                data={
                    "chat_token": self.chat_token,
                    "jwt_token": self.jwt_token,
                    "channel": self.channel,
                    "room_id": self.room_id,
                },
            )
            return None  # pylint: disable=W0719
        chat_url = "https://api.pandalive.co.kr/v1/chat/message"
        data = f"message={quote(message)}&roomid={self.room_id}&chatToken={self.chat_token}&t={int(time.time())}&channel={self.channel}&token={self.jwt_token}"
        dummy_header = self.default_header.copy()
        dummy_header["path"] = "/v1/chat/message"
        dummy_header["content-length"] = str(len(data))
        dummy_header["cookie"] = (
            f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        )
        try:
            result = await self.request_api_call(chat_url, data, dummy_header)
        except Exception as e:  # pylint: disable=W0703
            await logging_error(
                self.panda_id,
                "[chatting API 호출 실패]",
                {"data": str(e)},
            )
            return None  # pylint: disable=W0719 W0707
        return result

    async def guest_login(self):
        """게스트 로그인"""
        guest_login_url = "https://api.pandalive.co.kr/v1/member/login_info"
        dummy_header = self.default_header.copy()
        data = {}
        try:
            result = await self.request_api_call(guest_login_url, data, dummy_header)
        except Exception as e:  # pylint: disable=W0703
            print(str(e))
            await logging_error(
                self.panda_id,
                "[게스트 로그인 실패]",
                {"data": str(e)},
            )
            return HTTPException(status_code=409, detail="게스트 로그인 실패")
        login_info = result["loginInfo"]
        self.sess_key = login_info["sessKey"]
        self.user_idx = ""
        print(self.sess_key, self.user_idx)
        return self.sess_key

    async def guest_play(self, panda_id):
        """방송 시청 API 호출, 아마 방송에 대한 정보를 받는 API일듯"""
        play_url = "https://api.pandalive.co.kr/v1/live/play"
        data = f"action=watch&userId={panda_id}&password=&shareLinkType="
        dummy_header = self.default_header.copy()
        dummy_header["path"] = "/v1/live/play"
        dummy_header["content-length"] = str(len(data))
        dummy_header["cookie"] = f"sessKey={self.sess_key};"
        result = await self.request_api_call(play_url, data, dummy_header)
        print(result)
        # await logging_info(self.panda_id, "[view_play API 결과]", result)
        try:
            self.chat_token = result["chatServer"]["token"]
            self.jwt_token = result["token"]
            self.channel = result["media"]["userIdx"]
            self.room_id = result["media"]["code"]
            self.is_manager = result["fan"]["isManager"]
            return result
        except Exception as e:  # pylint: disable=W0703
            await logging_error(
                self.panda_id,
                "[play API 결과 파싱 실패]",
                {"error": str(e), "result": result},
            )
            raise HTTPException(status_code=409, detail=str(e)) from e

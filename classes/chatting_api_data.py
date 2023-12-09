"""채팅 요청에 관련된 Api에 필요한 데이터"""

import requests
from urllib.parse import quote


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
        self.message = quote(message)

    async def send_chatting_message(self):
        """채널의 유저 수를 요청하는 함수"""
        url = "https://api.pandalive.co.kr/v1/chat/message"
        if self.valid:
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
                response = requests.post(
                    url, headers=self.headers, data=post_data, timeout=5
                )
                json = response.json()
                if json["result"] is False:
                    self.valid = False
                return True
            except Exception as e:  # pylint: disable= W0702
                print("채팅 요청에 실패했습니다.")
                print(e)
                self.valid = False
                return False
        else:
            return False

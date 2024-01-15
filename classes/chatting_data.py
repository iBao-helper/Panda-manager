"""채팅 클래스"""


import json
import pprint


class ChattingData:
    """웹소켓 채팅 데이터 클래스"""

    def __init__(self, chatting_data):
        chatting_data = json.loads(chatting_data)
        result = chatting_data["result"]
        self.offset = result.get("offset", None)
        self.level = result["data"]["data"].get("lev", 0)
        self.nickname = result["data"]["data"].get("nk", None)
        self.ranking = result["data"]["data"].get("rk", 99)
        self.message = result["data"]["data"].get("message", "")
        self.type = result["data"]["data"].get("type", None)
        self.sex = result["data"]["data"].get("sex", "U")

    def __str__(self):
        return pprint.pformat(self.__dict__, indent=4)

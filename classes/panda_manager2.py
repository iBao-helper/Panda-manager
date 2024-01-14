"""팬더 매니저 V2"""
from classes.api_client import APIClient
from util.my_util import logging_error, logging_info


class PandaManager2:
    """팬더 매니저를 담당하는 클래스"""

    def __init__(self, panda_id: str, sess_key: str, user_idx: str):
        self.api_client = APIClient()
        self.api_client.set_login_data(sess_key, user_idx)
        self.panda_id = panda_id

    async def connect_webscoket(self):
        """웹소켓에 연결을 시도함"""
        await logging_info(self.panda_id, "웹소켓 연결 작업 시작", {})
        try:
            await self.api_client.play(self.panda_id)
        except Exception as e:  # pylint: disable=W0718
            print(e)
            print("play요청 실패")
            await logging_error(self.panda_id, "play요청 실패", e)

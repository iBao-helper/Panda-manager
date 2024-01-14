"""팬더 매니저 V2"""
import json
import time
from classes.api_client import APIClient
from util.my_util import logging_error, logging_info
import websockets


class PandaManager2:
    """팬더 매니저를 담당하는 클래스"""

    def __init__(self, panda_id: str, sess_key: str, user_idx: str, proxy_ip: str):
        self.api_client = APIClient(panda_id=panda_id, proxy_ip=proxy_ip)
        self.api_client.set_login_data(sess_key, user_idx)
        self.panda_id = panda_id
        self.is_running = False
        self.websocket = None
        self.websocket_url = "wss://chat-ws.neolive.kr/connection/websocket"

    async def connect_webscoket(self):
        """웹소켓에 연결을 시도함"""
        await logging_info(self.panda_id, "웹소켓 연결 작업 시작", {})
        result = await self.api_client.play(self.panda_id)
        if result is None:
            return None
        user_data = {
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
            await self.websocket.send(json.dumps(user_data))
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

    async def start(self):
        """팬더 매니저 시작"""
        self.is_running = True
        while self.is_running:
            ## 매크로 작업중
            time.sleep(1)

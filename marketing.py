from dataclasses import dataclass
import json
import threading
from time import sleep
from typing import Optional

from pydantic import BaseModel
import websockets
from classes.chatting_data import ChattingData
from classes.panda_manager import PandaManager
from classes.api_client import APIClient
from classes.total_ip_manager import TotalIpManager
import asyncio

from util.my_util import TrackerData, get_all_managers, send_hart_history
from view import (
    connect_websocket,
    update_jwt_refresh,
)

api_client = APIClient()
tim = TotalIpManager()
tim.sort_ips()
websockets_dict = {}

current_watching = []
lock = threading.Lock()
duplicate_lock = threading.Lock()


class WebsocketData:
    """대리접속 관련 데이터 클래스"""

    def __init__(
        self,
        websocket: websockets.WebSocketClientProtocol,
        api_client: APIClient,
        tracker_data: TrackerData,
        proxy_ip: str,
    ):
        self.websocket = websocket
        self.api_client = api_client
        self.request_data = tracker_data
        self.proxy_ip = proxy_ip


async def update_jwt_refresh(
    api_client: APIClient,
    websocket: websockets.WebSocketClientProtocol,
):
    """JWT 토큰 갱신"""
    await asyncio.sleep(60 * 20)
    while api_client.panda_id in current_watching:
        await api_client.refresh_token()
        message = {
            "id": 3,
            "method": 10,
            "params": {"token": api_client.jwt_token},
        }
        await websocket.send(json.dumps(message))
        await asyncio.sleep(60 * 20)


async def viewbot_start(
    api_client: APIClient,
    websocket: websockets.WebSocketClientProtocol,
    tracker_data: TrackerData,
):
    global tim
    """팬더 매니저 시작"""
    # 닉네임이 변경된 게 있다면 업데이트
    asyncio.create_task(update_jwt_refresh(api_client=api_client, websocket=websocket))

    tim.decrease_ip(api_client.proxy_ip)
    while tracker_data.panda_id in current_watching:
        try:
            data = await websocket.recv()
            try:
                chat = ChattingData(data)
                if chat.type is None:
                    continue
                if chat.type == "SponCoin":
                    chat_message_class = json.loads(chat.message)
                    await send_hart_history(
                        bj_name=f"{tracker_data.panda_id}",
                        user_id=chat_message_class["id"],
                        nickname=chat_message_class["nick"],
                        hart_count=chat_message_class["coin"],
                    )
                elif chat.type == "personal":
                    print("이런일은 일어나지 않음. ")
            except Exception as e:  # pylint: disable=W0718 W0612
                pass
        except websockets.exceptions.ConnectionClosedOK as e:
            # 정상 종료됨
            break
        except websockets.exceptions.ConnectionClosedError as e:
            break
        except websockets.exceptions.ConnectionClosed as e:
            break
        except Exception as e:  # pylint: disable=W0703
            break


async def main():
    # 5분마다 실행될 쓰레드 생성
    api_client = APIClient("siveriness00", "pandalive", "")
    await api_client.login("42papawolf", "Ehdrn0990!PD", "")
    await api_client.play("siveriness00")
    message = {
        "id": 1,
        "params": {
            "name": "js",
            "token": api_client.jwt_token,  # 실제 토큰 값
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
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  # pylint: disable=C0301
        "X-Device-Info": '{"t":"webPc","v":"1.0","ui":0}',
    }
    websocket_url = "wss://chat-ws.neolive.kr/connection/websocket"
    websocket = await websockets.connect(
        uri=websocket_url,
        extra_headers=extra_headers,
    )
    await websocket.send(json.dumps(message))
    response = await websocket.recv()
    print(f"서버로부터 메시지 수신: {response}")
    message = {
        "id": 2,
        "method": 1,
        "params": {"channel": str(api_client.channel)},
    }
    await websocket.send(json.dumps(message))
    response = await websocket.recv()
    print(f"서버로부터 메시지 수신: {response}")
    while True:
        await asyncio.sleep(50)


if __name__ == "__main__":
    asyncio.run(main())

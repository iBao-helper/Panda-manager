"""
AWS EC2에서 돌아갈 View Server
한 서버당 4명의 유저를 접속관리함
"""

import asyncio
import json
import threading
from typing import Optional, Dict
import uvicorn
import requests
import websockets

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse

from classes.api_client import APIClient
from util.my_util import (
    logging_error,
    logging_info,
)

class WebsocketData:
    """대리접속 관련 데이터 클래스"""

    def __init__(
        self, websocket: websockets.WebSocketClientProtocol, api_client: APIClient
    ):
        self.websocket = websocket
        self.api_client = api_client

app = FastAPI()
app.counter = 0
app.ws_dict = {}


BACKEND_URL = "175.200.191.11"

async def connect_websocket(token: str, channel: str):
    """웹소켓 연결 하는 함수"""
    message = {
        "id": 1,
        "params": {
            "name": "js",
            "token": token,  # 실제 토큰 값
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
        "params": {"channel": str(channel)},
    }
    await websocket.send(json.dumps(message))
    response = await websocket.recv()
    print(f"서버로부터 메시지 수신: {response}")
    return websocket


async def process_guest(api_client: APIClient, panda_id: str, instance_id: str):
    """게스트를 처리하고 성공한다면 app.ws_dict에 추가"""
    await api_client.guest_login()
    await api_client.guest_play(panda_id=panda_id)
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
        origin=f"http://{api_client.proxy_ip}:8888",
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
    ws_data = WebsocketData(websocket, api_client)
    app.ws_dict[instance_id] = ws_data


@app.delete("/disconnect/{instance_id}")
async def disconnect_proxy(instance_id: str):
    """게스트 세션 끊기"""
    copy_dict: Dict[str, WebsocketData] = app.ws_dict
    print(len(copy_dict))
    if instance_id in copy_dict:
        print(app.ws_dict.keys())
        await copy_dict[instance_id].websocket.close()
        del app.ws_dict[instance_id]
        print(app.ws_dict.keys())
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "success"},
    )


async def refresh_ws():
    """웹소켓 리프레쉬"""
    while True:
        print("AA")
        await asyncio.sleep(60 * 20)


def run_refresh_ws():
    asyncio.set_event_loop(asyncio.new_event_loop())
    asyncio.run(refresh_ws())


@app.on_event("startup")
async def startup_event():
    """메인쓰레드 이벤트루프 설정"""
    threading.Thread(target=run_refresh_ws, daemon=True).start()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3010)

"""
AWS EC2에서 돌아갈 View Server
한 서버당 4명의 유저를 접속관리함
"""

import asyncio
import json
import threading
from typing import Optional, Dict, List
from pydantic import BaseModel
import requests
import uvicorn
import websockets
from dataclasses import dataclass
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse

from classes.api_client import APIClient
from util.my_util import (
    logging_error,
    logging_info,
)


@dataclass
class Account:
    """계정 정보"""

    id: int
    user_pk: int
    login_id: str
    login_pw: str
    logined: bool


class RequestData(BaseModel):
    """매니저 생성 DTO"""

    user_id: str
    panda_id: str
    proxy_ip: str
    instance_id: str
    kinds: str
    login_id: Optional[str] = None
    login_pw: Optional[str] = None

    def set(
        self,
        user_id: str,
        panda_id: str,
        proxy_ip: str,
        instance_id: str,
        kinds: str,
        login_id: Optional[str] = None,
        login_pw: Optional[str] = None,
    ):
        """set"""
        self.user_id = user_id
        self.panda_id = panda_id
        self.proxy_ip = proxy_ip
        self.instance_id = instance_id
        self.login_id = login_id
        self.login_pw = login_pw
        self.kinds = kinds


class WebsocketData:
    """대리접속 관련 데이터 클래스"""

    def __init__(
        self,
        websocket: websockets.WebSocketClientProtocol,
        api_client: APIClient,
        request_data: RequestData,
    ):
        self.websocket = websocket
        self.api_client = api_client
        self.request_data = request_data


class MyFastAPI(FastAPI):
    """전역변수를 사용하기 위해 확장한 클래스"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_dict: Dict[str, List[WebsocketData]] = {}
        self.refresh_dict = []


app = MyFastAPI()


BACKEND_URL = "175.200.191.11"


async def connect_websocket(token: str, channel: str, proxy_ip: str):
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
        origin=f"http://{proxy_ip}:8888",
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


async def update_jwt_refresh(
    api_client: APIClient, websocket: websockets.WebSocketClientProtocol
):
    """JWT 토큰 갱신"""
    await asyncio.sleep(60 * 25)
    while api_client.proxy_ip in app.refresh_dict:
        await api_client.refresh_token()
        message = {
            "id": 3,
            "method": 10,
            "params": {"token": api_client.jwt_token},
        }
        await websocket.send(json.dumps(message))
        await asyncio.sleep(60 * 25)


async def viewbot_start(
    api_client: APIClient, websocket: websockets.WebSocketClientProtocol
):
    """팬더 매니저 시작"""
    is_running = True
    # 닉네임이 변경된 게 있다면 업데이트
    asyncio.create_task(update_jwt_refresh(api_client=api_client, websocket=websocket))
    # asyncio.create_task(self.promotion())
    while is_running:
        try:
            await websocket.recv()
        except websockets.exceptions.ConnectionClosedOK as e:
            print(str(e))
            break
        except websockets.exceptions.ConnectionClosedError as e:
            print(str(e))
            break


async def get_account(user_id: str):
    """멤버 아이디 가져오기"""
    response = requests.get(
        url=f"http://{BACKEND_URL}:3000/user-proxy/member/{user_id}",
        timeout=5,
    )
    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 유저가 존재하지 않습니다.",
        )
    data = response.json()
    account = Account(**data)
    return account


def start_view_bot(
    request_data: RequestData,
):
    """매니저 쓰레드 함수"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if request_data.kinds == "guest":
        api_client = APIClient(
            panda_id=request_data.panda_id, proxy_ip=request_data.proxy_ip
        )
        loop.run_until_complete(api_client.guest_login())
        loop.run_until_complete(api_client.guest_play())
        websocket = loop.run_until_complete(
            connect_websocket(
                api_client.jwt_token, api_client.channel, api_client.proxy_ip
            )
        )
    elif request_data.kinds == "member":
        account = loop.run_until_complete(get_account(user_id=request_data.user_id))
        print(account)
        api_client = APIClient(
            panda_id=request_data.panda_id, proxy_ip=request_data.proxy_ip
        )
        loop.run_until_complete(api_client.member_login(account))
        loop.run_until_complete(api_client.member_play(request_data.panda_id))
        print(api_client.jwt_token, api_client.sess_key, api_client.user_idx)
        websocket = loop.run_until_complete(
            connect_websocket(
                api_client.jwt_token, api_client.channel, api_client.proxy_ip
            )
        )
    ws_data = WebsocketData(websocket, api_client, request_data)
    if request_data.instance_id not in app.ws_dict:
        app.ws_dict[request_data.instance_id] = []
    app.ws_dict[request_data.instance_id].append(ws_data)
    app.refresh_dict.append(api_client.proxy_ip)
    loop.run_until_complete(viewbot_start(websocket=websocket, api_client=api_client))
    return


async def process_request_thread(request_data: RequestData):
    """게스트를 처리하고 성공한다면 app.ws_dict에 추가"""
    threading.Thread(
        target=start_view_bot,
        args=(request_data,),
        daemon=True,
    ).start()


@app.post("/connect")
async def connect_proxy(request_data: RequestData):
    """
    이러한 구조를 채택한 이유는 Backend서버의 Pending 시간을 줄이기 위함 (40개 기준 10초넘게 걸림)
    1. reqeustProxyList로부터 요청한 정보를 가져옴
    2. requestProxyList의 정보를 바탕으로 해당 User가 가지고 있는 Proxy 하나 가져옴
    3. 가져온 프록시의 남은 용량이 다 차거나, reqeustProxyList 개수만큼 넣거나, 최대 4개까지 넣는다면 종료
    """
    print(request_data)
    if request_data.kinds not in ["guest", "member"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="kinds 값이 올바르지 않습니다.",
        )
    try:
        await process_request_thread(request_data=request_data)
    except:  # pylint: disable=W0702
        return HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="웹소켓 접속 실패.",
        )


@app.delete("/disconnect/{instance_id}")
async def disconnect_proxy(instance_id: str):
    """게스트 세션 끊기"""
    if instance_id in app.ws_dict:
        print(app.ws_dict.keys())
        socket_datas: List[WebsocketData] = app.ws_dict[instance_id]
        for socket_data in socket_datas:
            message = {
                "id": 2,
                "method": 2,
                "params": {"channel": str(socket_data.api_client.channel)},
            }
            await socket_data.websocket.send(json.dumps(message))
            await socket_data.websocket.close()
        del app.ws_dict[instance_id]
        print(app.ws_dict.keys())
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "success"},
    )


@app.delete("/disconnect/{instance_id}/{ip}")
async def disconnect_proxy_by_ip(instance_id: str, ip: str):
    """게스트 세션 끊기"""
    if instance_id in app.ws_dict:
        print(app.ws_dict.keys())
        socket_datas: List[WebsocketData] = app.ws_dict[instance_id]
        for socket_data in socket_datas:
            if socket_data.api_client.proxy_ip == ip:
                message = {
                    "id": 2,
                    "method": 2,
                    "params": {"channel": str(socket_data.api_client.channel)},
                }
                await socket_data.websocket.send(json.dumps(message))
                await socket_data.websocket.close()
                socket_datas.remove(socket_data)
                break
        app.ws_dict[instance_id] = socket_datas
        print(app.ws_dict.keys())
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "success"},
    )


@app.get("/check")
async def check():
    """a"""
    count = 0
    for key, value in app.ws_dict.items():
        for v in value:
            if v.websocket.open:
                count += 1
    print(count)


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3010)

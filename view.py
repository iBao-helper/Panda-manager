"""
AWS EC2에서 돌아갈 View Server
한 서버당 4명의 유저를 접속관리함
"""

import string
import random
import asyncio
import json
import threading
from typing import Optional, Dict, List
from dataclasses import dataclass
from pydantic import BaseModel
import requests
import uvicorn
import websockets
from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from classes.api_client import APIClient
from util.my_util import callback_create_proxy_history, logging_info


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
    kinds: str
    login_id: Optional[str] = None
    login_pw: Optional[str] = None

    def set(
        self,
        user_id: str,
        panda_id: str,
        proxy_ip: str,
        kinds: str,
        login_id: Optional[str] = None,
        login_pw: Optional[str] = None,
    ):
        """set"""
        self.user_id = user_id
        self.panda_id = panda_id
        self.proxy_ip = proxy_ip
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
        random_string: str,
        proxy_ip: str,
        user_id: str,
    ):
        self.websocket = websocket
        self.api_client = api_client
        self.request_data = request_data
        self.random_string = random_string
        self.proxy_ip = proxy_ip
        self.user_id = user_id


class MyFastAPI(FastAPI):
    """전역변수를 사용하기 위해 확장한 클래스"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ws_dict: Dict[str, WebsocketData] = {}
        self.refresh_dict = []
        self.thread_lists = []
        self.lock = threading.Lock()


app = MyFastAPI()


BACKEND_URL = "panda-manager.com"
# BACKEND_URL = "175.200.191.38"


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
        origin=f"http://{proxy_ip}:8800",
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
    api_client: APIClient,
    websocket: websockets.WebSocketClientProtocol,
    random_string: str,
):
    """JWT 토큰 갱신"""
    await asyncio.sleep(60 * 20)
    while random_string in app.thread_lists:
        await api_client.refresh_token()
        message = {
            "id": 3,
            "method": 10,
            "params": {"token": api_client.jwt_token},
        }
        await websocket.send(json.dumps(message))
        await asyncio.sleep(60 * 20)


async def reqeust_delete_point(user_id: str, login_id: str, proxy_ip: str):
    """인스턴스 제거 및 포인트 차감 요청"""
    requests.delete(
        url=f"http://{BACKEND_URL}:3000/proxy/decrease/{user_id}/{login_id}/{proxy_ip}",
        timeout=10,
    )


async def request_increase_ip(proxy_ip: str):
    """프록시 IP 차감 요청"""
    requests.patch(
        url=f"http://{BACKEND_URL}:3000/proxy/increase/{proxy_ip}", timeout=10
    )


async def request_callback_failed_member_id(account: Account):
    """실패한 계정의 로그인 상태를 변경"""
    requests.patch(
        url=f"http://{BACKEND_URL}:3000/proxy/callback-failed-login/{account.id}",
        timeout=10,
    )


async def viewbot_start(
    api_client: APIClient,
    websocket: websockets.WebSocketClientProtocol,
    random_string: str,
    proxy_ip: str,
    user_id: str,
    account: Account,
):
    """팬더 매니저 시작"""
    # 닉네임이 변경된 게 있다면 업데이트
    asyncio.create_task(
        update_jwt_refresh(
            api_client=api_client, websocket=websocket, random_string=random_string
        )
    )
    await callback_create_proxy_history(user_pk=account.user_pk, proxy_ip=proxy_ip)
    # asyncio.create_task(self.promotion())
    while random_string in app.thread_lists:
        try:
            data = await websocket.recv()
            chatting_data = json.loads(data)
            result = chatting_data.get("result", None)
            if result is not None:
                ws_type = result["data"]["data"].get("type", None)
                if ws_type == "RoomEnd":
                    for key, value in app.ws_dict.items():
                        if key == random_string:
                            app.thread_lists.remove(random_string)
                            del app.ws_dict[key]
                            break
                    break
        except websockets.exceptions.ConnectionClosedOK as e:
            await logging_info(
                panda_id=api_client.panda_id,
                description="view 에러 - ConnectionClosedOK",
                data=e,
            )
            print(str(e))
            break
        except websockets.exceptions.ConnectionClosedError as e:
            await logging_info(
                panda_id=api_client.panda_id,
                description="view 에러 - ConnectionClosedError",
                data=e,
            )
            print(str(e))
            break
        except websockets.exceptions.ConnectionClosed as e:
            await logging_info(
                panda_id=api_client.panda_id,
                description="view 에러 - ConnectionClosed",
                data=e,
            )
            print(str(e))
            break
        except Exception as e:  # pylint: disable=W0703
            await logging_info(
                panda_id=api_client.panda_id,
                description="view 에러 - Exception",
                data=e,
            )
            pass
    message = {
        "id": 2,
        "method": 2,
        "params": {"channel": str(api_client.channel)},
    }
    try:
        await websocket.send(json.dumps(message))
        await websocket.close()
    except Exception as e:
        await logging_info(
            panda_id=api_client.panda_id, description="view 에러 - await send", data=e
        )
        print("send 실패")
        pass

    exist = False
    # 해당 인스턴스가 모두 삭제되었을 경우 백엔드에 해당 인스턴스의 종료 요청을 보냄
    for key, value in app.ws_dict.items():
        if value.api_client.proxy_ip == proxy_ip:
            exist = True
            break
    if not exist:
        await reqeust_delete_point(
            user_id=user_id, login_id=account.login_id, proxy_ip=proxy_ip
        )
        await request_increase_ip(proxy_ip=proxy_ip)
        print("ip is deleted in dict. len")
        return

    if proxy_ip not in app.ws_dict:

        return


async def get_account(user_id: str):
    """멤버 아이디 가져오기"""
    response = requests.get(
        url=f"http://{BACKEND_URL}:3000/proxy/member/{user_id}",
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


def generate_random_string(length=12):
    """쓰레드를 지칭하기 위한 랜덤 문자열 생성"""
    characters = string.ascii_letters + string.digits
    random_string = "".join(random.choices(characters, k=length))
    while random_string in app.thread_lists:
        random_string = "".join(random.choices(characters, k=length))
    return random_string


def start_view_bot(
    request_data: RequestData,
):
    """매니저 쓰레드 함수"""
    app.lock.acquire()
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    if request_data.kinds == "guest":
        try:
            dummy_account = {
                "id": 0,
                "user_pk": 0,
                "login_id": "guest",
                "login_pw": "guest",
                "logined": False,
            }
            account = Account(**dummy_account)
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
        except Exception as e:  # pylint: disable=W0702 W0718
            print(str(e))
            loop.run_until_complete(request_increase_ip(proxy_ip=request_data.proxy_ip))
            app.lock.release()
            return
    elif request_data.kinds == "member":
        try:
            account = loop.run_until_complete(get_account(user_id=request_data.user_id))
            print(account)
            api_client = APIClient(
                panda_id=request_data.panda_id, proxy_ip=request_data.proxy_ip
            )
            loop.run_until_complete(api_client.member_login(account))
            loop.run_until_complete(api_client.member_play(request_data.panda_id))
            websocket = loop.run_until_complete(
                connect_websocket(
                    api_client.jwt_token, api_client.channel, api_client.proxy_ip
                )
            )
        except:  # pylint: disable=W0702
            app.lock.release()
            loop.run_until_complete(request_increase_ip(proxy_ip=request_data.proxy_ip))
            loop.run_until_complete(request_callback_failed_member_id(account))
            return
    random_string = generate_random_string()
    ws_data = WebsocketData(
        websocket,
        api_client,
        request_data,
        random_string,
        request_data.proxy_ip,
        request_data.user_id,
    )
    if random_string not in app.ws_dict:
        app.ws_dict[random_string] = ws_data
    app.ws_dict[random_string] = ws_data
    app.thread_lists.append(random_string)
    app.lock.release()
    loop.run_until_complete(
        viewbot_start(
            websocket=websocket,
            api_client=api_client,
            random_string=random_string,
            proxy_ip=request_data.proxy_ip,
            user_id=request_data.user_id,
            account=account,
        )
    )
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
    except Exception as e:  # pylint: disable=W0702
        print(str(e))
        return HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="웹소켓 접속 실패.",
        )


@app.delete("/disconnect/proxy_ip/{proxy_ip}")
async def disconnect_proxy(proxy_ip: str):
    """게스트 세션 끊기"""
    print(app.ws_dict.keys())
    print(app.thread_lists)
    for key, value in app.ws_dict.items():
        if value.proxy_ip == proxy_ip:
            app.thread_lists.remove(value.random_string)
            del app.ws_dict[key]
            break
    print(app.ws_dict.keys())
    print(app.thread_lists)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "success"},
    )


@app.delete("/disconnect/one/{user_id}")
async def disconnect_proxy2(user_id: str):
    """게스트 세션 끊기"""
    print(app.ws_dict.keys())
    print(app.thread_lists)
    for key, value in app.ws_dict.items():
        if value.user_id == user_id:
            app.thread_lists.remove(value.random_string)
            del app.ws_dict[key]
            break
    print(app.ws_dict.keys())
    print(app.thread_lists)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "success"},
    )


@app.delete("/disconnect/{user_id}")
async def disconnect_proxy_by_ip(user_id: str):
    """게스트 세션 끊기"""
    print(app.ws_dict.keys())
    print(app.thread_lists)
    for key, value in app.ws_dict.items():
        if value.user_id == user_id:
            app.thread_lists.remove(value.random_string)
            del app.ws_dict[key]
    print(app.ws_dict.keys())
    print(app.thread_lists)
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": "success"},
    )


@app.get("/check")
async def check():
    """a"""
    count = 0
    result = []
    for key, value in app.ws_dict.items():
        if value.websocket.open:
            result.append(
                {
                    "user_id": value.user_id,
                    "proxy_ip": value.proxy_ip,
                    "random_string": key,
                    "panda_id": value.request_data.panda_id,
                }
            )
            count += 1
    result = {
        "len": len(result),
        "result": result,
    }
    return result


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=3010)

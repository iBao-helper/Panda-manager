"""
AWS EC2에서 돌아갈 View Server
한 서버당 4명의 유저를 접속관리함
"""

import asyncio
import json
import threading
from typing import Optional
from pydantic import BaseModel
import uvicorn
import requests
import websockets
from typing import Dict
from fastapi import FastAPI, status, HTTPException, WebSocketException
from fastapi.responses import JSONResponse

from classes.api_client import APIClient


class ProxyConnectDto(BaseModel):
    """로그인 DTO"""

    panda_id: str
    ip: str
    instance_id: str
    kinds: str
    login_id: Optional[str] = None
    login_pw: Optional[str] = None


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

# # EC2 Instance-id, IP 가져오기
# # Exporting variables
# SERVER_IP = "panda-manager.com"

# # Getting the token
# token_response = requests.put(
#     "http://169.254.169.254/latest/api/token",
#     headers={"X-aws-ec2-metadata-token-ttl-seconds": "21600"},
#     timeout=5,
# )
# TOKEN = token_response.text.strip()

# # Getting instance ID
# instance_id_response = requests.get(
#     "http://169.254.169.254/latest/meta-data/instance-id",
#     headers={"X-aws-ec2-metadata-token": TOKEN},
#     timeout=5,
# )
# INSTANCE_ID = instance_id_response.text.strip()

# # Getting public IP
# public_ip_response = requests.get(
#     "http://169.254.169.254/latest/meta-data/public-ipv4",
#     headers={"X-aws-ec2-metadata-token": TOKEN},
#     timeout=5,
# )
# PUBLIC_IP = public_ip_response.text.strip()

# # Constructing data
# data = {"instance_id": INSTANCE_ID, "ip": PUBLIC_IP}
# print(data)

BACKEND_URL = "175.200.191.11"

default_header: dict = {
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
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",  # pylint: disable=C0301
    "X-Device-Info": '{"t":"webPc","v":"1.0","ui":24229319}',
}


async def get_guest_session():
    """백엔드로부터 게스트 세션키 받아오는 함수"""
    try:
        response = requests.get(
            url=f"http://{BACKEND_URL}:3000/nightwatch/session/guest",
            timeout=5,
        )
        print(response.json())
        result = response.json()["sess_key"]
        return result
    except:  # pylint: disable=W0702
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "게스트 세션을 받아오는데 실패하였습니다"},
        )


async def get_member_session(login_id: str, login_pw: str):
    """백엔드로부터 멤버 세션키 받아오는 함수"""
    try:
        response = requests.get(
            url=f"http://{BACKEND_URL}:3000/nightwatch/session/member?login_id={login_id}&login_pw={login_pw}",  # pylint: disable=C0301
            timeout=5,
        )
        result = response.json()["sess_key"]
        return result
    except:  # pylint: disable=W0702
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "멤버 세션을 받아오는데 실패하였습니다"},
        )


async def get_token_and_channel(panda_id: str, sess_key: str):
    """팬더티비 play토큰 얻기"""
    play_url = "https://api.pandalive.co.kr/v1/live/play"
    data = f"action=watch&userId={panda_id}&password=&shareLinkType="
    d_header: dict = {
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
    dummy_header = d_header.copy()
    dummy_header["path"] = "/v1/live/play"
    dummy_header["content-length"] = str(len(data))
    dummy_header["cookie"] = f"sessKey={sess_key};"
    proxy_ip = "52.79.227.47"
    try:
        response = requests.post(
            url=play_url,
            headers=dummy_header,
            data=data,
            proxies={
                "http": f"http://{proxy_ip}:8888",
                "https": f"http://{proxy_ip}:8888",
            },
            timeout=10,
        )
        result = response.json()
        print(result)
        if "errorData" in result:
            raise Exception()  # pylint: disable=W0719
        token = response.json()["token"]
        channel = response.json()["media"]["userIdx"]
        return token, channel
    except:  # pylint: disable=W0702
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "Play token을 받아오는데 실패하였습니다"},
        )


async def get_refresh_token(channel, token, sess_key, user_idx):
    """리프레쉬 토큰 발급 요청"""
    refresh_token_url = "https://api.pandalive.co.kr/v1/chat/refresh_token"
    data = f"channel={channel}&token={token}"
    dummy_header = default_header.copy()
    dummy_header["path"] = "/v1/chat/refresh_token"
    dummy_header["content-length"] = str(len(data))
    dummy_header["cookie"] = f"sessKey={sess_key}; userLoginIdx={user_idx}"
    try:
        result = requests.post(
            url=refresh_token_url, headers=dummy_header, data=data, timeout=5
        )
        result = result.json()
        print(result)
        if "token" in result:
            print(result["token"])
            token = result["token"]
            return token
    except:  # pylint: disable=W0702
        return None  # pylint: disable=W0719


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


@app.post("/proxy_connect")
async def proxy_connect(data: ProxyConnectDto):
    """프록시커넥트(변경해야함)"""
    if data.kinds != "guest" and data.kinds != "member":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="너 누군데 규칙도 모르니?",
        )
    print(data)
    if data.kinds == "guest":
        api_client = APIClient(panda_id=data.panda_id, proxy_ip=data.ip)
        await process_guest(api_client, data.panda_id, data.instance_id)
    elif data.kinds == "memeber":
        k = 9
        # await process_member(data)


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


@app.get("/member/{panda_id}")
async def tmp2(panda_id: str, login_id: str, login_pw: str):
    """게스트 세션키를 가져오는 함수"""
    # login_id와 login_pw 변수로 본문 데이터에 접근할 수 있음
    print(panda_id, login_id, login_pw)
    try:
        sess_key = await get_member_session(login_id, login_pw)
        print(sess_key)
        token, channel = await get_token_and_channel(panda_id, sess_key)
        print(token, channel)
        await connect_websocket(token, channel)
        app.counter += 1
        print(app.counter)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={"message": "success"},
        )
    except:  # pylint: disable=W0702
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "게스트 세션을 받아오는데 실패하였습니다"},
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

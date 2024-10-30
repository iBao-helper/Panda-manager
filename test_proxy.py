""" 모듈 테스트 하는 용도의 파일"""

import asyncio
import json
import requests
import websockets
from classes import playwright_watch as pws
from classes.bj_info import BjInfo
from classes.panda_manager import PandaManager
from classes.api_client import APIClient
from util.my_util import get_bj_data

play_watch: pws.PlayWrightNightWatch = pws.PlayWrightNightWatch(
    "siveriness1", "Adkflfkd1"
)

body = {
    "panda_id": "siveriness01",
    "proxy_ip": "",
    "manager_id": "siveriness01",
    "manager_pw": "Adkflfkd1",
    "resource_ip": "",
}
# manager: PandaManager = PandaManager(body=body)

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
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Device-Info": '{"t":"webPc","v":"1.0","ui":24229319}',
}


async def main():
    """docstring"""
    url = "https://api.pandalive.co.kr/v1/member/login_info"
    proxy_ip = "52.79.227.47"
    proxy_port = "8888"
    response = requests.post(
        url=url,
        headers=default_header,
        data={},
        timeout=10,
        proxies={
            "http": f"http://{proxy_ip}:{proxy_port}",
            "https": f"http://{proxy_ip}:{proxy_port}",
        },
    )
    sess_key = response.json()["loginInfo"]["sessKey"]
    print(sess_key)

    url = "https://api.pandalive.co.kr/v1/live/play"
    default_header["cookie"] = f"sessKey={sess_key};"
    data = {
        "action": "watch",
        "userId": "doitbabe",
        "password": "",
        "shareLinkType": "",
    }
    response = requests.post(
        url=url,
        headers=default_header,
        data=data,
        timeout=10,
        proxies={
            "http": f"http://{proxy_ip}:{proxy_port}",
            "https": f"http://{proxy_ip}:{proxy_port}",
        },
    )
    token = response.json()["token"]
    channel = response.json()["media"]["userIdx"]
    print(token)
    print(channel)

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
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Device-Info": '{"t":"webPc","v":"1.0","ui":0}',
    }
    websocket_url = "wss://chat-ws.neolive.kr/connection/websocket"
    websocket = await websockets.connect(
        uri=websocket_url,
        extra_headers=extra_headers,
        origin=f"http://{proxy_ip}:{proxy_port}",
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
    while True:
        await asyncio.sleep(100)


asyncio.run(main())

""" 모듈 테스트 하는 용도의 파일"""
import asyncio
import json
import requests
import websockets
from classes import playwright_watch as pws
import tmp_panda_manager as tmp
from classes.api_client import APIClient

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
manager: tmp.PandaManager = tmp.PandaManager(body=body)

login_headers = {
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
DATA = "id=siveriness00&pw=Adkflfkd1&idSave=N"


async def main():
    """docstring"""
    # t = int(time.time())
    # # print(t)
    # await manager.create_playwright("3.37.127.2")
    # await manager.set_interceptor()
    # await manager.login("siveriness01", "Adkflfkd1")

    # sess_key, user_idx = await manager.get_login_data()
    # print(sess_key, user_idx)
    api_client = APIClient()
    # api_client.set_login_data(sess_key, user_idx)
    response = await api_client.login("siveriness01", "Adkflfkd1")
    response = await api_client.play("qaaq36")
    user_data = {
        "id": 1,
        "params": {
            "name": "js",
            "token": api_client.jwt_token,  # 실제 토큰 값
        },
    }

    websocket_url = "wss://chat-ws.neolive.kr/connection/websocket"
    async with websockets.connect(
        websocket_url, extra_headers=login_headers
    ) as websocket:
        print("웹소켓 연결 성공!")

        # 연결이 열리면 메시지를 보낼 수 있습니다.
        message = {"id": user_data["id"], "params": user_data["params"]}

        # JSON 형태의 메시지를 서버로 보냅니다.
        await websocket.send(json.dumps(message))

        # 서버로부터 메시지를 기다립니다.
        response = await websocket.recv()
        print(f"서버로부터 메시지 수신: {response}")

        message = {"id": 2, "method": 1, "params": {"channel": str(api_client.channel)}}
        await websocket.send(json.dumps(message))

        response = await websocket.recv()
        print(f"서버로부터 메시지 수신: {response}")

        message = {
            "id": 199,
            "method": 2,
            "params": {"channel": str(api_client.channel)},
        }
        await websocket.send(json.dumps(message))

        response = await websocket.recv()
        print(f"서버로부터 메시지 수신: {response}")
        while True:
            try:
                response = await websocket.recv()
                data = json.loads(response)
                nickname = data["result"]["data"]["data"]["nk"]
                message = data["result"]["data"]["data"]["message"]
                
                if nickname == "크기가전부는아니자나연":
                    api_client.send_chatting(data["result"]["data"]["data"]["message"])
                    await websocket.recv()

                print(f"서버로부터 메시지 수신: {response}")
            except Exception as e:  # pylint: disable=W0718 W0612
                print(e)


asyncio.run(main())

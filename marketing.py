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

from util.my_util import (
    TrackerData,
    get_history_marcketing,
)
from view import (
    update_jwt_refresh,
)

api_client = APIClient()

user_list = []
prev_user_list = []


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
    while True:
        await api_client.refresh_token()
        message = {
            "id": 3,
            "method": 10,
            "params": {"token": api_client.jwt_token},
        }
        await websocket.send(json.dumps(message))
        await asyncio.sleep(60 * 20)


async def update_room_list(api_client: APIClient):
    """방에 있는 유저를 갱신시키는 함수"""
    room_user_list = await api_client.get_current_room_user()
    if room_user_list is None:
        return [], []
    return room_user_list


async def update_room_user_timer(api_client: APIClient):
    """방 유저 갱신 타이머"""
    global user_list
    global prev_user_list
    try:
        while True:
            catched = False
            prev_user_list = user_list
            room_user_list = await update_room_list(api_client=api_client)
            # print(room_user_list)
            get_user_list = [
                user["nick"] for user in room_user_list if user["nick"] != "게스트"
            ]
            new_users = [
                new_user for new_user in get_user_list if new_user not in prev_user_list
            ]
            idle_users = [
                prev_user for prev_user in user_list if prev_user not in get_user_list
            ]
            user_list = get_user_list
            # print(f"새로 들어온 유저: {new_users}")
            for user in new_users:
                history = await get_history_marcketing(user)
                message = ""
                for history_data in history:
                    catched = True
                    message += f"{history_data["date"]} / {history_data['user_name']} -> {history_data['bj_name']} ♥{history_data['count']}\n"
            if catched:
                print(message)
                if message != "":
                    await api_client.send_chatting(message)
                    await api_client.send_chatting("ex)써칭 크기가전부는아니자나연")
                else:
                    await api_client.send_chatting("사용방법\nex)써칭 매직쇼2")
                    await api_client.send_chatting("써칭 매직쇼2")

            await asyncio.sleep(2)
    except Exception as e:  # pylint: disable=W0702 W0718
        open("error.txt", "a").write(f"update_room_user error\n- {e}\n")
        pass


async def connect_webscoket(api_client: APIClient):
    """웹소켓에 연결을 시도함"""
    websocket_url = "wss://chat-ws.neolive.kr/connection/websocket"
    result = await api_client.play("siveriness00")
    if result is None:
        print("웹소켓 연결 실패 - Play 호출 실패")
        return None
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
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Device-Info": '{"t":"webPc","v":"1.0","ui":0}',
    }
    try:
        websocket = await websockets.connect(
            uri=websocket_url,
            extra_headers=extra_headers,
        )

        if websocket:
            print("websocket = ", websocket)
            print("웹소켓 연결 성공")
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
    except Exception as e:  # pylint: disable=W0703
        print("웹소켓 연결 실패")
        return None
    return websocket


async def response_macro(
    api_client: APIClient, websocket: websockets.WebSocketClientProtocol
):
    id_count = 1
    while True:
        try:
            data = await websocket.recv()
            try:
                chat = ChattingData(data)
                # print(chat)
                id_count += 1
            except Exception as e:  # pylint: disable=W0718 W0612
                continue
            if chat.type is None:
                continue
            try:
                splits_message = chat.message.split(" ")
                print(splits_message)
                if splits_message[0] == "써칭":
                    finded = False
                    search_user = splits_message[1]
                    history = await get_history_marcketing(search_user)
                    message = ""
                    for history_data in history:
                        finded = True
                        message += f"{history_data['date']} / {history_data['user_name']} -> {history_data['bj_name']} ♥{history_data['count']}\n"
                    if finded:
                        print(message)
                        await api_client.send_chatting(message)
                    else:
                        print(f"{search_user}의 하트 기록이 없습니다.")
                        await api_client.send_chatting(
                            f"{search_user}의 하트 기록이 없습니다."
                        )
                    await api_client.send_chatting(
                        "하트 트래커 홍보중 - panda-manager.com"
                    )
            except Exception as e:  # pylint: disable=W0703
                print(str(e))
                pass
        except websockets.exceptions.ConnectionClosedOK as e:
            print(str(e))
            break
        except websockets.exceptions.ConnectionClosedError as e:
            websocket = await connect_webscoket()
            if websocket is None:
                print("소켓 재접속 실패")
                break
            else:
                print("소켓 재접속 성공")


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
    asyncio.create_task(update_jwt_refresh(api_client, websocket))
    asyncio.create_task(update_room_user_timer(api_client))
    asyncio.create_task(response_macro(api_client, websocket))
    while True:
        print("Websocket connection status:", websocket.open)
        if websocket.open == False:
            break
        await asyncio.sleep(300)


if __name__ == "__main__":
    asyncio.run(main())

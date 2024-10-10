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


def start_view_bot(
    tracker_data: TrackerData,
    last_flag: Optional[bool] = False,
):
    """매니저 쓰레드 함수"""
    global lock
    global duplicate_lock

    # 마지막 요소라면 중복방지락을 풀어줌
    lock.acquire()
    # 아이피 부족하면 pass 다음 루프로
    if tim.get_total_ip() <= 0:
        print("IP 용량 부족:", tim.get_total_ip())
        if last_flag:
            duplicate_lock.release()
        lock.release()
        return

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    proxy_ip = tim.get_ip()
    print(proxy_ip)

    try:
        api_client = APIClient(panda_id=tracker_data.panda_id, proxy_ip=proxy_ip)
        loop.run_until_complete(api_client.guest_login())
        loop.run_until_complete(api_client.guest_play())
        print(api_client.channel)
        websocket = loop.run_until_complete(
            connect_websocket(
                api_client.jwt_token, api_client.channel, api_client.proxy_ip
            )
        )
    except Exception as e:  # pylint: disable=W0702 W0718
        print(f"웹소켓 연결 실패 에러 - {str(e)}")
        if last_flag:
            duplicate_lock.release()
        lock.release()
        return

    try:
        current_watching.append(tracker_data.panda_id)
        websockets_dict[tracker_data.panda_id] = [websocket, api_client]
        # 실행되면 proxy_ip 용량 차감
        if last_flag:
            duplicate_lock.release()
        lock.release()
        loop.run_until_complete(
            viewbot_start(
                websocket=websocket,
                api_client=api_client,
                tracker_data=tracker_data,
            )
        )
    except Exception as e:  # pylint: disable=W0702 W0718
        print(f"viewbot_start 에러  {str(e)}")
    return


def ger_starting_list(lists) -> list[TrackerData]:
    starting_lists = [
        item for item in lists if item["panda_id"] not in current_watching
    ]
    ip_count = tim.get_total_ip()
    return starting_lists[0:ip_count]


def get_terminated_lists(lists) -> list[TrackerData]:
    terminated_lists = []
    # 감시중인 리스트에 있으면서
    for item in current_watching:
        finded = False
        for list_item in lists:
            # 새로 받은 리스트에 없다면, 있다면 finded는 True가 됨
            if item == list_item["panda_id"]:
                finded = True
                break
        if not finded:
            terminated_lists.append(item)
    for panda_id in websockets_dict:
        if not websockets_dict[panda_id][0].open:
            terminated_lists.append(panda_id)
    return terminated_lists


def event_thread():
    global api_client
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(api_client.login("siveriness01", "Adkflfkd1", ""))
    managers = loop.run_until_complete(get_all_managers())
    managers = [item["panda_id"] for item in managers]
    print(managers)
    while True:
        try:
            duplicate_lock.acquire()
            starting_count = 0
            remove_count = 0
            lists = loop.run_until_complete(api_client.get_live_lists(managers))
            print("받아온 리스트 크기:", len(lists))
            starting_list = ger_starting_list(lists)
            terminating_list = get_terminated_lists(lists)
            if len(starting_list) == 0:
                duplicate_lock.release()
                pass
            for starting_item in starting_list:
                if starting_item == starting_list[-1]:
                    last_flag = True
                else:
                    last_flag = False
                tracker_data = TrackerData(**starting_item)
                threading.Thread(
                    target=start_view_bot,
                    args=(tracker_data, last_flag),
                    daemon=True,
                ).start()
                starting_count += 1
            for terminated_item in terminating_list:
                panda_ids = websockets_dict.keys()
                for panda_id in panda_ids:
                    if panda_id == terminated_item:
                        try:
                            websocket = websockets_dict[panda_id][0]
                            api_client = websockets_dict[panda_id][1]
                            message = {
                                "id": 2,
                                "method": 2,
                                "params": {"channel": str(api_client.channel)},
                            }
                            loop.run_until_complete(websocket.send(json.dumps(message)))
                            websockets_dict.pop(panda_id)
                            current_watching.remove(panda_id)
                            tim.increase_ip(api_client.proxy_ip)
                        except:
                            websockets_dict.pop(panda_id)
                            current_watching.remove(panda_id)
                            tim.increase_ip(api_client.proxy_ip)
                            print("panda_id의 웹소켓이 없음")
                        break
                remove_count += 1
            print(
                "가져옴:",
                len(lists),
                "새로킨 수:",
                starting_count,
                "종료 수:",
                remove_count,
            )
            sleep(300)  # Sleep for 5 minutes
        except Exception as e:  # pylint: disable=W0703
            print("event_trehad detect:", str(e))
            with open("example.txt", "w") as file:  # 파일을 쓰기 모드로 오픈
                file.write("Hello, Python!")  # 파일에 내용 쓰기


async def main():
    # 5분마다 실행될 쓰레드 생성
    threading.Thread(
        target=event_thread,
        daemon=True,
    ).start()
    while True:
        open("current_watching.txt", "w").write(str(current_watching))
        open("websockets_dict.txt", "w").write(str(websockets_dict))
        print("현재 감시중인 리스트:", len(current_watching))
        print("남은 IP 용량:", tim.get_total_ip())
        connected = 0
        disconnected = 0
        disconnected_list = []
        for panda_id in websockets_dict:
            if websockets_dict[panda_id][0].open:
                connected += 1
            else:
                disconnected_list.append(panda_id)
                disconnected += 1

        print(f"웹소켓 연결중: {connected}")
        print(f"웹소켓 연결끊김: {disconnected}")
        await asyncio.sleep(10)


if __name__ == "__main__":
    asyncio.run(main())

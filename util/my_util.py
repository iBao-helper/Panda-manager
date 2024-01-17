""" 잡다한 함수로 뺼 것들 모아놓은곳"""
import emoji
from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")


class User(BaseModel):
    """매니저 생성 DTO"""

    id: int
    panda_id: str
    nickname: str
    manager_id: str
    manager_pw: str
    manager_nick: str
    rc_message: str
    hart_message: str
    pr_message: str
    greet_message: str
    doosan_message: str
    pr_period: int
    resource_id: int | None
    toggle_greet: bool
    toggle_hart: bool
    toggle_rc: bool
    toggle_pr: bool
    toggle_doosan: bool


async def remove_proxy_instance(proxy_ip: str):
    """생성된 AWS의 proxy_ip를 지닌 인스턴스 제거"""
    try:
        requests.delete(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/proxy/{proxy_ip}",
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None


async def delete_bj_manager_by_panda_id(panda_id: str):
    """panda_id의 팬더 매니저 해제"""
    try:
        requests.delete(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/{panda_id}",
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None


async def success_connect_websocket(panda_id: str, proxy_ip: str, resource_ip: str):
    """웹소켓 연결 성공"""
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/success-proxy-task",
            json={
                "ip": proxy_ip,
                "panda_id": panda_id,
                "resource_ip": resource_ip,
            },
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None


async def send_hart_history(user_id: str, nickname: str, bj_name, hart_count):
    """하트 내역 전송"""
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/hart-history/{bj_name}",
            json={
                "nickname": emoji.emojize(nickname),
                "user_id": emoji.emojize(user_id),
                "count": hart_count,
            },
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None


async def delete_normal_command(panda_id: str, key: str):
    """일반 커맨드 삭제"""
    try:
        response = requests.delete(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/command/{panda_id}/{key}",
            timeout=5,
        )
        if response.status_code == 404:
            return "존재하지 않는 커맨드입니다"
        return "삭제되었습니다"
    except:  # pylint: disable=W0702
        return None


async def regist_normal_command(panda_id: str, key: str, value: str):
    """일반 커맨드 등록"""
    try:
        response = requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/command/{panda_id}",
            json={"key": key, "value": value},
            timeout=5,
        )
        if response.status_code == 409:
            return "이미 등록된 커맨드입니다"
        return "등록되었습니다"
    except:  # pylint: disable=W0702
        return None


async def get_hart_history_with_three(user):
    """하드 내역 조회"""
    try:
        response = requests.get(
            f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/hart-history/{emoji.emojize(user)}?mode=search",
            timeout=5,
        )
        json_data = response.json()
        print("써칭 리스폰스", json_data)
        message = ""
        if len(json_data) > 0:
            for data in json_data:
                message = (
                    message
                    + f"[{data['user_name']}] -> [{data['bj_name']}] ♥{data['count']}개\n"
                )
            return message
        else:
            return f"{user}님의 하트 내역이 없습니다. 하트 내역은 매니저봇이 있는 방에서만 집계됩니다."
    except:  # pylint: disable=W0702
        return None  # pylint: disable=W0702


async def get_hart_history_with_total(user):
    """하트 총 내역 조회"""
    try:
        response = requests.get(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/hart-history/{emoji.emojize(user)}?mode=sum",
            timeout=5,
        )
        print(response)
        message = f"{user} : {response.text}개"
        return message
    except:  # pylint: disable=W0702
        return None


async def regist_hart_message(panda_id, hart_message):
    """하트 메세지 등록"""
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/hart-message/{panda_id}",
            json={"message": hart_message},
            timeout=5,
        )
        return "하트 메세지가 등록되었습니다"
    except:  # pylint: disable=W0702
        return None


async def regist_recommend_message(panda_id: str, rc_message: str):
    """추천 메세지 등록"""
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/rc-message/{panda_id}",
            json={"message": rc_message},
            timeout=5,
        )
        return "추천 메세지가 등록되었습니다"
    except:  # pylint: disable=W0702
        return None


async def get_bj_data(panda_id: str) -> User:
    """panda_id의 bj_data를 가져온다"""
    try:
        data = requests.get(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/{panda_id}?relaiton=true",
            timeout=5,
        )
        print(data.json())
        user = User(**data.json())
        return user
    except:  # pylint: disable=W0702
        return None


async def update_bj_nickname(panda_id: str, nickname: str):
    """panda_id의 bj_data의 nickname을 변경한다"""
    try:
        data = requests.patch(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/{panda_id}/nickname",
            json={"nickname": nickname},
            timeout=5,
        )
        return data
    except:  # pylint: disable=W0702
        return None


async def update_manager_nickanme(panda_id: str, nickname: str):
    """panda_id의 bj_data의 manager_nick을 변경한다"""
    try:
        data = requests.patch(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/{panda_id}/manager-nickname",
            json={"manager_nick": nickname},
            timeout=5,
        )
        return data
    except:  # pylint: disable=W0702
        return None


async def add_room_user(panda_id: str, new_users: dict):
    """방에 새로운 유저를 추가함"""
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/room/user",
            json={"panda_id": panda_id, "user_list": list(new_users)},
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None


async def remove_room_user(panda_id: str, remove_users: list):
    """방에 새로운 유저를 추가함"""
    try:
        requests.patch(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/room/user",
            json={"panda_id": panda_id, "user_list": list(remove_users)},
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None


async def get_commands(panda_id: str):
    """panda_id의 command리스트를 가져온다"""
    try:
        commands = requests.get(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/command/{panda_id}",
            timeout=5,
        )
        command_dict = commands.json()
        command_dict = {item["keyword"]: item["response"] for item in command_dict}
        return command_dict
    except:  # pylint: disable=W0702
        return None


async def get_rc_message(panda_id: str):
    """panda_id의 추천메세지 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/rc-message/{panda_id}",
        timeout=5,
    )
    return message


async def get_hart_message(panda_id: str):
    """panda_id의 하트메세지 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/hart-message/{panda_id}",
        timeout=5,
    )
    return message


async def get_pr_message(panda_id: str):
    """panda_id의 command리스트를 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/pr-message/{panda_id}",
        timeout=5,
    )
    return message


async def get_greet_message(panda_id: str):
    """panda_id의 자동인사 메세지를 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/greet-message/{panda_id}",
        timeout=5,
    )
    return message


async def get_doosan_message(panda_id: str):
    """panda_id의 자동인사 메세지를 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/doosan-message/{panda_id}",
        timeout=5,
    )
    return message


async def get_rc_toggle(panda_id: str):
    """panda_id의 추천 토글 상태를 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/rc-message/{panda_id}/toggle",
        timeout=5,
    )
    return message


async def get_hart_toggle(panda_id: str):
    """panda_id의 하트 토글 상태를 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/hart-message/{panda_id}/toggle",
        timeout=5,
    )
    return message


async def get_pr_toggle(panda_id: str):
    """panda_id의 PR 토글 상태를 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/pr-message/{panda_id}/toggle",
        timeout=5,
    )
    return message


async def get_greet_toggle(panda_id: str):
    """panda_id의 PR 토글 상태를 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/greet-message/{panda_id}/toggle",
        timeout=5,
    )
    return message


async def get_doosan_toggle(panda_id: str):
    """panda_id의 PR 토글 상태를 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/doosan-message/{panda_id}/toggle",
        timeout=5,
    )
    return message


async def get_pr_period(panda_id: str):
    """panda_id의 command리스트를 가져온다"""
    message = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/pr-period/{panda_id}",
        timeout=5,
    )
    return message


async def error_in_chatting_room(panda_id: str):
    """채팅보내기 버튼이 눌러지지 않는 경우(다른 기기 로그인, 비정상 탐지 등) 리소스 회수하고 재시작"""
    message = requests.post(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/error-in-chatting-room",
        data={"panda_id": panda_id},
        timeout=5,
    )
    return message


async def create_room_user(panda_id: str, user_list: list):
    """새로 접속한 유저를 입력한다"""
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/room/user",
            json={"panda_id": panda_id, "user_list": user_list},
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None


async def delete_room_user(panda_id: str, user_list: list):
    """나간 유저를 삭제함"""
    try:
        requests.delete(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/room/user",
            json={"panda_id": panda_id, "user_list": user_list},
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None


async def get_song_list(panda_id: str):
    """panda_id의 songList를 가져온다"""
    try:
        song_list = requests.get(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/song-list/{panda_id}",
            timeout=5,
        )
        return song_list
    except:  # pylint: disable=W0702
        return None


async def add_song_list(panda_id: str, nickname: str, song: str):
    """panda_id의 songList에 노래를 추가한다"""
    try:
        response = requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/song-list/{panda_id}",
            json={"nickname": nickname, "song": song},
            timeout=5,
        )
        return response
    except:  # pylint: disable=W0702
        return None


async def delete_song_list(panda_id: str):
    """panda_id의 songList를 삭제한다"""
    try:
        response = requests.delete(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/song-list/{panda_id}",
            timeout=5,
        )
        return response
    except:  # pylint: disable=W0702
        return None


async def logging_debug(panda_id: str, description: str, data):
    """백엔드 서버에 로그를 남긴다"""
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log/debug",
            json={"panda_id": panda_id, "description": description, "data": data},
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None


async def logging_info(panda_id: str, description: str, data):
    """백엔드 서버에 로그를 남긴다"""
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log/info",
            json={"panda_id": panda_id, "description": description, "data": data},
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None


async def logging_error(panda_id: str, description: str, data):
    """백엔드 서버에 로그를 남긴다"""
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log/error",
            json={"panda_id": panda_id, "description": description, "data": data},
            timeout=5,
        )
    except:  # pylint: disable=W0702
        return None

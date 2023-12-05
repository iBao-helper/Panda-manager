""" 잡다한 함수로 뺼 것들 모아놓은곳"""
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
    pr_period: int
    resource_id: int | None


async def get_commands(panda_id: str):
    """panda_id의 command리스트를 가져온다"""
    commands = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/command/{panda_id}",
        timeout=5,
    )
    command_dict = commands.json()
    return command_dict


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


async def logging_debug(panda_id: str, description: str, data):
    """백엔드 서버에 로그를 남긴다"""
    requests.post(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log/debug",
        json={"panda_id": panda_id, "description": description, "data": data},
        timeout=5,
    )


async def logging_info(panda_id: str, description: str, data):
    """백엔드 서버에 로그를 남긴다"""
    requests.post(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log/info",
        json={"panda_id": panda_id, "description": description, "data": data},
        timeout=5,
    )


async def logging_error(panda_id: str, description: str, data):
    """백엔드 서버에 로그를 남긴다"""
    requests.post(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log/error",
        json={"panda_id": panda_id, "description": description, "data": data},
        timeout=5,
    )

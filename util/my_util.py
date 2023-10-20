""" 잡다한 함수로 뺼 것들 모아놓은곳"""
from pydantic import BaseModel
import requests

from util.my_env import BACKEND_PORT, BACKEND_URL


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
    resourceId: str | None


async def get_commands(panda_id: str):
    """panda_id의 command리스트를 가져온다"""
    commands = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/user/command/{panda_id}",
        timeout=5,
    )
    command_dict = commands.json()
    return command_dict

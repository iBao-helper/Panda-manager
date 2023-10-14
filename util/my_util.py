""" 잡다한 함수로 뺼 것들 모아놓은곳"""
import requests

from util.my_env import BACKEND_PORT, BACKEND_URL


async def get_commands(panda_id: str):
    """panda_id의 command리스트를 가져온다"""
    commands = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/user/command/{panda_id}",
        timeout=5,
    )
    command_dict = commands.json()
    return command_dict

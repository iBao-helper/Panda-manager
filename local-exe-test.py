import os
import threading
from classes.api_client import APIClient
from classes.panda_manager import PandaManager
from util.my_util import (
    get_info,
    logging_info,
    login,
    get_manager_data,
    program_login_success,
)
from classes.dto.CreateManagerDto import CreateManagerDto
import asyncio

login_api_client = APIClient()


class CreateManagerDto:
    """매니저 생성 DTO"""

    def __init__(
        self,
        panda_id: str,
        proxy_ip: str,
        manager_id: str,
        manager_pw: str,
    ):
        """set"""
        self.panda_id = panda_id
        self.manager_id = manager_id
        self.manager_pw = manager_pw
        self.proxy_ip = proxy_ip


async def get_jwt():
    """파일로부터 jwt 추출 또는 ID/PW를 입력받아 jwt 반환"""
    file_path = "authentication"
    if os.path.isfile(file_path):
        with open(file_path, "r") as file:
            jwt = file.read().strip()
        return jwt
    else:
        print("The 'authentication' file does not exist.")
        id = input("Enter your ID: ")
        pw = input("Enter your password: ")
        jwt = await login(id, pw)
        with open(file_path, "w") as file:
            file.write(jwt)
        print("JWT saved to 'authentication' file.")
        return jwt


async def start_manager(
    panda_id,
    body: CreateManagerDto,
    sess_key: str,
    user_idx: str,
    manager_nick: str,
    jwt: str,
):
    """매니저 쓰레드 함수"""
    # loop = asyncio.get_event_loop()
    # loop = asyncio.new_event_loop()
    # asyncio.set_event_loop(loop)

    manager = PandaManager(
        panda_id=panda_id,
        sess_key=sess_key,
        user_idx=user_idx,
        proxy_ip=body.proxy_ip,
        manager_nick=manager_nick,
    )
    result = await manager.connect_webscoket()
    if result is None:
        # loop.run_until_complete(callback_login_failure(panda_id))
        print("매니저 연결에 실패하였습니다")
        return None
    print(panda_id, "매니저 연결 성공")
    # loop.run_until_complete(
    #     success_connect_websocket(
    #         panda_id=panda_id, proxy_ip=body.proxy_ip, resource_ip=body.resource_ip
    #     )
    # )
    await program_login_success(jwt)
    await manager.start()
    return


async def main():
    jwt = await get_jwt()
    info = await get_info(jwt)
    if "statusCode" in info:
        print(
            "유효하지 않은 인증정보입니다. authentication 파일을 삭제합니다. 다시 시도하세요"
        )
        os.remove("authentication")
        return
    print(info)
    if info["is_expired"] == True:
        print("사용이 만료된 사용자입니다")
        return
    manager_data_json = await get_manager_data(jwt)
    manager_data: CreateManagerDto = CreateManagerDto(**manager_data_json)
    print(manager_data_json)

    await logging_info(
        panda_id=manager_data.panda_id,
        description="[리소스] - 매니저 요청 받음",
        data=manager_data_json,
    )
    manager_nick = await login_api_client.login(
        manager_data.manager_id, manager_data.manager_pw, manager_data.panda_id
    )
    if manager_nick is None:
        return
    sess_key, user_idx = await login_api_client.get_login_data()
    await start_manager(
        manager_data.panda_id, manager_data, sess_key, user_idx, manager_nick, jwt
    )


asyncio.run(main())

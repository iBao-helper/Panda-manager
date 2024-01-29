"""manager subprocess test"""
import asyncio
import sys
from classes.api_client import APIClient
from classes.panda_manager import PandaManager
from util.my_util import callback_login_failure, logging_info, success_connect_websocket

login_api_client = APIClient()


async def main(sys_argv: list):
    """subprocess main"""
    print(sys_argv)
    panda_id: str = sys_argv[1]
    proxy_ip: str = sys_argv[2]
    manager_id: str = sys_argv[3]
    manager_pw: str = sys_argv[4]
    resource_ip: str = sys_argv[5]
    # print(panda_id, proxy_ip, manager_id, manager_pw, resource_ip)
    await logging_info(
        panda_id=panda_id,
        description="[리소스] - 매니저 요청 받음",
        data={
            "panda_id": panda_id,
            "proxy_ip": proxy_ip,
            "manager_id": manager_id,
            "manager_pw": manager_pw,
            "resource_ip": resource_ip,
        },
    )
    manager_nick = await login_api_client.login(manager_id, manager_pw, panda_id)
    if manager_nick is None:
        return
    sess_key, user_idx = await login_api_client.get_login_data()

    manager = PandaManager(
        panda_id=panda_id,
        sess_key=sess_key,
        user_idx=user_idx,
        proxy_ip=proxy_ip,
        manager_nick=manager_nick,
    )
    result = await manager.connect_webscoket()
    if result is None:
        await callback_login_failure(panda_id)
        print("k")
        return None
    print(panda_id, "웹소켓 연결 성공")
    await success_connect_websocket(
        panda_id=panda_id, proxy_ip=proxy_ip, resource_ip=resource_ip
    )
    await manager.start()
    return


if __name__ == "__main__":
    asyncio.run(main(sys.argv))

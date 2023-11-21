"""테스트"""
import asyncio
import time
from typing import Dict
from tmp_manager import PandaManager as pm

panda_managers: Dict[str, pm] = {}
tmp = {
    "panda_id": "",
    "proxy_ip": "",
    "manager_id": "",
    "manager_pw": "",
    "resource_ip": "",
}


async def test():
    panda_manager: pm = pm(tmp)
    await panda_manager.create_playwright()
    panda_managers["0"] = panda_manager
    panda_manager2: pm = pm(tmp)
    await panda_manager2.create_playwright()
    panda_managers["1"] = panda_manager2
    await panda_managers["0"].goto_url(
        "https://www.pandalive.co.kr/live/play/live1004h"
    )
    await panda_managers["1"].goto_url(
        "https://www.pandalive.co.kr/live/play/live1004h"
    )
    await panda_managers["0"].remove_elements()
    await panda_managers["1"].remove_elements()


asyncio.run(test())

while True:
    time.sleep(1000)
# while True:
#     sele_watch = SeleWatch()
#     sele_watch.create_selenium()
#     # 닫기 버튼 클릭
#     sele_watch.element_click_with_css("button.btnClose")

#     # 로그인 과정
#     sele_watch.login()
#     user_list = sele_watch.get_user_list()
#     save_list = requests.get(
#         url="http://localhost:3000/user/tmp-user",
#         timeout=5,
#     ).json()
#     print(save_list)
#     for user in user_list:
#         if user["name"] in save_list:
#             continue
#         else:
#             sele_watch = SeleWatch()
#             sele_watch.create_selenium()
#             sele_watch.goto_url(
#                 f"https://www.pandalive.co.kr/live/search?text={user['name']}#bj"
#             )
#             # 닫기 버튼 클릭
#             # sele_watch.element_click_with_css("button.btnClose")
#             sele_watch.add_user(user["name"])
#     print("one cycle clear")
#     time.sleep(300)

"""테스트"""
import asyncio
import time
import tmp_manager as pm


def log_request(request):
    print(">>", request.method, request.url)


async def main():
    """테스트"""
    panda_manager: pm.PandaManager = pm.PandaManager()
    await panda_manager.create_playwright()
    await panda_manager.login(login_id="siveriness01", login_pw="Adkflfkd1")
    await panda_manager.goto_url("https://www.pandalive.co.kr/live/play/siveriness00")
    panda_manager.page.on("request", log_request)
    print("k")


asyncio.run(main())
while True:
    time.sleep(10)

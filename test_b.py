import asyncio
import aiohttp
import requests
from classes import playwright_watch as pm


async def main():
    """메인"""
    night_watch = pm.PlayWrightNightWatch()
    await night_watch.create_selenium()
    await night_watch.page.get_by_role("button", name="닫기").click()
    await night_watch.login()
    while True:
        await asyncio.sleep(5)


asyncio.run(main())

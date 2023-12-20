import asyncio
import aiohttp
import requests
from classes import playwright_watch as pm


async def main():
    """메인"""
    # night_watch = pm.PlayWrightNightWatch()
    # await night_watch.create_selenium()
    # await night_watch.page.get_by_role("button", name="닫기").click()
    # await night_watch.login()
    # while True:
    #     await asyncio.sleep(5)
    song_list = requests.get(
        url="http://panda-manager.com:3000/song-list/1",
        timeout=5,
    )
    print(song_list.json())


asyncio.run(main())

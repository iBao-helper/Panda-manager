import asyncio
import aiohttp
import requests
from playwright.async_api import async_playwright


async def intercept_channel_user_count(route, request):
    print(f"Intercepted WebSocket request: {request.url}")
    headers = request.headers
    async with aiohttp.ClientSession() as session:
        url = request.url.replace("channel_user_count", "channel_user_list")
        tmp: str = request.url
        query = tmp.split("?")[1].split("&")
        print(query)
        async with session.get(url, headers=headers) as response:
            print(await response.json())
    await route.continue_()


async def intercept_channel_user_list(route, request):
    print(f"Intercepted WebSocket request: {request.url}")
    headers = request.headers
    async with aiohttp.ClientSession() as session:
        async with session.get(request.url, headers=headers) as response:
            print(await response.json())
    await route.continue_()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # WebSocket 요청을 인터셉트하는 함수를 등록
        await context.route("**/channel_user_count*", intercept_channel_user_count)
        await context.route("**/channel_user_list*", intercept_channel_user_list)

        # 새 페이지 열기
        page = await context.new_page()

        # WebSocket을 사용하는 작업 수행
        await page.goto("https://www.pandalive.co.kr/live/play/siveriness00")

        while True:
            await asyncio.sleep(1)

        # 페이지 작업 완료 후 브라우저 종료
        await browser.close()


asyncio.run(main())

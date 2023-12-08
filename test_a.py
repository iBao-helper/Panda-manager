import asyncio
import aiohttp
import requests
from playwright.async_api import async_playwright


async def intercept_websocket(route, request):
    # print(f"Intercepted WebSocket request: {request.url}")
    # if "channel_user_list" in request.url:
    #     print(request.url)
    #     headers = request.headers
    #     async with aiohttp.ClientSession() as session:
    #         async with session.get(request.url, headers=headers) as response:
    #             print(await response.json())
    # if "message" in request.url:
    #     print(request.url)
    #     print(request.post_data)
    #     headers = request.headers
    #     async with aiohttp.ClientSession() as session:
    #         async with session.post(request.url, headers=headers) as response:
    #             print(await response.json())
    if "websocket" in request.url:
        print(request.url)
    await route.continue_()


async def main():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # WebSocket 요청을 인터셉트하는 함수를 등록
        # await context.route("**/*", intercept_websocket)

        # 새 페이지 열기
        page = await context.new_page()

        # WebSocket을 사용하는 작업 수행
        await page.goto("https://www.pandalive.co.kr/live/play/siveriness00")

        while True:
            await asyncio.sleep(1)

        # 페이지 작업 완료 후 브라우저 종료
        await browser.close()


asyncio.run(main())

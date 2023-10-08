""" 후........ 쉬발 파이린트는 넘 빡세다 """
import asyncio
import re
from classes.night_watch import NightWatch
from playwright.async_api import async_playwright
from playwright.async_api import Page
from playwright.async_api import Browser
import time
import urllib
import os

from stt import sample_recognize

night_watch = NightWatch()


async def check_manager_login(id: str, pw: str):
    """매니저 로그인 확인"""
    print(id)
    apw = await async_playwright().start()
    browser = await apw.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto(f"https://www.pandalive.co.kr/channel/{id}/notice")
    if page.url != f"https://www.pandalive.co.kr/channel/{id}/notice":
        print("aaa")
        return "null"
    book_mark = await page.query_selector(".btn_bookmark")
    book_mark_class = await book_mark.get_attribute("class")
    print(book_mark_class)
    nickname = await page.query_selector(".nickname")
    nickname = await nickname.inner_text()
    result = re.sub(r"\([^)]*\)", "", nickname)
    print(result)
    return {"message": "ok"}


async def test():
    await check_manager_login("qaaq36", "Adkflfkd1")


asyncio.run(test())
while True:
    time.sleep(1)

import asyncio
from playwright.async_api import async_playwright
from playwright.async_api import Page


async def element_click_with_css(page: Page, css_selector: str):
    """css 엘리먼트 클릭"""
    try:
        element = await page.query_selector(css_selector)
        if element:
            await element.click()
    except:  # pylint: disable=W0702
        pass


async def element_fill_with_css(page: Page, css_selector, value):
    """css 엘리먼트 입력"""
    element = await page.query_selector(css_selector)
    if element:
        await element.fill(value)


async def main():
    """docstring"""
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False, proxy={"server": "13.212.176.68:8888"}
        )
        context = await browser.new_context()
        # 새 페이지 열기
        page = await context.new_page()
        await page.goto("https://www.pandalive.co.kr/live")
        await browser.close()


asyncio.run(main())

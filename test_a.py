import asyncio
import aiohttp
import requests
from playwright.async_api import async_playwright
from playwright.async_api import Page


async def element_click_with_css(page: Page, css_selector: str):
    """css 엘리먼트 클릭"""
    try:
        element = await page.query_selector(css_selector)
        if element:
            await element.click()
    except:
        pass


async def element_fill_with_css(page: Page, css_selector, value):
    """css 엘리먼트 입력"""
    element = await page.query_selector(css_selector)
    if element:
        await element.fill(value)


async def login(page: Page, manager_id, manager_pw):
    """login기능"""
    await element_click_with_css(page, ".btn_login.btn_my_infor")
    await element_click_with_css(page, "div.profile_infor > a > span.name")
    await element_click_with_css(page, "ul.memTab > li > a")
    await element_click_with_css(page, "div.input_set > input#login-user-id")
    await element_fill_with_css(page, "div.input_set > input#login-user-id", manager_id)
    await element_click_with_css(page, "div.input_set > input#login-user-pw")
    await element_fill_with_css(page, "div.input_set > input#login-user-pw", manager_pw)
    await element_click_with_css(page, "div.btnList > span.btnBc > input[type=button]")
    await element_click_with_css(page, "div.profile_img")


async def is_scroll_at_bottom(page: Page) -> bool:
    """스크롤이 가장 밑에 있나"""
    scroll_height = await page.evaluate("document.documentElement.scrollHeight")
    scroll_top = await page.evaluate(
        "window.pageYOffset || document.documentElement.scrollTop"
    )
    scroll_inner_height = await page.evaluate("window.innerHeight")
    # If the scroll top plus window height is greater than or equal to scroll height,
    # we consider it to be at the bottom
    return scroll_top + scroll_inner_height >= (scroll_height - 200)


async def scroll_down(page: Page):
    """page를 스크롤 끝까지 내리는 함수"""
    page.set_default_timeout(0)
    while True:
        try:
            is_bottom = await is_scroll_at_bottom(page)
            if not is_bottom:
                element = await page.query_selector("div.listBtnMore")
                await element.click()
                await asyncio.sleep(2)
                print(await is_scroll_at_bottom(page))
            else:
                break
        except Exception as e:  # pylint: disable=W0703 W0612
            break
    page.set_default_timeout(30000)


async def get_proceed_data_list(page: Page):
    """진행중인 방송 리스트를 가져옴"""
    ret_list = []
    lists = await page.query_selector_all("div.liveList > ul > li")
    for list_item in lists:
        name = await list_item.query_selector("div.infor > span.name")
        viewer = await list_item.query_selector("div.infor > span.viewr")
        name_text = await name.inner_text()
        viewer_text = await viewer.inner_text()
        if viewer_text == "FULL":
            view_count = 700
        else:
            view_count = int(viewer_text.replace("'", "").replace(",", ""))
        if view_count >= 2:
            ret_list.append({"name": name_text.replace(" ", ""), "viewer": view_count})
    return ret_list


message = """** 하루에 1번만 자동 홍보합니당 :D **
자동 접속하고 프로그램이 필요없는 매니저 봇 서비스입니당! 
http://panda-manager.com 에서 사용가능합니다!
"""
message2 = """무료니까 한번 사용해보세욥 ~! 
실례했습니당~! 다들 즐방하세욥! ㅡㅡㄱ
"""


async def check_and_send_message(page: Page, nickname: str):
    """backend에서 200을 보내면 홍보하고 아니면 넘어가기"""
    await element_fill_with_css(
        page,
        "xpath=/html/body/div[2]/div/div/div[2]/div[2]/div/div/div[2]/div/div[2]/div[2]/div[2]/div[3]/textarea",
        message,
    )
    await asyncio.sleep(0.3)
    await element_click_with_css(
        page,
        "xpath=/html/body/div[2]/div/div/div[2]/div[2]/div/div/div[2]/div/div[2]/div[2]/div[2]/div[3]/input",
    )
    await asyncio.sleep(0.3)
    await element_fill_with_css(
        page,
        "xpath=/html/body/div[2]/div/div/div[2]/div[2]/div/div/div[2]/div/div[2]/div[2]/div[2]/div[3]/textarea",
        message2,
    )
    await asyncio.sleep(0.3)
    await element_click_with_css(
        page,
        "xpath=/html/body/div[2]/div/div/div[2]/div[2]/div/div/div[2]/div/div[2]/div[2]/div[2]/div[3]/input",
    )
    await asyncio.sleep(0.3)
    requests.post(
        url="http://panda-manager.com:3000/master/tmp-user",
        json={"nickname": nickname},
        timeout=5,
    )
    return


async def main():
    async with async_playwright() as p:
        while True:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context()
            # 새 페이지 열기
            page = await context.new_page()
            # WebSocket을 사용하는 작업 수행
            await page.goto("https://www.pandalive.co.kr/live")
            await login(page, "danagga", "Ehdrn0990!PD")
            await asyncio.sleep(2)
            await scroll_down(page)
            user_lists = await get_proceed_data_list(page)
            backend_list = requests.get(
                url="http://panda-manager.com:3000/master/tmp-user",
                timeout=5,
            ).json()
            print("findCurrentUserList Length =", len(user_lists))
            print("backendList Length =", backend_list)

            for user in user_lists:
                if (
                    any(
                        user["name"] == backend_user["nickname"]
                        for backend_user in backend_list
                    )
                    is True
                ):
                    continue
                await page.goto(
                    f"https://www.pandalive.co.kr/live/search?text={user['name']}#live"
                )
                page_img = await page.query_selector(
                    "xpath=/html/body/div/div/div/div[2]/div[2]/div/div/div[3]/ul/li/a/div[1]/img"
                )
                if page_img:
                    await page_img.click()
                    await asyncio.sleep(3)
                    # 등급 방이라면 continue
                    hart_cancel = await page.query_selector(
                        "xpath=/html/body/div[2]/div/div[3]/button[3]"
                    )
                    if hart_cancel:
                        continue
                    # 비번 방이라면 continue
                    pass_cancel = await page.query_selector(
                        "xpath=/html/body/div/div/div/div[2]/div[3]/div[1]/div/div[2]/div[2]/span[1]/input"
                    )
                    if pass_cancel:
                        continue
                    # 확인 버튼이 있다면 클릭
                    await element_click_with_css(
                        page,
                        "xpath=/html/body/div[2]/div/div/div[2]/div[2]/div/div/div[3]/div/div/div[3]/span/input",
                    )
                    try:
                        await element_click_with_css(
                            page,
                            "/html/body/div[2]/div/div/div[2]/div[2]/div/div/div[3]/div/div/div[3]/span",
                        )
                    except:
                        pass
                    await check_and_send_message(page, user["name"])

                else:
                    continue
                await asyncio.sleep(2)
            await browser.close()
            await asyncio.sleep(600)


asyncio.run(main())

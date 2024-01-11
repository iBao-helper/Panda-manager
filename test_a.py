""" 모듈 테스트 하는 용도의 파일"""
import asyncio
from playwright.async_api import async_playwright
from playwright.async_api import Page
import requests
from classes import playwright_watch as pws
from classes.api_client import APIClient
from classes.search_member_bj import SearchMemberBj


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


play_watch: pws.PlayWrightNightWatch = pws.PlayWrightNightWatch(
    "siveriness1", "Adkflfkd1"
)
member_bj = SearchMemberBj()

login_headers = {
    "authority": "api.pandalive.co.kr",
    "method": "POST",
    "path": "/v1/member/login",
    "scheme": "https",
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br",
    "accept-language": "ko",
    "content-length": "37",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.pandalive.co.kr",
    "referer": "https://www.pandalive.co.kr/",
    "sec-ch-ua": '"Not_A Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Windows"',
    "Sec-Fetch-Dest": "empty",
    "Sec-Fetch-Mode": "cors",
    "Sec-Fetch-Site": "same-site",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "X-Device-Info": '{"t":"webPc","v":"1.0","ui":0}',
}
DATA = "id=siveriness00&pw=Adkflfkd1&idSave=N"

# cookie = "au_id=ef7aafb76d48a16a4415d1ae18a88ee3446-6fee; id_merge=1; REALUCODE=MTQuMzkuMTcxLjg5fDE2OTUzMDk2MTl8MjQ5Mw%3D%3D; _gcl_au=1.1.51034929.1702291134; userLoginSaveYN=Y; _gid=GA1.3.1546340540.1704363807; sessKey=aa0ba624486831d2b19a8e53c8f13446d86f958eb890523e29bb4ec2e21285ea; userLoginYN=Y; PPAP=MQ%3D%3D; c9a3e0324fcc917fb3ceabb43511e44d3ec34328d7a2e56b16dc6995bcbcea80=0nJVkl8F%2FBpzfbElRS9ubHX4d91Jq%2F57XjlOMgy6Ve7U5FwutQZDRapajtGUZgFtMNLhlfE9TBMzska9O%2BiNWPZJM1ABOyGDJ27OWlUpHk09vNr%2BS3m%2FkQMc4EH1XM4i1gYBAn%2BwcADjaAT1WddlWpXHUet5KMKLwdCrfMdGh%2FQ%3D; partner=sa36001; userLoginSaveID=YzJsMlpYSnBibVZ6Y3pBdw%3D%3D; _ga=GA1.1.495013088.1694514442; _ga_ZJ51R4C39H=GS1.3.1704964507.740.1.1704966121.60.0.0; userLoginIdx=24229319; 3be3f8e358abbf54cec643229de77fc9e4f3f0bbc9b171580d45d13aaa374c16=L5Vq7b26kEU5KXAM1r"
cookie = "sessKey=aa0ba624486831d2b19a8e53c8f13446d86f958eb890523e29bb4ec2e21285ea; userLoginYN=Y; userLoginIdx=24229319"
cookie_split = cookie.split("; ")
print(cookie_split)


async def intercept_member_bj(route, request):
    """북마크 인터셉터"""
    if member_bj.headers is None:
        member_bj.set_headers(request.headers)
    await route.continue_()


async def main():
    """docstring"""
    # await play_watch.create_selenium(headless=False)
    # await play_watch.context.route(
    #     "https://api.pandalive.co.kr/v1/member/bj", intercept_member_bj
    # )
    # await play_watch.page.get_by_role("button", name="닫기").click()
    # play_watch.watch_id = "siveriness01"
    # play_watch.watch_pw = "Adkflfkd1"
    # await play_watch.login()
    # await play_watch.goto_url("https://www.pandalive.co.kr/channel/siveriness01/notice")

    api_client = APIClient()
    response = api_client.login("siveriness00", "Adkflfkd1")
    print(response)
    # response = api_client.search_bj("siveriness01")
    # print(response)
    # api_client.add_book_mark("2307111505@ka")
    # api_client.delete_book_mark("2307111505@ka")
    response = api_client.get_bookmark_list_to_nickname()
    print(response)

    # response = requests.post(
    #     url="https://api.pandalive.co.kr/v1/member/login",
    #     headers=login_headers,
    #     data=DATA,
    #     timeout=5,
    # )
    # data = response.json()
    # sess_key = data["loginInfo"]["sessKey"]
    # user_idx = data["loginInfo"]["userInfo"]["idx"]
    # list_data = []
    # for cookie_data in cookie_split:
    #     if "sessKey" in cookie_data:
    #         splited_cookie = cookie_data.split("=")
    #         splited_cookie[1] = sess_key
    #         cookie_data = "=".join(splited_cookie)
    #         print(cookie_data)
    #     if "userLoginIdx" in cookie_data:
    #         splited_cookie = cookie_data.split("=")
    #         splited_cookie[1] = str(user_idx)
    #         cookie_data = "=".join(splited_cookie)
    #         print(cookie_data)
    #     list_data.append(cookie_data)
    # print(sess_key, user_idx)
    # print(list_data)
    # new_cookie = "; ".join(list_data)
    # print(new_cookie)
    # bookmark_add_headers = {
    #     "authority": "api.pandalive.co.kr",
    #     "method": "POST",
    #     "scheme": "https",
    #     "accept": "application/json, text/plain, */*",
    #     "accept-encoding": "gzip, deflate, br",
    #     "Accept-Language": "ko,ko-KR;q=0.9",
    #     "content-type": "application/x-www-form-urlencoded",
    #     "origin": "https://www.pandalive.co.kr",
    #     "referer": "https://www.pandalive.co.kr/",
    #     "sec-ch-ua": '"Not_A Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
    #     "sec-ch-ua-mobile": "?0",
    #     "sec-ch-ua-platform": '"Windows"',
    #     "Sec-Fetch-Dest": "empty",
    #     "Sec-Fetch-Mode": "cors",
    #     "Sec-Fetch-Site": "same-site",
    #     "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    #     "X-Device-Info": '{"t":"webPc","v":"1.0","ui":24229319}',
    #     "cookie": new_cookie,
    #     "path": "/v1/member/bj",
    #     "content-length": "23",
    # }

    # response = requests.post(
    #     url="https://api.pandalive.co.kr/v1/member/bj",
    #     headers=bookmark_add_headers,
    #     data="userId=2307111505%40ka&info=media%20fanGrade%20bookmark",
    #     timeout=5,
    # )
    # print(response.json())

    # while True:
    #     data = await member_bj.get_nickname("gwong1")
    #     print(data)
    #     await asyncio.sleep(10)


asyncio.run(main())

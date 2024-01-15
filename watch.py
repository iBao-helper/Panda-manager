""" 후........ 쉬발 파이린트는 넘 빡세다 """
import os
import asyncio
import urllib.request
import concurrent.futures
import requests
import uvicorn
from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse

# from playwright.async_api import async_playwright
from playwright.async_api import Page
from playwright.async_api import FrameLocator
from dotenv import load_dotenv
from classes import playwright_watch as pws
from custom_exception import custom_exceptions as ex
from stt_v2 import sample_recognize
from util.my_util import logging_debug, logging_error, logging_info

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
app = FastAPI()
play_watch: pws.PlayWrightNightWatch = pws.PlayWrightNightWatch(
    watch_id="siveriness1", watch_pw="Adkflfkd1"
)

# ThreadPoolExecutor를 생성하여 loop2 함수를 별도의 스레드에서 실행합니다.
executor = concurrent.futures.ThreadPoolExecutor()


async def loop2():
    """aaa"""
    while True:
        await asyncio.sleep(10)
        await play_watch.start()


@app.post("/NightWatch")
async def night_watch_start():
    """감시자 시작"""
    await play_watch.login()
    await asyncio.sleep(1)
    asyncio.create_task(loop2())
    return {"message": "NightWatch"}


@app.delete("/NightWatch")
async def night_watch_stop():
    """감시자 종료"""
    # await play_watch.destroy()
    return {"message": "NightWatch"}


@app.get("/test")
async def test(response: Response):
    """테스트"""
    response.status_code = status.HTTP_202_ACCEPTED
    return {"message": "Something went wrong"}, status.HTTP_400_BAD_REQUEST


@app.get("/check-manager")
async def check_manager_login(manager_id: str, manager_pw: str, response: Response):
    """매니저로 사용하는 id/pw가 로그인이 가능한지 확인하는 함수"""
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
    data = f"id={manager_id}&pw={manager_pw}&idSave=N"
    await logging_info(
        "리소스 서버", "매니저 등록 시도", {manager_id: manager_id, manager_pw: manager_pw}
    )
    try:
        api_response = requests.post(
            url="https://api.pandalive.co.kr/v1/member/login",
            headers=login_headers,
            data=data,
            timeout=5,
        )
        response_data = api_response.json()
        print(response_data)
        if "loginInfo" in response_data:
            login_info = response_data["loginInfo"]
            if "userInfo" in login_info:
                user_info = login_info["userInfo"]
                if user_info["authYN"] == "N":
                    response.status_code = status.HTTP_404_NOT_FOUND
                    return
                print(user_info["nick"])
                await logging_info(
                    "리소스 서버", "매니저 등록 성공", {"매니저 닉네임": user_info["nick"]}
                )
                return user_info["nick"]
        if "errorData" in response_data:
            await logging_error("리소스서버", "매니저 로그인 에러", data)
            print(response_data["errorData"]["code"])
            if "비밀번호" in response_data["message"]:
                response.status_code = 405
            elif "wrongId" in response_data["errorData"]["code"]:
                response.status_code = 406
            elif "noid" in response_data["errorData"]["code"]:
                response.status_code = 406
            elif response_data["errorData"]["code"] == "recaptcha":
                response.status_code = 410
            return
    except Exception as e:  # pylint: disable=W0718
        print("error - ", str(e))
        return


@app.get("/panda-nickname", status_code=status.HTTP_200_OK)
async def get_panda_nickname(bj_id: str, response: Response):
    """panda_id로 검색된 닉네임 리턴하는 함수"""
    is_excute = play_watch.get_nickname_by_panda_id(bj_id)
    if is_excute is None:
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "null"}
    return is_excute


@app.get("/add-bookmark", status_code=status.HTTP_200_OK)
async def add_book_mark(bj_id: str):
    """북마크 추가"""
    play_watch.add_book_mark_list(bj_id)
    lists = await play_watch.get_bookmark_list_to_nickname()
    await logging_info("add-bookmark", "북마크 삭제", lists)
    return {"message": "success"}


@app.get("/delete-bookmark", status_code=status.HTTP_200_OK)
async def delete_book_mark(bj_id: str):
    """북마크 추가"""
    play_watch.delete_book_mark_list(bj_id)
    lists = await play_watch.get_bookmark_list_to_nickname()
    await logging_info("delete-bookmark", "북마크 삭제", lists)
    return {"message": "success"}


@app.get("/check-bookmark", status_code=status.HTTP_200_OK)
async def check_book_mark():
    """북마크 상태 체크"""

    return {"message": "success"}


# @app.on_event("startup")
# async def startup_event():
#     """
#     NightWatch 가동시 backend에 등록 요청을 시도함
#     이미 있다면 등록되지 않음
#     """
#     try:
#         requests.post(
#             url=f"http://{BACKEND_URL}:{BACKEND_PORT}/nightwatch",
#             json={"ip": "112.185.118.249"},
#             timeout=5,
#         )
#     except:  # pylint: disable=W0702
#         print("nightwatch already registered")


## 현재 로컬환경에서 테스트라 localServer 리소스가 실행될때 backend 에 등록하지 않음
## 차후 localServer 리소스가 실행될때 backend 에 등록하는 기능을 추가해야함


#######  manager 관련 유틸 함수들 #######
async def check_popup_recaptcha_failed(show_frame: FrameLocator):
    """popup recaptcha failed"""
    retry_detect = await show_frame.get_by_text("나중에 다시 시도해 주세요").is_visible()
    print("retry_detect", retry_detect)
    if retry_detect:
        print("잦은 재시도 탐지에 걸림")
        await logging_error(
            "check-manager", "잦은 재시도 탐지에 걸림", {"debug_message": "잦은 재시도 탐지에 걸림"}
        )
        raise ex.PlayWrightException(ex.PWEEnum.PD_LOGIN_STT_FAILED)


async def login(page: Page, manager_id, manager_pw):
    """로그인 시도"""
    await logging_debug("check-manager", "[login] - 닫기", {"debug_message": "닫기 성공"})
    await page.get_by_role("button", name="로그인 / 회원가입").click()
    await logging_debug(
        "check-manager", "[login] - 회원가입 버튼 클릭", {"debug_message": "로그인 / 회원가입"}
    )
    await asyncio.sleep(0.3)
    await page.get_by_role("link", name="로그인 / 회원가입").click()
    await logging_debug(
        "check-manager", "[login] - 로그인 / 회원가입 링크 클릭", {"debug_message": "로그인 / 회원가입"}
    )
    await asyncio.sleep(0.3)
    await page.get_by_role("link", name="로그인").click()
    await logging_debug(
        "check-manager", "[login] - 로그인 링크 클릭", {"debug_message": "로그인"}
    )
    await page.get_by_role("textbox").nth(1).fill(manager_id)
    await page.get_by_role("textbox").nth(2).fill(manager_pw)
    await asyncio.sleep(2)
    await page.get_by_role("button", name="로그인", exact=True).click()
    await logging_debug(
        "check-manager", "[login] - 로그인 버튼 클릭", {"debug_message": "로그인"}
    )
    await asyncio.sleep(2)
    invalid_text_id = await page.get_by_text("존재하지 않는 사용자입니다.").is_visible()
    invalid_text_pw = await page.query_selector(".inputBox.fon.err > p")
    if invalid_text_id or invalid_text_pw:
        await logging_debug(
            "check-manager",
            "Invalid ID/PW",
            {"maanager_id": manager_id, "manager_pw": manager_pw},
        )
        raise ex.PlayWrightException(
            ex.PWEEnum.PD_LOGIN_INVALID_ID_OR_PW,
        )
    await logging_debug(
        "check-manager",
        "[빨간줄 통과]",
        {"id": manager_id, "pw": manager_pw},
    )
    invalid_label_id = await page.get_by_label("존재하지 않는 사용자입니다.").is_visible()
    invalid_label_pw = await page.get_by_label(
        "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
    ).is_visible()
    await logging_debug(
        "check-manager",
        "[팝업 통과]",
        {"id": manager_id, "pw": manager_pw},
    )
    if invalid_label_id or invalid_label_pw:
        await logging_debug(
            "check-manager", "Popup Invalid ID/PW", {"id": manager_id, "pw": manager_pw}
        )
        await page.get_by_role("button", name="확인").click()
        raise ex.PlayWrightException(ex.PWEEnum.PD_LOGIN_INVALID_ID_OR_PW)
    invalid_login_detect = await page.get_by_label(
        "비정상적인 로그인이 감지되었습니다.잠시 후 다시 시도해 주세요."
    ).is_visible()
    auto_detect = await page.get_by_label("자동접속방지 체크박스를 확인해주세요").is_visible()
    await logging_debug(
        "check-manager",
        "[invalid-login_detect check]",
        {"invalid_login_detect": invalid_login_detect, "auto_detect": auto_detect},
    )
    if invalid_login_detect or auto_detect:
        await logging_debug(
            "check-manager",
            "[비정상적인 로그인 / 자동접속방지 체크박스] 감지됨",
            {"비정상 로그인 감지": invalid_login_detect, "자동접속방지 체크박스": auto_detect},
        )
        await page.get_by_role("button", name="확인").click()
        await asyncio.sleep(2)
        click_frame = None
        show_frame = None
        frames = page.frames
        for frame in frames:
            print(frame.name)
            if "/api2/bframe" in frame.url:
                show_frame = page.frame_locator(f'iframe[name="{frame.name}"]')
            if "/api2/anchor" in frame.url:
                click_frame = page.frame_locator(f'iframe[name="{frame.name}"]')
        await click_frame.get_by_label("로봇이 아닙니다.").click()
        await logging_debug(
            "check-manager", "[로봇이 아닙니다]", {"debug_message": "로봇이 아닙니다."}
        )
        await asyncio.sleep(1)
        # 리캡챠 떳는지 확인
        await check_popup_recaptcha_failed(show_frame)
        await show_frame.get_by_role("button", name="음성 보안문자 듣기").click()
        await logging_debug(
            "check-manager", "[음성 보안문자 듣기]", {"debug_message": "음성 보안문자 듣기"}
        )
        await asyncio.sleep(1)
        # 보안문자 떳는지 확인
        await check_popup_recaptcha_failed(show_frame)
        audio_url = await show_frame.get_by_role(
            "link", name="또는 오디오를 MP3로 다운로드하세요."
        ).get_attribute("href")
        await logging_debug(
            "check-manager", "[음성 보안문자 듣기] - 다운로드 주소", {"debug_message": audio_url}
        )
        await asyncio.sleep(1)
        urllib.request.urlretrieve(audio_url, "stt/audio.mp3")
        response = sample_recognize("stt/audio.mp3")
        if response:
            print(response)
            await logging_debug(
                "check-manager", "[음성 보안문자 듣기] - 음성인식 결과", {"stt_result": response}
            )
            await show_frame.get_by_label("들리는 대로 입력하세요.").fill(response)
            await show_frame.get_by_role("button", name="확인").click()
            await logging_debug(
                "check-manager", "[들리는대로 입력하세요 확인]", {"debug_message": "들리는대로 입력하세요 확인"}
            )
            # 보안 문자 떳는지 확인
            await asyncio.sleep(1)
            await check_popup_recaptcha_failed(show_frame)
            await page.get_by_role("button", name="로그인", exact=True).click()
            await logging_debug(
                "check-manager", "마지막 로그인", {"debug_message": "마지막 로그인"}
            )
            await asyncio.sleep(1)
            await check_popup_recaptcha_failed(show_frame)
            await page.wait_for_selector("div.profile_img")
        else:
            await logging_error("check-manager", "stt 실패", {"err_message": "stt 실패"})
            print("stt 실패")
            await logging_debug("check-manager", "stt 실패", {"debug_message": "stt 실패"})
            raise ex.PlayWrightException(ex.PWEEnum.PD_LOGIN_STT_FAILED)
    else:
        print("로그인 성공")
        login_profile = await page.query_selector("div.profile_img")
        manager_nickname = await login_profile.inner_text()
        await logging_debug("check-manager", "로그인 성공", {"debug_message": "로그인 성공"})
        return manager_nickname


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
    night_watch_start()

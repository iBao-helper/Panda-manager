""" 후........ 쉬발 파이린트는 넘 빡세다 """
import os
import asyncio
import re
import time
import uvicorn
import requests
import concurrent.futures
from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
from dotenv import load_dotenv
from classes import night_watch as nw
from classes import night_watch_selenium as nws
from custom_exception import custom_exceptions as ex
from stt import sample_recognize
from util.my_util import logging_debug


load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"
app = FastAPI()
night_watch: nw.NightWatch = nw.NightWatch()
sele_watch: nws.SeleWatch = nws.SeleWatch()

# ThreadPoolExecutor를 생성하여 loop2 함수를 별도의 스레드에서 실행합니다.
executor = concurrent.futures.ThreadPoolExecutor()


def loop2():
    """aaa"""
    while True:
        time.sleep(5)
        sele_watch.refresh()
        time.sleep(5)
        sele_watch.start()


@app.post("/NightWatch")
async def night_watch_start():
    """감시자 시작"""
    sele_watch.create_selenium()
    sele_watch.element_click_with_css("button.btnClose")
    sele_watch.login()
    sele_watch.goto_url("https://www.pandalive.co.kr/pick#bookmark")
    await asyncio.sleep(1)
    executor.submit(loop2)
    return {"message": "NightWatch"}


@app.delete("/NightWatch")
async def night_watch_stop():
    """감시자 종료"""
    await night_watch.destroy()
    await night_watch.stop()
    return {"message": "NightWatch"}


@app.get("/test")
async def test(response: Response):
    """테스트"""
    response.status_code = status.HTTP_202_ACCEPTED
    return {"message": "Something went wrong"}, status.HTTP_400_BAD_REQUEST


@app.get("/check-manager", status_code=status.HTTP_200_OK)
async def check_manager_login(manager_id: str, manager_pw: str, response: Response):
    """매니저로 사용하는 id/pw가 로그인이 가능한지 확인하는 함수"""
    print(manager_id)
    print(manager_pw)
    apw = await async_playwright().start()
    browser = await apw.chromium.launch(headless=False)
    page = await browser.new_page()
    await logging_debug("check_manager_login", "매니저 체크", {
        "manager_id": manager_id,
        "manager_pw": manager_pw
    })
    try:
        await page.goto("http://pandalive.co.kr")
        await page.get_by_role("button", name="닫기").click()
        await page.get_by_role("button", name="로그인 / 회원가입").click()
        await page.get_by_role("link", name="로그인 / 회원가입").click()
        await page.get_by_role("link", name="로그인").click()
        # await page.get_by_role("textbox").nth(1).fill("siveriness0")
        # await page.get_by_role("textbox").nth(2).fill("dkflfkd12#")
        await page.get_by_role("textbox").nth(1).fill(manager_id)
        await page.get_by_role("textbox").nth(2).fill(manager_pw)
        await asyncio.sleep(2)
        await page.get_by_role("button", name="로그인", exact=True).click()
        await asyncio.sleep(2)
        invalid_text_id = await page.get_by_text("존재하지 않는 사용자입니다.").is_visible()
        invalid_text_pw = await page.get_by_text("비밀번호가 일치하지 않습니다.다시 입력해 주세요.").is_visible()
        if invalid_text_id or invalid_text_pw:
            raise ex.PlayWrightException(ex.PWEEnum.NW_LOGIN_INVALID_ID_OR_PW)  # pylint: disable=W0719
        invalid_label_id = await page.get_by_label("존재하지 않는 사용자입니다.").is_visible()
        invalid_label_pw = await page.get_by_label(
            "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
        ).is_visible()
        if invalid_label_id or invalid_label_pw:
            raise ex.PlayWrightException(ex.PWEEnum.NW_LOGIN_INVALID_ID_OR_PW)  # pylint: disable=W0719
        invalid_login_detect = await page.get_by_label(
            "비정상적인 로그인이 감지되었습니다.잠시 후 다시 시도해 주세요."
        ).is_visible()
        auto_detect = await page.get_by_label("자동접속방지 체크박스를 확인해주세요").is_visible()
        print(invalid_login_detect, auto_detect)
        if invalid_login_detect or auto_detect:
            # print("Invliad login popup")
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
            await show_frame.get_by_role("button", name="음성 보안문자 듣기").click()
            audio_url = await show_frame.get_by_role(
                "link", name="또는 오디오를 MP3로 다운로드하세요."
            ).get_attribute("href")
            print(audio_url)
            os.system(f"curl {audio_url} --output stt/audio.mp3")
            stt_response = sample_recognize("stt/audio.mp3")
            if stt_response:
                print(stt_response)
                await show_frame.get_by_label("들리는 대로 입력하세요.").fill(stt_response)
                await show_frame.get_by_role("button", name="확인").click()
                await page.get_by_role("button", name="로그인", exact=True).click()
                await page.wait_for_selector("div.profile_img")
            else:
                print("stt 실패")
                raise ex.PlayWrightException(ex.PWEEnum.NW_LOGIN_STT_FAILED)  # pylint: disable=W0719
        else:
            print("로그인 성공")
            await logging_debug("check_manager_login", "매니저 체크 성공", {
              "manager_id": manager_id,
              "manager_pw": manager_pw
            })
            login_profile = await page.query_selector("div.profile_img")
            manager_nickname = await login_profile.inner_text()
            await browser.close()
            return manager_nickname
    except ex.PlayWrightException as exc: # pylint: disable=W0718 W0702
        await page.goto("http://pandalive.co.kr")
        await page.get_by_role("button", name="로그인 / 회원가입").click()
        await page.get_by_role("link", name="로그인 / 회원가입").click()
        await page.get_by_role("link", name="로그인").click()
        await page.get_by_role("textbox").nth(1).fill("resetaccount")
        await page.get_by_role("textbox").nth(2).fill("Adkflfkd1")
        await asyncio.sleep(2)
        await page.get_by_role("button", name="로그인", exact=True).click()
        await asyncio.sleep(2)
        await browser.close()
        if exc.description == ex.PWEEnum.NW_LOGIN_INVALID_ID_OR_PW:
            await logging_debug("check_manager_login", "매니저 체크 실패", {
              "manager_id": manager_id,
              "manager_pw": manager_pw,
              "err_message": "ID/PW 불일치"
            })
            response.status_code = status.HTTP_400_BAD_REQUEST
            return {"message": "ID/PW 불일치"}
            
        elif exc.description == ex.PWEEnum.NW_LOGIN_STT_FAILED:
            await logging_debug("check_manager_login", "매니저 체크 실패", {
              "manager_id": manager_id,
              "manager_pw": manager_pw,
              "err_message": "STT 실패"
            })
            response.status_code = status.HTTP_409_CONFLICT
            return {"message": "STT 실패"}
  


@app.get("/panda-nickname", status_code=status.HTTP_200_OK)
async def get_panda_nickname(bj_id: str, response: Response):
    """panda-id로 방송국에 접속하여 닉네임을 가져와서 반환하는 함수"""
    apw = await async_playwright().start()
    browser = await apw.chromium.launch(headless=HEADLESS)
    page = await browser.new_page()
    await page.goto(f"https://www.pandalive.co.kr/channel/{bj_id}/notice")
    await asyncio.sleep(1)
    if page.url != f"https://www.pandalive.co.kr/channel/{bj_id}/notice":
        response.status_code = status.HTTP_404_NOT_FOUND
        await browser.close()
        return {"message": "null"}
    nickname = await page.query_selector(".nickname")
    nickname = await nickname.inner_text()
    result = re.sub(r"\([^)]*\)", "", nickname)
    await browser.close()
    print(result)
    return result


@app.get("/add-bookmark", status_code=status.HTTP_200_OK)
async def add_book_mark(bj_id: str):
    """북마크 추가"""
    sele_watch.add_book_mark_list(bj_id)
    return {"message": "success"}


@app.get("/delete-bookmark", status_code=status.HTTP_200_OK)
async def delete_book_mark(bj_id: str):
    """북마크 추가"""
    sele_watch.delete_book_mark_list(bj_id)
    return {"message": "success"}




@app.on_event("startup")
async def startup_event():
    """
    NightWatch 가동시 backend에 등록 요청을 시도함
    이미 있다면 등록되지 않음
    """
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/nightwatch",
            json={"ip": "112.185.118.249"},
            timeout=5,
        )
    except:  # pylint: disable=W0702
        print("nightwatch already registered")


## 현재 로컬환경에서 테스트라 localServer 리소스가 실행될때 backend 에 등록하지 않음
## 차후 localServer 리소스가 실행될때 backend 에 등록하는 기능을 추가해야함


## Exception Handler 모음
@app.exception_handler(ex.PlayWrightException)
async def play_wright_handler(exc: ex.PlayWrightException):
    """PlayWright Exception Handler"""
    print(os.getcwd())
    print(exc.description)
    if exc.description == ex.PWEEnum.NW_CREATE_ERROR:
        # nw 가동 실패
        print(exc)
        await night_watch.destroy()

    elif exc.description == ex.PWEEnum.NW_LOGIN_INVALID_ID_OR_PW:
        # nigthwatch 로그인 실패
        print(exc)
        await night_watch.destroy()
    elif exc.description == ex.PWEEnum.NW_LOGIN_STT_FAILED:
        # STT 실패
        print(exc)
        await night_watch.destroy()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "PlayWright Exception"},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
    night_watch_start()

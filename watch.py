""" 후........ 쉬발 파이린트는 넘 빡세다 """
import datetime
import os
import asyncio
import re
import uvicorn
import requests
from fastapi import FastAPI, Response, status, Request
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
import aiofiles as aiof
from classes import night_watch as nw
from custom_exception import custom_exceptions as ex
from stt import sample_recognize
from util.my_env import BACKEND_URL, BACKEND_PORT


app = FastAPI()
night_watch: nw.NightWatch = nw.NightWatch()


@app.post("/NightWatch")
async def night_watch_start():
    """감시자 시작"""
    await night_watch.create_playwright()
    await night_watch.login()
    await night_watch.goto_url("https://www.pandalive.co.kr/pick#bookmark")
    await asyncio.sleep(1)
    asyncio.create_task(night_watch.start_night_watch())
    return {"message": "NightWatch"}


@app.delete("/NightWatch")
async def night_watch_stop():
    """감시자 종료"""
    await night_watch.destroy()
    await night_watch.stop()
    return {"message": "NightWatch"}


@app.get("/test")
async def test():
    """테스트"""
    return {"message": "test"}


@app.get("/check-manager", status_code=status.HTTP_200_OK)
async def check_manager_login(id: str, pw: str, response: Response):
    """매니저로 사용하는 id/pw가 로그인이 가능한지 확인하는 함수"""
    print(id)
    print(pw)
    apw = await async_playwright().start()
    browser = await apw.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto("http://pandalive.co.kr")
    await page.get_by_role("button", name="닫기").click()
    await page.get_by_role("button", name="로그인 / 회원가입").click()
    await page.get_by_role("link", name="로그인 / 회원가입").click()
    await page.get_by_role("link", name="로그인").click()
    # await page.get_by_role("textbox").nth(1).fill("siveriness0")
    # await page.get_by_role("textbox").nth(2).fill("dkflfkd12#")
    await page.get_by_role("textbox").nth(1).fill(id)
    await page.get_by_role("textbox").nth(2).fill(pw)
    await asyncio.sleep(2)
    await page.get_by_role("button", name="로그인", exact=True).click()
    await asyncio.sleep(2)
    invalid_text_id = await page.get_by_text("존재하지 않는 사용자입니다.").is_visible()
    invalid_text_pw = await page.get_by_text("비밀번호가 일치하지 않습니다.다시 입력해 주세요.").is_visible()
    if invalid_text_id or invalid_text_pw:
        await browser.close()
        raise ex.PlayWrightException("Invalid Id/PW")  # pylint: disable=W0719
    invalid_label_id = await page.get_by_label("존재하지 않는 사용자입니다.").is_visible()
    invalid_label_pw = await page.get_by_label(
        "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
    ).is_visible()
    if invalid_label_id or invalid_label_pw:
        await browser.close()
        raise ex.PlayWrightException("Invalid Id/PW")  # pylint: disable=W0719
    invalid_login_detect = await page.get_by_label(
        "비정상적인 로그인이 감지되었습니다.잠시 후 다시 시도해 주세요."
    ).is_visible()
    auto_detect = await page.get_by_label("자동접속방지 체크박스를 확인해주세요").is_visible()
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
        test = await show_frame.get_by_role(
            "link", name="또는 오디오를 MP3로 다운로드하세요."
        ).get_attribute("href")
        print(test)
        os.system(f"curl {test} --output stt/audio.mp3")
        response = sample_recognize("stt/audio.mp3")
        if response:
            print(response)
            await show_frame.get_by_label("들리는 대로 입력하세요.").fill(response)
            await show_frame.get_by_role("button", name="확인").click()
            await page.get_by_role("button", name="로그인", exact=True).click()
            await page.wait_for_selector("div.profile_img")
        else:
            print("stt 실패")
            raise ex.PlayWrightException("stt 실패")  # pylint: disable=W0719
    else:
        print("로그인 성공")
        login_profile = await page.query_selector("div.profile_img")
        manager_nickname = await login_profile.inner_text()
        await browser.close()
    return manager_nickname


@app.get("/panda-nickname", status_code=status.HTTP_200_OK)
async def get_panda_nickname(id: str, response: Response):
    """panda-id로 방송국에 접속하여 닉네임을 가져와서 반환하는 함수"""
    apw = await async_playwright().start()
    browser = await apw.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto(f"https://www.pandalive.co.kr/channel/{id}/notice")
    await asyncio.sleep(1)
    if page.url != f"https://www.pandalive.co.kr/channel/{id}/notice":
        response.status_code = status.HTTP_404_NOT_FOUND
        return {"message": "null"}
    nickname = await page.query_selector(".nickname")
    nickname = await nickname.inner_text()
    result = re.sub(r"\([^)]*\)", "", nickname)
    asyncio.create_task(night_watch.add_book_mark_list(id))
    await browser.close()
    print(result)
    return result


@app.on_event("startup")
async def startup_event():
    """
    NightWatch 가동시 backend에 등록 요청을 시도함
    이미 있다면 등록되지 않음
    """
    try:
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/nightwatch",
            json={"ip": "222.110.198.130"},
            timeout=5,
        )
    except:  # pylint: disable=W0702
        print("nightwatch already registered")


## 현재 로컬환경에서 테스트라 localServer 리소스가 실행될때 backend 에 등록하지 않음
## 차후 localServer 리소스가 실행될때 backend 에 등록하는 기능을 추가해야함


## Exception Handler 모음
@app.exception_handler(ex.PlayWrightException)
async def play_wright_handler(request: Request, exc: ex.PlayWrightException):
    """PlayWright Exception Handler"""
    print(os.getcwd())
    print(exc.description)
    file_path = os.path.join(os.getcwd(), "logs", "nw.log")
    if exc.description == ex.PWEEnum.NW_CREATE_ERROR:
        # nw 가동 실패
        await night_watch.destroy()
        async with aiof.open(file_path, "a") as out:
            await out.write(
                (
                    f"{datetime.datetime.now()} : {request.url} / {await request.body()} / "
                    f"{exc.description} / {request.query_params}\n"
                )
            )
            await out.flush()

    elif exc.description == ex.PWEEnum.NW_LOGIN_INVALID_ID_OR_PW:
        # nigthwatch 로그인 실패
        await night_watch.destroy()
        async with aiof.open(file_path, "a") as out:
            await out.write(
                (
                    f"{datetime.datetime.now()} : {request.url} / {await request.body()} / "
                    f"{exc.description} / {request.query_params}\n"
                )
            )
            await out.flush()
    elif exc.description == ex.PWEEnum.NW_LOGIN_STT_FAILED:
        # STT 실패
        await night_watch.destroy()
        async with aiof.open(file_path, "a") as out:
            await out.write(
                (
                    f"{datetime.datetime.now()} : {request.url} / {await request.body()} / "
                    f"{exc.description} / {request.query_params}\n"
                )
            )
            await out.flush()

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"message": "PlayWright Exception"},
    )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)

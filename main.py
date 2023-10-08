""" 후........ 쉬발 파이린트는 넘 빡세다 """
import os
import asyncio
import re
import uvicorn
from fastapi import FastAPI, Response, status
from playwright.async_api import async_playwright
from classes.night_watch import NightWatch
from stt import sample_recognize

app = FastAPI()
night_watch: NightWatch = NightWatch()


@app.get("/")
async def root():
    """root"""
    asyncio.create_task(night_watch.create_playwright())
    return {"message": "Hello World"}


@app.post("/NightWatch")
async def night_watch_start():
    """감시자 시작"""
    task = asyncio.create_task(night_watch.create_playwright())
    await task
    task = asyncio.create_task(night_watch.login())
    await task
    task = asyncio.create_task(
        night_watch.goto_url("https://www.pandalive.co.kr/pick#bookmark")
    )
    asyncio.create_task(night_watch.start_night_watch())
    return {"message": "NightWatch"}


@app.delete("/NightWatch")
async def night_watch_stop():
    """감시자 종료"""
    asyncio.create_task(night_watch.stop())
    return {"message": "NightWatch"}


@app.get("/userlist")
async def userlist():
    """유저리스트"""
    asyncio.create_task(night_watch.get_user_status())
    return {"message": "userlist"}


@app.get("/test")
async def test():
    """테스트"""
    asyncio.create_task(night_watch.test2())
    return {"message": "test"}


@app.get("/check-manager", status_code=status.HTTP_200_OK)
async def check_manager_login(id: str, pw: str, response: Response):
    """매니저 로그인 확인"""
    print(id)
    print(pw)
    apw = await async_playwright().start()
    browser = await apw.chromium.launch(headless=False)
    page = await browser.new_page()
    await page.goto("http://pandalive.co.kr")
    try:
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
        invalid_text_pw = await page.get_by_text(
            "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
        ).is_visible()
        if invalid_text_id or invalid_text_pw:
            print("Invalid Id or PW")
            raise Exception("Invalid Id/PW")  # pylint: disable=W0719
        invalid_label_id = await page.get_by_label("존재하지 않는 사용자입니다.").is_visible()
        invalid_label_pw = await page.get_by_label(
            "비밀번호가 일치하지 않습니다.다시 입력해 주세요."
        ).is_visible()
        if invalid_label_id or invalid_label_pw:
            print("popup Invalid Id or PW")
            await page.get_by_role("button", name="확인").click()
            raise Exception("Invalid Id/PW")  # pylint: disable=W0719
        invalid_login_detect = await page.get_by_label(
            "비정상적인 로그인이 감지되었습니다.잠시 후 다시 시도해 주세요."
        ).is_visible()
        auto_detect = await page.get_by_label("자동접속방지 체크박스를 확인해주세요").is_visible()
        if invalid_login_detect or auto_detect:
            print("Invliad login popup")
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
            print(f"curl {test} --output stt/audio.mp3")
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
                raise Exception("stt 실패")  # pylint: disable=W0719
        else:
            print("로그인 성공")
    except Exception as e:  # pylint: disable=C0103,W0718
        print(e)
        response.status_code = status.HTTP_404_NOT_FOUND
        # await browser.close()
    return {"message": "ok"}


@app.get("/panda-nickname", status_code=status.HTTP_200_OK)
async def get(id: str, response: Response):
    """매니저 로그인 확인"""
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


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

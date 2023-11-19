""" 후........ 쉬발 파이린트는 넘 빡세다 """
import os
import asyncio
import re
from typing import Dict
import uvicorn
import requests
from fastapi import FastAPI, Response, status, Request
from fastapi.responses import JSONResponse
from playwright.async_api import async_playwright
from classes import night_watch as nw
from classes import panda_manager as pm
from custom_exception import custom_exceptions as ex
from stt import sample_recognize
from util.my_util import User, logging
from dotenv import load_dotenv
import traceback

load_dotenv()


BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")
CAPACITY = os.getenv("CAPACITY")
SERVER_KIND = os.getenv("SERVER_KIND")
PUBLIC_IP = os.getenv("PUBLIC_IP")
INSTANCE_ID = os.getenv("INSTANCE_ID")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

app = FastAPI()
night_watch: nw.NightWatch = nw.NightWatch()
panda_managers: Dict[str, pm.PandaManager] = {}


@app.post("/panda_manager/{panda_id}")
async def panda_manager_start(body: pm.CreateManagerDto, panda_id: str):
    """판다매니저 시작"""
    await logging(body.panda_id, f"[panda_manager_start] - body data\n{body}")
    print(body, panda_id)
    panda_manager: pm.PandaManager = pm.PandaManager(body)
    panda_managers[panda_id] = panda_manager

    await logging(
        body.panda_id,
        f"[panda_manager_start] - create_playwright start\nproxy_ip:{body.proxy_ip}",
    )
    await panda_manager.create_playwright(body.proxy_ip)

    await logging(
        body.panda_id,
        f"[panda_manager_start] - login start\nlogin_id:{body.manager_id}, login_pw={body.manager_pw}",
    )
    # 로그인이 실패할 경우 PD_LOIGIN_이유 발생
    try:
        await panda_manager.login(login_id=body.manager_id, login_pw=body.manager_pw)
    except TimeoutError:
        await panda_manager.page.screenshot(path=body.panda_id + ".png")
        files = {
            "file": (
                body.panda_id + ".png",
                open(body.panda_id + ".png", "rb"),
                "image/png",
            )
        }
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log/upload",
            files=files,
            timeout=20,
        )
        raise ex.PlayWrightException(
            panda_id, ex.PWEEnum.PD_LOGIN_STT_FAILED, "로그인 시간 초과"
        ) from TimeoutError

    await logging(
        body.panda_id,
        f"[panda_manager_start] - goto url \nhttps://www.pandalive.co.kr/live/play/{panda_id}",
    )
    await panda_manager.goto_url(f"https://www.pandalive.co.kr/live/play/{panda_id}")
    # 처음 들어갈때 팝업 제거
    await panda_manager.page.get_by_role("button", name="확인").click()

    ## 무사히 방송에 접속하였다면 DB에 관계를 설정해준다
    if SERVER_KIND == "local":
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/success-proxy-task",
            json={
                "ip": body.proxy_ip,
                "panda_id": panda_id,
                "resource_ip": body.resource_ip,
            },
            timeout=5,
        )
    elif SERVER_KIND == "ec2":
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/success-ec2-task",
            json={
                "panda_id": panda_id,
                "resource_ip": body.resource_ip,
            },
            timeout=5,
        )
    data = requests.get(
        url=f"http://{BACKEND_URL}:{BACKEND_PORT}/bj/{panda_id}?relaiton=true",
        timeout=5,
    )
    user = User(**data.json())
    panda_manager.set_user(user)
    print("response user relation data : ", user)
    await panda_manager.remove_elements()
    asyncio.create_task(panda_manager.macro())
    ## 이후 DB에 capacity 감소 하는 로직이 필요함
    return {"message": "PandaManager"}


@app.delete("/panda_manager/{panda_id}")
async def destory_panda_manager(panda_id: str):
    """dict에서 해당 panda_id를 키로 가진 리소스 제거"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].destroy()
        del panda_managers[panda_id]
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is deleted"},
    )


@app.put("/panda_manager/{panda_id}/command")
async def update_manager_command(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_commands()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/rc-message")
async def update_manager_rc(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_recommend()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/hart-message")
async def update_manager_hart(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_hart_message()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/pr-message")
async def update_manager_pr(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_pr()
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.get("/test")
async def test():
    """테스트"""
    # asyncio.create_task(night_watch.test2())
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
        await browser.close()

    return {"message": "ok"}


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


## 현재 로컬환경에서 테스트라 localServer 리소스가 실행될때 backend 에 등록하지 않음
## 차후 localServer 리소스가 실행될때 backend 에 등록하는 기능을 추가해야함


## Exception Handler 모음
@app.exception_handler(ex.PlayWrightException)
async def play_wright_handler(request: Request, exc: ex.PlayWrightException):
    """PlayWright Exception Handler"""
    await panda_managers[exc.panada_id].send_screenshot()
    if SERVER_KIND == "ec2":
        print("ec2 task 실패")
        if exc.description == ex.PWEEnum.PD_CREATE_ERROR:
            # nw 가동 실패
            print("PD 가동 실패", exc.panada_id, exc.description)
            status_code = status.HTTP_400_BAD_REQUEST
            message = "PandaManager 생성 실패"
            await logging(
                exc.panada_id,
                f"{SERVER_KIND} - PlayWright Error\n{message}",
            )
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-ec2-task",
                json={"panda_id": exc.panada_id, message: exc.message},
                timeout=10,
            )
        elif exc.description == ex.PWEEnum.PD_LOGIN_INVALID_ID_OR_PW:
            # nigthwatch 로그인 실패
            status_code = status.HTTP_200_OK
            message = "ID/PW 로그인 실패"
            # ID/PW가 틀려서 실패했다면 재시도 하지 않는게 맞다. 다른 콜백 경로로 리소스만 해제해주는것이 옳음.
            await logging(
                exc.panada_id,
                f"{SERVER_KIND} - PlayWright Error\n{message}",
            )
            requests.delete(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-ec2-login",
                json={"panda_id": exc.panada_id},
                timeout=10,
            )
        elif exc.description == ex.PWEEnum.PD_LOGIN_STT_FAILED:
            # 이 경우는 stt에 실패했거나 봇 탐지에 걸렸을 경우 재시작 해야함
            status_code = status.HTTP_400_BAD_REQUEST
            message = "stt 실패"
            await logging(
                exc.panada_id,
                f"{SERVER_KIND} - PlayWright Error\n{message}",
            )
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-ec2-task",
                json={"panda_id": exc.panada_id, message: exc.message},
                timeout=10,
            )
        message = "EC2 task 실패"
    elif SERVER_KIND == "local":
        print("ec2 task 실패")
        if exc.description == ex.PWEEnum.PD_CREATE_ERROR:
            # nw 가동 실패
            print("PD 가동 실패", exc.panada_id, exc.description)
            status_code = status.HTTP_400_BAD_REQUEST
            message = "PandaManager 생성 실패"
            await logging(
                exc.panada_id,
                f"{SERVER_KIND} - PlayWright Error\n{message}",
            )
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-proxy-task",
                json={"panda_id": exc.panada_id, "message": message},
                timeout=10,
            )
        elif exc.description == ex.PWEEnum.PD_LOGIN_INVALID_ID_OR_PW:
            # nigthwatch 로그인 실패
            status_code = status.HTTP_200_OK
            message = "ID/PW 로그인 실패"
            await logging(
                exc.panada_id,
                f"{SERVER_KIND} - PlayWright Error\n{message}",
            )
            # ID/PW가 틀려서 실패했다면 재시도 하지 않는게 맞다. 다른 콜백 경로로 리소스만 해제해주는것이 옳음.
            requests.delete(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-proxy-login",
                json={"panda_id": exc.panada_id, "message": message},
                timeout=10,
            )
        elif exc.description == ex.PWEEnum.PD_LOGIN_STT_FAILED:
            # 이 경우는 stt에 실패했거나 봇 탐지에 걸렸을 경우 재시작 해야함
            status_code = status.HTTP_400_BAD_REQUEST
            message = "stt 실패"
            await logging(
                exc.panada_id,
                f"{SERVER_KIND} - PlayWright Error\n{message}",
            )
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-proxy-task",
                json={"panda_id": exc.panada_id, "message": message},
                timeout=10,
            )
    return JSONResponse(
        status_code=status_code,
        content={"message": message},
    )


@app.exception_handler(Exception)
async def default_exception_filter(request: Request, e: Exception):
    """예상치 못한 에러가 발생했을때 백엔드에 로깅하기 위한 필터"""
    if "panda_id" in request.path_params:
        panda_id = request.path_params["panda_id"]
        if SERVER_KIND == "ec2":
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-ec2-task",
                json={"panda_id": panda_id, "message": "Unkown-Ec2-Error"},
                timeout=10,
            )
        elif SERVER_KIND == "local":
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-proxy-task",
                json={"panda_id": panda_id, "message": "Unkown-Proxy-Error"},
                timeout=10,
            )
        await logging(panda_id, f"Exception Error\n{str(e)}")
        await logging(panda_id, {traceback.print_exc()})
    else:
        await logging("Unkown-Error", f"{SERVER_KIND} - Exception Error\n{str(e)}")
        await logging("Unkown-Error", {traceback.print_exc()})

    return JSONResponse(
        status_code=500,
        content={"message": str(e)},
    )


@app.on_event("startup")
async def startup_event():
    """
    PandaManager 가동시 backend에 등록 요청을 시도함
    이미 있다면 등록되지 않음
    """
    try:
        print(f"{PUBLIC_IP}")
        await logging(
            "common-env-check",
            f"PUBLIC_IP : {PUBLIC_IP}, CAPACITY : {CAPACITY}, INSTANCE_ID : {INSTANCE_ID}, "
            f"SERVER_KIND : {SERVER_KIND}",
        )
        requests.post(
            url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource",
            json={
                "ip": PUBLIC_IP,
                "capacity": int(CAPACITY),
                "kind": SERVER_KIND,
                "instance_id": INSTANCE_ID,
            },
            timeout=5,
        )

    except:  # pylint: disable=W0702
        print("nightwatch already registered")


# @app.on_event("shutdown")
# async def shutdown_event():
#     """
#     PandaManager 가동시 backend에 등록 요청을 시도함
#     이미 있다면 등록되지 않음
#     """
#     try:
#         requests.delete(
#             url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource",
#             json={"ip": "222.110.198.130"},
#             timeout=5,
#         )
#     except:  # pylint: disable=W0702
#         print("nightwatch already registered")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

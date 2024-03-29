""" 후........ 쉬발 파이린트는 넘 빡세다 """
import os
import asyncio
from typing import Dict
import traceback
import uvicorn
import requests
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from classes import panda_manager as pm
from custom_exception import custom_exceptions as ex
from util.my_util import User, logging_debug, logging_error, logging_info


load_dotenv()


BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")
CAPACITY = os.getenv("CAPACITY")
SERVER_KIND = os.getenv("SERVER_KIND")
PUBLIC_IP = os.getenv("PUBLIC_IP")
INSTANCE_ID = os.getenv("INSTANCE_ID")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

app = FastAPI()
panda_managers: Dict[str, pm.PandaManager] = {}


@app.post("/panda_manager/{panda_id}")
async def panda_manager_start(body: pm.CreateManagerDto, panda_id: str):
    """판다매니저 시작"""
    await logging_info(
        body.panda_id,
        f"[매니저 요청 루틴 시작] - {body.panda_id}",
        {
            "panda_id": body.panda_id,
            "proxy_ip": body.proxy_ip,
            "manager_id": body.manager_id,
            "manager_pw": body.manager_pw,
            "resource_ip": body.resource_ip,
        },
    )
    panda_manager: pm.PandaManager = pm.PandaManager(body)
    panda_managers[panda_id] = panda_manager

    await logging_debug(
        body.panda_id,
        f"[panda_manager_start] - proxy_ip {body.proxy_ip}",
        {"proxy_ip": body.proxy_ip},
    )
    await panda_manager.create_playwright(body.proxy_ip)

    await logging_debug(
        body.panda_id,
        "[panda_manager_start] - login start",
        {"login_id": body.manager_id, "login_pw": body.manager_pw},
    )
    # 로그인이 실패할 경우 PD_LOIGIN_이유 발생
    try:
        await panda_manager.login(login_id=body.manager_id, login_pw=body.manager_pw)
    except TimeoutError:
        await logging_error(
            body.panda_id, "TimeOut Error", {"err_messagE": "로그인 시간 초과"}
        )
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
    await panda_manager.set_interceptor()
    ## 실험용 코드 - search API를 사용하기 위한 헤더 설정을 위한 요청
    await panda_manager.goto_url(
        "https://www.pandalive.co.kr/live/search?text=%ED%85%8C%EC%8A%A4%ED%8A%B8"
    )
    ##
    await logging_info(body.panda_id, "로그인 작업 성공", {"message": "로그인 작업 성공"})
    await panda_manager.goto_url(f"https://www.pandalive.co.kr/live/play/{panda_id}")
    # 처음 들어갈때 팝업 제거
    try:
        await panda_manager.page.get_by_role("button", name="확인").click()
    except:  # pylint: disable=W0702
        await logging_error(body.panda_id, "확인 버튼 없음", {"message": "확인 버튼 없음"})

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
    await logging_info(body.panda_id, "[매니저 정보 획득]", {"message": "매니저 정보 획득"})
    await panda_manager.remove_elements()
    await logging_info(body.panda_id, "[delete elements]", {"message": "elements"})
    asyncio.create_task(panda_manager.macro())
    ## 이후 DB에 capacity 감소 하는 로직이 필요함
    return {"message": "PandaManager"}


@app.delete("/panda_manager/{panda_id}")
async def destory_panda_manager(panda_id: str):
    """dict에서 해당 panda_id를 키로 가진 리소스 제거"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].destroy()
        del panda_managers[panda_id]
        await logging_info(panda_id, "[리소스 회수 성공]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is deleted"},
    )


@app.put("/panda_manager/{panda_id}/command")
async def update_manager_command(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_commands()
        await logging_info(panda_id, "[Front - 커맨드 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/rc-message")
async def update_manager_rc(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_recommend()
        await logging_info(panda_id, "[Front - 추천 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/hart-message")
async def update_manager_hart(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_hart_message()
        await logging_info(panda_id, "[Front - 하트 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/pr-message")
async def update_manager_pr(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_pr()
        await logging_info(panda_id, "[Front - PR 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/greet-message")
async def update_manager_greet(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_greet_message()
        await logging_info(panda_id, "[Front - Greet 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/doosan-message")
async def update_manager_doosan(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_doosan_message()
        await logging_info(panda_id, "[Front - Doosan 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/rc-message/toggle")
async def update_rc_toggle(panda_id: str):
    """RC 토글 업데이트"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].toggle_rc()
        await logging_info(panda_id, "[Front - 추천 토글 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/hart-message/toggle")
async def update_hart_toggle(panda_id: str):
    """Hart 토글 업데이트"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].toggle_hart()
        await logging_info(panda_id, "[Front - 하트 토글 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/pr-message/toggle")
async def update_pr_toggle(panda_id: str):
    """PR 토글 업데이트"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].toggle_pr()
        await logging_info(panda_id, "[Front - PR 토글 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/greet-message/toggle")
async def update_greet_toggle(panda_id: str):
    """Greet 토글 업데이트"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].toggle_greet()
        await logging_info(panda_id, "[Front - Greet 토글 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/doosan-message/toggle")
async def update_doosan_toggle(panda_id: str):
    """Greet 토글 업데이트"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].toggle_doosan()
        await logging_info(panda_id, "[Front - Doosan 토글 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.get("/screen-shot/{panda_id}")
async def screen_shot(panda_id: str):
    """스크린샷"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].send_screenshot()
        await logging_info(panda_id, "[스크린샷 요청 성공]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.get("/test")
async def test():
    """테스트"""
    # asyncio.create_task(night_watch.test2())
    len(panda_managers)
    return {"manager_size": len(panda_managers)}


## Exception Handler 모음
@app.exception_handler(ex.PlayWrightException)
async def play_wright_handler(request: Request, exc: ex.PlayWrightException):
    """PlayWright Exception Handler"""
    await panda_managers[exc.panda_id].send_screenshot()
    await panda_managers[exc.panda_id].destroy()
    if SERVER_KIND == "ec2":
        print("ec2 task 실패")
        if exc.description == ex.PWEEnum.PD_CREATE_ERROR:
            # nw 가동 실패
            print("PD 가동 실패", exc.panda_id, exc.description)
            status_code = status.HTTP_400_BAD_REQUEST
            message = "PandaManager 생성 실패"
            await logging_error(
                exc.panda_id,
                "PlayWright Error",
                {"server_kind": SERVER_KIND, "message": message},
            )
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-ec2-task",
                json={"panda_id": exc.panda_id, message: exc.message},
                timeout=10,
            )
        elif exc.description == ex.PWEEnum.PD_LOGIN_INVALID_ID_OR_PW:
            # nigthwatch 로그인 실패
            status_code = status.HTTP_200_OK
            message = "ID/PW 로그인 실패"
            # ID/PW가 틀려서 실패했다면 재시도 하지 않는게 맞다. 다른 콜백 경로로 리소스만 해제해주는것이 옳음.
            await logging_error(
                exc.panda_id,
                "PlayWright Error",
                {"server_kind": SERVER_KIND, "message": message},
            )
            requests.delete(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-ec2-login",
                json={"panda_id": exc.panda_id},
                timeout=10,
            )
        elif exc.description == ex.PWEEnum.PD_LOGIN_STT_FAILED:
            # 이 경우는 stt에 실패했거나 봇 탐지에 걸렸을 경우 재시작 해야함
            status_code = status.HTTP_400_BAD_REQUEST
            message = "stt 실패"
            await logging_error(
                exc.panda_id,
                "PlayWright Error",
                {"server_kind": SERVER_KIND, "message": message},
            )
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-ec2-task",
                json={"panda_id": exc.panda_id, message: exc.message},
                timeout=10,
            )
        message = "EC2 task 실패"
    elif SERVER_KIND == "local":
        print("ec2 task 실패")
        if exc.description == ex.PWEEnum.PD_CREATE_ERROR:
            # nw 가동 실패
            print("PD 가동 실패", exc.panda_id, exc.description)
            status_code = status.HTTP_400_BAD_REQUEST
            message = "PandaManager 생성 실패"
            await logging_error(
                exc.panda_id,
                "PlayWright Error",
                {"server_kind": SERVER_KIND, "message": message},
            )
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-proxy-task",
                json={"panda_id": exc.panda_id, "message": message},
                timeout=10,
            )
        elif exc.description == ex.PWEEnum.PD_LOGIN_INVALID_ID_OR_PW:
            # nigthwatch 로그인 실패
            status_code = status.HTTP_200_OK
            message = "ID/PW 로그인 실패"
            await logging_error(
                exc.panda_id,
                "PlayWright Error",
                {"server_kind": SERVER_KIND, "message": message},
            )
            # ID/PW가 틀려서 실패했다면 재시도 하지 않는게 맞다. 다른 콜백 경로로 리소스만 해제해주는것이 옳음.
            requests.delete(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-proxy-login",
                json={"panda_id": exc.panda_id, "message": message},
                timeout=10,
            )
        elif exc.description == ex.PWEEnum.PD_LOGIN_STT_FAILED:
            # 이 경우는 stt에 실패했거나 봇 탐지에 걸렸을 경우 재시작 해야함
            status_code = status.HTTP_400_BAD_REQUEST
            message = "stt 실패"
            await logging_error(
                exc.panda_id,
                "PlayWright Error",
                {"server_kind": SERVER_KIND, "message": message},
            )
            requests.post(
                url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource/callbacks/failure-proxy-task",
                json={"panda_id": exc.panda_id, "message": message},
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
        await panda_managers[panda_id].send_screenshot()
        await panda_managers[panda_id].destroy()
        await logging_error(panda_id, "Unkown Error", str(e))
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
        await logging_error(
            panda_id,
            "Unkown Error",
            {"message": str(e), "trace": traceback.print_exc()},
        )
    else:
        await logging_error(
            panda_id,
            "Unkown Error",
            {"message": str(e), "trace": traceback.print_exc()},
        )

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
        await logging_debug(
            "Manager",
            "PandaManager StartUp Function",
            {
                "PUBLIC_IP": PUBLIC_IP,
                "CAPACITY": CAPACITY,
                "INSTANCE_ID": INSTANCE_ID,
                "SERVER_KIND": SERVER_KIND,
            },
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

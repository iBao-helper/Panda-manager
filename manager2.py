""" 후........ 쉬발 파이린트는 넘 빡세다 """
import os
import asyncio
import threading
import subprocess
from typing import Dict
import uvicorn
from fastapi import FastAPI, status, Request
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from classes.panda_manager import PandaManager
from classes.dto.CreateManagerDto import CreateManagerDto
from classes.api_client import APIClient
from util.my_util import logging_info


load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")
CAPACITY = os.getenv("CAPACITY")
SERVER_KIND = os.getenv("SERVER_KIND")
PUBLIC_IP = os.getenv("PUBLIC_IP")
INSTANCE_ID = os.getenv("INSTANCE_ID")
HEADLESS = os.getenv("HEADLESS", "true").lower() == "true"

app = FastAPI()
panda_managers: Dict[str, subprocess.Popen] = {}
login_api_client = APIClient()


@app.post("/panda_manager/{panda_id}")
async def panda_manager_start(body: CreateManagerDto, panda_id: str):
    """판다매니저 시작"""
    sub_process = subprocess.Popen(
        [
            "python",
            "subprocess_test.py",
            body.panda_id,
            body.proxy_ip,
            body.manager_id,
            body.manager_pw,
            body.resource_ip,
        ],
    )
    panda_managers[panda_id] = sub_process
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is created"},
    )


@app.delete("/panda_manager/{panda_id}")
async def destroy_panda_manager(panda_id: str):
    """dict에서 해당 panda_id를 키로 가진 리소스 제거"""
    if panda_id in panda_managers:
        panda_managers[panda_id].terminate()
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
        await panda_managers[panda_id].update_user()
        await logging_info(panda_id, "[Front - 추천 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/hart-message")
async def update_manager_hart(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_user()
        await logging_info(panda_id, "[Front - 하트 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/pr-message")
async def update_manager_pr(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_user()
        await logging_info(panda_id, "[Front - PR 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/greet-message")
async def update_manager_greet(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_user()
        await logging_info(panda_id, "[Front - Greet 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/doosan-message")
async def update_manager_doosan(panda_id: str):
    """백엔드로부터 커맨드가 업데이트 될 경우"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_user()
        await logging_info(panda_id, "[Front - Doosan 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/rc-message/toggle")
async def update_rc_toggle(panda_id: str):
    """RC 토글 업데이트"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_user()
        await logging_info(panda_id, "[Front - 추천 토글 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/hart-message/toggle")
async def update_hart_toggle(panda_id: str):
    """Hart 토글 업데이트"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_user()
        await logging_info(panda_id, "[Front - 하트 토글 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/pr-message/toggle")
async def update_pr_toggle(panda_id: str):
    """PR 토글 업데이트"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_user()
        await logging_info(panda_id, "[Front - PR 토글 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/greet-message/toggle")
async def update_greet_toggle(panda_id: str):
    """Greet 토글 업데이트"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_user()
        await logging_info(panda_id, "[Front - Greet 토글 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.put("/panda_manager/{panda_id}/doosan-message/toggle")
async def update_doosan_toggle(panda_id: str):
    """Greet 토글 업데이트"""
    if panda_id in panda_managers:
        await panda_managers[panda_id].update_user()
        await logging_info(panda_id, "[Front - Doosan 토글 업데이트]", {"panda_id": panda_id})
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"message": f"{panda_id} is command updated"},
    )


@app.get("/test")
async def test():
    """테스트"""
    # asyncio.create_task(night_watch.test2())
    len(panda_managers)
    return {
        "manager_size": len(panda_managers),
        "data": [value.panda_id for i, value in panda_managers.items()],
    }


@app.exception_handler(Exception)
async def default_exception_filter(
    request: Request, e: Exception
):  # pylint: disable=W0613
    """예상치 못한 에러가 발생했을때 백엔드에 로깅하기 위한 필터"""
    print("default_exception_filter")
    return JSONResponse(
        status_code=500,
        content={"message": str(e)},
    )


# @app.on_event("startup")
# async def startup_event():
#     """메인쓰레드 이벤트루프 설정"""
#     asyncio.set_event_loop(asyncio.new_event_loop())

# """
# PandaManager 가동시 backend에 등록 요청을 시도함
# 이미 있다면 등록되지 않음
# """
# try:
#     await logging_debug(
#         "Manager",
#         "PandaManager StartUp Function",
#         {
#             "PUBLIC_IP": PUBLIC_IP,
#             "CAPACITY": CAPACITY,
#             "INSTANCE_ID": INSTANCE_ID,
#             "SERVER_KIND": SERVER_KIND,
#         },
#     )
#     requests.post(
#         url=f"http://{BACKEND_URL}:{BACKEND_PORT}/resource",
#         json={
#             "ip": PUBLIC_IP,
#             "capacity": int(CAPACITY),
#             "kind": SERVER_KIND,
#             "instance_id": INSTANCE_ID,
#         },
#         timeout=5,
#     )

# except:  # pylint: disable=W0702
#     print("nightwatch already registered")


@app.on_event("shutdown")
async def shutdown_event():
    """
    PandaManager 가동시 backend에 등록 요청을 시도함
    이미 있다면 등록되지 않음
    """
    for panda_id, manager in panda_managers.items():
        await logging_info(panda_id, "Manager 종료", {})
        await manager.stop()


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)

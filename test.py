""" 모듈 테스트 하는 용도의 파일"""
import asyncio
import json
import requests
import websockets
from classes import playwright_watch as pws
from classes.bj_info import BjInfo
from classes.panda_manager import PandaManager
from classes.api_client import APIClient
from util.my_util import get_bj_data

play_watch: pws.PlayWrightNightWatch = pws.PlayWrightNightWatch(
    "siveriness1", "Adkflfkd1"
)

body = {
    "panda_id": "siveriness01",
    "proxy_ip": "",
    "manager_id": "siveriness01",
    "manager_pw": "Adkflfkd1",
    "resource_ip": "",
}
# manager: PandaManager = PandaManager(body=body)

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


async def main():
    """docstring"""
    api_client = APIClient()
    response = await api_client.login("siveriness00", "Adkflfkd1", "siveriness00")
    response = await api_client.play("doubletest3")
    print(response)


asyncio.run(main())

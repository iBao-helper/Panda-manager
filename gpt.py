"""oepnAI 사용 예제"""

import asyncio
import time
from urllib.parse import quote
from openai import OpenAI
import requests
from classes.api_client import APIClient
from util.my_util import get_sum_hart_history
import re

client = OpenAI()


def gpt4_omni(question, room_id, chat_token, jwt_token, channel, sess_key, user_idx):
    """GPT3.5 turbo에게 물어보기"""
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "Answer questions as if you were talking to a close friend.",
            },
            {
                "role": "system",
                "content": "Just answer the questions asked and don't use flowery language.",
            },
            {
                "role": "system",
                "content": "Keep your answers short and simple.",
            },
            {
                "role": "user",
                "content": question,
            },
        ],
    )

    print(completion.choices[0].message)
    chat_url = "https://api.pandalive.co.kr/v1/chat/message"
    data = f"message={quote(completion.choices[0].message.content)}&roomid={room_id}&chatToken={chat_token}&t={int(time.time())}&channel={channel}&token={jwt_token}"
    dummy_header: dict = {
        "authority": "api.pandalive.co.kr",
        "method": "POST",
        "scheme": "https",
        "accept": "application/json, text/plain, */*",
        "accept-encoding": "gzip, deflate, br",
        "Accept-Language": "ko,ko-KR;q=0.9",
        "content-type": "application/x-www-form-urlencoded",
        "origin": "https://www.pandalive.co.kr",
        "referer": "https://www.pandalive.co.kr/",
        "sec-ch-ua": '"Not_A Brand";v="99", "Chromium";v="99", "Google Chrome";v="99"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "Windows",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "X-Device-Info": '{"t":"webPc","v":"1.0","ui":24229319}',
    }
    dummy_header["path"] = "/v1/chat/message"
    dummy_header["content-length"] = str(len(data))
    dummy_header["cookie"] = f"sessKey={sess_key}; userLoginIdx={user_idx}"

    try:
        requests.post(url=chat_url, headers=dummy_header, data=data, timeout=5)
    except:  # pylint: disable=W0703 W0612
        return None  # pylint: disable=W0719 W0707
    return True


async def gpt4_omni_by_api_client(question, panda_id: str):
    """GPT3.5 turbo에게 물어보기"""
    match = re.search(r'"([^"]*)"', question)
    messages = []
    messages.append(
        {
            "role": "system",
            "content": "Answer questions as if you were talking to a close friend.",
        },
    )
    messages.append(
        {
            "role": "system",
            "content": "Just answer the questions asked and don't use flowery language.",
        },
    )
    messages.append(
        {
            "role": "system",
            "content": "Keep your answers short and simple.",
        },
    )

    if match:
        nickname = match.group(1)
        nickname.replace(" ", "")
        hart_count = await get_sum_hart_history(user_name=nickname)
        messages.append(
            {
                "role": "system",
                "content": f"The result of the search is the number of donations, and the number of donations is {hart_count}",
            },
        )
    print(messages)
    messages.append(
        {
            "role": "user",
            "content": question,
        },
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
    )

    print(completion.choices[0].message)
    dummy_api_client = APIClient()
    await dummy_api_client.login(
        login_id="siveriness01",
        login_pw="Adkflfkd1",
        panda_id="chat_bot",
    )
    print(panda_id)
    await dummy_api_client.play(panda_id)
    await dummy_api_client.send_chatting(completion.choices[0].message.content)
    return completion.choices[0].message.content

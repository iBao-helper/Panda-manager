"""oepnAI 사용 예제"""

import time
from urllib.parse import quote
from openai import OpenAI
import requests

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

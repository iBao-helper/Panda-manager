import asyncio
from classes.api_client import APIClient


async def main():
    """docstring"""
    api_client = APIClient()
    await api_client.login(
        login_id="siveriness01", login_pw="Adkflfkd1", panda_id="chat_bot"
    )
    await api_client.play(panda_id="aaa983")
    await api_client.send_chatting("유령이야 껄껄")


asyncio.run(main())

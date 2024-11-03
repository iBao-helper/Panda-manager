import asyncio
from classes.api_client import APIClient
from gpt import gpt4_omni_by_api_client


async def main():
    """docstring"""
    question = '"미키™"는 몇개 쏨?'
    await gpt4_omni_by_api_client(question, panda_id="1")


asyncio.run(main())

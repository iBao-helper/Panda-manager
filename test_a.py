"""테스트"""
import asyncio
import tmp_manager as pm


async def main():
    """테스트"""
    panda_manager: pm.PandaManager = pm.PandaManager()
    panda_manager.create_playwright()
    print("k")


asyncio.run(main())

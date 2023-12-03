"""테스트용 모듈"""
import time
from classes import night_watch_selenium as nws
import requests

sele_watch: nws.SeleWatch = nws.SeleWatch()


def main():
    """메인"""

    bj_lists = requests.get(
        url="http://panda-manager.com:3000/master/tmp-user",
        timeout=5,
    ).json()
    print(bj_lists)
    sele_watch.create_selenium()
    sele_watch.element_click_with_css("button.btnClose")
    sele_watch.login("ibao123", "Adkflfkd1")
    sele_watch.goto_url("https://www.pandalive.co.kr/my/post")
    for bj in bj_lists:
        print(bj)
        sele_watch.send_jjockji_message(
            bj["panda_id"],
            """매니저봇 서비스를 만들었습니다! 
한번 이용해 보세요~!
매니저 서비스를 원격리소스로 지원하고, 방송을 감지하여 자동으로 접속합니다.
panda-manager.com 에서 사용 가능하고
현재는 베타테스트로 무료로 사용가능하며 
서버비용을 받는다고 하여도 최저비용인 분당1원 정도로 생각하고 있습니다~!
사용중 불편한 사항이나 개선사항이 있다면 오픈톡으로 알려주세요~!
좋은하루 되시고 즐방하세연 :D """,
        )
        requests.delete(
            url=f"http://panda-manager.com:3000/master/tmp-user?panda_id={bj['panda_id']}",
            timeout=5,
        )
        time.sleep(3)
    print("end")


main()

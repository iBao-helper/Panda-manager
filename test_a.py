"""테스트용 모듈"""
from classes import night_watch_selenium as nws
import requests

sele_watch: nws.SeleWatch = nws.SeleWatch()


def main():
    """메인"""

    # bj_lists = requests.get(
    #     url="http://panda-manager.com:3000/master/tmp-user",
    #     timeout=5,
    # ).json()
    # print(bj_lists)
    sele_watch.create_selenium()
    sele_watch.element_click_with_css("button.btnClose")
    sele_watch.login("ibao123", "Adkflfkd1")
    sele_watch.goto_url("https://www.pandalive.co.kr/pick#bookmark")
    live = sele_watch.get_user_status()
    backend_live_users = requests.get(
        url="http://panda-manager.com:3000/bj?mode=playing",
        timeout=5,
    ).json()
    backend_idle_users = requests.get(
        "http://panda-manager.com:3000/bj?mode=idle",
        timeout=5,
    ).json()
    wanted_play_list = sele_watch.filter_wanted_play_list(live, backend_idle_users)
    wanted_stop_list = sele_watch.filter_wanted_stop_list(live, backend_live_users)
    # sele_watch.goto_url("https://www.pandalive.co.kr/my/post")
    # for bj in bj_lists:
    # sele_watch.send_jjockji_message("k1990121", "awef")
    print("end")


main()

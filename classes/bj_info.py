"""BJ INFO CLASS"""


import pprint


class PlayTime:
    """BJ 방송 시간 클래스"""

    def __init__(self, play_time):
        self.month_time = play_time["monthTime"]
        self.total_time = play_time["totalTime"]
        self.month = play_time["month"]
        self.total = play_time["total"]

    def __str__(self):
        return pprint.pformat(self.__dict__, indent=4)


class BjInfo:
    """BJ 정보 클래스"""

    def __init__(self, bj_info):
        self.idx = bj_info["idx"]
        self.id = bj_info["id"]
        self.nick = bj_info["nick"]
        self.thumb_url = bj_info["thumbUrl"]
        self.score_total = bj_info["scoreTotal"]
        self.score_watch = bj_info["scoreWatch"]
        self.score_like = bj_info["scoreLike"]
        self.score_bookmark = bj_info["scoreBookmark"]
        self.fan_cnt = bj_info["fanCnt"]
        self.channel_title = bj_info["channelTitle"]
        self.channel_desc = bj_info["channelDesc"]
        self.is_img_profile = bj_info["isImgProfile"]
        self.is_asp = bj_info["isAsp"]
        self.bj_anni = bj_info["bjAnni"]
        self.play_time = PlayTime(bj_info["playTime"])
        self.rank = bj_info["rank"]
        self.vip_deco = bj_info["vipDeco"]
        self.block_service = bj_info["blockService"]

    def __str__(self):
        return "\n".join(
            f"{k}: {v if not isinstance(v, PlayTime) else str(v)}"
            for k, v in self.__dict__.items()
        )

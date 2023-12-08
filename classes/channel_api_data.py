"""ChannelApiData"""
import requests


class ChannelApiData:
    """채널 요청에 관련된 Api에 필요한 데이터"""

    def __init__(self):
        self.headers = None
        self.channel = ""
        self.token = ""
        self.valid = False
        self.is_manager = False
        self.user_list = []
        self.prev_user_list = []
        self.count = 0
        self.real_count = 0
        self.guest_count = 0

    def is_valid(self):
        """현재 토큰이 올바른지 변수"""
        return self.valid

    def is_list_enabled(self):
        """직전 list요청이 성공했는지 여부"""
        return self.is_manager

    def set_data(self, headers, channel: str, token: str):
        """API에 필요한 데이터를 설정 하는 함수"""
        self.headers = headers
        self.channel = channel
        self.token = token
        self.valid = True
        self.is_manager = True

    async def send_channel_user_count(self):
        """채널의 유저 수를 요청하는 함수"""
        url = (
            "https://api.pandalive.co.kr/v1/chat/channel_user_count?"
            f"channel={self.channel}&token={self.token}"
        )
        # print(url)
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
        except:  # pylint: disable= W0702
            self.valid = False
        return response

    async def get_new_users(self):
        """새로 들어온 유저를 반환하는 함수"""
        url = (
            "https://api.pandalive.co.kr/v1/chat/channel_user_list?"
            f"channel={self.channel}&token={self.token}"
        )
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            tmp = response.json()["list"]
            self.prev_user_list = self.user_list
            self.user_list = [user["nick"] for user in tmp if user["nick"] != "게스트"]
            new_users = [
                user for user in self.user_list if user not in self.prev_user_list
            ]
            return new_users
        except:  # pylint: disable= W0702
            self.is_manager = False
        return []

    async def get_current_user(self):
        """새로 들어온 유저를 반환하는 함수"""
        url = (
            "https://api.pandalive.co.kr/v1/chat/channel_user_list?"
            f"channel={self.channel}&token={self.token}"
        )
        try:
            response = requests.get(url, headers=self.headers, timeout=5)
            tmp = response.json()["list"]
            self.prev_user_list = self.user_list
            self.user_list = [user["nick"] for user in tmp]
            return self.user_list
        except:  # pylint: disable= W0702
            self.is_manager = False
        return []

    def get_user_list(self):
        """현재 접속중인 유저리스트 반환"""
        return self.user_list

"""팬더백엔드 서버에 API를 호출하는 클래스"""
import requests


class APIClient:
    """API를 호출하는 클래스"""

    def __init__(self):
        self.default_header: dict = {
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
            "sec-ch-ua-platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "X-Device-Info": '{"t":"webPc","v":"1.0","ui":24229319}',
        }
        self.sess_key = None
        self.user_idx = None

    def login(self, login_id, login_pw):
        """팬더서버에 로그인 요청하는 함수"""
        login_url = "https://api.pandalive.co.kr/v1/member/login"
        dummy_header = self.default_header.copy()
        data = f"id={login_id}&pw={login_pw}&idSave=N"
        dummy_header["path"] = "/v1/member/login"
        dummy_header["content-length"] = str(len(data))
        response = requests.post(
            url=login_url, headers=self.default_header, data=data, timeout=5
        )
        if response.status_code == 200:
            result = response.json()
            login_info = result["loginInfo"]
            print(login_info)
            self.sess_key = login_info["sessKey"]
            self.user_idx = login_info["userInfo"]["idx"]
            print(self.sess_key, self.user_idx)
            return result
        raise Exception("로그인 실패")  # pylint: disable=W0719

    def search_bj(self, panda_id: str):
        """BJ검색 API 호출"""
        if self.sess_key is None or self.user_idx is None:
            raise Exception("로그인이 필요합니다")  # pylint: disable=W0719
        search_bj_url = "https://api.pandalive.co.kr/v1/member/bj"
        dummy_header = self.default_header.copy()
        data = f"userId={panda_id}&info=media%20fanGrade%20bookmark"
        dummy_header["path"] = "/v1/member/bj"
        dummy_header["content-length"] = str(len(data))
        dummy_header[
            "cookie"
        ] = f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        response = requests.post(
            url=search_bj_url, headers=dummy_header, data=data, timeout=5
        )
        if response.status_code == 200:
            return response.json()
        raise Exception("API 호출 실패")  # pylint: disable=W0719

    def get_user_idx(self, panda_id):
        """search_bj를 호출하여 user_idx를 얻는 함수"""
        response = self.search_bj(panda_id)
        return response["bjInfo"]["idx"]

    def add_book_mark(self, panda_id):
        """panda_id를 북마크에 추가하는 함수"""
        user_idx = self.get_user_idx(panda_id)
        add_bookmark_url = "https://api.pandalive.co.kr/v1/bookmark/add"
        dummy_header = self.default_header.copy()
        data = f"userIdx={user_idx}"
        dummy_header["path"] = "/v1/bookmark/add"
        dummy_header["content-length"] = str(len(data))
        dummy_header[
            "cookie"
        ] = f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        requests.post(url=add_bookmark_url, headers=dummy_header, data=data, timeout=5)
        return

    def delete_book_mark(self, panda_id):
        """panda_id를 북마크에서 삭제하는 함수"""
        user_idx = self.get_user_idx(panda_id)
        delete_bookmark_url = "https://api.pandalive.co.kr/v1/bookmark/delete"
        dummy_header = self.default_header.copy()
        data = f"userIdx%5B0%5D={user_idx}"
        dummy_header["path"] = "/v1/bookmark/delete"
        dummy_header["content-length"] = str(len(data))
        dummy_header[
            "cookie"
        ] = f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        requests.post(
            url=delete_bookmark_url, headers=dummy_header, data=data, timeout=5
        )
        return

    def get_nickname_by_panda_id(self, panda_id):
        """panda_id를 통해 닉네임을 얻는 함수"""
        response = self.search_bj(panda_id)
        return response["bjInfo"]["nick"]

    def get_bookmark_list(self):
        """북마크 리스트를 얻는 함수"""
        if self.sess_key is None or self.user_idx is None:
            raise Exception("로그인이 필요합니다")  # pylint: disable=W0719
        book_mark_url = "https://api.pandalive.co.kr/v1/live/bookmark"
        dummy_header = self.default_header.copy()
        data = "offset=0&limit=200&isLive=&hideOnly=N"
        dummy_header["path"] = "/v1/live/bookmark"
        dummy_header["content-length"] = str(len(data))
        dummy_header[
            "cookie"
        ] = f"sessKey={self.sess_key}; userLoginIdx={self.user_idx}"
        response = requests.post(
            url=book_mark_url, headers=dummy_header, data=data, timeout=5
        )
        if response.status_code == 200:
            return response.json()["list"]

    def get_bookmark_list_to_nickname(self):
        """북마크 닉네임 리스트를 얻는 함수"""
        book_mark_list = self.get_bookmark_list()
        filtered_list = [user["userNick"] for user in book_mark_list]
        return filtered_list

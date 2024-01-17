"""북마크 리스트 얻어오는 API 인터셉터 클래스"""
import requests


class BookMarkListApiData:
    """ "북마크 API 요청 데이터"""

    def __init__(self):
        self.offset = 0
        self.limit = 200
        self.is_live = ""
        self.hide_only = "N"
        self.book_mark_list_headers: dict = None

    def is_need_list_headers(self):
        """헤더정보가 있는지 체크"""
        if self.book_mark_list_headers is None:
            return True
        else:
            return False

    def set_list_headers(self, headers):
        """API에 필요한 데이터를 설정 하는 함수"""
        self.book_mark_list_headers = headers

    def set_book_mark_list_headers(self, headers):
        """API에 필요한 데이터를 설정 하는 함수"""
        self.book_mark_list_headers = headers

    async def get_bookmark_list(self):
        """북마크 리스트를 요청하는 함수"""
        if self.book_mark_list_headers is None:
            print("헤더가 없는 요청입니다")
            return None
        try:
            response = requests.post(
                url="https://api.pandalive.co.kr/v1/live/bookmark",
                headers=self.book_mark_list_headers,
                json={
                    "offset": self.offset,
                    "limit": self.limit,
                    "isLive": self.is_live,
                    "hideOnly": self.hide_only,
                },
                timeout=5,
            )
            return response
        except Exception as e:
            self.book_mark_list_headers = None
            print("북마크 리스트 API 요청 실패", e)
            return None

    async def get_heart_user_list(self):
        """실험용 API"""
        if self.book_mark_list_headers is None:
            print("헤더가 없는 요청입니다")
            return None
        response = requests.get(
            url="https://api.pandalive.co.kr/v1/heart/use_list",
            headers=self.book_mark_list_headers,
            json={"offset": 0, "limit": 10},
            timeout=5,
        )
        print(response.json())
        return response

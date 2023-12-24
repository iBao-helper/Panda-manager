""""실시간 방송중인 BJ의 정보를 검색하는 클래스"""
from urllib.parse import quote
import requests


class SearchLiveBj:
    """실시간 방송중인 BJ 검색 클래스"""

    def __init__(self):
        self.headers: dict = None

    def set_list_headers(self, headers):
        """API에 필요한 데이터를 설정 하는 함수"""
        self.headers = headers

    async def search_live_bj(self, searchVal: str):
        """실시간 방송중인 BJ 검색"""
        if self.headers is None:
            print("헤더가 없는 요청입니다")
            return None
        try:
            response = requests.post(
                url="https://api.pandalive.co.kr/v1/live",
                headers=self.headers,
                data=f"offset=0&limit=20&orderBy=user&searchVal={quote(searchVal)}",
                timeout=5,
            )
            lists = response.json()["list"]
            if len(lists) > 0:
                print(lists[0])
            return response
        except Exception as e:
            self.headers = None
            print("실시간 방송중인 BJ 검색 실패", e)
            return None

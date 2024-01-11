""""실시간 방송중인 BJ의 정보를 검색하는 클래스"""
import requests


class SearchMemberBj:
    """실시간 방송중인 BJ 검색 클래스"""

    def __init__(self):
        self.headers: dict = None

    def set_headers(self, headers):
        """API에 필요한 데이터를 설정 하는 함수"""
        self.headers = headers

    async def search_live_bj(self, panda_id: str):
        """실시간 방송중인 BJ 검색"""
        if self.headers is None:
            print("헤더가 없는 요청입니다")
            return None
        try:
            response = requests.post(
                url="https://api.pandalive.co.kr/v1/member/bj",
                headers=self.headers,
                data=f"userId={panda_id}&info=media%20fanGrade%20bookmark",
                timeout=5,
            )
            data = response.json()
            return data
        except Exception as e:  # pylint: disable=W0718
            self.headers = None
            print(f"{panda_id} BJ 검색 실패", e)
            return None

    async def get_fan_grade(self, panda_id: str):
        """팬등급 조회 얻기"""
        if self.headers is None:
            print("헤더가 없는 요청입니다")
            return None
        try:
            response = requests.post(
                url="https://api.pandalive.co.kr/v1/member/bj",
                headers=self.headers,
                data=f"userId={panda_id}&info=media%20fanGrade%20bookmark",
                timeout=5,
            )
            data = response.json()
            data = [[tmp["name"], tmp["coin"]] for tmp in data["fanGrade"]]
            return data
        except Exception as e:  # pylint: disable=W0718
            self.headers = None
            print(f"{panda_id} BJ 검색 실패", e)
            return None

    async def get_nickname(self, panda_id: str):
        """실시간 방송중인 BJ 검색"""
        if self.headers is None:
            print("헤더가 없는 요청입니다")
            return None
        try:
            response = requests.post(
                url="https://api.pandalive.co.kr/v1/member/bj",
                headers=self.headers,
                data=f"userId={panda_id}&info=media%20fanGrade%20bookmark",
                timeout=5,
            )
            data = response.json()
            if "bjInfo" in data:
                print(data["bjInfo"]["nick"])
                return data["bjInfo"]["nick"]
            raise Exception("BJ 정보가 없습니다")  # pylint: disable=W0719
        except Exception as e:  # pylint: disable=W0718
            self.headers = None
            print(f"{panda_id} BJ 검색 실패", str(e))
            return None

""" Exception 모음 파일 """
from enum import Enum


class PWEEnum(Enum):
    """PlayWright Exception Enum"""

    NW_CREATE_ERROR = 0
    NW_LOGIN_INVALID_ID_OR_PW = 1
    NW_LOGIN_STT_FAILED = 2

    PD_CREATE_ERROR = 3
    PD_LOGIN_INVALID_ID_OR_PW = 4
    PD_LOGIN_STT_FAILED = 5


class PlayWrightException(Exception):
    """Base exception for all PlayWright exceptions."""

    def __init__(
        self,
        description: PWEEnum,
        panda_id: str = "",
        resource_ip: str = "",
        message: str = "",
    ) -> None:
        self.description = description
        self.panda_id = panda_id
        self.resource_ip = resource_ip
        self.message = message

class APIException(Exception):
    """Base exception for all API exceptions."""

    def __init__(
        self,
        description: PWEEnum,
        panda_id: str = "",
        resource_ip: str = "",
        message: str = "",
    ) -> None:
        self.description = description
        self.panda_id = panda_id
        self.resource_ip = resource_ip
        self.message = message
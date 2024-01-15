from pydantic import BaseModel

class CreateManagerDto(BaseModel):
    """매니저 생성 DTO"""

    panda_id: str
    proxy_ip: str
    manager_id: str
    manager_pw: str
    resource_ip: str

    def set(
        self,
        panda_id: str,
        proxy_ip: str,
        manager_id: str,
        manager_pw: str,
        resource_ip: str,
    ):
        """set"""
        self.panda_id = panda_id
        self.proxy_ip = proxy_ip
        self.manager_id = manager_id
        self.manager_pw = manager_pw
        self.resource_ip = resource_ip

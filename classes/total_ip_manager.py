import threading


class TotalIpManager:
    def __init__(self):
        self.ips = [
            ("38.153.21.194", 4),
            ("152.89.10.50", 4),
            ("38.153.245.226", 4),
            ("38.153.21.202", 4),
            ("212.115.62.233", 4),
            ("194.55.81.2", 4),
            ("194.55.81.30", 4),
            ("38.153.21.146", 4),
            ("212.115.62.100", 4),
            ("38.153.21.107", 4),
            ("212.115.62.23", 4),
            ("154.26.170.112", 4),
            ("212.115.62.89", 4),
            ("38.153.245.87", 4),
            ("194.55.81.6", 4),
            ("194.55.81.243", 4),
            ("38.153.245.177", 4),
            ("154.26.170.101", 4),
            ("152.89.10.219", 4),
            ("152.89.10.17", 4),
            ("154.26.170.152", 4),
            ("152.89.10.36", 4),
            ("38.153.21.92", 4),
            ("38.153.245.167", 4),
            ("154.26.170.59", 4),
        ]
        self.lock = threading.Lock()
        self.websockets = []

    def sort_ips(self):
        self.ips = sorted(self.ips, key=lambda x: x[1], reverse=True)

    def get_total_ip(self):
        return sum([ip[1] for ip in self.ips])

    def is_available_ip(self):
        for ip in self.ips:
            if ip[1] > 0:
                return True
        return False

    def get_ip(self):
        self.lock.acquire()
        for ip in self.ips:
            if ip[1] > 0:
                self.lock.release()
                return ip[0]
        self.lock.release()
        return None

    def decrease_ip(self, ip):
        """아이피 사용가능량 감소"""
        self.lock.acquire()
        for i in range(len(self.ips)):
            if self.ips[i][0] == ip:
                self.ips[i] = (self.ips[i][0], self.ips[i][1] - 1)
                break
        self.lock.release()

    def increase_ip(self, ip):
        """아이피 사용가능량 증가"""
        self.lock.acquire()
        for i in range(len(self.ips)):
            if self.ips[i][0] == ip:
                self.ips[i] = (self.ips[i][0], self.ips[i][1] + 1)
                break
        self.lock.release()

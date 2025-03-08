import threading


class TotalIpManager:
    def __init__(self):
        self.ips = [
            ("196.51.108.143", 1),
            ("38.170.112.108", 1),
            ("38.170.112.27", 1),
            ("38.152.82.110", 1),
            ("38.170.112.127", 1),
            ("38.152.31.206", 1),
            ("38.152.31.143", 1),
            ("192.126.178.192", 1),
            ("192.126.178.164", 1),
            ("196.51.109.188", 1),
            ("196.51.106.108", 1),
            ("196.51.109.62", 1),
            ("192.126.178.60", 1),
            ("192.126.156.117", 1),
            ("196.51.108.238", 1),
            ("196.51.111.131", 1),
            ("196.51.111.74", 1),
            ("108.62.70.22", 1),
            ("108.62.70.142", 1),
            ("38.152.31.113", 1),
            ("38.152.31.138", 1),
            ("173.208.36.2", 1),
            ("173.208.36.168", 1),
            ("173.208.36.37", 1),
            ("173.208.36.12", 1),
            ("167.160.176.55", 1),
            ("167.160.176.217", 1),
            ("167.160.176.31", 1),
            ("167.160.176.133", 1),
            ("167.160.176.122", 1),
        ]
        self.account = [
            ["rit099", "mmkk1212!", False],
            ["uoi8788", "mmkk1212!", False],
            ["se0100", "mmkk1212!", False],
            ["pio1011", "mmkk1212!", False],
            ["vsa0120", "mmkk1212!", False],
            ["joki9876", "mmkk1212!", False],
            ["koon0000", "mmkk1212!", False],
            ["soso443", "mmkk1212!", False],
            ["you0115", "mmkk1212!", False],
            ["090909bb", "mmkk1212!", False],
            ["dew0900", "mmkk1212!", False],
            ["vbx321", "mmkk1212!", False],
            ["fgg1856", "mmkk1212!", False],
            ["rto0631", "mmkk1212!", False],
            ["ezh0821", "mmkk1212!", False],
            ["osx3123", "mmkk1212!", False],
            ["vise4398", "mmkk1212!", False],
            ["sldl434", "mmkk1212!", False],
            ["notimetodie", "mmkk1212!", False],
            ["toy031", "mmkk1212!", False],
            ["ert789", "mmkk1212!", False],
            ["law71780", "aass1212!", False],
            ["why011", "aass1212!", False],
            ["tee011", "aass1212!", False],
            ["ssi001", "aass1212!", False],
            ["uum011", "aass1212!", False],
            ["toc001", "aass1212!", False],
            ["cvc011", "aass1212!", False],
        ]
        self.lock = threading.Lock()
        self.websockets = []

    def get_account(self):
        for i in range(len(self.account)):
            if not self.account[i][2]:
                self.account[i][2] = True
                return self.account[i]
        return None

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

    def set_state_true(self, account_id):
        for i in range(len(self.account)):
            if self.account[i][0] == account_id:
                self.account[i][2] = True
                break
        return None

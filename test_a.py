import os

import requests
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL")
BACKEND_PORT = os.getenv("BACKEND_PORT")
print(BACKEND_URL)


requests.post(
    url=f"http://{BACKEND_URL}:{BACKEND_PORT}/log",
    json={"panda_id": "test", "message": "awfpoejpfwejpowfjepoawjefpoajfpoe"},
    timeout=5,
)

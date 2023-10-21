import os
from dotenv import load_dotenv
load_dotenv()

backend = os.getenv("BACKEND_URL")
print(backend)

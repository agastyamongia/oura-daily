import os

import requests
from dotenv import load_dotenv


load_dotenv()

access_token = os.environ["OURA_ACCESS_TOKEN"]

response = requests.get(
    "https://api.ouraring.com/v2/usercollection/personal_info",
    headers={"Authorization": f"Bearer {access_token}"},
    timeout=30,
)

response.raise_for_status()
print(response.json())
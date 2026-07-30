import os
from datetime import date, timedelta

import requests
from dotenv import load_dotenv

load_dotenv()

access_token = os.environ["OURA_ACCESS_TOKEN"]

end_date = date.today()
start_date = end_date - timedelta(days=7)

endpoints = {
    "daily_sleep": "daily_sleep",
    "daily_readiness": "daily_readiness",
    "daily_activity": "daily_activity",
    "sleep": "sleep",
}

headers = {
    "Authorization": f"Bearer {access_token}",
}

for name, endpoint in endpoints.items():
    response = requests.get(
        f"https://api.ouraring.com/v2/usercollection/{endpoint}",
        headers=headers,
        params={
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        timeout=30,
    )

    print(f"\n{name}: {response.status_code}")

    if response.ok:
        payload = response.json()
        print(f"Records: {len(payload.get('data', []))}")
    else:
        print(response.text)
import requests

# Test GET endpoint to see current config
print("Testing GET /bot/config...")
try:
    r = requests.get('http://localhost:8000/bot/config')
    print(f"Status: {r.status_code}")
    if r.status_code == 200:
        data = r.json()
        print(f"followup_timeout_minutes: {data.get('followup_timeout_minutes')}")
        print(f"followup_max_retries: {data.get('followup_max_retries')}")
    else:
        print(f"Error: {r.text}")
except Exception as e:
    print(f"Exception: {e}")

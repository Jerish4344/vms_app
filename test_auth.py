import requests

url = "http://192.168.250.153:8000/api/v1/token-auth/"
data = {
    "username": "admin",
    "password": "@dmin@123"
}

try:
    response = requests.post(url, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
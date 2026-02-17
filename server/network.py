import requests

url = "http://172.20.10.1"  # replace with the URL Phyphox gives
resp = requests.get(url)
data = resp.json()
print(data)

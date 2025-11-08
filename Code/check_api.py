import requests, time

url = "http://127.0.0.1:5055/counts"

while True:
    try:
        data = requests.get(url, timeout=1).json()
        print(data)
    except Exception as e:
        print("Error:", e)
    time.sleep(2)

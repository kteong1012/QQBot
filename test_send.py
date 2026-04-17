import requests
import json

url = "http://127.0.0.1:3000/send_group_msg"
payload = {
    "group_id": "733746606",
    "message": "测试: 大脑已重启完毕，准备好接客了喵~"
}
try:
    res = requests.post(url, json=payload, timeout=5)
    print(res.status_code)
    print(res.text)
except Exception as e:
    print(e)

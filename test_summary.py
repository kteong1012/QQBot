import requests

url = "http://127.0.0.1:5000/napcat_event"
payload = {
    "post_type": "message",
    "message_type": "group",
    "group_id": "733746606",
    "sender": {
        "user_id": "396098651",
        "nickname": "数字泔水搬运师"
    },
    "raw_message": "[CQ:at,qq=562258240] 总结一下[CQ:at,qq=2913939161]",
    "message": [
        {"type": "at", "data": {"qq": "562258240"}},
        {"type": "text", "data": {"text": " 总结一下"}},
        {"type": "at", "data": {"qq": "2913939161"}}
    ]
}
requests.post(url, json=payload)

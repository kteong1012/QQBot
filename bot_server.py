from flask import Flask, request, jsonify
from db_manager import (
    init_db, insert_message, get_unsummarized_messages, get_recent_messages, mark_messages_as_summarized,
    insert_group_event, get_unprofiled_messages, mark_messages_as_profiled, count_unprofiled_messages
)
from character_parser import (
    load_profile, save_profile, analyze_and_summarize, analyze_profiles_increment, merge_character_traits, chat_with_bot, guess_mbti_from_profile
)
import requests
import json
import subprocess
import os
import threading
import base64
import time
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
init_db()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
NAPCAT_URL = "http://172.17.0.1:3000"
BOT_QQ = "562258240"
LISTENED_GROUPS = ["733746606", "170477952", "1074955381"]
PROFILE_THRESHOLD = 500
GLM_API_KEY = os.getenv("GLM_API_KEY")

SUPER_ADMINS = ["396098651", "415753928"]
ADMINS_FILE = os.path.join(BASE_DIR, "data", "admins.json")

LAST_SUMMARY_TIME = {}

def load_admins():
    if not os.path.exists(ADMINS_FILE):
        os.makedirs(os.path.dirname(ADMINS_FILE), exist_ok=True)
        return {"super_admins": SUPER_ADMINS, "groups": {}}
    with open(ADMINS_FILE, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if "super_admins" not in data:
                data["super_admins"] = SUPER_ADMINS
            return data
        except:
            return {"super_admins": SUPER_ADMINS, "groups": {}}

def save_admins(data):
    os.makedirs(os.path.dirname(ADMINS_FILE), exist_ok=True)
    with open(ADMINS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(group_id, user_id):
    admins_data = load_admins()
    if str(user_id) in SUPER_ADMINS:
        return True
    
    group_admins = admins_data.get("groups", {}).get(str(group_id), [])
    if str(user_id) in group_admins or "ALL" in group_admins:
        return True
    return False

def is_bot_in_group(group_id):
    url = f"{NAPCAT_URL}/get_group_info"
    payload = {"group_id": group_id, "no_cache": False}
    try:
        res = requests.post(url, json=payload, timeout=5)
        data = res.json()
        if data.get("status") == "ok":
            return True
    except:
        pass
    return False

def send_group_msg(group_id, message):
    url = f"{NAPCAT_URL}/send_group_msg"
    payload = {"group_id": group_id, "message": message}
    try:
        requests.post(url, json=payload, timeout=5)
    except Exception as e:
        print(f"Failed to send message: {e}")

def send_group_image(group_id, img_path):
    url = f"{NAPCAT_URL}/send_group_msg"
    try:
        with open(img_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
        cq_image = f"[CQ:image,file=base64://{encoded_string}]"
        payload = {"group_id": group_id, "message": cq_image}
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Failed to send image message via base64: {e}")

def get_image_ocr(image_url):
    if not GLM_API_KEY:
        return "[图片]"
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {GLM_API_KEY}"
        }
        payload = {
            "model": "glm-4v",
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": image_url}},
                        {"type": "text", "text": "简短描述这张图片的核心内容，1句话概括即可。"}
                    ]
                }
            ]
        }
        res = requests.post("https://open.bigmodel.cn/api/paas/v4/chat/completions", headers=headers, json=payload, timeout=10)
        data = res.json()
        if "choices" in data and len(data["choices"]) > 0:
            desc = data["choices"][0]["message"]["content"].strip()
            return f"[图片描述: {desc}]"
    except Exception as e:
        print(f"Failed to get image OCR from GLM: {e}")
    return "[图片]"

def extract_image_urls_and_transform(message_list):
    content = ""
    for seg in message_list:
        if seg.get("type") == "text":
            content += seg.get("data", {}).get("text", "")
        elif seg.get("type") == "image":
            url = seg.get("data", {}).get("url", "")
            if url:
                image_desc = get_image_ocr(url)
                content += f" {image_desc} "
            else:
                content += " [图片] "
        elif seg.get("type") == "at":
            content += f"@{seg.get('data', {}).get('qq')} "
        elif seg.get("type") == "face":
            content += "[表情] "
        elif seg.get("type") == "forward":
            content += "[转发记录] "
        else:
            content += f"[{seg.get('type')}] "
    return content.strip()

def run_summary_and_send_card(group_id, limit=500, use_unsummarized_only=False):
    global LAST_SUMMARY_TIME
    now = time.time()
    if group_id in LAST_SUMMARY_TIME and now - LAST_SUMMARY_TIME[group_id] < 180:
        send_group_msg(group_id, "操作过于频繁，请稍后再试（冷却期3分钟）。")
        return
        
    try:
        print(f"[SUMMARY] Triggered for group {group_id}")
        
        if use_unsummarized_only:
            messages = get_unsummarized_messages(group_id, limit=limit)
        else:
            messages = get_recent_messages(group_id, limit=limit)
            
        if not messages:
            send_group_msg(group_id, "近期没有可供总结的有效群聊记录。")
            return
            
        chat_history_text = ""
        message_ids = []
        start_time = messages[0][4]
        end_time = messages[-1][4]
        
        filtered_messages = []
        for i in range(len(messages) - 1, -1, -1):
            filtered_messages.insert(0, messages[i])
            if i > 0 and (messages[i][4] - messages[i-1][4]) > 7200:
                break
                
        messages = filtered_messages
        start_time = messages[0][4]
        
        participant_profiles = {}
        for msg in messages:
            msg_id, sender_id, sender_name, content, timestamp = msg
            message_ids.append(msg_id)
            if not content:
                continue
            
            if content.strip():
                chat_history_text += f"{sender_id}({sender_name}): {content}\n"
                if sender_id not in participant_profiles:
                    profile = load_profile(group_id, sender_id)
                    participant_profiles[sender_id] = profile.get("historical_summary", "记录不足")

        analysis_result = analyze_and_summarize(chat_history_text, str(participant_profiles))
        if not analysis_result:
            send_group_msg(group_id, "总结生成失败，请检查服务状态。")
            return

        topic_summary = analysis_result.get("topic_summary", "未知话题")
        participants_performance = analysis_result.get("participants_performance", [])

        if use_unsummarized_only:
            mark_messages_as_summarized(message_ids)
            
        insert_group_event(group_id, topic_summary, start_time, end_time)

        img_path = f"/tmp/summary_{group_id}_{int(end_time)}.png"
        render_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "render_card.js")
        
        for p in participants_performance:
            p['trait'] = p.get('performance', '')
        
        json_str = json.dumps({
            "topic_summary": topic_summary,
            "character_increments": participants_performance
        })
        
        env = os.environ.copy()
        env["NODE_PATH"] = "/app/node_modules:/usr/lib/node_modules:/home/carson/.npm-global/lib/node_modules"
        subprocess.run(["node", render_script, json_str, img_path], check=True, env=env)
        send_group_image(group_id, img_path)
        LAST_SUMMARY_TIME[group_id] = time.time()
    except Exception as e:
        print(f"Fatal error in background thread (summary): {e}")

def run_silent_profile_merge(group_id):
    try:
        print(f"[PROFILING] Running silent profile merge for group {group_id}")
        messages = get_unprofiled_messages(group_id, limit=PROFILE_THRESHOLD)
        if not messages:
            print("[PROFILING] No unprofiled messages.")
            return
            
        chat_history_text = ""
        message_ids = []
        for msg in messages:
            msg_id, sender_id, sender_name, content, timestamp = msg
            message_ids.append(msg_id)
            if not content:
                continue
            if content.strip():
                chat_history_text += f"{sender_id}({sender_name}): {content}\n"

        increment_data = analyze_profiles_increment(chat_history_text, str(group_id))
        if not increment_data:
            return

        increments = increment_data.get("increments", [])
        for inc in increments:
            user_id = inc.get("user_id")
            nickname = inc.get("nickname", str(user_id))
            trait_increment = inc.get("trait_increment", "")
            
            if not trait_increment:
                continue

            old_profile = load_profile(group_id, user_id)
            new_profile = merge_character_traits(old_profile, trait_increment, group_id=group_id)
            new_profile["nickname"] = nickname
            save_profile(group_id, user_id, new_profile)

        mark_messages_as_profiled(message_ids)
        print(f"[PROFILING] Done for {len(message_ids)} messages in group {group_id}")
    except Exception as e:
        print(f"Fatal error in background thread (profiling): {e}")

def send_personal_profile_card(group_id, target_id_or_name):
    found_profile = None
    target = str(target_id_or_name).strip()
    
    if target.startswith("@"):
        target = target[1:].strip()

    if target.isdigit():
        p = load_profile(group_id, target)
        if "traits" in p and len(p["traits"]) > 0:
            found_profile = p
    else:
        profiles_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "profiles")
        for filename in os.listdir(profiles_dir):
            if filename.startswith(f"{group_id}_") and filename.endswith(".json"):
                with open(os.path.join(profiles_dir, filename), 'r', encoding='utf-8') as f:
                    p_data = json.load(f)
                    file_nickname = p_data.get("nickname", "")
                    if (target in filename) or \
                       (target.lower() == file_nickname.lower()) or \
                       (target.lower() in file_nickname.lower()) or \
                       (file_nickname.lower() in target.lower()):
                        found_profile = p_data
                        break

    if not found_profile:
        send_group_msg(group_id, f"系统未找到该用户的性格档案（{target}）。")
        return

    # Call LLM to instantly guess MBTI based on profile data
    mbti_result = guess_mbti_from_profile(found_profile)
    found_profile["mbti"] = mbti_result.get("mbti", "未知")
    found_profile["mbti_desc"] = mbti_result.get("mbti_desc", "暂无解读")

    img_path = f"/tmp/personal_{group_id}_{int(time.time())}.png"
    render_script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "render_personal_card.js")
    json_str = json.dumps(found_profile)

    try:
        env = os.environ.copy()
        env["NODE_PATH"] = "/app/node_modules:/usr/lib/node_modules:/home/carson/.npm-global/lib/node_modules"
        subprocess.run(["node", render_script, json_str, img_path], check=True, env=env)
        send_group_image(group_id, img_path)
    except Exception as e:
        print(f"Failed to render personal card: {e}")
        nickname = found_profile.get("nickname", found_profile.get("user_id"))
        traits_str = ", ".join(found_profile.get("traits", []))
        summary = found_profile.get("historical_summary", "")
        mbti_text = f"{found_profile.get('mbti')} ({found_profile.get('mbti_desc')})"
        reply = f"【群友性格侧写: {nickname}】\n\n📌 核心标签: {traits_str}\n\n🎭 MBTI推测: {mbti_text}\n\n🕵️ 画像分析: {summary}"
        send_group_msg(group_id, reply)

def handle_free_chat(group_id, sender_id, sender_name, text_content):
    messages = get_recent_messages(group_id, limit=30)
    chat_history_text = "\n".join([f"{m[2]}: {m[3]}" for m in messages if m[3].strip()])
    
    sender_profile = load_profile(group_id, sender_id)
    is_super_admin = (str(sender_id) in SUPER_ADMINS)

    reply_text = chat_with_bot(sender_name, text_content, chat_history_text, sender_profile, is_super_admin)
    
    at_str = f"[CQ:at,qq={sender_id}] "
    send_group_msg(group_id, at_str + reply_text)

@app.route('/napcat_event', methods=['POST'])
def handle_event():
    data = request.json
    if not data:
        return jsonify({"status": "ok"})
        
    post_type = data.get('post_type')
    message_type = data.get('message_type')
    
    if post_type == 'message' and message_type == 'group':
        group_id = str(data.get('group_id'))
        sender_id = str(data.get('sender', {}).get('user_id'))
        sender_name = data.get('sender', {}).get('card') or data.get('sender', {}).get('nickname') or sender_id
        
        message = data.get('message', [])
        raw_message = data.get('raw_message', '')
        
        if isinstance(message, list):
            transformed_content = extract_image_urls_and_transform(message)
        else:
            transformed_content = raw_message
            
        insert_message(group_id, sender_id, sender_name, transformed_content)

        if group_id in LISTENED_GROUPS:
            if count_unprofiled_messages(group_id) >= PROFILE_THRESHOLD:
                if is_bot_in_group(group_id):
                    t = threading.Thread(target=run_silent_profile_merge, args=(group_id,))
                    t.start()

        is_at_me = False
        at_bot_cq = f"[CQ:at,qq={BOT_QQ}]"
        
        if at_bot_cq in raw_message or f"@{BOT_QQ}" in raw_message:
            is_at_me = True
        
        if isinstance(message, list):
            for seg in message:
                if seg.get("type") == "at" and str(seg.get("data", {}).get("qq")) == BOT_QQ:
                    is_at_me = True
                    break

        if is_at_me:
            target_qq = None
            if isinstance(message, list):
                for seg in message:
                    if seg.get("type") == "at" and str(seg.get("data", {}).get("qq")) != BOT_QQ:
                        target_qq = str(seg.get("data", {}).get("qq"))
                        break

            text_content = ""
            if isinstance(message, list):
                text_content = "".join([c.get("data", {}).get("text", "") for c in message if c.get("type") == "text"]).strip()
            else:
                text_content = raw_message.replace(at_bot_cq, "").replace(f"@{BOT_QQ}", "").strip()

            print(f"Received command: text_content='{text_content}', target_qq='{target_qq}'")

            is_add_admin = any(k in text_content for k in ["提拔", "任命", "添加管理员"])
            is_remove_admin = any(k in text_content for k in ["罢免", "革职", "移除管理员"])
            is_all_admin = any(k in text_content for k in ["全员放开", "全员管理员", "开放权限"])
            is_revoke_all = any(k in text_content for k in ["收回权限", "全员禁言"])

            if is_add_admin or is_remove_admin or is_all_admin or is_revoke_all:
                if sender_id not in SUPER_ADMINS:
                    send_group_msg(group_id, f"[CQ:at,qq={sender_id}] 权限不足，仅超级管理员可执行权限配置操作。")
                    return jsonify({"status": "ok"})
                
                admins_data = load_admins()
                if "groups" not in admins_data:
                    admins_data["groups"] = {}
                group_admins = admins_data["groups"].get(group_id, [])

                if is_all_admin:
                    if "ALL" not in group_admins:
                        group_admins.append("ALL")
                        admins_data["groups"][group_id] = group_admins
                        save_admins(admins_data)
                    send_group_msg(group_id, "权限已全员放开：本群所有成员均可直接对话与发送指令。")
                    return jsonify({"status": "ok"})
                    
                if is_revoke_all:
                    if "ALL" in group_admins:
                        group_admins.remove("ALL")
                        admins_data["groups"][group_id] = group_admins
                        save_admins(admins_data)
                    send_group_msg(group_id, "权限已收回：恢复白名单机制，仅超管与指定管理员可发指令。")
                    return jsonify({"status": "ok"})

                if not target_qq:
                    send_group_msg(group_id, "未指定目标用户，请艾特目标对象。")
                    return jsonify({"status": "ok"})
                
                if is_add_admin:
                    if target_qq not in group_admins:
                        group_admins.append(target_qq)
                        admins_data["groups"][group_id] = group_admins
                        save_admins(admins_data)
                        send_group_msg(group_id, f"操作成功：已将 {target_qq} 设为本群管理员。")
                    else:
                        send_group_msg(group_id, "该用户已经是管理员。")
                elif is_remove_admin:
                    if target_qq in group_admins:
                        group_admins.remove(target_qq)
                        admins_data["groups"][group_id] = group_admins
                        save_admins(admins_data)
                        send_group_msg(group_id, f"操作成功：已移除 {target_qq} 的管理员权限。")
                    else:
                        send_group_msg(group_id, "该用户并非管理员，无法移除。")
                return jsonify({"status": "ok"})

            if not is_admin(group_id, sender_id):
                send_group_msg(group_id, f"[CQ:at,qq={sender_id}] 权限不足，请联系群内管理员或超管进行操作。")
                return jsonify({"status": "ok"})


            is_help_request = any(k in text_content for k in ["干什么", "功能", "菜单", "帮助", "你会"])
            is_summary_request = "总结" in text_content
            is_update_profile_request = "更新档案" in text_content

            if is_help_request:
                help_msg = (
                    "当前支持的系统指令列表如下：\n"
                    "1. 【话题提取】@机器人 总结一下\n"
                    "   （自动截取近期有效群聊，生成话题结论与发言者表现）\n"
                    "2. 【全量补充】@机器人 全量总结\n"
                    "   （盘点系统漏捕的、尚未进行总结的所有碎条消息）\n"
                    "3. 【个人画像】@机器人 总结一下 @某人\n"
                    "   （调取该用户的核心性格标签与深度行为侧写）\n"
                    "4. 【强制入库】@机器人 更新档案\n"
                    "   （触发后台静默脚本，强制刷新并计算群友的人格参数）\n"
                    "5. 【权限任免】@机器人 添加/移除管理员 @某人\n"
                    "   （超管指令，赋予某人操作机器人的特权）\n"
                    "6. 【自由问答】直接艾特机器人并说话\n"
                    "   （支持结合前30条语境的智能回答）"
                )
                send_group_msg(group_id, help_msg)
            elif is_summary_request:
                if target_qq:
                    t = threading.Thread(target=send_personal_profile_card, args=(group_id, target_qq))
                    t.start()
                else:
                    if "全量总结" in text_content:
                        t = threading.Thread(target=run_summary_and_send_card, args=(group_id, 1000, True))
                        t.start()
                    elif "总结" in text_content:
                        target = text_content.replace("总结一下", "").replace("总结", "").strip()
                        if target.startswith("@"):
                            target = target[1:].strip()
                        if target:
                            t = threading.Thread(target=send_personal_profile_card, args=(group_id, target))
                            t.start()
                        else:
                            t = threading.Thread(target=run_summary_and_send_card, args=(group_id, 500, False))
                            t.start()
                    else:
                        t = threading.Thread(target=run_summary_and_send_card, args=(group_id, 500, False))
                        t.start()
            elif is_update_profile_request:
                send_group_msg(group_id, "正在后台执行档案数据聚类与更新，请稍候...")
                t = threading.Thread(target=run_silent_profile_merge, args=(group_id,))
                t.start()
            else:
                t = threading.Thread(target=handle_free_chat, args=(group_id, sender_id, sender_name, text_content))
                t.start()

    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("QQ Robot API Server running on port 5000...")
    app.run(host="0.0.0.0", port=5000)

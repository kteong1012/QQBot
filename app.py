from db_manager import init_db, insert_message, get_unsummarized_messages, mark_messages_as_summarized, insert_group_event
from character_parser import load_profile, save_profile, analyze_and_summarize, merge_character_traits
from datetime import datetime
import json
import sqlite3

def run_summary(group_id):
    # 1. 从 SQLite 拉取未总结的聊天记录（最多 1000 条）
    print(f"Fetching unsummarized messages for group {group_id}...")
    messages = get_unsummarized_messages(group_id, limit=1000)
    
    if not messages:
        print("No new messages to summarize.")
        return "近期没有新的聊天记录需要总结哦~"
    
    # 2. 组装给 DeepSeek 的巨大 prompt 字符串
    chat_history_text = ""
    message_ids = []
    start_time = messages[0][4]
    end_time = messages[-1][4]
    
    for msg in messages:
        msg_id, sender_id, sender_name, content, timestamp = msg
        message_ids.append(msg_id)
        # 格式：[时间] 用户ID(用户名称): 发言内容
        time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')
        chat_history_text += f"[{time_str}] {sender_id}({sender_name}): {content}\n"
    
    print(f"Loaded {len(messages)} messages. Sending to DeepSeek API...")
    
    # 3. 发给 DeepSeek 提取话题和性格增量
    analysis_result = analyze_and_summarize(chat_history_text)
    if not analysis_result:
        return "呼叫大模型大脑失败了，请稍后再试喵~ 🐾"
    
    topic_summary = analysis_result.get("topic_summary", "未知话题")
    character_increments = analysis_result.get("character_increments", {})
    
    print(f"--- Topic Summary ---\n{topic_summary}")
    
    # 4. 更新每个参与者的性格画像 (JSON 覆写)
    print("Updating character profiles...")
    for user_id, increment in character_increments.items():
        print(f"Merging profile for user {user_id}...")
        old_profile = load_profile(group_id, user_id)
        
        # 融合旧画像和新表现
        new_profile = merge_character_traits(old_profile, increment)
        
        # 写回磁盘
        save_profile(group_id, user_id, new_profile)
    
    # 5. 收尾：将这批消息标记为已总结（未来可滚动删除）
    print(f"Marking {len(message_ids)} messages as summarized...")
    mark_messages_as_summarized(message_ids)
    
    # 记录该次事件到数据库，防止话题丢失
    insert_group_event(group_id, topic_summary, start_time, end_time)
    
    # 6. 返回给 QQ 的提示
    reply_text = f"【本群近期话题摘要】\n{topic_summary}\n\n（我已静默更新了 {len(character_increments)} 位群友的性格赛博档案喵~ 🐾）"
    return reply_text

if __name__ == "__main__":
    init_db()
    # 手动插入几条假数据测试
    insert_message("test_group", "111", "老林", "今天A股怎么又绿了")
    insert_message("test_group", "222", "群友A", "早就清仓了，我现在只玩美股")
    insert_message("test_group", "111", "老林", "太惨了，我要去吃碗面压压惊")
    
    # 测试总结流程
    res = run_summary("test_group")
    print("\n[Final Reply for NapCatQQ]")
    print(res)

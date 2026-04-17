import os
import json
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROFILES_DIR = os.path.join(BASE_DIR, "profiles")
GROUP_CONFIGS_FILE = os.path.join(BASE_DIR, "group_configs.json")
os.makedirs(PROFILES_DIR, exist_ok=True)

client = OpenAI(
    api_key=os.getenv("DEEPSEEK_API_KEY"),
    base_url="https://api.deepseek.com" 
)

def get_group_context(group_id):
    if os.path.exists(GROUP_CONFIGS_FILE):
        try:
            with open(GROUP_CONFIGS_FILE, 'r', encoding='utf-8') as f:
                configs = json.load(f)
            return configs.get(str(group_id), {}).get("environment_context", "")
        except:
            pass
    return ""

def get_profiling_rules(group_id):
    group_context = get_group_context(group_id)
    env_clause = ""
    if group_context:
        env_clause = f"\n【群聊专属环境背景声明（极度重要）】\n{group_context}\n"

    return f"""<reference id="profiling_rules">{env_clause}
【性格与行为模型分析规范】
目标是凝练出一份【极具深度的】性格与行为模型分析报告。

数据结构与内容要求：
1. **外号与代称 (aliases)**：【非常重要】在阅读聊天记录时，必须敏锐捕捉别人是如何称呼该群友的。将所有出现过的网名、真名、缩写、黑话代称、乃至蔑称，全部提取并存入 aliases 数组中。
2. **标签 (traits)**：深度提炼，【最多保留 8 个】最精准的标签，坚决剔除矛盾和过时的标签。
3. **展示画像 (historical_summary)**：用于对外展示。要求使用【互联网锐评风】，语言极度生动、犀利，必须分为三个明确的段落进行论述：
  - 🎭 **社交面具与生态位**：概括他在群里扮演什么角色（捧哏/懂哥/理中客/键盘侠/气氛组）。
  - 💬 **语言风格与雷区**：深入剖析他习惯怎么说话（反问/句号党/表情包），以及什么话题能瞬间让他兴奋（例如二次元、数码、搞钱）。在分析情绪输出时，尽量弱化粗口与愤怒/暴躁情绪的绝对关联，注意这在很多男性群聊中仅仅是语气助词。
  - 📍 **籍贯与生活轨迹**：必须尽可能从他的历史聊天中挖掘并推测出他的【籍贯】、【现居地】或【方言特征】。如果完全没有提及，可以用一句幽默的锐评（例如“防逆向追踪大师，未在互联网留下任何地理坐标”）。
  【排版要求】：保留上述三个小标题（含Emoji）和换行，字数控制在 300-400 字之间。
4. **隐藏预测模型 (behavior_prediction)**：【独立字段】，用于后续AI模仿该群友发言。基于客观事实，深度预测当群里爆发激烈争吵或抛出一个全新话题时，他会作何反应，并总结出“如果想要模仿他说话，应该掌握哪些精髓”（比如：冷眼旁观最后用一句话补刀，还是立刻下场站队）。字数 100-200 字。在分析情绪表达时，请弱化粗口与情绪爆发的绝对关联，注意识别这些词汇是否仅为口头禅或语气词。

【捕捉他者评价（交叉侧写）极其重要】：
不要只盯着发言者本人。如果群友 A 在聊天中爆料、锐评或调侃了群友 B（例如：“大川这小子天天就知道研究降噪耳机”），请**必须将这条事实切片提取出来，并归属到 B 的档案增量中**！
</reference>"""

def load_profile(group_id, user_id):
    path = os.path.join(PROFILES_DIR, f"{group_id}_{user_id}.json")
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "user_id": user_id, 
        "nickname": user_id, 
        "aliases": [], 
        "traits": [], 
        "historical_summary": "该用户暂无足够的历史发言记录进行侧写。",
        "behavior_prediction": "暂无行为预测模型。"
    }

def save_profile(group_id, user_id, data):
    path = os.path.join(PROFILES_DIR, f"{group_id}_{user_id}.json")
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def analyze_and_summarize(chat_history_text, profiles_context):
    system_prompt = """你是一个高效、幽默且洞察力极强的群聊总结引擎。你需要分析用户提供的聊天记录，并严格按照 JSON 格式返回。"""
    user_prompt = f"""请根据以下 <reference> 标签中的群友背景设定和聊天记录，完成总结任务：

<reference id="profiles_context">
{profiles_context}
</reference>

<reference id="chat_history">
{chat_history_text}
</reference>

任务要求：
1. "topic_summary": 字符串。客观、高效且生动地总结近期的核心吃瓜话题、争议点或结论。在总结每个核心话题时，请【直接将相关群友的关键发言和表现融入其中】，让这段总结读起来像是一段连贯且生动的群聊脱口秀（字数可适度放宽，不少于 150 字，不超过 500 字）。请忽略“@机器人 总结”等触发指令。
2. "participants_performance": 数组。请挑选 2 到 4 名在这段期间活跃度最高、发言最具代表性的群友，结合他们具体的发言内容，对他们的性格特点进行深度且有趣的 **MBTI 性格解析**（不要写成单调的流水账，要像心理咨询师一样给出毒舌或幽默的解读）。

返回 JSON 示例：
{{
  "topic_summary": "...",
  "participants_performance": [
    {{
      "user_id": "123456",
      "nickname": "张三",
      "performance": "基于发言，MBTI 可能是 ENTP（辩论家），因为..."
    }}
  ]
}}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.6
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"DeepSeek API Error (Summarize): {e}")
        return None

def analyze_profiles_increment(chat_history_text, group_id):
    system_prompt = """你是一个客观的资料提取员。你的任务是从聊天记录中，提取出能够支撑【性格与行为模型分析规范】所需的底层事实素材。
【核心原则】：不要做主观心理评判，只提取纯粹的客观事实依据，为后续的画像定性提供弹药。"""

    profiling_rules = get_profiling_rules(group_id)
    user_prompt = f"""{profiling_rules}

请阅读以下 <reference id="chat_log"> 中的聊天记录：
<reference id="chat_log">
{chat_history_text}
</reference>

请提取符合 `profiling_rules` 规范所需的客观事实论据（特别是：观点、用词、反应模式、【任何关于地名、方言、老家的提及】、以及【别人对他的外号/代称/评价】）。
⚠️ 注意：如果 A 发言八卦/评价了 B，请把切片算在 B 头上。
返回 JSON 格式示例：
{{
  "increments": [
    {{
      "user_id": "A的QQ",
      "nickname": "张三",
      "trait_increment": "事实切片：1.[生态位] 参与理财话题并连发科普；2.[语言] 经常使用‘卧槽’等词；3.[地域] 提到了广东；4.[外号收集] 群友叫他‘三哥’。"
    }},
    {{
      "user_id": "B的QQ", 
      "nickname": "李四",
      "trait_increment": "事实切片：[他者评价] 被张三爆料说天天沉迷降噪耳机；[外号收集] 被张三叫做‘耳机狂魔’。"
    }}
  ]
}}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.4
        )
        return json.loads(response.choices[0].message.content)
    except Exception as e:
        print(f"DeepSeek API Error (Profile Increment): {e}")
        return None

def merge_character_traits(old_profile, new_increment_trait, group_id):
    system_prompt = """你是一个极具洞察力的心理侧写师。你的任务是将该用户过去的【历史档案】与最新采集的【客观事实切片】进行深度融合。"""
    
    profiling_rules = get_profiling_rules(group_id)
    user_prompt = f"""{profiling_rules}

请仔细阅读以下材料，并基于客观事实，对该用户进行更新、定性和重塑：

<reference id="old_profile">
当前外号/代称：{', '.join(old_profile.get('aliases', []))}
当前标签：{', '.join(old_profile.get('traits', []))}
旧展示画像：
{old_profile.get('historical_summary', '无')}
旧隐藏预测模型：
{old_profile.get('behavior_prediction', '无')}
</reference>

<reference id="new_behaviors">
近期新增事实论据切片：
{new_increment_trait}
</reference>

请严格遵循 <reference id="profiling_rules"> 中的所有维度要求、语言风格要求（互联网锐评风）和排版要求，输出合并后的最终画像 JSON。

返回 JSON 格式示例：
{{
  "aliases": ["三哥", "张总", "耳机狂魔"],
  "traits": ["逻辑严密", "INTJ", "广东土著"], 
  "historical_summary": "🎭 **社交面具与生态位**\n作为群内的首席捧哏...\n\n💬 **语言风格与雷区**\n聊天习惯带狗头...\n\n📍 **籍贯与生活轨迹**\n正宗广东土著，偶尔暴露湖南血统...",
  "behavior_prediction": "如果群里开始讨论股票，他绝对会冷眼旁观。模仿他的精髓在于：多用‘卧槽’作为起手式，语气要不屑，少用表情包。"
}}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        merged_data = json.loads(response.choices[0].message.content)
        
        final_traits = merged_data.get("traits", [])
        if not isinstance(final_traits, list):
            final_traits = []
            
        final_aliases = merged_data.get("aliases", [])
        if not isinstance(final_aliases, list):
            final_aliases = []
            
        old_profile["aliases"] = list(set(old_profile.get("aliases", []) + final_aliases))
        old_profile["traits"] = final_traits[:8]
        old_profile["historical_summary"] = merged_data.get("historical_summary", old_profile.get("historical_summary", ""))
        old_profile["behavior_prediction"] = merged_data.get("behavior_prediction", old_profile.get("behavior_prediction", ""))
        return old_profile
    except Exception as e:
        print(f"Merge Error: {e}")
        return old_profile

def guess_mbti_from_profile(profile_data):
    summary = profile_data.get("historical_summary", "")
    prediction = profile_data.get("behavior_prediction", "")
    traits = ", ".join(profile_data.get("traits", []))
    
    if not summary or summary == "该用户暂无足够的历史发言记录进行侧写。":
        return {"mbti": "未知", "mbti_desc": "暂无足够数据进行人格推测。"}
        
    system_prompt = "你是一位精通 MBTI 人格理论的心理学专家。"
    user_prompt = f"""请根据以下 <reference> 标签中的该群友社交档案与行为预测，推测其最可能的 MBTI 类型（必须是标准的 16 型人格之一），并给出一句简短的“定制化解读”（结合他在群里的实际表现，用网感语言犀利点评，字数在30字以内）。

<reference id="user_profile">
用户标签：{traits}
用户档案：{summary}
行为预测：{prediction}
</reference>

请严格按 JSON 格式返回：
{{
  "mbti": "ENTP",
  "mbti_desc": "群聊里的节奏大师，擅长用直击要害的逻辑反问终结无聊话题。"
}}
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={"type": "json_object"},
            temperature=0.7
        )
        return json.loads(response.choices[0].message.content)
    except:
        return {"mbti": "未知", "mbti_desc": "推测失败。"}

def chat_with_bot(sender_name, text_content, recent_chat_text, sender_profile, is_super_admin, mentioned_profiles=None):
    if mentioned_profiles is None:
        mentioned_profiles = []
        
    traits_str = ", ".join(sender_profile.get("traits", []))
    summary_str = sender_profile.get("historical_summary", "该用户暂无足够记录。")
    
    mentioned_context = ""
    if mentioned_profiles:
        mentioned_context = "<reference id=\"mentioned_users_profiles\">\n【话题中涉及的其他群友画像】：\n"
        for mp in mentioned_profiles:
            mentioned_context += f"- {mp.get('nickname', mp.get('user_id'))}:\n"
            mentioned_context += f"  标签: {', '.join(mp.get('traits', []))}\n"
            mentioned_context += f"  画像: {mp.get('historical_summary', '暂无记录')}\n"
        mentioned_context += "</reference>\n"
    
    system_prompt = """你是一个高情商、幽默、有网感的群聊搭子。有人在群里直接艾特你跟你搭话。
你的回复准则：
1. 像真人一样聊天，要有情绪起伏、网感和幽默感，可以使用群聊常见语气词（哈、卧槽、啊这、绝了等），不用把粗口当成严重的情绪输出。
2. 不要像干巴巴的 AI 客服，拒绝“首先、其次、总之”等机械式长篇大论。
3. 如果话题涉及到其他群友，一定要结合你所掌握的他们的【性格画像】进行调侃、吐槽或犀利点评，展现出你对群友的深刻洞察。
4. 语言尽量口语化、接地气，篇幅自然，不要过长（建议控制在两三句话内），让人有阅读和接梗的欲望。
5. 遇到不懂的就大方承认或插科打诨，绝不说死板的套话。"""

    user_prompt = f"""请仔细阅读以下 <reference> 标签中的信息，并对用户的发言进行回复：

<reference id="interlocutor_info">
【与你对话的人】：{sender_name}
此人的行为画像：标签[{traits_str}]，档案[{summary_str}]
</reference>

{mentioned_context}

<reference id="recent_chat_context">
当前群里的环境风向（最近几条消息）：
{recent_chat_text}
</reference>

对方的发言内容：
"{text_content}"

要求：
- 结合 <reference> 中的群聊语境、对方画像以及可能涉及到的第三方画像，直接输出回复内容（纯文本）。
- 字数控制在 100 字以内，简明扼要，一针见血。
"""
    try:
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"DeepSeek API Error (Free Chat): {e}")
        return "服务异常，请稍后再试。"
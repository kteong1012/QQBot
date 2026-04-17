# 🐟 小宝鱼 QQ 机器人 (QQ Robot)

本项目是一个基于 Napcat (OneBot11 协议) 和大模型（DeepSeek + 智谱 GLM-4V）的智能 QQ 群聊机器人。由老林创立，现由刘静（AI 助手）负责日常看护与维护。

## 🌟 核心功能与使用指令

只要在配置的白名单群内，小宝鱼就会在后台默默倾听、记忆群友的发言，并在累计满一定消息（默认 500 条）后静默凝练大家的性格档案。

用户在群内通过 `@小宝鱼` 加上以下指令即可唤醒对应功能：

1. **吃瓜总结 (群聊总结)**
   - **指令**: `@小宝鱼 总结一下`
   - **功能**: 机器人会把大家最近聊的几百条记录浓缩成一张精美的图文卡片，包含吃瓜要点和活跃参与人的神吐槽。

2. **赛博相面 (单人性格画像)**
   - **指令**: `@小宝鱼 总结一下 @某人` 或 `@小宝鱼 总结一下 <昵称>`
   - **功能**: 机器人会翻阅该用户在群里一贯的发言历史，生成专属【赛博相面报告】图片，包含性格标签、口头禅和 MBTI 猜测。

3. **强制凝练 (更新档案)**
   - **指令**: `@小宝鱼 更新档案`
   - **功能**: 强制机器人立刻将群内还没来得及分析的新聊天记录吸收，合并更新到大家的性格数据库中。

4. **功能布道 (菜单帮助)**
   - **指令**: `@小宝鱼 你能干什么` / `@小宝鱼 帮助` / `@小宝鱼 功能`
   - **功能**: 输出机器人的绝学菜单说明。

## 🧠 技术架构

- **通信底层**: Napcat (对接 QQ，提供 HTTP Webhook)
- **后端服务**: Python Flask (`bot_server.py`) 运行在 5000 端口。
- **思考大脑 (LLM)**: DeepSeek-Chat (处理文字吃瓜总结和侧写分析)。
- **视觉眼睛 (VLM)**: 智谱 GLM-4V (解析群内图片、截图和表情包，转化为文字语境)。
- **绘图引擎**: Node.js + Puppeteer (`render_card.js` & `render_personal_card.js`) 用于将 JSON 数据渲染为美观的 HTML 卡片并截图下发。
- **数据库**: SQLite (`bot_data.db`) 存储历史消息；本地 JSON 文件 (`profiles/`) 存储各群友的独立性格档案。

## ⚙️ 运维与维护

### 环境依赖
- Python 3
- Node.js (需全局安装 `puppeteer`)
- `.env` 环境变量配置 (包含 `DEEPSEEK_API_KEY` 和 `GLM_API_KEY`)

### 启停服务
启动服务（后台运行）：
```bash
nohup python3 /home/carson/.openclaw/workspace/qq-robot/bot_server.py > /home/carson/.openclaw/workspace/qq-robot/bot.log 2>&1 &
```

停止服务：
```bash
pkill -f "python3 /home/carson/.openclaw/workspace/qq-robot/bot_server.py"
```

查看日志：
```bash
tail -f /home/carson/.openclaw/workspace/qq-robot/bot.log
```

---
*Documented by 刘静 on 2026-04-14*

FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装必要的系统依赖（由于需要 Puppeteer/Chrome 渲染图片，必须安装浏览器环境依赖）
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    ca-certificates \
    procps \
    libxss1 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxi6 \
    libxtst6 \
    libnss3 \
    libcups2 \
    libxss1 \
    libxrandr2 \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libpango-1.0-0 \
    libgtk-3-0 \
    fonts-liberation \
    libappindicator3-1 \
    xdg-utils \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# 安装 Node.js (用于运行 Puppeteer)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs

# 拷贝并安装 Python 依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 拷贝并安装 Node.js 依赖 (Puppeteer)
COPY package.json .
# 设置 Puppeteer 跳过自动下载，或者如果你希望它自己下，去掉下面这行。
# 考虑到国内网络，我们让它自己装，但需要注意网络环境
RUN npm install

# 将整个项目代码拷贝到容器中
COPY . .

# 创建必要的数据和临时目录
RUN mkdir -p /app/data /app/profiles /tmp

# 设置环境变量，确保 puppeteer 可以找到系统环境或者自带的 chrome
ENV NODE_PATH=/app/node_modules
ENV FLASK_APP=bot_server.py
ENV FLASK_ENV=production

# 暴露 Flask 端口
EXPOSE 5000

# 运行 Flask 服务
CMD ["python", "bot_server.py"]

const puppeteer = require("puppeteer");
const fs = require("fs");
const path = require("path");

async function generateSummaryCard(jsonData, outputPath) {
  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 750, height: 800, deviceScaleFactor: 2 });

  let characterHtml = "";
  if (jsonData.character_increments && jsonData.character_increments.length > 0) {
    for (const inc of jsonData.character_increments) {
      const nickname = inc.nickname || inc.user_id;
      const trait = inc.trait || inc.performance || "";
      characterHtml += `
        <div class="user-row">
          <div class="user-id">@${nickname}</div>
          <div class="user-trait">${trait}</div>
        </div>
      `;
    }
  } else {
    characterHtml = `<div class="empty-state">大家都在潜水，并没有什么特别出彩的发言。</div>`;
  }

  const currentDate = new Date().toLocaleString("zh-CN", {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit"
  });

  const htmlContent = `
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <style>
        :root {
          --bg-color: #F5F5F7;
          --card-bg: #FFFFFF;
          --text-main: #1D1D1F;
          --text-sub: #86868B;
          --accent-blue: #0066CC;
          --border-color: #E5E5EA;
        }
        body {
          font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "Helvetica Neue", Arial, sans-serif;
          background-color: var(--bg-color);
          margin: 0;
          padding: 40px;
          display: flex;
          justify-content: center;
          align-items: flex-start;
          -webkit-font-smoothing: antialiased;
        }
        .container {
          background-color: var(--card-bg);
          border-radius: 20px;
          box-shadow: 0 10px 40px -10px rgba(0,0,0,0.08);
          width: 100%;
          max-width: 670px;
          overflow: hidden;
        }
        .header {
          padding: 32px 36px 24px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .header-title {
          font-size: 28px;
          font-weight: 700;
          color: var(--text-main);
          letter-spacing: -0.5px;
        }
        .header-subtitle {
          font-size: 13px;
          font-weight: 500;
          color: var(--text-sub);
          text-transform: uppercase;
          letter-spacing: 1px;
        }
        .content {
          padding: 36px;
        }
        .section-title {
          font-size: 14px;
          font-weight: 600;
          color: var(--accent-blue);
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 16px;
          display: flex;
          align-items: center;
        }
        .section-title svg {
          margin-right: 8px;
          width: 18px;
          height: 18px;
        }
        .summary-box {
          font-size: 17px;
          line-height: 1.6;
          color: var(--text-main);
          background-color: #F9F9FB;
          padding: 24px;
          border-radius: 14px;
          margin-bottom: 36px;
        }
        .character-list {
          background-color: #FFFFFF;
          border: 1px solid var(--border-color);
          border-radius: 14px;
          overflow: hidden;
        }
        .user-row {
          padding: 16px 20px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          flex-direction: column;
        }
        .user-row:last-child {
          border-bottom: none;
        }
        .user-id {
          font-size: 14px;
          font-weight: 600;
          color: var(--text-main);
          margin-bottom: 4px;
        }
        .user-trait {
          font-size: 14px;
          color: var(--text-sub);
          line-height: 1.5;
        }
        .empty-state {
          padding: 24px;
          text-align: center;
          color: var(--text-sub);
          font-size: 14px;
        }
        .footer {
          padding: 20px 36px;
          background-color: #FBFBFD;
          border-top: 1px solid var(--border-color);
          text-align: center;
          font-size: 12px;
          color: var(--text-sub);
          font-weight: 500;
        }
      </style>
    </head>
    <body>
      <div class="container" id="capture-area">
        <div class="header">
          <div class="header-title">群聊总结报告</div>
          <div class="header-subtitle">${currentDate}</div>
        </div>
        
        <div class="content">
          <div class="section-title">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path></svg>
            近期核心话题
          </div>
          <div class="summary-box">
            ${jsonData.topic_summary}
          </div>

          <div class="section-title">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"></path></svg>
            活跃群友 MBTI 毒舌解析
          </div>
          <div class="character-list">
            ${characterHtml}
          </div>
        </div>

        <div class="footer">
          Generated by DeepSeek & Node Engine • AI 视界
        </div>
      </div>
    </body>
    </html>
  `;

  await page.setContent(htmlContent);
  const element = await page.$('#capture-area');
  await element.screenshot({ path: outputPath });
  await browser.close();
  console.log(outputPath);
}

const inputJsonStr = process.argv[2];
const outputPath = process.argv[3] || "/tmp/summary_card.png";

try {
  const data = JSON.parse(inputJsonStr);
  generateSummaryCard(data, outputPath);
} catch (e) {
  console.error("Invalid JSON input or rendering error", e);
  process.exit(1);
}

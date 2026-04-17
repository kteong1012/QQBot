const puppeteer = require("puppeteer");

async function generatePersonalCard(jsonData, outputPath) {
  const browser = await puppeteer.launch({
    args: ["--no-sandbox", "--disable-setuid-sandbox"]
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 600, height: 800, deviceScaleFactor: 2 }); 

  const currentDate = new Date().toLocaleString("zh-CN", {
    year: "numeric", month: "2-digit", day: "2-digit",
    hour: "2-digit", minute: "2-digit"
  });

  
  // 修复Markdown加粗语法
  if (jsonData.historical_summary) {
    jsonData.historical_summary = jsonData.historical_summary.replace(/\*\*(.*?)\*\*/g, "<b>$1</b>");
  }
  
  let aliasesHtml = "";
  if (jsonData.aliases && jsonData.aliases.length > 0) {
    aliasesHtml = `<div class="aliases-text">🏷️ 群内代称/外号：${jsonData.aliases.join("、")}</div>`;
  }
  
  let traitsHtml = "";
  for (const t of jsonData.traits || []) {
    traitsHtml += `<span class="trait-tag">${t}</span>`;
  }
  
  if (!traitsHtml) {
      traitsHtml = `<span class="trait-tag" style="color: var(--text-sub); border-color: var(--border-color); background: none;">暂无标签</span>`;
  }

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
          max-width: 500px;
          overflow: hidden;
        }
        .header {
          padding: 32px 36px 24px;
          border-bottom: 1px solid var(--border-color);
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: linear-gradient(135deg, #e0eafc, #cfdef3);
        }
        .header-title {
          font-size: 26px;
          font-weight: 700;
          color: var(--text-main);
          letter-spacing: -0.5px;
        }
        .header-subtitle {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-main);
          opacity: 0.6;
          text-transform: uppercase;
        }
        .content {
          padding: 36px;
        }
        .user-name {
          font-size: 20px;
          font-weight: 600;
          color: var(--text-main);
          margin-bottom: 20px;
          display: flex;
          align-items: center;
        }
        .user-name svg {
          margin-right: 8px;
          width: 24px;
          height: 24px;
          color: var(--accent-blue);
        }
        .aliases-text {
          font-size: 13px;
          color: var(--text-sub);
          margin-top: -15px;
          margin-bottom: 20px;
          font-weight: 500;
        }
        .section-title {
          font-size: 13px;
          font-weight: 600;
          color: var(--text-sub);
          text-transform: uppercase;
          margin-bottom: 12px;
          letter-spacing: 0.5px;
        }
        .traits-container {
          margin-bottom: 28px;
          display: flex;
          flex-wrap: wrap;
          gap: 8px;
        }
        .trait-tag {
          background-color: #f0f4f8;
          color: var(--accent-blue);
          padding: 6px 14px;
          border-radius: 20px;
          font-size: 14px;
          font-weight: 500;
          border: 1px solid #d9e2ec;
        }
        .summary-box {
          white-space: pre-wrap;
          font-size: 16px;
          line-height: 1.7;
          color: var(--text-main);
          background-color: #F9F9FB;
          padding: 24px;
          border-radius: 14px;
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
          <div class="header-title">赛博相面报告</div>
          <div class="header-subtitle">${currentDate}</div>
        </div>
        
        <div class="content">
          <div class="user-name">
            <svg fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"></path></svg>
            @${jsonData.nickname || jsonData.user_id}
          </div>
          ${aliasesHtml}
          
          <div class="section-title">核心标签</div>
          <div class="traits-container">
            ${traitsHtml}
          </div>

          <div class="section-title">🕵️ 侧写画像</div>
          <div class="summary-box">
            ${(jsonData.historical_summary || "暂无画像记录。").replace(/\*\*(.*?)\*\*/g, "<b>$1</b>")}
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
const outputPath = process.argv[3] || "/tmp/personal_card.png";

try {
  const data = JSON.parse(inputJsonStr);
  generatePersonalCard(data, outputPath);
} catch (e) {
  console.error("Invalid JSON input or rendering error", e);
  process.exit(1);
}

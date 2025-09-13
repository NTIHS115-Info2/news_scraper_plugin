// C:\VS_Code\news_scraper_plugin\test_plugin.js

import NewsScraperPlugin from './plugins/news_scraper/index.js';

async function runTest() {
    console.log('--- 啟動 news_scraper 插件 V8.0 整合測試 (自主研究代理) ---');

    const options = { pythonPath: 'python' };
    const plugin = new NewsScraperPlugin(options);

    await plugin.online();
    
    // --- 測試案例: 主動發現來源並進行深度分析 ---
    console.log("\n--- [測試案例] 自主研究任務 ---");
    const task = {
        // [V8.0 核心改造] 不再提供 URL，而是提供研究主題
        topic: "NVIDIA Blackwell architecture", 
        // 插件將根據 topic 找到的文章，回答這個具體問題
        query: "What are the performance improvements of Blackwell over Hopper?",
        // [V8.0 新增] 精細化控制參數
        depth: 3, // 讓 researcher 尋找 3 個最相關的來源
        summary_length: 'long' // 請求一份長摘要
    };
    console.log('正在處理自主研究任務:', task);
    const result = await plugin.send(task);
    console.log('插件回傳的最終研究報告:');
    console.log(JSON.stringify(result, null, 2));

    await plugin.offline();
    console.log(`\n[測試] 插件最終狀態: ${await plugin.state() === 0 ? '下線 (Offline)' : '錯誤'}`);
}

runTest();
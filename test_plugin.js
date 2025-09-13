// C:\VS_Code\news_scraper_plugin\test_plugin.js

import NewsScraperPlugin from './plugins/news_scraper/index.js';

async function runTest() {
    console.log('--- 啟動 news_scraper 插件 V3.0 整合測試 ---');

    const options = { pythonPath: 'python' };
    const plugin = new NewsScraperPlugin(options);

    await plugin.online();
    const currentState = await plugin.state();
    if (currentState !== 1) {
        console.error('插件未能成功上線，測試中止。');
        await plugin.offline();
        return;
    }

    // --- 測試案例 1: 預設行為 (單一、中等長度摘要) ---
    console.log("\n--- [測試案例 1] 預設行為 (single, medium) ---");
    const task1 = {
        url: 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
        query: 'What is happening with European leaders and Russia?'
    };
    console.log('正在處理任務:', task1);
    const result1 = await plugin.send(task1);
    console.log('插件回傳的最終情報摘要:');
    console.log(JSON.stringify(result1, null, 2));

    // --- 測試案例 2: 多角度、短摘要 ---
    console.log("\n--- [測試案例 2] 多角度、短摘要 (multi, short) ---");
    const task2 = {
        url: 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
        query: 'Palestine Action ban',
        summary_mode: 'multi', // <--- V3.0 新參數
        summary_length: 'short'  // <--- V3.0 新參數
    };
    console.log('正在處理任務:', task2);
    const result2 = await plugin.send(task2);
    console.log('插件回傳的多角度情報摘要:');
    console.log(JSON.stringify(result2, null, 2));


    await plugin.offline();
    console.log(`\n[測試] 插件最終狀態: ${await plugin.state() === 0 ? '下線 (Offline)' : '錯誤'}`);
}

runTest();
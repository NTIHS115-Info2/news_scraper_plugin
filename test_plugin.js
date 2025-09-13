// C:\VS_Code\news_scraper_plugin\test_plugin.js

import NewsScraperPlugin from './plugins/news_scraper/index.js';

async function runTest() {
    console.log('--- 啟動 news_scraper 插件 V4.0 整合測試 (情報聚合器) ---');

    const options = { pythonPath: 'python' };
    const plugin = new NewsScraperPlugin(options);

    await plugin.online();
    const currentState = await plugin.state();
    if (currentState !== 1) {
        console.error('插件未能成功上線，測試中止。');
        await plugin.offline();
        return;
    }

    // --- 測試案例: 同時從多個來源抓取，並進行單一總結 ---
    console.log("\n--- [測試案例] 多源聚合抓取 ---");
    const task = {
        // [V4.0 核心改造] 提供一個包含多個可靠 RSS Feed 的數組
        urls: [
            'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
            'http://feeds.bbci.co.uk/news/world/rss.xml',
            'https://feeds.reuters.com/Reuters/worldNews'
        ],
        query: 'What are the major international conflicts or tensions mentioned?'
    };
    console.log('正在處理任務:', task);
    const result = await plugin.send(task);
    console.log('插件回傳的最終情報摘要:');
    console.log(JSON.stringify(result, null, 2));

    await plugin.offline();
    console.log(`\n[測試] 插件最終狀態: ${await plugin.state() === 0 ? '下線 (Offline)' : '錯誤'}`);
}

runTest();
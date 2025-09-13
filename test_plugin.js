// C:\VS_Code\news_scraper_plugin\test_plugin.js

import NewsScraperPlugin from './plugins/news_scraper/index.js';

async function runTest() {
    console.log('--- 啟動 news_scraper 插件 V2.0 整合測試 (含摘要功能) ---');

    const options = { pythonPath: 'python' };
    const plugin = new NewsScraperPlugin(options);

    console.log('\n[測試] 正在調用 online() ...');
    await plugin.online();
    const currentState = await plugin.state();
    console.log(`[測試] 插件當前狀態: ${currentState === 1 ? '上線 (Online)' : '錯誤或離線'}`);
    if (currentState !== 1) {
        console.error('插件未能成功上線，測試中止。');
        return;
    }

    const task = {
        url: 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
        query: 'What are the global economic challenges?'
    };
    console.log('\n[測試] 正在調用 send() 處理任務:');
    console.log(task);

    const result = await plugin.send(task);

    console.log('\n--- 整合測試完成 ---');
    console.log('插件回傳的最終情報摘要:');
    
    console.log(JSON.stringify(result, null, 2));

    console.log('\n[測試] 正在調用 offline() ...');
    await plugin.offline();
    const finalState = await plugin.state();
    console.log(`[測試] 插件最終狀態: ${finalState === 0 ? '下線 (Offline)' : '錯誤'}`);
}

runTest();
// C:\VS_Code\news_scraper_plugin\test_plugin.js

import NewsScraperPlugin from './plugins/news_scraper/index.js';

async function runTest() {
    console.log('--- 啟動 news_scraper 插件 V9.0.1 整合測試 (降級策略驗收) ---');

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

    // [V9.0.1 核心改造] 使用一個已知需要 Playwright 的 URL 進行壓力測試
    const task = {
        url: 'https://www.cloudflare.com/learning/bots/what-is-a-web-crawler/',
        query: 'What is a web crawler?'
    };
    console.log('\n[測試] 正在調用 send() 處理任務:');
    console.log(task);

    const result = await plugin.send(task);

    console.log('\n--- 整合測試完成 ---');
    console.log('插件回傳的最終結果 (預覽):');
    
    if (result.success && result.result && result.result.length > 0) {
        console.log(`成功找到 ${result.result.length} 個相關片段。`);
        console.log("最佳匹配片段預覽:");
        console.log(JSON.stringify(result.result[0], null, 2));
    } else {
        console.log(JSON.stringify(result, null, 2));
    }


    console.log('\n[測試] 正在調用 offline() ...');
    await plugin.offline();
    const finalState = await plugin.state();
    console.log(`[測試] 插件最終狀態: ${finalState === 0 ? '下線 (Offline)' : '錯誤'}`);
}

runTest();
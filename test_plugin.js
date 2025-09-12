// C:\VS_Code\news_scraper_plugin\test_plugin.js

import NewsScraperPlugin from './plugins/news_scraper/index.js';

async function runTest() {
    console.log('--- 啟動 news_scraper 插件整合測試 (RSS Feed 穩健版) ---');

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

    // [V1.0.3 核心修正] 使用紐約時報世界新聞 RSS Feed 作為穩定測試源
    const task = {
        url: 'https://rss.nytimes.com/services/xml/rss/nyt/World.xml',
        query: 'What are the global economic challenges?'
    };
    console.log('\n[測試] 正在調用 send() 處理任務:');
    console.log(task);

    const result = await plugin.send(task);

    console.log('\n--- 整合測試完成 ---');
    console.log('插件回傳的最終結果 (預覽):');
    
    // 對結果進行美化和預覽，避免因內容過長而刷屏
    if (result.success && result.result.length > 0) {
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
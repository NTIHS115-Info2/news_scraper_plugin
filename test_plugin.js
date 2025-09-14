// C:\VS_Code\news_scraper_plugin\test_plugin.js

import NewsScraperPlugin from './plugins/news_scraper/index.js';

async function runTest() {
    console.log('--- 啟動 news_scraper 插件 V10.0.2 整合測試 ---');

    // [V10.0.2 核心修正] 恢復被錯誤省略的插件初始化與上線流程
    const options = { pythonPath: 'python' };
    const plugin = new NewsScraperPlugin(options);

    console.log('\n[測試] 正在調用 online() ...');
    await plugin.online();
    const currentState = await plugin.state();
    console.log(`[測試] 插件當前狀態: ${currentState === 1 ? '上線 (Online)' : '錯誤或離線'}`);
    if (currentState !== 1) {
        console.error('插件未能成功上線，測試中止。');
        await plugin.offline();
        return;
    }
    
    const task = {
        url: 'https://www.cloudflare.com/learning/bots/what-is-a-web-crawler/',
        query: 'What is a web crawler?'
    };
    
    console.log("\n--- [測試案例] 首次請求 (預期從網路抓取) ---");
    console.time("first_request_duration");
    const result1 = await plugin.send(task);
    console.timeEnd("first_request_duration");
    
    console.log('插件回傳的完整結果 (首次):');
    console.log(JSON.stringify(result1, null, 2));

    // --- 第二次執行：預期會從快取命中 ---
    console.log("\n--- [測試案例 2] 重複請求 (預期從快取命中) ---");
    console.time("second_request_duration");
    const result2 = await plugin.send(task);
    console.timeEnd("second_request_duration");

    console.log('插件回傳的完整結果 (快取):');
    console.log(JSON.stringify(result2, null, 2));
    
    console.log("\n--- 測試結論 ---");
    console.log("請比較兩次請求的時間。第二次請求的時間應遠小於第一次，以證明快取生效。");

    console.log('\n[測試] 正在調用 offline() ...');
    await plugin.offline();
    const finalState = await plugin.state();
    console.log(`[測試] 插件最終狀態: ${finalState === 0 ? '下線 (Offline)' : '錯誤'}`);
}

runTest();
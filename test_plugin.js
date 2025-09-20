// C:\VS_Code\news_scraper_plugin\test_plugin.js

import NewsScraperPlugin from './plugins/news_scraper/index.js';

async function runTest() {
    console.log('--- 啟動 news_scraper 插件 V11.0.1 整合測試 (自主研究代理) ---');
    const options = { pythonPath: 'python3' };
    const plugin = new NewsScraperPlugin(options);

    console.log('\n[測試] 正在調用 online() ...');
    await plugin.online();
    
    // [V11.0.1 核心修正] 任務物件現在使用 "topic"，而不是 "url"
    console.log("\n--- [測試案例] 自主研究任務 ---");
    const task = {
        topic: "NVIDIA Blackwell architecture",
        query: "What are the performance improvements of Blackwell over Hopper?",
        depth: 3 
    };
    console.log('正在處理自主研究任務:', task);
    const result = await plugin.send(task);

    console.log('\n--- 整合測試完成 ---');
    console.log('插件回傳的最終研究報告 (預覽):');
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
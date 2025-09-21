// C:\VS_Code\news_scraper_plugin\test_plugin.js

import NewsScraperPlugin from './plugins/news_scraper/index.js';

async function runTest() {
    console.log('--- 啟動 news_scraper 插件 V13.0 整合測試 (新規範適配) ---');
    const options = { pythonPath: 'python3' };
    const plugin = new NewsScraperPlugin(options);

    console.log('\n[測試] 正在調用 online() ...');
    await plugin.online();

    // [V13.0 核心改造] 任務物件現在是 payload
    const payload = {
        toolName: "news_scraper.autonomous_researcher", // 模擬主控 LLM 的調用
        input: {
            topic: "NVIDIA Blackwell performance vs Hopper",
            query: "What are the key performance metrics of Blackwell?",
            depth: 3 
        }
    };
    
    console.log("\n--- [測試案例] 自主研究任務 ---");
    console.time("request_duration");
    console.log('正在發送 payload:', payload);
    const result = await plugin.send(payload.input); // [V13.0] 將 payload.input 傳遞給 send
    console.timeEnd("request_duration");
    
    console.log('\n--- 整合測試完成 ---');
    console.log('插件回傳的最終研究報告:');
    console.log(JSON.stringify(result, null, 2));

    console.log('\n[測試] 正在調用 offline() ...');
    await plugin.offline();
    const finalState = await plugin.state();
    console.log(`[測試] 插件最終狀態: ${finalState === 0 ? '下線 (Offline)' : '錯誤'}`);
}

runTest();
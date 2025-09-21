// plugins/news_scraper/index.js

import RemoteStrategy from './strategies/remote/index.js';

class NewsScraperPlugin {
    constructor(options) {
        this.currentState = -2; // -2: state 未定義
        this.strategy = new RemoteStrategy(options);
        this.currentState = 0; // 0: 初始化完成，處於下線狀態
        console.log("NewsScraperPlugin (V13.0) 已初始化，當前為離線狀態。");
    }

    async online(option) {
        console.log("NewsScraperPlugin 收到上線指令...");
        this.currentState = 1; // 1: 上線
        console.log("NewsScraperPlugin 已成功上線。");
    }

    async offline() {
        console.log("NewsScraperPlugin 收到下線指令...");
        this.currentState = 0; // 0: 下線
        console.log("NewsScraperPlugin 已成功下線。");
    }

    async state() {
        return this.currentState;
    }

    async send(payload) { // [V13.0 核心改造] 參數從 option 改為 payload
        if (this.currentState !== 1) {
            const errorMsg = "插件未上線，無法處理請求。";
            console.error(errorMsg);
            return { success: false, error: errorMsg };
        }
        console.log("NewsScraperPlugin 正在將 'send' 指令轉發給策略...");
        // 將 payload 直接交給 remote 策略的 send 方法處理
        return this.strategy.send(payload);
    }

    async updateStrategy(option) {
        console.log("updateStrategy 功能尚未實現。");
        return { success: false, error: "Not implemented." };
    }
}

export default NewsScraperPlugin;
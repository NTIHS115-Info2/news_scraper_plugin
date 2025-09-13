// plugins/news_scraper/strategies/remote/index.js

import { spawn } from 'child_process';
import path from 'path';

class RemoteStrategy {
    constructor(options) {
        this.pythonPath = options.pythonPath || 'python';
        this.strategyPath = path.join(process.cwd(), 'plugins', 'news_scraper', 'strategies', 'remote');
        this.priority = 100;
        console.log("遠程新聞抓取策略 (RemoteStrategy) V8.0.1 已初始化。");
    }

    _runPythonScript(scriptName, args) {
        return new Promise((resolve, reject) => {
            const scriptPath = path.join(this.strategyPath, scriptName);
            const pyProcess = spawn(this.pythonPath, [scriptPath, ...args]);

            let stdout = '';
            let stderr = '';

            pyProcess.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            pyProcess.stderr.on('data', (data) => {
                stderr += data.toString();
            });
            
            // [V8.0.1 核心修正] 增加對 spawn 本身錯誤的監聽
            pyProcess.on('error', (err) => {
                console.error(`[RemoteStrategy] 無法啟動子進程 ${scriptName}:`, err);
                reject(err);
            });

            pyProcess.on('close', (code) => {
                if (code !== 0) {
                    const errorMessage = stderr || `Python script ${scriptName} exited with code ${code}`;
                    console.error(`[RemoteStrategy] Python 腳本 ${scriptName} 執行錯誤 (code ${code}): ${errorMessage}`);
                    reject(new Error(errorMessage));
                } else {
                    console.log(`[RemoteStrategy] Python 腳本 ${scriptName} 執行成功。`);
                    resolve(stdout);
                }
            });
        });
    }

    async send(option) {
        // ... (send 函數邏輯不變)
        const { topic, query, depth = 3, summary_mode = 'single', summary_length = 'medium' } = option;

        if (!topic) {
            return { success: false, error: "缺少 'topic' 參數。" };
        }
        if (!query) {
             return { success: false, error: "缺少 'query' 參數。" };
        }

        try {
            console.log(`[RemoteStrategy] 步驟 1: 調用 researcher 發現關於 '${topic}' 的來源...`);
            const researcherResult = await this._runPythonScript('researcher.py', [topic, depth.toString()]);
            const researcherData = JSON.parse(researcherResult);
            if (!researcherData.success || !researcherData.result) { return researcherData; }
            const discoveredUrls = researcherData.result.discovered_urls;
            if (discoveredUrls.length === 0) {
                return { success: true, result: { summary: "No relevant sources found for the topic." }, resultType: "object" };
            }

            const urls_string = discoveredUrls.join(',');
            console.log(`[RemoteStrategy] 步驟 2: 調用 scraper 並發抓取 ${discoveredUrls.length} 個已發現的來源...`);
            const scrapedContent = await this._runPythonScript('scraper.py', [urls_string]);
            const scrapedData = JSON.parse(scrapedContent);
            if (scrapedData.errors && scrapedData.errors.length > 0) {
                console.warn(`[RemoteStrategy] Scraper 報告了 ${scrapedData.errors.length} 個錯誤。`);
            }
            if (!scrapedData.success || !scrapedData.result) { return scrapedData; }
            const articleText = scrapedData.result.article_text;

            console.log(`[RemoteStrategy] 步驟 3: 調用 librarian 過濾內容，查詢: "${query}"`);
            const filteredResult = await this._runPythonScript('librarian.py', [articleText, query]);
            const filteredData = JSON.parse(filteredResult);
            if (!filteredData.success || !filteredData.result) { return filteredData; }

            console.log(`[RemoteStrategy] 步驟 4: 調用 summarizer 生成情報摘要...`);
            const chunksToSummarize = filteredData.result.relevant_sections.map(item => item.chunk);
            const summarizerInput = JSON.stringify({
                chunks: chunksToSummarize,
                mode: summary_mode,
                length: summary_length
            });
            const summaryResult = await this._runPythonScript('summarizer.py', [summarizerInput]);
            
            return JSON.parse(summaryResult);

        } catch (error) {
            // 這個 catch 現在能捕獲到更精確的錯誤訊息
            return { success: false, error: `RemoteStrategy 執行失敗: ${error.message}` };
        }
    }
}

export default RemoteStrategy;
// plugins/news_scraper/strategies/remote/index.js

import { spawn } from 'child_process';
import path from 'path';

class RemoteStrategy {
    constructor(options) {
        this.pythonPath = options.pythonPath || 'python';
        this.strategyPath = path.join(process.cwd(), 'plugins', 'news_scraper', 'strategies', 'remote');
        this.priority = 100;
        console.log("遠程新聞抓取策略 (RemoteStrategy) V4.0 已初始化。");
    }

    // _runPythonScript 函數保持不變
    _runPythonScript(scriptName, args) {
        return new Promise((resolve, reject) => {
            const scriptPath = path.join(this.strategyPath, scriptName);
            console.log(`[RemoteStrategy] 正在執行 Python 腳本: ${scriptName} 帶有參數...`);
            const pyProcess = spawn(this.pythonPath, [scriptPath, ...args]);

            let stdout = '';
            let stderr = '';

            pyProcess.stdout.on('data', (data) => {
                stdout += data.toString();
            });

            pyProcess.stderr.on('data', (data) => {
                stderr += data.toString();
            });

            pyProcess.on('close', (code) => {
                if (code !== 0) {
                    console.error(`[RemoteStrategy] Python 腳本 ${scriptName} 執行錯誤 (code ${code}): ${stderr}`);
                    return reject(new Error(stderr));
                }
                console.log(`[RemoteStrategy] Python 腳本 ${scriptName} 執行成功。`);
                resolve(stdout);
            });
        });
    }

    async send(option) {
        // [V4.0 改造] url 參數現在是一個 URL 數組
        const { urls, query, summary_mode = 'single', summary_length = 'medium' } = option;

        if (!urls || !Array.isArray(urls) || urls.length === 0) {
            return { success: false, error: "缺少 'urls' 參數，或格式不正確 (應為數組)。" };
        }
        if (!query) {
             return { success: false, error: "缺少 'query' 參數。" };
        }

        try {
            // [V4.0 改造] 將 URL 數組轉換為以逗號分隔的字符串
            const urls_string = urls.join(',');
            console.log(`[RemoteStrategy] 步驟 1: 調用 scraper 並發抓取 ${urls.length} 個來源...`);
            const scrapedContent = await this._runPythonScript('scraper.py', [urls_string]);
            const scrapedData = JSON.parse(scrapedContent);
            if (!scrapedData.success) { return scrapedData; }
            const articleText = scrapedData.result.article_text;

            console.log(`[RemoteStrategy] 步驟 2: 調用 librarian 過濾內容，查詢: "${query}"`);
            const filteredResult = await this._runPythonScript('librarian.py', [articleText, query]);
            const filteredData = JSON.parse(filteredResult);
            if (!filteredData.success) { return filteredData; }

            console.log(`[RemoteStrategy] 步驟 3: 調用 summarizer 生成情報摘要 (模式: ${summary_mode}, 長度: ${summary_length})...`);
            const chunksToSummarize = filteredData.result.map(item => item.chunk);

            const summarizerInput = JSON.stringify({
                chunks: chunksToSummarize,
                mode: summary_mode,
                length: summary_length
            });

            const summaryResult = await this._runPythonScript('summarizer.py', [summarizerInput]);
            
            return JSON.parse(summaryResult);

        } catch (error) {
            return { success: false, error: `RemoteStrategy 執行失敗: ${error.message}` };
        }
    }
}

export default RemoteStrategy;
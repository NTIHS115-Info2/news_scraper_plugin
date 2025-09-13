// plugins/news_scraper/strategies/remote/index.js

import { spawn } from 'child_process';
import path from 'path';

class RemoteStrategy {
    constructor(options) {
        this.pythonPath = options.pythonPath || 'python';
        this.strategyPath = path.join(process.cwd(), 'plugins', 'news_scraper', 'strategies', 'remote');
        this.priority = 100;
        console.log("遠程新聞抓取策略 (RemoteStrategy) V9.0.1 已初始化。");
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
            
            // [V8.0.1 歷史修正恢復] 增加對 spawn 本身錯誤的監聽，防止靜默失敗
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
                    // [鑽石定律] 確保即使 stdout 為空，也返回一個有效的空字符串 JSON
                    if (stdout.trim() === '') {
                        console.warn(`[RemoteStrategy] Python 腳本 ${scriptName} 成功執行，但 stdout 為空。`);
                        resolve('{}'); 
                        return;
                    }
                    console.log(`[RemoteStrategy] Python 腳本 ${scriptName} 執行成功。`);
                    resolve(stdout);
                }
            });
        });
    }

    async send(option) {
        const { url, query } = option;

        if (!url || !query) {
            return { success: false, error: "缺少 'url' 或 'query' 參數。" };
        }

        try {
            console.log(`[RemoteStrategy] 步驟 1: 調用 scraper 抓取通用 URL: ${url}`);
            const scrapedContent = await this._runPythonScript('scraper.py', [url]);
            // 增加對空JSON的防禦
            if (!scrapedContent || scrapedContent.trim() === '{}') {
                return { success: false, error: "Scraper returned empty content." };
            }
            const scrapedData = JSON.parse(scrapedContent);

            if (!scrapedData.success || !scrapedData.result) {
                return scrapedData;
            }

            const articleText = scrapedData.result.article_text;
            if (!articleText || articleText.trim() === '') {
                 return { success: true, result: { relevant_sections: [] }, resultType: "list" };
            }

            console.log(`[RemoteStrategy] 步驟 2: 調用 librarian 過濾內容，查詢: "${query}"`);
            const filteredResult = await this._runPythonScript('librarian.py', [articleText, query]);
            const filteredData = JSON.parse(filteredResult);
            
            // 修正 V9.0 測試腳本中的一個小錯誤，librarian 的結果是在 result.relevant_sections
            if (filteredData.success && filteredData.result && filteredData.result.relevant_sections) {
                 // 為了與 test_plugin.js 的預期輸出格式匹配，我們直接返回 librarian 的結果
                 // 並將其內部的 relevant_sections 提升一層
                 return { success: true, result: filteredData.result.relevant_sections, resultType: 'list' };
            }
            return filteredData;

        } catch (error) {
            return { success: false, error: `RemoteStrategy 執行失敗: ${error.message}` };
        }
    }
}

export default RemoteStrategy;
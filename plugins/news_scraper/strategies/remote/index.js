// plugins/news_scraper/strategies/remote/index.js

import { spawn } from 'child_process';
import path from 'path';

class RemoteStrategy {
    constructor(options) {
        this.pythonPath = options.pythonPath || 'python';
        this.strategyPath = path.join(process.cwd(), 'plugins', 'news_scraper', 'strategies', 'remote');
        console.log("遠程新聞抓取策略 (RemoteStrategy) V10.0.2 已初始化。");
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
                    if (stdout.trim() === '') {
                        console.warn(`[RemoteStrategy] Python 腳本 ${scriptName} 成功執行，但 stdout 為空。`);
                        resolve('{}'); // 返回一個有效的空 JSON
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
            
            if (!scrapedContent) {
                 return { success: false, error: "Scraper returned no content." };
            }
            const scrapedData = JSON.parse(scrapedContent);
            
            if (!scrapedData.success) {
                console.error(`[RemoteStrategy] Scraper 執行失敗:`, scrapedData.error);
                return scrapedData;
            }

            const articleText = scrapedData.result.article_text;
            if (!articleText || articleText.trim() === '') {
                 return { success: true, result: [], resultType: "list" }; // 返回空列表
            }

            console.log(`[RemoteStrategy] 步驟 2: 調用 librarian 過濾內容...`);
            const filteredResult = await this._runPythonScript('librarian.py', [articleText, query]);
            const filteredData = JSON.parse(filteredResult);

            if (filteredData.success && filteredData.result) {
                 return { success: true, result: filteredData.result.relevant_sections, resultType: 'list' };
            }
            return filteredData;

        } catch (error) {
            return { success: false, error: `RemoteStrategy 執行失敗: ${error.message}` };
        }
    }
}

export default RemoteStrategy;
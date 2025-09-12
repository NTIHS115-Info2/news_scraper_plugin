// plugins/news_scraper/strategies/remote/index.js

import { spawn } from 'child_process';
import path from 'path';

class RemoteStrategy {
    constructor(options) {
        this.pythonPath = options.pythonPath || 'python';
        this.strategyPath = path.join(process.cwd(), 'plugins', 'news_scraper', 'strategies', 'remote');
        this.priority = 100; // 作為 remote 策略，優先級最高
        console.log("遠程新聞抓取策略 (RemoteStrategy) 已初始化。");
    }

    /**
     * 執行指定的 Python 腳本
     * @param {string} scriptName - 腳本檔案名稱
     * @param {Array<string>} args - 傳遞給腳本的參數
     * @returns {Promise<string>} - 返回腳本的標準輸出
     */
    _runPythonScript(scriptName, args) {
        return new Promise((resolve, reject) => {
            const scriptPath = path.join(this.strategyPath, scriptName);
            console.log(`[RemoteStrategy] 正在執行 Python 腳本: ${scriptPath} 帶有參數: ${args}`);
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
                    console.error(`[RemoteStrategy] Python 腳本執行錯誤 (code ${code}): ${stderr}`);
                    return reject(new Error(stderr));
                }
                console.log(`[RemoteStrategy] Python 腳本執行成功。`);
                resolve(stdout);
            });
        });
    }

    /**
     * 處理 send 請求，協調 scraper 和 librarian
     * @param {object} option - 包含 url 和 query 的物件
     * @returns {Promise<object>} - 返回處理結果
     */
    async send(option) {
        const { url, query } = option;

        if (!url || !query) {
            return { success: false, error: "缺少 'url' 或 'query' 參數。" };
        }

        try {
            // 步驟一：調用 scraper.py 抓取網頁內容
            console.log(`[RemoteStrategy] 步驟 1: 調用 scraper 抓取 URL: ${url}`);
            const scrapedContent = await this._runPythonScript('scraper.py', [url]);
            const scrapedData = JSON.parse(scrapedContent);

            if (!scrapedData.success) {
                return scrapedData; // 如果抓取失敗，直接返回錯誤
            }

            const articleText = scrapedData.result.article_text;

            // 步驟二：調用 librarian.py 過濾內容
            console.log(`[RemoteStrategy] 步驟 2: 調用 librarian 過濾內容，查詢: "${query}"`);
            const filteredContent = await this._runPythonScript('librarian.py', [articleText, query]);
            
            // librarian.py 的輸出本身就是一個 JSON 字符串，直接解析返回即可
            return JSON.parse(filteredContent);

        } catch (error) {
            return { success: false, error: `RemoteStrategy 執行失敗: ${error.message}` };
        }
    }
}

export default RemoteStrategy;
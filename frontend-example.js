/**
 * Paper Interpreter 前端集成示例
 * 在 getainote.com 页面中引用此代码
 */

class PaperInterpreter {
  constructor(apiBaseUrl) {
    this.apiBaseUrl = apiBaseUrl || 'https://your-api-domain.com';
  }

  /**
   * 提交论文解读任务
   * @param {string} url - 论文链接
   * @param {object} options - 配置选项
   * @returns {Promise<{taskId: string}>}
   */
  async submitTask(url, options = {}) {
    const response = await fetch(`${this.apiBaseUrl}/api/paper/interpret`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: url,
        illustration_count: options.illustrationCount || 3,
        email: options.email,
      }),
    });

    if (!response.ok) {
      throw new Error('提交任务失败');
    }

    return response.json();
  }

  /**
   * 轮询查询任务状态
   * @param {string} taskId - 任务ID
   * @param {function} onProgress - 进度回调 (progress) => void
   * @returns {Promise<object>}
   */
  async pollStatus(taskId, onProgress) {
    return new Promise((resolve, reject) => {
      const interval = setInterval(async () => {
        try {
          const response = await fetch(
            `${this.apiBaseUrl}/api/paper/status/${taskId}`
          );
          const data = await response.json();

          if (onProgress) {
            onProgress(data.progress, data.status);
          }

          if (data.status === 'completed') {
            clearInterval(interval);
            resolve(data.result);
          } else if (data.status === 'failed') {
            clearInterval(interval);
            reject(new Error(data.error));
          }
        } catch (err) {
          clearInterval(interval);
          reject(err);
        }
      }, 2000); // 每2秒查询一次
    });
  }

  /**
   * 下载生成的文件
   * @param {string} taskId - 任务ID
   * @param {string} format - 'html' 或 'pdf'
   */
  downloadResult(taskId, format = 'pdf') {
    const filename = format === 'pdf' ? 'article.pdf' : 'article.html';
    window.open(
      `${this.apiBaseUrl}/api/paper/download/${taskId}/${filename}`,
      '_blank'
    );
  }
}

// ==================== 使用示例 ====================

// HTML 结构示例：
/*
<div id="paper-interpreter-widget">
  <input type="url" id="paper-url" placeholder="输入论文链接 (arXiv/DOI等)" />
  <button onclick="startInterpret()">开始解读</button>
  <div id="progress" style="display:none;">
    <div class="progress-bar"></div>
    <span class="status-text">处理中...</span>
  </div>
  <div id="result" style="display:none;">
    <a id="download-html" target="_blank">查看 HTML</a>
    <a id="download-pdf" target="_blank">下载 PDF</a>
  </div>
</div>
*/

const interpreter = new PaperInterpreter('https://your-api-domain.com');

async function startInterpret() {
  const url = document.getElementById('paper-url').value;
  if (!url) {
    alert('请输入论文链接');
    return;
  }

  // 显示进度
  document.getElementById('progress').style.display = 'block';
  document.getElementById('result').style.display = 'none';

  try {
    // 提交任务
    const { task_id } = await interpreter.submitTask(url);

    // 轮询进度
    const result = await interpreter.pollStatus(
      task_id,
      (progress, status) => {
        console.log(`进度: ${progress}%, 状态: ${status}`);
        document.querySelector('.progress-bar').style.width = `${progress}%`;
        document.querySelector('.status-text').textContent =
          status === 'processing' ? '正在生成文章...' : '等待中...';
      }
    );

    // 显示结果
    document.getElementById('progress').style.display = 'none';
    document.getElementById('result').style.display = 'block';
    document.getElementById('download-html').href = result.html_url;
    document.getElementById('download-pdf').href = result.pdf_url;

  } catch (err) {
    alert('处理失败: ' + err.message);
    document.getElementById('progress').style.display = 'none';
  }
}

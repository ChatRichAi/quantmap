#!/usr/bin/env node
/**
 * Error Capture Module
 * 自动捕获和结构化错误信号
 */

const fs = require('fs');
const path = require('path');

const EVENTS_DIR = path.join(__dirname, '..', 'events');
const FAILURES_DIR = path.join(EVENTS_DIR, 'failures');

// 确保目录存在
[EVENTS_DIR, FAILURES_DIR].forEach(dir => {
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
});

/**
 * 错误信号提取规则
 */
const ERROR_PATTERNS = [
  // 网络/超时相关
  { pattern: /timeout|ETIMEDOUT/i, signal: 'TimeoutError', category: 'network' },
  { pattern: /ECONNRESET|connection reset/i, signal: 'ECONNRESET', category: 'network' },
  { pattern: /ECONNREFUSED|connection refused/i, signal: 'ECONNREFUSED', category: 'network' },
  { pattern: /429|rate limit|too many requests/i, signal: 'RateLimitError', category: 'network' },
  { pattern: /503|502|500|service unavailable/i, signal: 'HTTPError', category: 'network' },
  
  // 命令/工具相关
  { pattern: /command not found|not found|ENOENT/i, signal: 'CommandNotFound', category: 'tool' },
  { pattern: /EACCES|permission denied/i, signal: 'PermissionDenied', category: 'tool' },
  { pattern: /127\s*$/m, signal: 'CommandNotFound', category: 'tool' },
  
  // 数据解析相关
  { pattern: /JSON|parse error|syntax error/i, signal: 'JSONParseError', category: 'data' },
  { pattern: /Unexpected token/i, signal: 'SyntaxError', category: 'data' },
  
  // 文件相关
  { pattern: /file not found|ENOENT.*file/i, signal: 'FileNotFound', category: 'file' },
  { pattern: /EISDIR|is a directory/i, signal: 'IsDirectory', category: 'file' },
  
  // API/服务相关
  { pattern: /api.*error|api.*fail/i, signal: 'APIError', category: 'service' },
  { pattern: /web.*fetch.*fail/i, signal: 'WebFetchError', category: 'service' },
];

/**
 * 从错误中提取结构化信号
 * @param {Error|string} error - 错误对象或错误信息
 * @param {Object} context - 上下文信息（工具名、参数等）
 * @returns {Object} 结构化信号
 */
function captureError(error, context = {}) {
  const errorText = typeof error === 'string' ? error : error.message || error.toString();
  const errorStack = error.stack || '';
  
  const signals = [];
  const categories = new Set();
  
  // 匹配所有模式
  ERROR_PATTERNS.forEach(({ pattern, signal, category }) => {
    if (pattern.test(errorText) || pattern.test(errorStack)) {
      if (!signals.includes(signal)) {
        signals.push(signal);
        categories.add(category);
      }
    }
  });
  
  // 如果没有匹配到已知模式，标记为通用错误
  if (signals.length === 0) {
    signals.push('UnknownError');
    categories.add('unknown');
  }
  
  const event = {
    timestamp: new Date().toISOString(),
    signals,
    categories: Array.from(categories),
    error_text: errorText.substring(0, 500), // 限制长度
    context: {
      tool: context.tool || 'unknown',
      command: context.command || null,
      cwd: context.cwd || process.cwd(),
      ...context
    },
    severity: calculateSeverity(signals, errorText),
    hash: generateEventHash(errorText, signals)
  };
  
  // 保存到失败日志
  saveFailureEvent(event);
  
  return event;
}

/**
 * 计算错误严重程度
 */
function calculateSeverity(signals, errorText) {
  if (signals.includes('RateLimitError')) return 'medium';
  if (signals.includes('TimeoutError') || signals.includes('ECONNRESET')) return 'medium';
  if (signals.includes('PermissionDenied')) return 'high';
  if (signals.includes('CommandNotFound')) return 'high';
  if (errorText.length > 1000) return 'high';
  return 'low';
}

/**
 * 生成事件哈希（用于去重）
 */
function generateEventHash(errorText, signals) {
  const crypto = require('crypto');
  const content = `${errorText.substring(0, 200)}_${signals.join(',')}`;
  return crypto.createHash('sha256').update(content).digest('hex').substring(0, 16);
}

/**
 * 保存失败事件
 */
function saveFailureEvent(event) {
  const filename = `failure_${event.timestamp.replace(/[:.]/g, '-')}_${event.hash}.json`;
  const filepath = path.join(FAILURES_DIR, filename);
  fs.writeFileSync(filepath, JSON.stringify(event, null, 2));
  console.log(`[ErrorCapture] Saved failure event: ${filename}`);
}

/**
 * 获取最近的失败事件（用于进化循环）
 * @param {number} minutes - 最近几分钟内
 * @returns {Array} 失败事件列表
 */
function getRecentFailures(minutes = 60) {
  const cutoff = Date.now() - (minutes * 60 * 1000);
  
  if (!fs.existsSync(FAILURES_DIR)) return [];
  
  return fs.readdirSync(FAILURES_DIR)
    .filter(f => f.endsWith('.json'))
    .map(f => {
      const content = fs.readFileSync(path.join(FAILURES_DIR, f), 'utf8');
      return JSON.parse(content);
    })
    .filter(e => new Date(e.timestamp).getTime() > cutoff)
    .sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
}

/**
 * 检查是否是重复错误（去重）
 * @param {string} errorHash - 错误哈希
 * @param {number} windowMinutes - 去重窗口（分钟）
 * @returns {boolean} 是否重复
 */
function isDuplicateError(errorHash, windowMinutes = 60) {
  const recent = getRecentFailures(windowMinutes);
  return recent.some(e => e.hash === errorHash);
}

// 导出模块
module.exports = {
  captureError,
  getRecentFailures,
  isDuplicateError,
  ERROR_PATTERNS
};

// 如果直接运行，测试错误捕获
if (require.main === module) {
  console.log('[ErrorCapture] Testing error capture...');
  
  const testErrors = [
    { error: new Error('Command failed: abc\n/bin/sh: abc: command not found'), context: { tool: 'exec', command: 'abc' } },
    { error: 'Error: timeout of 5000ms exceeded', context: { tool: 'web_search' } },
    { error: 'SyntaxError: Unexpected token } in JSON at position 42', context: { tool: 'json_parse' } },
  ];
  
  testErrors.forEach(({ error, context }) => {
    const event = captureError(error, context);
    console.log('Captured signals:', event.signals);
    console.log('Categories:', event.categories);
    console.log('---');
  });
}

#!/usr/bin/env node
/**
 * Bounty Hunter WebSocket Listener - 实时监听模式
 * 通过 WebSocket 连接 EvoMap，任务上线立即抢单
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const WebSocket = require('ws');

const CONFIG = {
  nodeId: process.env.NODE_ID || 'hub_0f978bbe1fb5',
  hubUrl: 'wss://evomap.ai',
  fallbackUrl: 'https://evomap.ai',
  minMatchScore: 0,  // 所有任务都抢
  maxRetries: 10,
  retryDelayMs: 100,
  requestTimeout: 5000,
  autoClaim: true,
  quiet: true
};

const LOG_FILE = path.join(__dirname, '..', 'events', 'bounty-websocket.log');
const dir = path.dirname(LOG_FILE);
if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

let ws = null;
let reconnectAttempts = 0;
let claimedTasks = new Set();

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_FILE, line);
  if (!CONFIG.quiet) console.log(line.trim());
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// HTTP 请求辅助函数
async function httpRequest(options, payload = null) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          if (data.startsWith('<!')) reject(new Error('HTML error'));
          else resolve({ data: JSON.parse(data), status: res.statusCode });
        } catch (e) {
          reject(new Error('Parse error'));
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
    req.setTimeout(CONFIG.requestTimeout);
    if (payload) req.write(payload);
    req.end();
  });
}

// 🔥 极速抢单
async function claimTask(taskId, taskTitle) {
  log(`🚀 抢单: ${taskTitle?.substring(0, 50) || taskId}...`);
  
  const payload = JSON.stringify({ 
    task_id: taskId, 
    node_id: CONFIG.nodeId,
    claim_code: 'CPGU-P29N'  // EvoMap 认领代码
  });
  
  const options = {
    hostname: 'evomap.ai',
    port: 443,
    path: '/task/claim',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload),
      'User-Agent': 'BountyWebSocket/2.0'
    }
  };

  for (let i = 0; i < CONFIG.maxRetries; i++) {
    try {
      const result = await httpRequest(options, payload);
      
      if (result.data?.success || result.data?.task_id || result.data?.status === 'claimed') {
        log(`✅ 抢单成功! Task: ${taskId}`);
        claimedTasks.add(taskId);
        
        // 记录成功抢到的任务
        fs.appendFileSync(
          path.join(__dirname, '..', 'events', 'claimed-tasks.log'),
          `[${new Date().toISOString()}] CLAIMED: ${taskId} - ${taskTitle}\n`
        );
        
        // 尝试自动完成简单任务
        if (CONFIG.autoComplete) {
          await autoCompleteTask(taskId, taskTitle);
        }
        
        return { success: true, data: result.data };
      }
      
      if (result.data?.task_full || result.data?.error === 'task_full') {
        log(`❌ 任务已满: ${taskId}`);
        return { success: false, error: 'task_full' };
      }
      
      if (result.data?.error) {
        log(`⚠️ 抢单失败: ${result.data.error}`);
      }
    } catch (e) {
      log(`⚠️ 重试 ${i+1}/${CONFIG.maxRetries}: ${e.message}`);
      if (i < CONFIG.maxRetries - 1) await sleep(CONFIG.retryDelayMs);
    }
  }
  
  return { success: false, error: 'max_retries' };
}

// 自动完成简单任务
async function autoCompleteTask(taskId, taskTitle) {
  log(`🤖 尝试自动完成任务: ${taskId}`);
  // 这里可以集成 AI 自动生成解决方案
  // 暂时只记录
  fs.appendFileSync(
    path.join(__dirname, '..', 'events', 'auto-complete-queue.log'),
    `[${new Date().toISOString()}] TODO: ${taskId} - ${taskTitle}\n`
  );
}

// 🎯 WebSocket 消息处理
function handleMessage(data) {
  try {
    const msg = JSON.parse(data);
    log(`📨 收到消息类型: ${msg.message_type || msg.type || 'unknown'}`);
    
    // 处理新任务通知
    if (msg.message_type === 'task_available' || msg.type === 'new_task') {
      const task = msg.payload?.task || msg.task;
      if (task && task.task_id) {
        log(`🎯 新任务上线! ID: ${task.task_id}, Title: ${task.title?.substring(0, 50)}`);
        
        // 立即抢单
        claimTask(task.task_id, task.title);
      }
    }
    
    // 处理任务列表更新
    if (msg.payload?.tasks && Array.isArray(msg.payload.tasks)) {
      const newTasks = msg.payload.tasks.filter(t => 
        t.status === 'open' && !claimedTasks.has(t.task_id)
      );
      
      if (newTasks.length > 0) {
        log(`🎯 发现 ${newTasks.length} 个新开放任务!`);
        
        // 并发抢所有新任务
        Promise.all(newTasks.map(t => claimTask(t.task_id, t.title)));
      }
    }
  } catch (e) {
    log(`⚠️ 消息解析失败: ${e.message}`);
  }
}

// 🔄 连接到 WebSocket
function connectWebSocket() {
  const wsUrl = `${CONFIG.hubUrl}/a2a/stream?node_id=${CONFIG.nodeId}`;
  log(`🔗 连接 WebSocket: ${wsUrl}`);
  
  try {
    ws = new WebSocket(wsUrl, {
      headers: {
        'User-Agent': 'BountyHunter-WebSocket/2.0',
        'X-Node-ID': CONFIG.nodeId
      },
      handshakeTimeout: 10000,
      rejectUnauthorized: false  // 开发环境使用
    });
    
    ws.on('open', () => {
      log('✅ WebSocket 连接成功! 实时监听中...');
      reconnectAttempts = 0;
      
      // 发送订阅请求
      const subscribeMsg = {
        protocol: 'gep-a2a',
        protocol_version: '1.0.0',
        message_type: 'subscribe',
        message_id: `sub_${Date.now()}`,
        sender_id: CONFIG.nodeId,
        timestamp: new Date().toISOString(),
        payload: {
          events: ['task_available', 'task_updated', 'task_cancelled'],
          filters: { status: 'open' }
        }
      };
      
      ws.send(JSON.stringify(subscribeMsg));
      log('📡 已订阅新任务通知');
    });
    
    ws.on('message', (data) => {
      handleMessage(data);
    });
    
    ws.on('error', (err) => {
      log(`❌ WebSocket 错误: ${err.message}`);
    });
    
    ws.on('close', (code, reason) => {
      log(`🔌 WebSocket 关闭: ${code} - ${reason}`);
      ws = null;
      
      // 指数退避重连
      reconnectAttempts++;
      const delay = Math.min(30000, 1000 * Math.pow(2, reconnectAttempts));
      log(`🔄 ${delay}ms 后重连 (尝试 #${reconnectAttempts})`);
      
      setTimeout(connectWebSocket, delay);
    });
    
    // 心跳保活
    const heartbeat = setInterval(() => {
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({ 
          message_type: 'ping', 
          timestamp: new Date().toISOString() 
        }));
      } else {
        clearInterval(heartbeat);
      }
    }, 30000);
    
  } catch (e) {
    log(`❌ 连接失败: ${e.message}`);
    setTimeout(connectWebSocket, 5000);
  }
}

// 🔄 备用轮询（WebSocket 失败时使用）
async function fallbackPolling() {
  log('🔄 启动备用轮询模式 (HTTP polling)');
  
  while (true) {
    try {
      const payload = JSON.stringify({
        protocol: 'gep-a2a',
        protocol_version: '1.0.0',
        message_type: 'fetch',
        message_id: `fetch_${Date.now()}`,
        sender_id: CONFIG.nodeId,
        timestamp: new Date().toISOString(),
        payload: { asset_type: 'Capsule', include_tasks: true }
      });
      
      const options = {
        hostname: 'evomap.ai',
        port: 443,
        path: '/a2a/fetch',
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Content-Length': Buffer.byteLength(payload)
        }
      };
      
      const result = await httpRequest(options, payload);
      const tasks = result.data?.payload?.tasks || [];
      const openTasks = tasks.filter(t => 
        t.status === 'open' && !claimedTasks.has(t.task_id)
      );
      
      if (openTasks.length > 0) {
        log(`🎯 轮询发现 ${openTasks.length} 个新任务!`);
        await Promise.all(openTasks.map(t => claimTask(t.task_id, t.title)));
      }
    } catch (e) {
      log(`⚠️ 轮询错误: ${e.message}`);
    }
    
    await sleep(10000);  // 10秒轮询一次作为备用
  }
}

// 🚀 主函数
async function main() {
  log('╔════════════════════════════════════════╗');
  log('║  🎯 Bounty Hunter WebSocket Listener   ║');
  log('║  实时监听 EvoMap 新任务并立即抢单      ║');
  log('╚════════════════════════════════════════╝');
  
  // 检查 WebSocket 模块
  try {
    require('ws');
  } catch (e) {
    log('⚠️ 未安装 ws 模块，使用备用轮询模式');
    log('💡 安装命令: npm install ws');
    return fallbackPolling();
  }
  
  // 尝试 WebSocket 连接
  connectWebSocket();
  
  // 同时启动备用轮询（双重保险）
  setTimeout(() => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      log('⚠️ WebSocket 未连接，启动备用轮询');
      fallbackPolling();
    }
  }, 30000);
}

// 优雅退出
process.on('SIGINT', () => {
  log('👋 收到退出信号，关闭连接...');
  if (ws) ws.close();
  process.exit(0);
});

process.on('SIGTERM', () => {
  log('👋 收到终止信号，关闭连接...');
  if (ws) ws.close();
  process.exit(0);
});

// 启动
if (require.main === module) {
  main().catch(e => {
    log(`💀 致命错误: ${e.message}`);
    process.exit(1);
  });
}

module.exports = { main, claimTask };

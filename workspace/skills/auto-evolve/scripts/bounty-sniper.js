#!/usr/bin/env node
/**
 * Bounty Hunter SNIPER MODE - 极速狙击模式
 * 每2秒扫描一次，发现任务立即认领
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG = {
  nodeId: process.env.NODE_ID || 'hub_0f978bbe1fb5',
  hubUrl: 'evomap.ai',
  scanIntervalMs: 2000,  // 🎯 每2秒扫描一次（秒级响应）
  minMatchScore: 0,      // 🎯 0分也抢（所有任务）
  maxRetries: 10,        // 🎯 疯狂重试
  retryDelayMs: 200,     // 🎯 200ms快速重试
  requestTimeout: 8000,  // 🎯 8秒超时
  quiet: false           // 🎯 输出日志
};

const LOG_FILE = path.join(__dirname, '..', 'events', 'bounty-sniper.log');
const dir = path.dirname(LOG_FILE);
if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_FILE, line);
  if (!CONFIG.quiet) console.log(line.trim());
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function request(options, payload = null) {
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

async function fetchTasks() {
  const payload = JSON.stringify({
    protocol: 'gep-a2a', protocol_version: '1.0.0', message_type: 'fetch',
    message_id: `msg_${Date.now()}`, sender_id: CONFIG.nodeId,
    timestamp: new Date().toISOString(),
    payload: { asset_type: 'Capsule', include_tasks: true }
  });

  const options = {
    hostname: CONFIG.hubUrl, port: 443, path: '/a2a/fetch',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload),
      'User-Agent': 'BountySniper/2.0'
    }
  };

  try {
    const result = await request(options, payload);
    const tasks = result.data?.payload?.tasks || [];
    log(`[Scan] 获取到 ${tasks.length} 个任务`);
    return tasks;
  } catch (e) {
    log(`[Scan] 获取任务失败: ${e.message}`);
    return [];
  }
}

async function claimTask(taskId) {
  const payload = JSON.stringify({ task_id: taskId, node_id: CONFIG.nodeId });
  const options = {
    hostname: CONFIG.hubUrl, port: 443, path: '/task/claim',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload)
    }
  };

  for (let i = 0; i < CONFIG.maxRetries; i++) {
    try {
      const result = await request(options, payload);
      if (result.data?.success || result.data?.task_id) {
        return { success: true, data: result.data };
      }
      if (result.data?.task_full) {
        return { success: false, error: 'task_full' };
      }
    } catch (e) {
      if (i < CONFIG.maxRetries - 1) await sleep(CONFIG.retryDelayMs);
    }
  }
  return { success: false, error: 'max_retries' };
}

// 🎯 主循环：极速狙击
async function sniperLoop() {
  log('🎯 SNIPER MODE ACTIVATED - 2秒极速扫描');
  let claimedCount = 0;
  
  while (true) {
    try {
      const tasks = await fetchTasks();
      const openTasks = tasks.filter(t => t.status === 'open' || !t.status);
      
      if (openTasks.length > 0) {
        log(`发现 ${openTasks.length} 个开放任务！开始抢单...`);
        
        // 🔥 并发抢所有开放任务
        const claims = await Promise.all(
          openTasks.map(async (task) => {
            log(`抢单: ${task.title?.substring(0, 50)}...`);
            const result = await claimTask(task.task_id);
            if (result.success) {
              claimedCount++;
              log(`✅ 抢单成功! [${claimedCount}] Task: ${task.task_id}`);
              return { task, result };
            } else {
              log(`❌ 抢单失败: ${result.error}`);
              return null;
            }
          })
        );
        
        const successful = claims.filter(c => c !== null);
        if (successful.length > 0) {
          log(`🎉 本轮成功抢到 ${successful.length} 个任务！累计: ${claimedCount}`);
        }
      }
    } catch (e) {
      log(`Error: ${e.message}`);
    }
    
    await sleep(CONFIG.scanIntervalMs);
  }
}

// 启动
if (require.main === module) {
  sniperLoop().catch(e => {
    log(`Fatal error: ${e.message}`);
    process.exit(1);
  });
}

module.exports = { sniperLoop };

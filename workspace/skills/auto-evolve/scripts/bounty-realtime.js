#!/usr/bin/env node
/**
 * Bounty Hunter Real-time Listener - 实时监听模式
 * 2秒轮询 + 发现新任务立即抢单
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const CONFIG = {
  nodeId: process.env.NODE_ID || 'hub_0f978bbe1fb5',
  hubUrl: 'evomap.ai',
  pollIntervalMs: 2000,
  fastPollIntervalMs: 500,
  minMatchScore: 0,
  maxRetries: 15,
  retryDelayMs: 50,
  requestTimeout: 3000,
  claimTimeout: 5000,
  autoClaim: true,
  quiet: false
};

const LOG_FILE = path.join(__dirname, '..', 'events', 'bounty-realtime.log');
const CLAIMED_FILE = path.join(__dirname, '..', 'events', 'claimed-tasks.log');
const dir = path.dirname(LOG_FILE);
if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

let lastTaskCount = 0;
let totalClaimed = 0;
let isFastMode = false;

function log(msg) {
  const line = `[${new Date().toISOString()}] ${msg}\n`;
  fs.appendFileSync(LOG_FILE, line);
  if (!CONFIG.quiet) console.log(line.trim());
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

async function request(options, payload = null, timeout = CONFIG.requestTimeout) {
  return new Promise((resolve, reject) => {
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          if (data.startsWith('<!')) reject(new Error('HTML'));
          else resolve({ data: JSON.parse(data), status: res.statusCode });
        } catch (e) {
          reject(new Error('JSON parse error'));
        }
      });
    });
    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
    req.setTimeout(timeout);
    if (payload) req.write(payload);
    req.end();
  });
}

async function fetchTasks() {
  const payload = JSON.stringify({
    protocol: 'gep-a2a',
    protocol_version: '1.0.0',
    message_type: 'fetch',
    message_id: `msg_${Date.now()}_${Math.random().toString(36).substr(2,5)}`,
    sender_id: CONFIG.nodeId,
    timestamp: new Date().toISOString(),
    payload: { asset_type: 'Capsule', include_tasks: true }
  });

  const options = {
    hostname: CONFIG.hubUrl,
    port: 443,
    path: '/a2a/fetch',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload),
      'User-Agent': 'BountyRealTime/3.0'
    }
  };

  try {
    const result = await request(options, payload);
    return result.data?.payload?.tasks || [];
  } catch (e) {
    return [];
  }
}

async function claimTask(taskId, taskTitle) {
  const startTime = Date.now();
  const payload = JSON.stringify({
    task_id: taskId,
    node_id: CONFIG.nodeId,
    claim_code: 'CPGU-P29N',
    timestamp: new Date().toISOString()
  });

  const options = {
    hostname: CONFIG.hubUrl,
    port: 443,
    path: '/task/claim',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Content-Length': Buffer.byteLength(payload),
      'User-Agent': 'BountyRealTime/3.0'
    }
  };

  for (let i = 0; i < CONFIG.maxRetries; i++) {
    try {
      const result = await request(options, payload, CONFIG.claimTimeout);
      const elapsed = Date.now() - startTime;

      if (result.data?.success || result.data?.task_id || result.data?.status === 'claimed') {
        totalClaimed++;
        log(`✅ [${elapsed}ms] 抢单成功! #${totalClaimed} Task: ${taskId}`);
        fs.appendFileSync(CLAIMED_FILE, `[${new Date().toISOString()}] CLAIMED: ${taskId} - ${taskTitle}\n`);
        return { success: true, elapsed };
      }

      if (result.data?.task_full || result.data?.error === 'task_full') {
        return { success: false, error: 'task_full', elapsed };
      }
    } catch (e) {
      if (i < CONFIG.maxRetries - 1) await sleep(CONFIG.retryDelayMs);
    }
  }

  return { success: false, error: 'max_retries' };
}

async function realtimeLoop() {
  log('╔════════════════════════════════════════╗');
  log('║  🎯 REAL-TIME BOUNTY HUNTER            ║');
  log('║  2秒轮询 + 发现新任务立即抢单          ║');
  log('╚════════════════════════════════════════╝');

  while (true) {
    try {
      const startTime = Date.now();
      const tasks = await fetchTasks();
      const openTasks = tasks.filter(t => t.status === 'open' || !t.status);
      const fetchTime = Date.now() - startTime;

      if (openTasks.length > lastTaskCount) {
        const newCount = openTasks.length - lastTaskCount;
        log(`🎯 发现 ${newCount} 个新任务! (总计: ${openTasks.length})`);
        isFastMode = true;

        const results = await Promise.all(
          openTasks.slice(0, newCount).map(t =>
            claimTask(t.task_id, t.title)
          )
        );

        const successCount = results.filter(r => r.success).length;
        if (successCount > 0) {
          log(`🎉 抢到 ${successCount}/${newCount} 个新任务!`);
        }
      }

      lastTaskCount = openTasks.length;

      const interval = isFastMode ? CONFIG.fastPollIntervalMs : CONFIG.pollIntervalMs;
      if (isFastMode && openTasks.length === 0) {
        isFastMode = false;
        log('🔄 退出快速模式，恢复正常轮询');
      }

      await sleep(interval);

    } catch (e) {
      log(`⚠️ 错误: ${e.message}`);
      await sleep(CONFIG.pollIntervalMs);
    }
  }
}

process.on('SIGINT', () => {
  log('👋 退出中... 总抢单数: ' + totalClaimed);
  process.exit(0);
});

process.on('SIGTERM', () => {
  log('👋 终止中... 总抢单数: ' + totalClaimed);
  process.exit(0);
});

if (require.main === module) {
  realtimeLoop().catch(e => {
    log(`💀 致命错误: ${e.message}`);
    process.exit(1);
  });
}

module.exports = { realtimeLoop };

#!/usr/bin/env node
/**
 * Smart Bounty Sniper - 智能赏金猎人
 * 支持多节点分层策略：高信誉节点抢所有任务，零信誉节点抢零门槛任务
 */

const https = require('https');

// 节点分层配置
const HIGH_REPUTATION_NODES = [
  { id: 'hub_0f978bbe1fb5', name: 'DockerHub', reputation: 50, priority: 1 }
];

const ZERO_REP_NODES = [
  { id: 'node_fa6f1ba6ea293146', name: 'Alpha', reputation: 0, priority: 2 },
  { id: 'node_6a28592ba181afb5', name: 'Beta', reputation: 0, priority: 2 },
  { id: 'node_3724c0e0d8cf32eb', name: 'Gamma', reputation: 0, priority: 2 },
  { id: 'node_c4a2794b5fb0c327', name: 'Delta', reputation: 0, priority: 2 },
  { id: 'node_51c2d75b492b1d54', name: 'Epsilon', reputation: 0, priority: 2 },
  { id: 'node_8af28f6549052024', name: 'Zeta', reputation: 0, priority: 2 },
  { id: 'node_5e5316b19e8b64c8', name: 'Eta', reputation: 0, priority: 2 },
  { id: 'node_96f4fae6cc911e2a', name: 'Theta', reputation: 0, priority: 2 },
  { id: 'node_8544558ae8eb9ecd', name: 'Iota', reputation: 0, priority: 2 },
  { id: 'node_3b449d255e543b6c', name: 'Kappa', reputation: 0, priority: 2 }
];

const HUB_URL = 'evomap.ai';
const SCAN_INTERVAL = 500; // 500ms 扫描间隔 (平衡速度和资源)
const CLAIM_RETRY = 20; // 增加重试次数

let stats = {
  totalScans: 0,
  tasksFound: 0,
  tasksClaimed: 0,
  claimFailed: 0,
  errors: 0,
  startTime: Date.now(),
  lastTaskTime: null
};

// 发送 HTTP POST 请求
function postRequest(path, payload) {
  return new Promise((resolve, reject) => {
    const data = JSON.stringify(payload);
    const options = {
      hostname: HUB_URL,
      port: 443,
      path: path,
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': data.length
      },
      timeout: 5000
    };

    const req = https.request(options, (res) => {
      let responseData = '';
      res.on('data', (chunk) => responseData += chunk);
      res.on('end', () => {
        try {
          resolve(JSON.parse(responseData));
        } catch (e) {
          resolve({ error: 'parse_error', raw: responseData });
        }
      });
    });

    req.on('error', (e) => reject(e));
    req.on('timeout', () => {
      req.destroy();
      reject(new Error('timeout'));
    });

    req.write(data);
    req.end();
  });
}

// 生成协议信封
function createEnvelope(messageType, senderId, payload) {
  const timestamp = new Date().toISOString();
  const messageId = `msg_${Date.now()}_${Math.random().toString(36).substr(2, 8)}`;
  
  return {
    protocol: 'gep-a2a',
    protocol_version: '1.0.0',
    message_type: messageType,
    message_id: messageId,
    sender_id: senderId,
    timestamp: timestamp,
    payload: payload
  };
}

// 获取任务列表
async function fetchTasks(node) {
  try {
    const envelope = createEnvelope('fetch', node.id, {
      asset_type: 'Capsule',
      include_tasks: true
    });
    
    const response = await postRequest('/a2a/fetch', envelope);
    const tasks = response.payload?.tasks || [];
    return tasks;
  } catch (e) {
    console.error(`[${node.name}] Fetch failed: ${e.message}`);
    return [];
  }
}

// 抢单 - 使用正确的 /a2a/task/claim 端点 (Evolver 官方方式)
async function claimTask(node, taskId) {
  try {
    // 使用 /a2a/task/claim 端点，与 Evolver 保持一致
    const response = await postRequest('/a2a/task/claim', {
      task_id: taskId,
      node_id: node.id
    });
    
    // 详细的错误日志
    if (response.error) {
      if (response.error === 'rate_limited') {
        return { success: false, error: 'rate_limited', retry_after: response.retry_after_ms };
      }
      return { success: false, error: response.error };
    }
    
    return { success: true, data: response };
  } catch (e) {
    return { success: false, error: 'network_error', message: e.message };
  }
}

// 疯狂重试抢单 - 毫秒级响应
async function claimWithRetry(node, taskId, taskTitle, minRep) {
  // 立即抢单，不等待
  for (let i = 0; i < CLAIM_RETRY; i++) {
    const result = await claimTask(node, taskId);
    
    if (result.success) {
      console.log(`🎉 [${node.name}] 抢单成功: ${taskTitle} (信誉要求: ${minRep})`);
      return true;
    }
    
    if (result.error === 'task_full' || result.error === 'already_claimed') {
      console.log(`❌ [${node.name}] 任务已被抢: ${taskTitle}`);
      return false; // 任务已满，不再重试
    }
    
    if (result.error === 'insufficient_reputation') {
      console.log(`⚠️ [${node.name}] 信誉不足: ${taskTitle} (需要 ${minRep})`);
      return false;
    }
    
    if (result.error === 'rate_limited') {
      const waitMs = result.retry_after || 1000;
      console.log(`⏳ [${node.name}] 被限流，等待 ${waitMs}ms`);
      await new Promise(r => setTimeout(r, waitMs));
      continue; // 限流后继续重试
    }
    
    // 其他错误，极短间隔重试 (10ms)
    await new Promise(r => setTimeout(r, 10));
  }
  
  console.log(`❌ [${node.name}] 抢单失败 ${CLAIM_RETRY} 次: ${taskTitle}`);
  return false;
}

// 高信誉节点扫描循环 - 并发极速抢单
async function highRepScanLoop(node) {
  console.log(`[${node.name}] 🌟 高信誉节点启动 (信誉: ${node.reputation})`);
  
  while (true) {
    try {
      stats.totalScans++;
      
      const tasks = await fetchTasks(node);
      
      if (tasks.length > 0) {
        stats.tasksFound += tasks.length;
        stats.lastTaskTime = new Date().toISOString();
        
        // 高信誉节点抢所有开放任务
        const openTasks = tasks.filter(t => t.status === 'open');
        
        if (openTasks.length > 0) {
          console.log(`[${node.name}] 🔥 发现 ${openTasks.length} 个任务 - 立即抢单!`);
          
          // ⚡ 并发抢所有任务 (不等待)
          const claimPromises = openTasks.map(task => 
            claimWithRetry(node, task.task_id, task.title, task.min_reputation || 0)
              .then(success => {
                if (success) stats.tasksClaimed++;
              })
          );
          
          await Promise.all(claimPromises);
        }
      }
      
      await new Promise(r => setTimeout(r, SCAN_INTERVAL));
      
    } catch (e) {
      stats.errors++;
      console.error(`[${node.name}] 扫描错误: ${e.message}`);
      await new Promise(r => setTimeout(r, SCAN_INTERVAL));
    }
  }
}

// 零信誉节点扫描循环 - 并发极速抢单
async function zeroRepScanLoop(node) {
  console.log(`[${node.name}] 🔰 零信誉节点启动 (信誉: ${node.reputation})`);
  
  while (true) {
    try {
      stats.totalScans++;
      
      const tasks = await fetchTasks(node);
      
      if (tasks.length > 0) {
        // 零信誉节点只抢 min_reputation = 0 的任务
        const zeroRepTasks = tasks.filter(t => 
          t.status === 'open' && 
          (t.min_reputation === 0 || t.min_reputation === undefined || t.min_reputation === null)
        );
        
        if (zeroRepTasks.length > 0) {
          stats.tasksFound += zeroRepTasks.length;
          stats.lastTaskTime = new Date().toISOString();
          
          console.log(`[${node.name}] 💎 发现 ${zeroRepTasks.length} 个零门槛任务 - 立即抢单!`);
          
          // ⚡ 并发抢所有任务 (不等待)
          const claimPromises = zeroRepTasks.map(task => 
            claimWithRetry(node, task.task_id, task.title, 0)
              .then(success => {
                if (success) {
                  stats.tasksClaimed++;
                  console.log(`✨ [${node.name}] 首次完成任务将获得信誉分！`);
                } else {
                  stats.claimFailed++;
                }
              })
          );
          
          await Promise.all(claimPromises);
        }
      }
      
      await new Promise(r => setTimeout(r, SCAN_INTERVAL));
      
    } catch (e) {
      stats.errors++;
      console.error(`[${node.name}] 扫描错误: ${e.message}`);
      await new Promise(r => setTimeout(r, SCAN_INTERVAL));
    }
  }
}

// 打印统计
function printStats() {
  const uptime = Math.floor((Date.now() - stats.startTime) / 1000);
  const hours = Math.floor(uptime / 3600);
  const mins = Math.floor((uptime % 3600) / 60);
  const secs = uptime % 60;
  
  console.log('\n📊 === 智能赏金猎人统计 ===');
  console.log(`⏱️  运行时间: ${hours}h ${mins}m ${secs}s`);
  console.log(`🔍 总扫描: ${stats.totalScans.toLocaleString()}`);
  console.log(`📦 发现任务: ${stats.tasksFound}`);
  console.log(`🎉 抢单成功: ${stats.tasksClaimed}`);
  console.log(`❌ 抢单失败: ${stats.claimFailed}`);
  console.log(`⚠️  错误数: ${stats.errors}`);
  if (stats.lastTaskTime) {
    console.log(`🕐 最后发现任务: ${stats.lastTaskTime}`);
  }
  console.log('========================\n');
}

// 主函数
async function main() {
  console.log('🚀 智能赏金猎人系统启动');
  console.log('');
  console.log('🌟 高信誉节点:');
  HIGH_REPUTATION_NODES.forEach(n => console.log(`   - ${n.name}: ${n.reputation} 信誉分`));
  console.log('');
  console.log('🔰 零信誉节点 (抢零门槛任务):');
  ZERO_REP_NODES.forEach(n => console.log(`   - ${n.name}`));
  console.log('');
  console.log(`扫描间隔: ${SCAN_INTERVAL}ms (⚡ 毫秒级极速)`);
  console.log('');
  
  // 启动所有节点扫描
  const promises = [
    // 高信誉节点 - 抢所有任务
    ...HIGH_REPUTATION_NODES.map(node => highRepScanLoop(node)),
    // 零信誉节点 - 只抢零门槛任务
    ...ZERO_REP_NODES.map(node => zeroRepScanLoop(node))
  ];
  
  // 定期打印统计
  setInterval(printStats, 60000); // 每60秒打印一次
  
  // 等待所有节点
  await Promise.all(promises);
}

// 处理退出信号
process.on('SIGINT', () => {
  console.log('\n👋 收到退出信号，正在关闭...');
  printStats();
  process.exit(0);
});

process.on('SIGTERM', () => {
  console.log('\n👋 收到终止信号，正在关闭...');
  printStats();
  process.exit(0);
});

// 启动
main().catch(e => {
  console.error('系统错误:', e);
  process.exit(1);
});

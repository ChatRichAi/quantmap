#!/usr/bin/env node
/**
 * Multi-Node Bounty Sniper
 * 10节点并发抢单系统
 */

const https = require('https');
const http = require('http');

// 10个节点配置
const NODES = [
  { id: 'node_fa6f1ba6ea293146', name: 'Alpha' },
  { id: 'node_6a28592ba181afb5', name: 'Beta' },
  { id: 'node_3724c0e0d8cf32eb', name: 'Gamma' },
  { id: 'node_c4a2794b5fb0c327', name: 'Delta' },
  { id: 'node_51c2d75b492b1d54', name: 'Epsilon' },
  { id: 'node_8af28f6549052024', name: 'Zeta' },
  { id: 'node_5e5316b19e8b64c8', name: 'Eta' },
  { id: 'node_96f4fae6cc911e2a', name: 'Theta' },
  { id: 'node_8544558ae8eb9ecd', name: 'Iota' },
  { id: 'node_3b449d255e543b6c', name: 'Kappa' }
];

const HUB_URL = 'evomap.ai';
const SCAN_INTERVAL = 500; // 500ms 极速扫描
const CLAIM_RETRY = 10; // 抢单重试次数

let stats = {
  totalScans: 0,
  tasksClaimed: 0,
  errors: 0,
  startTime: Date.now()
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

// 节点发送心跳/hello
async function sendHello(node) {
  try {
    const envelope = createEnvelope('hello', node.id, {
      capabilities: {},
      env_fingerprint: { platform: 'darwin', arch: 'arm64' }
    });
    
    const response = await postRequest('/a2a/hello', envelope);
    console.log(`[${node.name}] Hello: ${response.payload?.status || 'unknown'} | Credits: ${response.payload?.credit_balance ?? '?'}`);
    return response;
  } catch (e) {
    console.error(`[${node.name}] Hello failed: ${e.message}`);
    return null;
  }
}

// 获取任务列表
async function fetchTasks(node) {
  try {
    const envelope = createEnvelope('fetch', node.id, {
      asset_type: 'Capsule',
      include_tasks: true
    });
    
    const response = await postRequest('/a2a/fetch', envelope);
    return response.payload?.tasks || [];
  } catch (e) {
    console.error(`[${node.name}] Fetch failed: ${e.message}`);
    return [];
  }
}

// 抢单
async function claimTask(node, taskId) {
  try {
    const response = await postRequest('/task/claim', {
      task_id: taskId,
      node_id: node.id
    });
    
    if (response.error) {
      return { success: false, error: response.error };
    }
    
    return { success: true, data: response };
  } catch (e) {
    return { success: false, error: e.message };
  }
}

// 疯狂重试抢单
async function claimWithRetry(node, taskId, taskTitle) {
  for (let i = 0; i < CLAIM_RETRY; i++) {
    const result = await claimTask(node, taskId);
    
    if (result.success) {
      console.log(`🎉 [${node.name}] 抢单成功: ${taskTitle} (task_id: ${taskId})`);
      stats.tasksClaimed++;
      return true;
    }
    
    if (result.error === 'task_full') {
      // 任务已满，不再重试
      return false;
    }
    
    // 其他错误，继续重试
    await new Promise(r => setTimeout(r, 50)); // 50ms 间隔重试
  }
  
  return false;
}

// 节点扫描循环
async function nodeScanLoop(node) {
  console.log(`[${node.name}] 节点启动: ${node.id}`);
  
  // 先发送 hello
  await sendHello(node);
  
  while (true) {
    try {
      stats.totalScans++;
      
      // 获取任务
      const tasks = await fetchTasks(node);
      
      if (tasks.length > 0) {
        // 只抢开放的、无最小信誉要求的任务
        const openTasks = tasks.filter(t => 
          t.status === 'open' && 
          (t.min_reputation === 0 || t.min_reputation === undefined)
        );
        
        if (openTasks.length > 0) {
          console.log(`[${node.name}] 发现 ${openTasks.length} 个可抢任务`);
          
          // 并发抢所有开放任务
          const claims = openTasks.map(task => 
            claimWithRetry(node, task.task_id, task.title)
          );
          
          await Promise.all(claims);
        }
      }
      
      // 扫描间隔
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
  const rate = stats.totalScans > 0 ? (stats.tasksClaimed / stats.totalScans * 100).toFixed(4) : 0;
  
  console.log('\n📊 === 统计 ===');
  console.log(`运行时间: ${uptime}s`);
  console.log(`总扫描: ${stats.totalScans}`);
  console.log(`抢单成功: ${stats.tasksClaimed}`);
  console.log(`错误数: ${stats.errors}`);
  console.log(`成功率: ${rate}%`);
  console.log('==============\n');
}

// 主函数
async function main() {
  console.log('🚀 10节点并发赏金猎人系统启动');
  console.log('节点列表:', NODES.map(n => n.name).join(', '));
  console.log(`扫描间隔: ${SCAN_INTERVAL}ms`);
  console.log(`抢单重试: ${CLAIM_RETRY}次`);
  console.log('');
  
  // 启动所有节点扫描
  const nodePromises = NODES.map(node => nodeScanLoop(node));
  
  // 定期打印统计
  setInterval(printStats, 30000); // 每30秒打印一次
  
  // 等待所有节点（实际上不会结束）
  await Promise.all(nodePromises);
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

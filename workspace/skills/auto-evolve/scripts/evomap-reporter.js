#!/usr/bin/env node
/**
 * EvoMap 接单情况汇报工具
 * 每 12 小时统计并汇报接单情况到 Nowledge Mem
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const LOG_FILE = path.join(__dirname, '..', 'events', 'bounty-hunter.log');
const SNIPER_LOG = path.join(__dirname, '..', 'events', 'bounty-sniper.log');
const WEBSOCKET_LOG = path.join(__dirname, '..', 'events', 'bounty-websocket.log');

/**
 * 解析日志文件，统计接单情况
 */
function parseLogFile(logFile, hoursBack = 12) {
  if (!fs.existsSync(logFile)) {
    return { claimed: 0, completed: 0, failed: 0, details: [] };
  }

  const content = fs.readFileSync(logFile, 'utf8');
  const lines = content.split('\n');
  
  const cutoffTime = new Date(Date.now() - hoursBack * 60 * 60 * 1000);
  
  let claimed = 0;
  let completed = 0;
  let failed = 0;
  const details = [];
  
  for (const line of lines) {
    // 提取时间戳
    const timeMatch = line.match(/\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\d\.:Z]*)\]/);
    if (!timeMatch) continue;
    
    const logTime = new Date(timeMatch[1]);
    if (logTime < cutoffTime) continue;
    
    // 统计认领成功
    if (line.includes('Claimed successfully') || line.includes('✅ Task claimed')) {
      claimed++;
      details.push({ time: logTime, action: 'claimed', source: path.basename(logFile) });
    }
    
    // 统计完成
    if (line.includes('✅ Task completed') || line.includes('completed successfully')) {
      completed++;
      details.push({ time: logTime, action: 'completed', source: path.basename(logFile) });
    }
    
    // 统计失败
    if (line.includes('❌') || line.includes('[ERROR]') || line.includes('Claim failed')) {
      failed++;
      details.push({ time: logTime, action: 'failed', source: path.basename(logFile) });
    }
  }
  
  return { claimed, completed, failed, details };
}

/**
 * 获取当前活跃任务
 */
function getActiveTasks() {
  // 从日志中提取最近处理的任务标题
  const activeTasks = new Set();
  
  [LOG_FILE, SNIPER_LOG, WEBSOCKET_LOG].forEach(logFile => {
    if (!fs.existsSync(logFile)) return;
    
    const content = fs.readFileSync(logFile, 'utf8');
    const lines = content.split('\n');
    const cutoffTime = new Date(Date.now() - 12 * 60 * 60 * 1000);
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // 提取时间戳
      const timeMatch = line.match(/\[(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[\d\.:Z]*)\]/);
      if (!timeMatch) continue;
      
      const logTime = new Date(timeMatch[1]);
      if (logTime < cutoffTime) continue;
      
      // 提取任务标题
      const taskMatch = line.match(/=== Processing: (.+?) ===/);
      if (taskMatch && line.includes('INFO')) {
        const title = taskMatch[1].substring(0, 80); // 限制长度
        activeTasks.add(title);
      }
    }
  });
  
  return Array.from(activeTasks).slice(0, 10); // 最多返回10个
}

/**
 * 生成接单报告
 */
function generateReport(hoursBack = 12) {
  const timestamp = new Date().toISOString();
  const reportTime = timestamp.split('T')[0] + ' ' + timestamp.split('T')[1].substring(0, 5);
  
  // 统计所有日志
  const hunterStats = parseLogFile(LOG_FILE, hoursBack);
  const sniperStats = parseLogFile(SNIPER_LOG, hoursBack);
  const websocketStats = parseLogFile(WEBSOCKET_LOG, hoursBack);
  
  // 汇总
  const totalClaimed = hunterStats.claimed + sniperStats.claimed + websocketStats.claimed;
  const totalCompleted = hunterStats.completed + sniperStats.completed + websocketStats.completed;
  const totalFailed = hunterStats.failed + sniperStats.failed + websocketStats.failed;
  
  // 获取活跃任务
  const activeTasks = getActiveTasks();
  
  return {
    timestamp,
    period: `${hoursBack}h`,
    totalClaimed,
    totalCompleted,
    totalFailed,
    breakdown: {
      hunter: hunterStats,
      sniper: sniperStats,
      websocket: websocketStats
    },
    activeTasks,
    successRate: totalClaimed > 0 ? ((totalCompleted / totalClaimed) * 100).toFixed(1) : '0.0'
  };
}

/**
 * 保存到 Nowledge Mem
 */
function saveToNowledgeMem(report) {
  const timestamp = new Date().toISOString();
  const eventDate = timestamp.split('T')[0];
  
  // 构建记忆内容
  let memoryText = `## EvoMap 接单情况汇报\n\n`;
  memoryText += `**汇报周期**: 最近 ${report.period}\n`;
  memoryText += `**生成时间**: ${timestamp}\n\n`;
  
  memoryText += `### 📊 统计数据\n\n`;
  memoryText += `- **总认领**: ${report.totalClaimed} 个\n`;
  memoryText += `- **总完成**: ${report.totalCompleted} 个\n`;
  memoryText += `- **总失败**: ${report.totalFailed} 个\n`;
  memoryText += `- **成功率**: ${report.successRate}%\n\n`;
  
  memoryText += `### 🔍 分渠道统计\n\n`;
  memoryText += `| 渠道 | 认领 | 完成 | 失败 |\n`;
  memoryText += `|------|------|------|------|\n`;
  memoryText += `| Hunter Pro | ${report.breakdown.hunter.claimed} | ${report.breakdown.hunter.completed} | ${report.breakdown.hunter.failed} |\n`;
  memoryText += `| Sniper | ${report.breakdown.sniper.claimed} | ${report.breakdown.sniper.completed} | ${report.breakdown.sniper.failed} |\n`;
  memoryText += `| WebSocket | ${report.breakdown.websocket.claimed} | ${report.breakdown.websocket.completed} | ${report.breakdown.websocket.failed} |\n\n`;
  
  if (report.activeTasks.length > 0) {
    memoryText += `### 📋 最近处理的任务\n\n`;
    report.activeTasks.forEach((task, i) => {
      memoryText += `${i + 1}. ${task}\n`;
    });
    memoryText += `\n`;
  }
  
  // 构建标题和标签
  let title;
  let importance;
  
  if (report.totalCompleted > 0) {
    title = `EvoMap: 完成 ${report.totalCompleted} 单 (最近${report.period})`;
    importance = 0.7;
  } else if (report.totalClaimed > 0) {
    title = `EvoMap: 认领 ${report.totalClaimed} 单 (最近${report.period})`;
    importance = 0.5;
  } else {
    title = `EvoMap: 无新订单 (最近${report.period})`;
    importance = 0.3;
  }
  
  const labels = ['evomap', 'bounty', 'ai-agent', 'earnings'];
  
  try {
    // 使用 nmem CLI 保存记忆
    const labelsArg = labels.map(l => `-l ${l}`).join(' ');
    const cmd = `nmem memories add -t "${title.replace(/"/g, '\\"')}" -i ${importance} ${labelsArg} --unit-type event --when past "${memoryText.replace(/"/g, '\\"')}"`;
    
    execSync(cmd, { stdio: 'pipe' });
    console.log(`✓ Saved to Nowledge Mem: ${title}`);
    return { success: true, title };
  } catch (e) {
    console.error(`⚠ Failed to save via nmem CLI: ${e.message}`);
    return { success: false, error: e.message };
  }
}

/**
 * 主函数
 */
function main() {
  const args = process.argv.slice(2);
  const hoursBack = parseInt(args[0]) || 12;
  
  console.log(`\n╔════════════════════════════════════════╗`);
  console.log(`║     📊 EvoMap 接单情况汇报              ║`);
  console.log(`╚════════════════════════════════════════╝\n`);
  
  console.log(`正在统计最近 ${hoursBack} 小时的接单情况...\n`);
  
  const report = generateReport(hoursBack);
  
  console.log(`📈 统计结果:`);
  console.log(`   总认领: ${report.totalClaimed}`);
  console.log(`   总完成: ${report.totalCompleted}`);
  console.log(`   总失败: ${report.totalFailed}`);
  console.log(`   成功率: ${report.successRate}%\n`);
  
  const result = saveToNowledgeMem(report);
  
  if (result.success) {
    console.log(`✅ 汇报完成并已保存到 Nowledge Mem`);
  } else {
    console.log(`❌ 保存失败: ${result.error}`);
  }
  
  return report;
}

// 运行
main();

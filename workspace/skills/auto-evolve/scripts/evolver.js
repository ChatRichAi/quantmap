#!/usr/bin/env node
/**
 * Evolver - 主进化循环
 * 全自动错误捕获 → Gene匹配 → 自动修复 → 验证 → 发布
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const errorCapture = require('./error-capture');
const geneMatcher = require('./gene-matcher');
const autoFix = require('./auto-fix');
const publish = require('./publish');

const EVENTS_DIR = path.join(__dirname, '..', 'events');
const LOG_FILE = path.join(EVENTS_DIR, 'evolver.log');

// 确保日志目录存在
if (!fs.existsSync(EVENTS_DIR)) fs.mkdirSync(EVENTS_DIR, { recursive: true });

/**
 * 日志记录
 */
function log(message) {
  const timestamp = new Date().toISOString();
  const line = `[${timestamp}] ${message}\n`;
  console.log(line.trim());
  fs.appendFileSync(LOG_FILE, line);
}

/**
 * 单次进化循环
 * @returns {Promise<Object>} 循环结果
 */
async function evolutionCycle() {
  log('=== Starting Evolution Cycle ===');
  
  const cycleResult = {
    timestamp: new Date().toISOString(),
    errors_found: 0,
    genes_matched: 0,
    fixes_applied: 0,
    fixes_successful: 0,
    capsules_published: 0,
    details: []
  };
  
  try {
    // Step 1: 获取最近的失败事件
    const recentFailures = errorCapture.getRecentFailures(60); // 最近1小时
    log(`Found ${recentFailures.length} recent failures`);
    cycleResult.errors_found = recentFailures.length;
    
    if (recentFailures.length === 0) {
      log('No errors to fix, cycle complete');
      saveToNowledgeMem(cycleResult);
      return cycleResult;
    }
    
    // 处理每个错误（去重后）
    const processedHashes = new Set();
    
    for (const error of recentFailures) {
      // 去重检查
      if (processedHashes.has(error.hash)) {
        log(`Skipping duplicate error: ${error.hash}`);
        continue;
      }
      processedHashes.add(error.hash);
      
      log(`\nProcessing error: ${error.signals.join(', ')} (${error.hash})`);
      
      const stepResult = {
        error_hash: error.hash,
        signals: error.signals,
        steps: {}
      };
      
      // Step 2: 匹配 Gene
      log('  → Matching genes...');
      const matchResult = await geneMatcher.matchGene(error.signals);
      stepResult.steps.gene_match = matchResult;
      
      if (!matchResult.found) {
        log('  ✗ No matching gene found');
        cycleResult.details.push(stepResult);
        continue;
      }
      
      cycleResult.genes_matched++;
      log(`  ✓ Matched gene: ${matchResult.gene.asset_id}`);
      
      // Step 3: 应用修复
      log('  → Applying fix...');
      const fixContext = {
        ...error.context,
        command: error.context.command,
        cwd: error.context.cwd,
        error_text: error.error_text
      };
      
      const fixResult = await autoFix.applyFix(matchResult.gene, fixContext);
      stepResult.steps.fix_application = fixResult;
      cycleResult.fixes_applied++;
      
      log(`  ${fixResult.success ? '✓' : '✗'} Fix ${fixResult.success ? 'succeeded' : 'failed'} (${fixResult.duration_ms}ms)`);
      
      // Step 4: 验证修复
      log('  → Validating fix...');
      const validation = await autoFix.validateFix(fixResult);
      stepResult.steps.validation = validation;
      
      log(`  ${validation.valid ? '✓' : '✗'} Validation ${validation.valid ? 'passed' : 'failed'}`);
      
      // Step 5: 更新连胜记录
      const streak = autoFix.updateSuccessStreak(fixResult.success && validation.valid);
      log(`  → Success streak: ${streak}`);
      
      // Step 6: 发布 Capsule（如果成功且通过验证）
      if (fixResult.success && validation.valid) {
        cycleResult.fixes_successful++;
        
        // 检查是否应该发布（去重）
        if (publish.shouldPublish(error.hash)) {
          log('  → Publishing capsule...');
          
          try {
            const publishResult = await publish.publishCapsule(fixResult, error);
            stepResult.steps.publication = publishResult;
            cycleResult.capsules_published++;
            
            log(`  ✓ Published! Gene: ${publishResult.gene_id.substring(0, 20)}...`);
          } catch (e) {
            log(`  ✗ Publication failed: ${e.message}`);
            stepResult.steps.publication = { success: false, error: e.message };
          }
        } else {
          log('  → Skipping publication (duplicate)');
        }
      }
      
      cycleResult.details.push(stepResult);
    }
    
    log(`\n=== Cycle Complete ===`);
    log(`Errors: ${cycleResult.errors_found}, Genes: ${cycleResult.genes_matched}, ` +
        `Fixes: ${cycleResult.fixes_applied}, Success: ${cycleResult.fixes_successful}, ` +
        `Published: ${cycleResult.capsules_published}`);
    
    // 保存到 Nowledge Mem
    saveToNowledgeMem(cycleResult);
    
    return cycleResult;
    
  } catch (e) {
    log(`ERROR in evolution cycle: ${e.message}`);
    log(e.stack);
    cycleResult.error = e.message;
    return cycleResult;
  }
}

/**
 * 持续循环模式
 */
async function loopMode(intervalMinutes = 5) {
  log('╔════════════════════════════════════╗');
  log('║  Auto-Evolve System Started        ║');
  log('║  Loop mode: checking every 5 min   ║');
  log('╚════════════════════════════════════╝');
  
  // 初始化
  geneMatcher.initLocalGeneLibrary();
  
  while (true) {
    try {
      await evolutionCycle();
    } catch (e) {
      log(`Unexpected error: ${e.message}`);
    }
    
    log(`\nWaiting ${intervalMinutes} minutes until next cycle...\n`);
    await sleep(intervalMinutes * 60 * 1000);
  }
}

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 保存进化事件到 Nowledge Mem
 * @param {Object} cycleResult - 进化循环结果
 */
function saveToNowledgeMem(cycleResult) {
  const timestamp = new Date().toISOString();
  const eventDate = timestamp.split('T')[0]; // YYYY-MM-DD
  
  // 构建记忆内容
  let memoryText = `## Auto-Evolve 进化事件\n\n`;
  memoryText += `**时间**: ${timestamp}\n`;
  memoryText += `**错误发现**: ${cycleResult.errors_found} 个\n`;
  memoryText += `**Gene 匹配**: ${cycleResult.genes_matched} 个\n`;
  memoryText += `**修复应用**: ${cycleResult.fixes_applied} 个\n`;
  memoryText += `**修复成功**: ${cycleResult.fixes_successful} 个\n`;
  memoryText += `**Capsule 发布**: ${cycleResult.capsules_published} 个\n\n`;
  
  // 添加详细修复信息（如果有）
  if (cycleResult.details && cycleResult.details.length > 0) {
    memoryText += `### 修复详情\n\n`;
    for (const detail of cycleResult.details) {
      memoryText += `- **错误信号**: ${detail.signals?.join(', ') || 'N/A'}\n`;
      
      if (detail.steps?.gene_match?.found) {
        memoryText += `  - Gene: ${detail.steps.gene_match.gene.asset_id}\n`;
      }
      
      if (detail.steps?.fix_application) {
        memoryText += `  - 修复结果: ${detail.steps.fix_application.success ? '✅ 成功' : '❌ 失败'}\n`;
      }
      
      if (detail.steps?.validation) {
        memoryText += `  - 验证结果: ${detail.steps.validation.valid ? '✅ 通过' : '❌ 失败'}\n`;
      }
      
      if (detail.steps?.publication?.success) {
        memoryText += `  - Capsule 发布: ✅ 已发布\n`;
      }
      
      memoryText += `\n`;
    }
  } else if (cycleResult.errors_found === 0) {
    memoryText += `*系统运行正常，未检测到需要修复的错误。*\n`;
  }
  
  // 构建 nmem 命令
  let title;
  let unitType;
  let importance;
  
  if (cycleResult.fixes_successful > 0) {
    title = `Auto-Evolve: ${cycleResult.fixes_successful} 个修复成功 (${eventDate})`;
    unitType = 'event';
    importance = 0.7;
  } else if (cycleResult.errors_found > 0) {
    title = `Auto-Evolve: 检测到 ${cycleResult.errors_found} 个错误 (${eventDate})`;
    unitType = 'context';
    importance = 0.5;
  } else {
    title = `Auto-Evolve: 常规检查完成 (${eventDate})`;
    unitType = 'context';
    importance = 0.3;
  }
  
  const labels = ['auto-evolve', 'ai-evolution', 'self-healing'];
  
  try {
    // 使用 nmem CLI 保存记忆
    // nmem memories add [-t TITLE] [-i IMPORTANCE] [-l LABELS] content
    const labelsArg = labels.map(l => `-l ${l}`).join(' ');
    const cmd = `nmem memories add -t "${title.replace(/"/g, '\\"')}" -i ${importance} ${labelsArg} --unit-type ${unitType} --when past "${memoryText.replace(/"/g, '\\"')}"`;
    
    execSync(cmd, { stdio: 'pipe' });
    log(`✓ Saved to Nowledge Mem: ${title}`);
  } catch (e) {
    // nmem 可能不可用，尝试备用方法：写入本地文件
    log(`⚠ Failed to save via nmem CLI: ${e.message}`);
    
    // 备用：保存到本地 events 目录
    const memoryFile = path.join(EVENTS_DIR, `memory-${eventDate}.md`);
    const entry = `\n---\n\n${memoryText}\n`;
    fs.appendFileSync(memoryFile, entry);
    log(`✓ Saved to local file: ${memoryFile}`);
  }
}

/**
 * 显示统计信息
 */
function showStats() {
  console.log('\n╔════════════════════════════════════╗');
  console.log('║       Auto-Evolve Statistics       ║');
  console.log('╚════════════════════════════════════╝\n');
  
  // 成功连胜
  const streak = autoFix.getSuccessStreak();
  console.log(`🎯 Success Streak: ${streak}`);
  
  // 最近失败数
  const failures = errorCapture.getRecentFailures(60 * 24); // 24小时
  console.log(`📉 Recent Failures (24h): ${failures.length}`);
  
  // 已发布的 Capsule
  const publishedDir = path.join(EVENTS_DIR, 'published');
  if (fs.existsSync(publishedDir)) {
    const published = fs.readdirSync(publishedDir).filter(f => f.endsWith('.json'));
    console.log(`📦 Total Capsules Published: ${published.length}`);
  }
  
  // 本地 Gene 库
  const genesDir = path.join(__dirname, '..', 'genes');
  if (fs.existsSync(genesDir)) {
    const genes = fs.readdirSync(genesDir).filter(f => f.endsWith('.json'));
    console.log(`🧬 Local Genes: ${genes.length}`);
  }
  
  console.log('\n═════════════════════════════════════\n');
}

// 主函数
async function main() {
  const args = process.argv.slice(2);
  const mode = args[0] || '--help';
  
  switch (mode) {
    case '--loop':
      await loopMode(5);
      break;
      
    case '--once':
      await evolutionCycle();
      break;
      
    case '--stats':
      showStats();
      break;
      
    case '--test':
      // 测试模式：创建一个测试错误并处理
      console.log('Running test mode...');
      const testError = errorCapture.captureError(
        new Error('Command failed: jq\n/bin/sh: jq: command not found'),
        { tool: 'exec', command: 'jq --version' }
      );
      console.log('Captured test error:', testError);
      
      const match = await geneMatcher.matchGene(testError.signals);
      console.log('Match result:', match.found ? `Found ${match.gene.asset_id}` : 'Not found');
      break;
      
    case '--help':
    default:
      console.log(`
Auto-Evolve System - 全自动 AI 代理进化

Usage:
  node evolver.js [option]

Options:
  --loop     持续循环模式（每5分钟检查一次）
  --once     单次运行模式
  --stats    显示统计信息
  --test     测试模式（创建测试错误）
  --help     显示帮助

Examples:
  node evolver.js --once     # 运行一次进化循环
  node evolver.js --loop     # 启动持续监控
  node evolver.js --stats    # 查看统计数据
`);
  }
}

// 运行主函数
main().catch(console.error);

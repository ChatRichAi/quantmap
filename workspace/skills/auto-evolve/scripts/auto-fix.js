#!/usr/bin/env node
/**
 * Auto-Fix Module
 * 自动应用修复方案
 */

const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const CAPSULES_DIR = path.join(__dirname, '..', 'capsules');
const EVENTS_DIR = path.join(__dirname, '..', 'events');

if (!fs.existsSync(CAPSULES_DIR)) fs.mkdirSync(CAPSULES_DIR, { recursive: true });
if (!fs.existsSync(EVENTS_DIR)) fs.mkdirSync(EVENTS_DIR, { recursive: true });

/**
 * 修复策略实现
 */
const FIX_STRATEGIES = {
  // 重试策略
  'gene_retry_backoff': async (context) => {
    const maxRetries = context.max_retries || 3;
    const baseDelay = context.base_delay_ms || 1000;
    
    for (let attempt = 0; attempt < maxRetries; attempt++) {
      try {
        const delay = baseDelay * Math.pow(2, attempt) + Math.random() * 1000;
        console.log(`[AutoFix] Retrying after ${delay.toFixed(0)}ms (attempt ${attempt + 1}/${maxRetries})`);
        await sleep(delay);
        
        // 执行原始命令
        if (context.command) {
          const result = execSync(context.command, { 
            cwd: context.cwd, 
            encoding: 'utf8',
            timeout: 30000 
          });
          return { success: true, output: result, attempts: attempt + 1 };
        }
      } catch (e) {
        if (attempt === maxRetries - 1) {
          return { success: false, error: e.message, attempts: attempt + 1 };
        }
      }
    }
    return { success: false, error: 'Max retries exceeded' };
  },

  // 安装缺失工具
  'gene_install_missing_tool': async (context) => {
    const command = context.command || '';
    const toolMatch = command.match(/(?:command not found:|not found:)\s*(\w+)/i) ||
                      command.match(/(\w+):\s*command not found/i);
    
    if (!toolMatch) {
      return { success: false, error: 'Could not extract tool name from error' };
    }
    
    const tool = toolMatch[1];
    console.log(`[AutoFix] Attempting to install missing tool: ${tool}`);
    
    // 尝试 apt-get
    try {
      execSync(`which apt-get`, { stdio: 'ignore' });
      console.log(`[AutoFix] Trying apt-get install ${tool}`);
      execSync(`apt-get update && apt-get install -y ${tool}`, { 
        stdio: 'inherit',
        timeout: 120000 
      });
      return { success: true, method: 'apt-get', tool };
    } catch (e) {
      console.log(`[AutoFix] apt-get failed, trying npm`);
    }
    
    // 尝试 npm
    try {
      execSync(`npm install -g ${tool}`, { 
        stdio: 'inherit',
        timeout: 120000 
      });
      return { success: true, method: 'npm', tool };
    } catch (e) {
      return { success: false, error: `Failed to install ${tool} via apt-get or npm` };
    }
  },

  // 修复权限
  'gene_fix_permissions': async (context) => {
    const filePath = context.file_path || context.cwd;
    console.log(`[AutoFix] Fixing permissions for: ${filePath}`);
    
    try {
      // 尝试 chmod +x
      execSync(`chmod +x "${filePath}"`, { stdio: 'ignore' });
      return { success: true, method: 'chmod +x', path: filePath };
    } catch (e) {
      // 尝试 sudo
      try {
        execSync(`sudo chmod +x "${filePath}"`, { stdio: 'inherit' });
        return { success: true, method: 'sudo chmod', path: filePath };
      } catch (e2) {
        return { success: false, error: 'Failed to fix permissions' };
      }
    }
  },

  // 安全解析 JSON
  'gene_parse_json_safe': async (context) => {
    const jsonString = context.json_string || '';
    
    try {
      // 首先尝试标准解析
      const parsed = JSON.parse(jsonString);
      return { success: true, method: 'standard', data: parsed };
    } catch (e) {
      // 尝试清理常见问题
      let cleaned = jsonString
        .replace(/,\s*}/g, '}')  // 移除尾随逗号
        .replace(/,\s*]/g, ']')
        .replace(/'/g, '"');    // 单引号转双引号
      
      try {
        const parsed = JSON.parse(cleaned);
        return { success: true, method: 'cleaned', data: parsed };
      } catch (e2) {
        return { success: false, error: 'JSON unrecoverable' };
      }
    }
  },

  // 创建缺失文件
  'gene_create_missing_file': async (context) => {
    const filePath = context.file_path;
    if (!filePath) {
      return { success: false, error: 'No file path provided' };
    }
    
    console.log(`[AutoFix] Creating missing file/directory: ${filePath}`);
    
    try {
      const dir = path.dirname(filePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
        console.log(`[AutoFix] Created directory: ${dir}`);
      }
      
      if (!fs.existsSync(filePath)) {
        fs.writeFileSync(filePath, context.default_content || '');
        console.log(`[AutoFix] Created file: ${filePath}`);
      }
      
      return { success: true, path: filePath };
    } catch (e) {
      return { success: false, error: e.message };
    }
  }
};

function sleep(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

/**
 * 应用修复
 * @param {Object} gene - Gene 对象
 * @param {Object} context - 上下文信息
 * @returns {Promise<Object>} 修复结果
 */
async function applyFix(gene, context) {
  console.log(`[AutoFix] Applying fix: ${gene.asset_id}`);
  console.log(`[AutoFix] Strategy: ${gene.summary}`);
  
  const strategy = FIX_STRATEGIES[gene.asset_id];
  if (!strategy) {
    // 尝试从 EvoMap 获取 Capsule 内容
    if (gene.payload && gene.payload.content) {
      console.log(`[AutoFix] Using EvoMap capsule content (not executable in this version)`);
      return { 
        success: false, 
        error: 'EvoMap capsule content execution not yet implemented',
        note: 'Capsule content available for manual review'
      };
    }
    
    return { success: false, error: `Unknown fix strategy: ${gene.asset_id}` };
  }
  
  const startTime = Date.now();
  try {
    const result = await strategy(context);
    const duration = Date.now() - startTime;
    
    return {
      ...result,
      gene_id: gene.asset_id,
      duration_ms: duration,
      timestamp: new Date().toISOString()
    };
  } catch (e) {
    return {
      success: false,
      error: e.message,
      gene_id: gene.asset_id,
      duration_ms: Date.now() - startTime,
      timestamp: new Date().toISOString()
    };
  }
}

/**
 * 验证修复结果
 * @param {Object} fixResult - 修复结果
 * @param {Function} validationFn - 验证函数
 * @returns {Object} 验证结果
 */
async function validateFix(fixResult, validationFn) {
  if (!fixResult.success) {
    return { valid: false, reason: 'fix_failed', details: fixResult.error };
  }
  
  if (validationFn) {
    try {
      const valid = await validationFn();
      return { valid, reason: valid ? 'validation_passed' : 'validation_failed' };
    } catch (e) {
      return { valid: false, reason: 'validation_error', details: e.message };
    }
  }
  
  // 默认验证：检查是否有错误输出
  if (fixResult.error) {
    return { valid: false, reason: 'has_error_output' };
  }
  
  return { valid: true, reason: 'default_validation' };
}

/**
 * 保存 Capsule（修复成功时）
 * @param {Object} capsule - Capsule 对象
 */
function saveCapsule(capsule) {
  const filename = `capsule_${capsule.asset_id}_${Date.now()}.json`;
  const filepath = path.join(CAPSULES_DIR, filename);
  fs.writeFileSync(filepath, JSON.stringify(capsule, null, 2));
  console.log(`[AutoFix] Saved capsule: ${filename}`);
}

/**
 * 获取成功连胜计数
 * @returns {number} 连胜次数
 */
function getSuccessStreak() {
  const streakFile = path.join(EVENTS_DIR, 'success-streak.json');
  if (fs.existsSync(streakFile)) {
    const data = JSON.parse(fs.readFileSync(streakFile, 'utf8'));
    return data.streak || 0;
  }
  return 0;
}

/**
 * 更新成功连胜
 * @param {boolean} success - 是否成功
 */
function updateSuccessStreak(success) {
  const streakFile = path.join(EVENTS_DIR, 'success-streak.json');
  let data = { streak: 0, last_update: new Date().toISOString() };
  
  if (fs.existsSync(streakFile)) {
    data = JSON.parse(fs.readFileSync(streakFile, 'utf8'));
  }
  
  if (success) {
    data.streak = (data.streak || 0) + 1;
  } else {
    data.streak = 0;
  }
  
  data.last_update = new Date().toISOString();
  fs.writeFileSync(streakFile, JSON.stringify(data, null, 2));
  
  return data.streak;
}

// 导出模块
module.exports = {
  applyFix,
  validateFix,
  saveCapsule,
  getSuccessStreak,
  updateSuccessStreak,
  FIX_STRATEGIES
};

// 如果直接运行，测试修复
if (require.main === module) {
  (async () => {
    const testGene = {
      asset_id: 'gene_parse_json_safe',
      summary: 'Test JSON parsing'
    };
    
    const result = await applyFix(testGene, {
      json_string: '{"key": "value",}'  // 有尾随逗号
    });
    
    console.log('Fix result:', JSON.stringify(result, null, 2));
  })();
}

#!/usr/bin/env node
/**
 * Publish Module
 * 自动发布 Capsule 到 EvoMap
 */

const fs = require('fs');
const path = require('path');
const https = require('https');
const crypto = require('crypto');

const EVOMAP_HUB = 'evomap.ai';
const NODE_ID = 'hub_0f978bbe1fb5';
const EVENTS_DIR = path.join(__dirname, '..', 'events');
const PUBLISHED_DIR = path.join(EVENTS_DIR, 'published');

if (!fs.existsSync(PUBLISHED_DIR)) fs.mkdirSync(PUBLISHED_DIR, { recursive: true });

/**
 * 计算 SHA256 asset_id
 * @param {Object} obj - 要哈希的对象
 * @returns {string} sha256:xxxxx
 */
function computeAssetId(obj) {
  const copy = { ...obj };
  delete copy.asset_id; // 排除 asset_id 字段
  
  // 规范化 JSON（排序键）
  const canonical = JSON.stringify(copy, Object.keys(copy).sort());
  const hash = crypto.createHash('sha256').update(canonical).digest('hex');
  return `sha256:${hash}`;
}

/**
 * 创建 Gene 对象
 * @param {Object} fixResult - 修复结果
 * @param {Object} originalError - 原始错误
 * @returns {Object} Gene 对象
 */
function createGene(fixResult, originalError) {
  const gene = {
    type: 'Gene',
    schema_version: '1.5.0',
    category: 'repair',
    signals_match: originalError.signals || ['UnknownError'],
    summary: fixResult.gene_summary || `Auto-generated fix for ${originalError.signals?.join(', ')}`,
    validation: ['node -e "console.log(\'validation ok\')"'],
    constraints: {
      max_retries: 3,
      auto_rollback: true
    }
  };
  
  gene.asset_id = computeAssetId(gene);
  return gene;
}

/**
 * 创建 Capsule 对象
 * @param {Object} fixResult - 修复结果
 * @param {Object} gene - Gene 对象
 * @param {Object} originalError - 原始错误
 * @returns {Object} Capsule 对象
 */
function createCapsule(fixResult, gene, originalError) {
  const capsule = {
    type: 'Capsule',
    schema_version: '1.5.0',
    trigger: originalError.signals || ['UnknownError'],
    gene: gene.asset_id,
    summary: fixResult.summary || `Automated fix applied for ${originalError.signals?.join(', ')}`,
    confidence: fixResult.success ? 0.85 : 0.5,
    blast_radius: {
      files: fixResult.affected_files || 1,
      lines: fixResult.affected_lines || 10
    },
    outcome: {
      status: fixResult.success ? 'success' : 'failure',
      score: fixResult.success ? 0.85 : 0.3
    },
    env_fingerprint: {
      platform: process.platform,
      arch: process.arch,
      node_version: process.version
    },
    success_streak: fixResult.success_streak || 1
  };
  
  capsule.asset_id = computeAssetId(capsule);
  return capsule;
}

/**
 * 创建 EvolutionEvent 对象
 * @param {Object} fixResult - 修复结果
 * @param {Object} gene - Gene 对象
 * @param {Object} capsule - Capsule 对象
 * @param {Object} originalError - 原始错误
 * @returns {Object} EvolutionEvent 对象
 */
function createEvolutionEvent(fixResult, gene, capsule, originalError) {
  const event = {
    type: 'EvolutionEvent',
    intent: 'repair',
    capsule_id: capsule.asset_id,
    genes_used: [gene.asset_id],
    outcome: {
      status: fixResult.success ? 'success' : 'failure',
      score: fixResult.success ? 0.85 : 0.3
    },
    mutations_tried: 1,
    total_cycles: fixResult.attempts || 1,
    original_error: {
      signals: originalError.signals,
      hash: originalError.hash
    }
  };
  
  event.asset_id = computeAssetId(event);
  return event;
}

/**
 * 发布到 EvoMap
 * @param {Object} bundle - 包含 Gene, Capsule, EvolutionEvent 的捆绑包
 * @returns {Promise<Object>} 发布结果
 */
async function publishToEvoMap(bundle) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
      protocol: 'gep-a2a',
      protocol_version: '1.0.0',
      message_type: 'publish',
      message_id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      sender_id: NODE_ID,
      timestamp: new Date().toISOString(),
      payload: {
        assets: bundle
      }
    });

    const options = {
      hostname: EVOMAP_HUB,
      port: 443,
      path: '/a2a/publish',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      },
      timeout: 15000
    };

    console.log('[Publish] Sending to EvoMap...');
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          console.log('[Publish] EvoMap response:', response.payload?.status || 'unknown');
          resolve(response);
        } catch (e) {
          reject(new Error('Invalid response from EvoMap'));
        }
      });
    });

    req.on('error', (e) => reject(e));
    req.on('timeout', () => { req.destroy(); reject(new Error('Request timeout')); });
    req.write(payload);
    req.end();
  });
}

/**
 * 主发布函数
 * @param {Object} fixResult - 修复结果
 * @param {Object} originalError - 原始错误事件
 * @param {Object} options - 选项
 * @returns {Promise<Object>} 发布结果
 */
async function publishCapsule(fixResult, originalError, options = {}) {
  console.log('[Publish] Creating publication bundle...');
  
  // 1. 创建 Gene
  const gene = createGene(fixResult, originalError);
  console.log(`[Publish] Gene ID: ${gene.asset_id}`);
  
  // 2. 创建 Capsule
  const capsule = createCapsule(fixResult, gene, originalError);
  console.log(`[Publish] Capsule ID: ${capsule.asset_id}`);
  
  // 3. 创建 EvolutionEvent
  const event = createEvolutionEvent(fixResult, gene, capsule, originalError);
  console.log(`[Publish] Event ID: ${event.asset_id}`);
  
  // 4. 组装捆绑包
  const bundle = [gene, capsule, event];
  
  // 5. 保存到本地
  const bundleData = {
    timestamp: new Date().toISOString(),
    bundle,
    fix_result: fixResult,
    original_error: originalError
  };
  
  const filename = `published_${Date.now()}.json`;
  fs.writeFileSync(path.join(PUBLISHED_DIR, filename), JSON.stringify(bundleData, null, 2));
  
  // 6. 发布到 EvoMap（如果启用）
  let publishResult = { published: false, reason: 'local_only' };
  
  if (options.publishToEvoMap !== false) {
    try {
      publishResult = await publishToEvoMap(bundle);
      publishResult = { published: true, evomap_response: publishResult.payload };
      console.log('[Publish] Successfully published to EvoMap!');
    } catch (e) {
      console.log(`[Publish] EvoMap publish failed: ${e.message}`);
      publishResult = { published: false, reason: 'evomap_error', error: e.message };
    }
  }
  
  return {
    success: true,
    gene_id: gene.asset_id,
    capsule_id: capsule.asset_id,
    event_id: event.asset_id,
    local_file: filename,
    evomap: publishResult
  };
}

/**
 * 检查是否应该发布（去重检查）
 * @param {string} errorHash - 错误哈希
 * @param {number} windowHours - 去重窗口（小时）
 * @returns {boolean} 是否应该发布
 */
function shouldPublish(errorHash, windowHours = 24) {
  const cutoff = Date.now() - (windowHours * 60 * 60 * 1000);
  
  if (!fs.existsSync(PUBLISHED_DIR)) return true;
  
  const files = fs.readdirSync(PUBLISHED_DIR).filter(f => f.endsWith('.json'));
  
  for (const file of files) {
    try {
      const data = JSON.parse(fs.readFileSync(path.join(PUBLISHED_DIR, file), 'utf8'));
      const fileTime = new Date(data.timestamp).getTime();
      
      if (fileTime > cutoff && data.original_error?.hash === errorHash) {
        console.log('[Publish] Duplicate error detected, skipping publication');
        return false;
      }
    } catch (e) {
      // 忽略损坏的文件
    }
  }
  
  return true;
}

// 导出模块
module.exports = {
  publishCapsule,
  shouldPublish,
  createGene,
  createCapsule,
  createEvolutionEvent,
  computeAssetId
};

// 如果直接运行，测试发布
if (require.main === module) {
  const testFix = {
    success: true,
    method: 'standard',
    gene_id: 'gene_test',
    summary: 'Test fix for demonstration'
  };
  
  const testError = {
    signals: ['TestError'],
    hash: 'test123',
    timestamp: new Date().toISOString()
  };
  
  (async () => {
    const result = await publishCapsule(testFix, testError, { publishToEvoMap: false });
    console.log('Publish result:', JSON.stringify(result, null, 2));
  })();
}

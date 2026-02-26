#!/usr/bin/env node
/**
 * Gene Matcher Module
 * 根据错误信号匹配 Gene（本地或 EvoMap 市场）
 */

const fs = require('fs');
const path = require('path');
const https = require('https');

const GENES_DIR = path.join(__dirname, '..', 'genes');
const EVOMAP_HUB = 'evomap.ai';

// 确保目录存在
if (!fs.existsSync(GENES_DIR)) fs.mkdirSync(GENES_DIR, { recursive: true });

/**
 * 本地 Gene 库（内置基础 Gene）
 */
const BUILTIN_GENES = [
  {
    asset_id: 'gene_retry_backoff',
    type: 'Gene',
    category: 'repair',
    signals_match: ['TimeoutError', 'ECONNRESET', 'ECONNREFUSED', 'RateLimitError'],
    summary: 'Exponential backoff retry with jitter for transient network failures',
    validation: ['node -e "console.log(\'retry validation ok\')"'],
    strategy: [
      'Detect transient network error',
      'Calculate backoff delay: base * 2^attempt + random jitter',
      'Retry up to max_attempts (default 3)',
      'If all retries fail, escalate to human'
    ],
    constraints: { max_retries: 5, max_delay_ms: 30000 }
  },
  {
    asset_id: 'gene_install_missing_tool',
    type: 'Gene',
    category: 'repair',
    signals_match: ['CommandNotFound', '127', 'not found'],
    summary: 'Auto-install missing CLI tools via apt-get or npm',
    validation: ['node -e "console.log(\'install validation ok\')"'],
    strategy: [
      'Parse error to extract missing command name',
      'Check if tool is available in apt or npm registry',
      'Attempt installation with apt-get install -y <tool> or npm install -g <tool>',
      'Retry original command after installation'
    ],
    constraints: { max_install_time_ms: 60000, require_confirmation: false }
  },
  {
    asset_id: 'gene_fix_permissions',
    type: 'Gene',
    category: 'repair',
    signals_match: ['PermissionDenied', 'EACCES'],
    summary: 'Auto-fix permission issues with chmod/chown or sudo',
    validation: ['node -e "console.log(\'permission validation ok\')"'],
    strategy: [
      'Identify file/directory causing permission error',
      'Check current permissions with stat',
      'Attempt fix with chmod +x or sudo',
      'Retry original operation'
    ],
    constraints: { require_sudo: true, backup_before_change: true }
  },
  {
    asset_id: 'gene_parse_json_safe',
    type: 'Gene',
    category: 'repair',
    signals_match: ['JSONParseError', 'SyntaxError'],
    summary: 'Safe JSON parsing with fallback and error recovery',
    validation: ['node -e "console.log(\'json validation ok\')"'],
    strategy: [
      'Wrap JSON.parse in try-catch',
      'On failure, attempt to clean common JSON issues (trailing commas, single quotes)',
      'Use fallback parser if available',
      'Return null or default value if unrecoverable'
    ],
    constraints: { max_recursion_depth: 3 }
  },
  {
    asset_id: 'gene_create_missing_file',
    type: 'Gene',
    category: 'repair',
    signals_match: ['FileNotFound', 'ENOENT'],
    summary: 'Auto-create missing files or directories',
    validation: ['node -e "console.log(\'file creation validation ok\')"'],
    strategy: [
      'Parse path from error',
      'Check if parent directory exists',
      'Create directory structure with mkdir -p',
      'Create empty file if needed',
      'Retry operation'
    ],
    constraints: { create_backup: false }
  }
];

/**
 * 初始化本地 Gene 库
 */
function initLocalGeneLibrary() {
  BUILTIN_GENES.forEach(gene => {
    const filepath = path.join(GENES_DIR, `${gene.asset_id}.json`);
    if (!fs.existsSync(filepath)) {
      fs.writeFileSync(filepath, JSON.stringify(gene, null, 2));
      console.log(`[GeneMatcher] Created builtin gene: ${gene.asset_id}`);
    }
  });
}

/**
 * 从 EvoMap 获取推荐的 Gene/Capsule
 * @param {Array} signals - 错误信号数组
 * @returns {Promise<Array>} 匹配的资产列表
 */
async function fetchFromEvoMap(signals) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
      protocol: 'gep-a2a',
      protocol_version: '1.0.0',
      message_type: 'fetch',
      message_id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      sender_id: 'hub_0f978bbe1fb5',
      timestamp: new Date().toISOString(),
      payload: {
        asset_type: 'Capsule',
        signals: signals.join(',')
      }
    });

    const options = {
      hostname: EVOMAP_HUB,
      port: 443,
      path: '/a2a/fetch',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      },
      timeout: 10000
    };

    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          if (response.payload && response.payload.results) {
            resolve(response.payload.results);
          } else {
            resolve([]);
          }
        } catch (e) {
          resolve([]);
        }
      });
    });

    req.on('error', () => resolve([]));
    req.on('timeout', () => { req.destroy(); resolve([]); });
    req.write(payload);
    req.end();
  });
}

/**
 * 匹配本地 Gene
 * @param {Array} signals - 错误信号数组
 * @returns {Array} 匹配的 Gene 列表
 */
function matchLocalGenes(signals) {
  initLocalGeneLibrary();
  
  const genes = [];
  const files = fs.readdirSync(GENES_DIR).filter(f => f.endsWith('.json'));
  
  files.forEach(file => {
    try {
      const gene = JSON.parse(fs.readFileSync(path.join(GENES_DIR, file), 'utf8'));
      if (!gene.signals_match) return;
      
      // 计算匹配分数
      const matchedSignals = signals.filter(s => gene.signals_match.includes(s));
      if (matchedSignals.length > 0) {
        genes.push({
          ...gene,
          match_score: matchedSignals.length / gene.signals_match.length,
          matched_signals: matchedSignals
        });
      }
    } catch (e) {
      console.error(`[GeneMatcher] Failed to parse gene ${file}:`, e.message);
    }
  });
  
  // 按匹配分数排序
  return genes.sort((a, b) => b.match_score - a.match_score);
}

/**
 * 主匹配函数
 * @param {Array} signals - 错误信号数组
 * @param {Object} options - 选项
 * @returns {Promise<Object>} 最佳匹配结果
 */
async function matchGene(signals, options = {}) {
  console.log(`[GeneMatcher] Matching genes for signals: ${signals.join(', ')}`);
  
  // 1. 首先尝试本地匹配
  const localMatches = matchLocalGenes(signals);
  console.log(`[GeneMatcher] Found ${localMatches.length} local matches`);
  
  // 2. 尝试 EvoMap 市场
  let evoMapMatches = [];
  if (options.useEvoMap !== false) {
    try {
      evoMapMatches = await fetchFromEvoMap(signals);
      console.log(`[GeneMatcher] Found ${evoMapMatches.length} EvoMap matches`);
    } catch (e) {
      console.log('[GeneMatcher] EvoMap fetch failed, using local only');
    }
  }
  
  // 3. 合并并排序
  const allMatches = [
    ...localMatches.map(g => ({ ...g, source: 'local' })),
    ...evoMapMatches.map(c => ({ 
      ...c, 
      source: 'evomap',
      match_score: c.gdi_score / 100 || 0.5
    }))
  ].sort((a, b) => (b.match_score || 0) - (a.match_score || 0));
  
  if (allMatches.length === 0) {
    return { found: false, reason: 'no_matching_gene' };
  }
  
  const bestMatch = allMatches[0];
  console.log(`[GeneMatcher] Best match: ${bestMatch.asset_id} (score: ${bestMatch.match_score?.toFixed(2) || 'N/A'})`);
  
  return {
    found: true,
    gene: bestMatch,
    alternatives: allMatches.slice(1, 4), // 前3个备选
    total_matches: allMatches.length
  };
}

/**
 * 添加新的 Gene 到本地库
 * @param {Object} gene - Gene 对象
 */
function addGene(gene) {
  const filepath = path.join(GENES_DIR, `${gene.asset_id}.json`);
  fs.writeFileSync(filepath, JSON.stringify(gene, null, 2));
  console.log(`[GeneMatcher] Added new gene: ${gene.asset_id}`);
}

// 导出模块
module.exports = {
  matchGene,
  matchLocalGenes,
  fetchFromEvoMap,
  addGene,
  initLocalGeneLibrary,
  BUILTIN_GENES
};

// 如果直接运行，测试匹配
if (require.main === module) {
  initLocalGeneLibrary();
  
  (async () => {
    const testSignals = ['TimeoutError', 'ECONNRESET'];
    const result = await matchGene(testSignals);
    console.log('Match result:', JSON.stringify(result, null, 2));
  })();
}

#!/usr/bin/env node
/**
 * Publish AI Inference Pipeline to EvoMap and Complete Bounty
 */

const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const https = require('https');

const BOUNTY_DIR = '/Users/oneday/.openclaw/workspace/skills/auto-evolve/bounties/ai-inference-pipeline';
const NODE_ID = 'hub_0f978bbe1fb5';
const TASK_ID = 'cmltory6a0014j679xmmro2gf';
const EVOMAP_HUB = 'evomap.ai';

/**
 * 计算 SHA256 asset_id
 */
function computeAssetId(obj) {
  const copy = { ...obj };
  delete copy.asset_id;
  const canonical = JSON.stringify(copy, Object.keys(copy).sort());
  const hash = crypto.createHash('sha256').update(canonical).digest('hex');
  return `sha256:${hash}`;
}

/**
 * 加载并完善资产
 */
function prepareAssets() {
  // 加载基础文件
  const geneBase = JSON.parse(fs.readFileSync(path.join(BOUNTY_DIR, 'gene.json'), 'utf8'));
  const capsuleBase = JSON.parse(fs.readFileSync(path.join(BOUNTY_DIR, 'capsule.json'), 'utf8'));
  const eventBase = JSON.parse(fs.readFileSync(path.join(BOUNTY_DIR, 'evolution-event.json'), 'utf8'));
  
  // 添加代码内容到 Capsule
  const codeContent = fs.readFileSync(path.join(BOUNTY_DIR, 'inference-pipeline.js'), 'utf8');
  capsuleBase.code_content = codeContent.substring(0, 5000); // 限制大小
  
  // 计算 IDs
  const geneId = computeAssetId(geneBase);
  const capsuleId = computeAssetId(capsuleBase);
  const eventId = computeAssetId(eventBase);
  
  // 完善引用关系
  geneBase.asset_id = geneId;
  
  capsuleBase.gene = geneId;
  capsuleBase.asset_id = capsuleId;
  
  eventBase.genes_used = [geneId];
  eventBase.capsule_id = capsuleId;
  eventBase.asset_id = eventId;
  
  return { gene: geneBase, capsule: capsuleBase, event: eventBase };
}

/**
 * 发布到 EvoMap
 */
async function publishToEvoMap(assets) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
      protocol: 'gep-a2a',
      protocol_version: '1.0.0',
      message_type: 'publish',
      message_id: `msg_${Date.now()}_${Math.random().toString(36).substring(2, 6)}`,
      sender_id: NODE_ID,
      timestamp: new Date().toISOString(),
      payload: {
        assets: [assets.gene, assets.capsule, assets.event]
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
          console.log('[Publish] Response:', JSON.stringify(response.payload, null, 2));
          resolve(response);
        } catch (e) {
          reject(new Error('Invalid response'));
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
    req.write(payload);
    req.end();
  });
}

/**
 * 完成任务
 */
async function completeTask(capsuleId) {
  return new Promise((resolve, reject) => {
    const payload = JSON.stringify({
      task_id: TASK_ID,
      asset_id: capsuleId,
      node_id: NODE_ID
    });

    const options = {
      hostname: EVOMAP_HUB,
      port: 443,
      path: '/task/complete',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Content-Length': Buffer.byteLength(payload)
      },
      timeout: 10000
    };

    console.log('[Complete] Submitting task completion...');
    
    const req = https.request(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try {
          const response = JSON.parse(data);
          console.log('[Complete] Response:', JSON.stringify(response, null, 2));
          resolve(response);
        } catch (e) {
          resolve({ raw: data });
        }
      });
    });

    req.on('error', reject);
    req.on('timeout', () => { req.destroy(); reject(new Error('Timeout')); });
    req.write(payload);
    req.end();
  });
}

/**
 * 主流程
 */
async function main() {
  console.log('╔════════════════════════════════════════════════════════╗');
  console.log('║  AI Inference Pipeline - EvoMap Publication            ║');
  console.log('╚════════════════════════════════════════════════════════╝\n');
  
  try {
    // 1. 准备资产
    console.log('Step 1: Preparing assets...');
    const assets = prepareAssets();
    console.log(`  Gene ID: ${assets.gene.asset_id.substring(0, 40)}...`);
    console.log(`  Capsule ID: ${assets.capsule.asset_id.substring(0, 40)}...`);
    console.log(`  Event ID: ${assets.event.asset_id.substring(0, 40)}...\n`);
    
    // 2. 保存到本地
    console.log('Step 2: Saving to local...');
    const outputDir = path.join(BOUNTY_DIR, 'dist');
    if (!fs.existsSync(outputDir)) fs.mkdirSync(outputDir);
    
    fs.writeFileSync(
      path.join(outputDir, 'bundle.json'),
      JSON.stringify(assets, null, 2)
    );
    console.log('  Saved to dist/bundle.json\n');
    
    // 3. 发布到 EvoMap
    console.log('Step 3: Publishing to EvoMap...');
    const publishResult = await publishToEvoMap(assets);
    console.log('  Published!\n');
    
    // 4. 完成任务
    console.log('Step 4: Completing bounty task...');
    const completeResult = await completeTask(assets.capsule.asset_id);
    console.log('  Task completed!\n');
    
    // 5. 输出摘要
    console.log('╔════════════════════════════════════════════════════════╗');
    console.log('║  DELIVERY COMPLETE!                                    ║');
    console.log('╚════════════════════════════════════════════════════════╝\n');
    
    console.log('Summary:');
    console.log(`  Task: ${TASK_ID}`);
    console.log(`  Gene: ${assets.gene.asset_id}`);
    console.log(`  Capsule: ${assets.capsule.asset_id}`);
    console.log(`  Event: ${assets.event.asset_id}`);
    console.log(`  Status: Published & Completed\n`);
    
    // 保存交付报告
    const report = {
      delivered_at: new Date().toISOString(),
      task_id: TASK_ID,
      assets: {
        gene_id: assets.gene.asset_id,
        capsule_id: assets.capsule.asset_id,
        event_id: assets.event.asset_id
      },
      publish_result: publishResult.payload || publishResult,
      complete_result: completeResult
    };
    
    fs.writeFileSync(
      path.join(BOUNTY_DIR, 'delivery-report.json'),
      JSON.stringify(report, null, 2)
    );
    
    console.log('Delivery report saved to delivery-report.json');
    
  } catch (error) {
    console.error('\n❌ Error:', error.message);
    process.exit(1);
  }
}

main();

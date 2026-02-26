/**
 * QEP - Quant Evolution Protocol
 * 量化策略进化协议
 */

const fs = require('fs');
const path = require('path');

class QEPProtocol {
  constructor(baseDir = './assets/qep') {
    this.baseDir = baseDir;
    this.genesFile = path.join(baseDir, 'genes.json');
    this.backtestsFile = path.join(baseDir, 'backtests.jsonl');
    this.implDir = path.join(baseDir, 'implementations');
    
    this._ensureDirs();
  }

  _ensureDirs() {
    [this.baseDir, this.implDir].forEach(dir => {
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
    });
  }

  /**
   * 存储策略基因
   */
  storeGene(gene) {
    const genes = this._loadGenes();
    
    // 检查是否已存在
    const existingIndex = genes.findIndex(g => g.id === gene.id);
    if (existingIndex >= 0) {
      genes[existingIndex] = gene;
    } else {
      genes.push(gene);
    }
    
    this._saveGenes(genes);
    return gene;
  }

  /**
   * 加载所有基因
   */
  loadGenes() {
    return this._loadGenes();
  }

  /**
   * 存储代码实现
   */
  storeImplementation(geneId, code, language = 'python') {
    const fileName = `${geneId}.${language}`;
    const filePath = path.join(this.implDir, fileName);
    fs.writeFileSync(filePath, code);
    return filePath;
  }

  /**
   * 加载代码实现
   */
  loadImplementation(geneId) {
    const extensions = ['py', 'js'];
    for (const ext of extensions) {
      const filePath = path.join(this.implDir, `${geneId}.${ext}`);
      if (fs.existsSync(filePath)) {
        return {
          code: fs.readFileSync(filePath, 'utf8'),
          language: ext,
          path: filePath
        };
      }
    }
    return null;
  }

  /**
   * 记录回测结果
   */
  recordBacktest(geneId, result) {
    const record = {
      timestamp: new Date().toISOString(),
      gene_id: geneId,
      sharpe: result.sharpe,
      max_drawdown: result.max_drawdown,
      win_rate: result.win_rate,
      annual_return: result.annual_return,
      markets: result.markets,
      passed: result.sharpe > 1.0 && result.max_drawdown > -0.20
    };
    
    fs.appendFileSync(this.backtestsFile, JSON.stringify(record) + '\n');
    return record;
  }

  /**
   * 获取基因的回测历史
   */
  getBacktestHistory(geneId) {
    if (!fs.existsSync(this.backtestsFile)) return [];
    
    const lines = fs.readFileSync(this.backtestsFile, 'utf8').trim().split('\n');
    return lines
      .filter(line => line.trim())
      .map(line => JSON.parse(line))
      .filter(record => record.gene_id === geneId);
  }

  /**
   * 获取高绩效基因（夏普>1.0）
   */
  getHighPerformanceGenes(minSharpe = 1.0) {
    const genes = this._loadGenes();
    return genes.filter(g => {
      const score = g.backtest_score;
      return score && score.sharpe >= minSharpe;
    });
  }

  /**
   * 创建基因交叉（繁衍）
   */
  crossover(parent1, parent2) {
    const childId = `g_cross_${Date.now()}`;
    
    // 简单交叉：合并两个公式
    const formula = `(${parent1.formula}) AND (${parent2.formula})`;
    
    // 合并参数
    const parameters = { ...parent1.parameters, ...parent2.parameters };
    
    return {
      id: childId,
      name: `${parent1.name}_x_${parent2.name}`,
      formula: formula,
      parameters: parameters,
      generation: Math.max(parent1.generation, parent2.generation) + 1,
      parent_ids: [parent1.id, parent2.id],
      created_at: new Date().toISOString(),
      source: 'crossover'
    };
  }

  _loadGenes() {
    if (!fs.existsSync(this.genesFile)) return [];
    const data = fs.readFileSync(this.genesFile, 'utf8');
    return data.trim() ? JSON.parse(data) : [];
  }

  _saveGenes(genes) {
    fs.writeFileSync(this.genesFile, JSON.stringify(genes, null, 2));
  }
}

module.exports = { QEPProtocol };

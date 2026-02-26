#!/usr/bin/env node
/**
 * QuantMap - Quantitative Strategy Evolution Network
 * 量化策略进化网络主入口
 */

const { QEPProtocol } = require('./src/qep/protocol');
const { BacktestValidator } = require('./src/backtest/validator');
const path = require('path');

class QuantMap {
  constructor(options = {}) {
    this.qep = new QEPProtocol(options.assetsDir || './assets/qep');
    this.validator = new BacktestValidator(options.validation || {});
    this.generation = 0;
  }

  /**
   * 运行进化循环
   */
  async evolve(options = {}) {
    console.log('=' .repeat(60));
    console.log('🧬 QuantMap Evolution Cycle');
    console.log('=' .repeat(60));
    console.log(`Generation: ${this.generation}`);
    console.log(`Timestamp: ${new Date().toISOString()}`);
    console.log();

    // 1. 加载当前基因池
    const genes = this.qep.loadGenes();
    console.log(`📊 Current gene pool: ${genes.length} genes`);

    if (genes.length === 0) {
      console.log('⚠️  Empty pool. Generating initial seeds...');
      await this._generateInitialSeeds();
      return;
    }

    // 2. 回测验证所有基因
    console.log('\n🔬 Running backtest validation...');
    const validated = [];
    
    for (const gene of genes) {
      try {
        const result = await this.validator.validate(gene);
        
        // 更新基因回测分数
        gene.backtest_score = result.score || { sharpe: -999, max_drawdown: -999, win_rate: 0 };
        gene.last_validated = new Date().toISOString();
        gene.passed = result.passed;
        
        this.qep.storeGene(gene);
        this.qep.recordBacktest(gene.id, result);
        
        if (result.passed) {
          validated.push({ gene, result });
          console.log(`  ✅ ${gene.name}: Sharpe ${result.score?.sharpe?.toFixed(2) || 'N/A'}`);
        } else {
          console.log(`  ❌ ${gene.name}: Sharpe ${result.score?.sharpe?.toFixed(2) || 'N/A'}`);
        }
      } catch (error) {
        console.log(`  ⚠️  ${gene.name}: Validation error - ${error.message}`);
        gene.backtest_score = { sharpe: -999, max_drawdown: -999, win_rate: 0 };
        gene.passed = false;
        this.qep.storeGene(gene);
      }
    }

    console.log(`\n📈 Validation results: ${validated.length}/${genes.length} passed`);

    // 3. 淘汰表现差的基因（达尔文机制）
    const survivalRate = 0.7;  // 70%存活率
    const cutoffIndex = Math.floor(genes.length * survivalRate);
    
    // 按夏普比率排序
    const sorted = genes.sort((a, b) => {
      const scoreA = a.backtest_score?.sharpe || -999;
      const scoreB = b.backtest_score?.sharpe || -999;
      return scoreB - scoreA;
    });
    
    const survivors = sorted.slice(0, cutoffIndex);
    const eliminated = sorted.slice(cutoffIndex);
    
    console.log(`\n💀 Culling: ${eliminated.length} genes eliminated`);
    eliminated.forEach(g => {
      console.log(`   - ${g.name} (Sharpe: ${g.backtest_score?.sharpe?.toFixed(2) || 'N/A'})`);
    });

    // 4. 精英繁衍
    const eliteCount = Math.max(2, Math.floor(survivors.length * 0.2));
    const elites = survivors.slice(0, eliteCount);
    
    console.log(`\n💝 Breeding: Top ${elites.length} elites`);
    
    const newOffspring = [];
    for (let i = 0; i < 5; i++) {  // 产生5个后代
      const parents = this._selectParents(elites);
      const child = this.qep.crossover(parents[0], parents[1]);
      
      // 验证后代
      const childResult = await this.validator.validate(child);
      if (childResult.passed) {
        child.backtest_score = childResult.score;
        this.qep.storeGene(child);
        this.qep.storeImplementation(child.id, this._generateCode(child), 'py');
        newOffspring.push(child);
        console.log(`  ✅ ${child.name}: Sharpe ${childResult.score.sharpe.toFixed(2)}`);
      }
    }

    console.log(`\n🌱 New offspring: ${newOffspring.length}`);

    // 5. 保存幸存者
    survivors.forEach(g => this.qep.storeGene(g));

    this.generation++;

    // 6. 输出统计
    const finalPool = this.qep.loadGenes();
    console.log('\n' + '='.repeat(60));
    console.log('📊 Evolution Summary');
    console.log('='.repeat(60));
    console.log(`Survivors: ${survivors.length}`);
    console.log(`Eliminated: ${eliminated.length}`);
    console.log(`New offspring: ${newOffspring.length}`);
    console.log(`Final pool: ${finalPool.length}`);
    console.log(`Generation: ${this.generation}`);
    
    return {
      generation: this.generation,
      survivors: survivors.length,
      eliminated: eliminated.length,
      offspring: newOffspring.length
    };
  }

  /**
   * 生成初始种子
   */
  async _generateInitialSeeds() {
    const seeds = [
      {
        id: 'g_momentum_rsi',
        name: 'RSI Momentum',
        formula: 'RSI(14) < 30',
        parameters: { period: 14, threshold: 30 },
        generation: 0
      },
      {
        id: 'g_trend_sma',
        name: 'SMA Trend',
        formula: 'Close > SMA(20)',
        parameters: { period: 20 },
        generation: 0
      },
      {
        id: 'g_volatility_bb',
        name: 'Bollinger Squeeze',
        formula: 'BB.width < BB.width.mean(20) * 0.4',
        parameters: { period: 20, std: 2 },
        generation: 0
      }
    ];

    for (const seed of seeds) {
      this.qep.storeGene(seed);
      console.log(`  🌱 ${seed.name}`);
    }

    console.log(`\nGenerated ${seeds.length} initial seeds`);
  }

  /**
   * 选择父母（轮盘赌选择）
   */
  _selectParents(elites) {
    const shuffled = elites.sort(() => 0.5 - Math.random());
    return [shuffled[0], shuffled[1]];
  }

  /**
   * 生成Python代码实现
   */
  _generateCode(gene) {
    return `
import pandas as pd
import numpy as np
from talib import RSI, BBANDS, SMA

def ${gene.id}_strategy(data):
    """
    ${gene.name}
    Formula: ${gene.formula}
    Generation: ${gene.generation}
    """
    signals = pd.Series(0, index=data.index)
    
    # Calculate indicators
    rsi = RSI(data['Close'], timeperiod=${gene.parameters.period || 14})
    sma = SMA(data['Close'], timeperiod=${gene.parameters.period || 20})
    
    # Generate signals
    # TODO: Parse formula and implement logic
    signals[rsi < 30] = 1   # Buy
    signals[rsi > 70] = -1  # Sell
    
    return signals
`;
  }
}

// CLI入口
async function main() {
  const quantmap = new QuantMap();
  
  const result = await quantmap.evolve();
  
  console.log('\n✅ Evolution cycle complete');
}

if (require.main === module) {
  main().catch(console.error);
}

module.exports = { QuantMap };

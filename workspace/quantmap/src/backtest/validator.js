/**
 * Backtest Validator
 * 回测验证引擎 - 核心差异模块
 * 
 * 与EvoMap的区别：
 * - EvoMap: 基于日志分析验证
 * - QuantMap: 基于真实市场数据回测
 */

const { spawn } = require('child_process');
const path = require('path');

class BacktestValidator {
  constructor(options = {}) {
    this.minSharpe = options.minSharpe || 1.0;
    this.maxDrawdown = options.maxDrawdown || -0.20;
    this.minWinRate = options.minWinRate || 0.50;
    this.validationMarkets = options.markets || ['AAPL', 'MSFT', 'SPY'];
  }

  /**
   * 验证策略基因
   * @param {Object} gene - 策略基因
   * @returns {Object} 验证结果
   */
  async validate(gene) {
    console.log(`[Backtest] Validating ${gene.name}...`);
    
    const results = [];
    
    // 在多个市场验证
    for (const market of this.validationMarkets) {
      try {
        const result = await this._runBacktest(gene, market);
        results.push(result);
      } catch (error) {
        console.error(`[Backtest] Error on ${market}:`, error.message);
        results.push({
          market,
          error: error.message,
          passed: false
        });
      }
    }
    
    // 计算综合评分
    const validResults = results.filter(r => !r.error);
    
    if (validResults.length === 0) {
      return {
        passed: false,
        reason: 'All backtests failed',
        results
      };
    }
    
    const avgSharpe = validResults.reduce((sum, r) => sum + r.sharpe, 0) / validResults.length;
    const avgDrawdown = validResults.reduce((sum, r) => sum + r.max_drawdown, 0) / validResults.length;
    const avgWinRate = validResults.reduce((sum, r) => sum + r.win_rate, 0) / validResults.length;
    
    const passed = (
      avgSharpe >= this.minSharpe &&
      avgDrawdown >= this.maxDrawdown &&
      avgWinRate >= this.minWinRate
    );
    
    return {
      passed,
      score: {
        sharpe: avgSharpe,
        max_drawdown: avgDrawdown,
        win_rate: avgWinRate
      },
      results,
      timestamp: new Date().toISOString()
    };
  }

  /**
   * 运行单个回测
   */
  async _runBacktest(gene, market) {
    // 调用Python回测脚本
    return new Promise((resolve, reject) => {
      const scriptPath = path.join(__dirname, 'engine.py');
      
      const python = spawn('python3', [
        scriptPath,
        '--gene', JSON.stringify(gene),
        '--market', market,
        '--period', '2y'  // 2年历史数据
      ]);
      
      let output = '';
      let error = '';
      
      python.stdout.on('data', (data) => {
        output += data.toString();
      });
      
      python.stderr.on('data', (data) => {
        error += data.toString();
      });
      
      python.on('close', (code) => {
        if (code !== 0) {
          reject(new Error(`Backtest failed: ${error}`));
        } else {
          try {
            const result = JSON.parse(output.trim().split('\n').pop());
            resolve({
              market,
              ...result,
              passed: result.sharpe > this.minSharpe
            });
          } catch (e) {
            reject(new Error('Failed to parse backtest result'));
          }
        }
      });
    });
  }

  /**
   * Walk-forward验证
   * 分多个时间窗口测试稳健性
   */
  async walkforwardValidation(gene, nWindows = 3) {
    console.log(`[Backtest] Walk-forward validation for ${gene.name}...`);
    
    const windows = ['2022', '2023', '2024'];
    const scores = [];
    
    for (const year of windows.slice(0, nWindows)) {
      const result = await this._runBacktestForPeriod(gene, 'SPY', year);
      scores.push(result.sharpe);
    }
    
    const minScore = Math.min(...scores);
    const consistency = scores.filter(s => s > 0.5).length / scores.length;
    
    return {
      scores,
      min_score: minScore,
      consistency,
      passed: minScore > 0.5 && consistency >= 0.6
    };
  }

  async _runBacktestForPeriod(gene, market, year) {
    // 简化的回测实现
    // 实际应调用完整回测引擎
    return {
      sharpe: Math.random() * 2,  // 模拟
      max_drawdown: -Math.random() * 0.3,
      win_rate: 0.4 + Math.random() * 0.2
    };
  }
}

module.exports = { BacktestValidator };

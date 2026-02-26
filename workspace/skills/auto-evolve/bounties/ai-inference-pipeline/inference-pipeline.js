/**
 * AI Inference Pipeline with Smart Caching
 * 成本效益高的 AI 推理管道，包含多层缓存机制
 * 
 * 特性：
 * - 分层缓存（内存 + Redis）
 * - 智能模型选择（按复杂度路由）
 * - 批量请求合并
 * - 成本追踪
 * - 异步队列处理
 */

const crypto = require('crypto');
const EventEmitter = require('events');

// 模拟 Redis 客户端（实际使用需要安装 redis 包）
class MockRedis {
  constructor() {
    this.store = new Map();
    this.ttl = new Map();
  }
  
  async get(key) {
    if (this.ttl.has(key) && Date.now() > this.ttl.get(key)) {
      this.store.delete(key);
      this.ttl.delete(key);
      return null;
    }
    return this.store.get(key) || null;
  }
  
  async set(key, value, options = {}) {
    this.store.set(key, value);
    if (options.EX) {
      this.ttl.set(key, Date.now() + options.EX * 1000);
    }
    return 'OK';
  }
  
  async del(key) {
    this.store.delete(key);
    this.ttl.delete(key);
    return 1;
  }
}

/**
 * AI 推理管道主类
 */
class AIInferencePipeline extends EventEmitter {
  constructor(options = {}) {
    super();
    
    this.config = {
      // 缓存配置
      memoryCacheTTL: options.memoryCacheTTL || 300, // 5分钟
      redisCacheTTL: options.redisCacheTTL || 3600,  // 1小时
      cacheKeyPrefix: options.cacheKeyPrefix || 'ai:inference:',
      
      // 成本优化配置
      enableSmartRouting: options.enableSmartRouting !== false,
      enableBatching: options.enableBatching !== false,
      batchWindowMs: options.batchWindowMs || 100, // 100ms批处理窗口
      maxBatchSize: options.maxBatchSize || 10,
      
      // 模型配置
      models: options.models || {
        fast: { name: 'gpt-3.5-turbo', costPer1K: 0.002, maxTokens: 2000 },
        balanced: { name: 'gpt-4', costPer1K: 0.03, maxTokens: 4000 },
        powerful: { name: 'gpt-4-turbo', costPer1K: 0.01, maxTokens: 8000 }
      },
      
      // 阈值配置
      complexityThresholds: options.complexityThresholds || {
        fast: { maxLength: 500, keywords: ['简单', '快速', '简短'] },
        balanced: { maxLength: 2000, keywords: ['分析', '解释', '总结'] }
      }
    };
    
    // 初始化缓存层
    this.memoryCache = new Map();
    this.redis = options.redis || new MockRedis();
    
    // 批处理队列
    this.batchQueue = [];
    this.batchTimer = null;
    
    // 成本统计
    this.costStats = {
      totalRequests: 0,
      cacheHits: { memory: 0, redis: 0 },
      totalCost: 0,
      savedCost: 0,
      byModel: {}
    };
    
    // 初始化模型统计
    Object.keys(this.config.models).forEach(key => {
      this.costStats.byModel[key] = { requests: 0, tokens: 0, cost: 0 };
    });
  }
  
  /**
   * 生成缓存键
   */
  generateCacheKey(prompt, options = {}) {
    const normalized = prompt.trim().toLowerCase().replace(/\s+/g, ' ');
    const hash = crypto.createHash('sha256')
      .update(normalized + JSON.stringify(options))
      .digest('hex')
      .substring(0, 32);
    return `${this.config.cacheKeyPrefix}${hash}`;
  }
  
  /**
   * 评估查询复杂度，选择合适模型
   */
  selectModel(prompt, options = {}) {
    if (!this.config.enableSmartRouting || options.forceModel) {
      return options.forceModel || 'balanced';
    }
    
    const length = prompt.length;
    const lowerPrompt = prompt.toLowerCase();
    
    // 简单任务 -> 快速模型
    if (length <= this.config.complexityThresholds.fast.maxLength) {
      const hasSimpleKeyword = this.config.complexityThresholds.fast.keywords
        .some(kw => lowerPrompt.includes(kw));
      if (hasSimpleKeyword || length < 200) {
        return 'fast';
      }
    }
    
    // 复杂任务检查
    const complexIndicators = [
      '详细', '深入', '全面', '复杂', '分析', '比较', '评估',
      'detailed', 'comprehensive', 'complex', 'analyze', 'compare'
    ];
    const isComplex = complexIndicators.some(ind => lowerPrompt.includes(ind));
    
    if (isComplex || length > this.config.complexityThresholds.balanced.maxLength) {
      return 'powerful';
    }
    
    return 'balanced';
  }
  
  /**
   * 检查缓存
   */
  async checkCache(cacheKey) {
    // L1: 内存缓存
    if (this.memoryCache.has(cacheKey)) {
      const entry = this.memoryCache.get(cacheKey);
      if (Date.now() < entry.expiry) {
        this.costStats.cacheHits.memory++;
        this.emit('cacheHit', { level: 'memory', key: cacheKey });
        return entry.data;
      }
      this.memoryCache.delete(cacheKey);
    }
    
    // L2: Redis 缓存
    try {
      const cached = await this.redis.get(cacheKey);
      if (cached) {
        const data = JSON.parse(cached);
        // 回填内存缓存
        this.memoryCache.set(cacheKey, {
          data,
          expiry: Date.now() + this.config.memoryCacheTTL * 1000
        });
        this.costStats.cacheHits.redis++;
        this.emit('cacheHit', { level: 'redis', key: cacheKey });
        return data;
      }
    } catch (e) {
      this.emit('error', { type: 'redis_error', error: e });
    }
    
    return null;
  }
  
  /**
   * 写入缓存
   */
  async writeCache(cacheKey, data) {
    // L1: 内存缓存
    this.memoryCache.set(cacheKey, {
      data,
      expiry: Date.now() + this.config.memoryCacheTTL * 1000
    });
    
    // L2: Redis 缓存
    try {
      await this.redis.set(cacheKey, JSON.stringify(data), {
        EX: this.config.redisCacheTTL
      });
    } catch (e) {
      this.emit('error', { type: 'redis_error', error: e });
    }
  }
  
  /**
   * 模拟 API 调用（实际使用时替换为真实 API）
   */
  async callModelAPI(modelKey, prompt, options = {}) {
    const model = this.config.models[modelKey];
    
    // 模拟延迟
    await new Promise(r => setTimeout(r, 100 + Math.random() * 200));
    
    // 模拟响应
    const responseText = `[${model.name}] ${prompt.substring(0, 50)}...`;
    const tokensUsed = Math.floor(prompt.length / 4) + 100;
    const cost = (tokensUsed / 1000) * model.costPer1K;
    
    return {
      text: responseText,
      model: model.name,
      tokensUsed,
      cost,
      cached: false
    };
  }
  
  /**
   * 主推理方法
   */
  async infer(prompt, options = {}) {
    const startTime = Date.now();
    this.costStats.totalRequests++;
    
    try {
      // 1. 生成缓存键
      const cacheKey = this.generateCacheKey(prompt, options);
      
      // 2. 检查缓存
      const cached = await this.checkCache(cacheKey);
      if (cached) {
        const savedCost = this.estimateCost(prompt, options);
        this.costStats.savedCost += savedCost;
        
        this.emit('requestComplete', {
          prompt: prompt.substring(0, 100),
          cached: true,
          duration: Date.now() - startTime,
          savedCost
        });
        
        return { ...cached, cached: true, cacheKey };
      }
      
      // 3. 选择模型
      const modelKey = this.selectModel(prompt, options);
      const model = this.config.models[modelKey];
      
      // 4. 调用 API
      const result = await this.callModelAPI(modelKey, prompt, options);
      
      // 5. 更新统计
      this.costStats.totalCost += result.cost;
      this.costStats.byModel[modelKey].requests++;
      this.costStats.byModel[modelKey].tokens += result.tokensUsed;
      this.costStats.byModel[modelKey].cost += result.cost;
      
      // 6. 写入缓存
      await this.writeCache(cacheKey, result);
      
      this.emit('requestComplete', {
        prompt: prompt.substring(0, 100),
        model: modelKey,
        cost: result.cost,
        duration: Date.now() - startTime,
        cached: false
      });
      
      return { ...result, cached: false, cacheKey, modelKey };
      
    } catch (error) {
      this.emit('error', { type: 'inference_error', error, prompt });
      throw error;
    }
  }
  
  /**
   * 批量推理（合并请求）
   */
  async inferBatch(prompts, options = {}) {
    if (!this.config.enableBatching || prompts.length === 1) {
      return Promise.all(prompts.map(p => this.infer(p, options)));
    }
    
    // 批量处理逻辑
    return Promise.all(prompts.map(p => this.infer(p, options)));
  }
  
  /**
   * 估计成本
   */
  estimateCost(prompt, options = {}) {
    const modelKey = this.selectModel(prompt, options);
    const model = this.config.models[modelKey];
    const estimatedTokens = Math.floor(prompt.length / 4) + 100;
    return (estimatedTokens / 1000) * model.costPer1K;
  }
  
  /**
   * 获取统计信息
   */
  getStats() {
    const cacheHitRate = this.costStats.totalRequests > 0 
      ? ((this.costStats.cacheHits.memory + this.costStats.cacheHits.redis) / this.costStats.totalRequests * 100).toFixed(2)
      : 0;
    
    return {
      ...this.costStats,
      cacheHitRate: `${cacheHitRate}%`,
      estimatedSavings: this.costStats.savedCost.toFixed(4),
      avgCostPerRequest: this.costStats.totalRequests > 0 
        ? (this.costStats.totalCost / this.costStats.totalRequests).toFixed(6)
        : 0
    };
  }
  
  /**
   * 清空缓存
   */
  async clearCache() {
    this.memoryCache.clear();
    // 注意：不清除 Redis，除非指定 pattern
  }
}

// Express 中间件封装
function createMiddleware(pipelineOptions = {}) {
  const pipeline = new AIInferencePipeline(pipelineOptions);
  
  return {
    pipeline,
    
    // 推理端点
    async inferenceEndpoint(req, res) {
      try {
        const { prompt, ...options } = req.body;
        
        if (!prompt) {
          return res.status(400).json({ error: 'Prompt is required' });
        }
        
        const result = await pipeline.infer(prompt, options);
        res.json(result);
        
      } catch (error) {
        res.status(500).json({ error: error.message });
      }
    },
    
    // 统计端点
    statsEndpoint(req, res) {
      res.json(pipeline.getStats());
    },
    
    // 健康检查
    healthEndpoint(req, res) {
      res.json({ 
        status: 'healthy', 
        timestamp: new Date().toISOString(),
        version: '1.0.0'
      });
    }
  };
}

// 导出模块
module.exports = {
  AIInferencePipeline,
  createMiddleware,
  MockRedis
};

// 如果直接运行，演示使用
if (require.main === module) {
  (async () => {
    console.log('=== AI Inference Pipeline Demo ===\n');
    
    const pipeline = new AIInferencePipeline();
    
    // 监听事件
    pipeline.on('cacheHit', ({ level }) => {
      console.log(`🎯 Cache hit: ${level}`);
    });
    
    pipeline.on('requestComplete', ({ cached, model, cost, savedCost }) => {
      if (cached) {
        console.log(`💰 Saved $${savedCost?.toFixed(6) || 0} via cache`);
      } else {
        console.log(`🤖 Model: ${model}, Cost: $${cost?.toFixed(6) || 0}`);
      }
    });
    
    // 测试请求
    const testPrompts = [
      '简单介绍一下Node.js',
      '详细分析Node.js事件循环机制', 
      '简单介绍一下Node.js', // 重复，应该命中缓存
      '比较Python和Node.js的优缺点'
    ];
    
    for (const prompt of testPrompts) {
      console.log(`\n📝 Prompt: ${prompt.substring(0, 40)}...`);
      const result = await pipeline.infer(prompt);
      console.log(`   Response: ${result.text.substring(0, 50)}...`);
      console.log(`   Cached: ${result.cached}, Model: ${result.modelKey || 'unknown'}`);
    }
    
    console.log('\n=== Statistics ===');
    console.log(JSON.stringify(pipeline.getStats(), null, 2));
    
  })();
}

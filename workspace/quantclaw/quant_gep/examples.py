"""
Quant-GEP 使用示例

演示如何完整使用Quant-GEP协议
"""

from quant_gep import (
    # Core
    GeneExpression, IndicatorType, IndicatorNode, OperatorNode, Operator,
    ConstantNode, VariableNode, create_buy_signal, create_crossover_signal,
    
    # Operators & Evolution
    GEPConfig, GEPAlgorithm, FitnessResult,
    
    # Backtest
    quick_backtest, create_adapter, MarketType, TimeFrame,
    
    # Protocol
    serialize_gene, deserialize_gene, gene_to_json, gene_from_json,
    ValidationInfo, Metadata, ValidationStatus, GeneSource
)


def example_1_create_gene():
    """示例1: 创建基因表达式"""
    print("=" * 60)
    print("示例1: 创建基因表达式")
    print("=" * 60)
    
    # 方法1: 使用快捷函数创建买入信号
    gene1 = create_buy_signal(IndicatorType.RSI, threshold=30, condition="<")
    print(f"\n方法1 - RSI超卖买入信号:")
    print(f"  Formula: {gene1.to_formula()}")
    print(f"  AST深度: {gene1.get_depth()}")
    print(f"  节点数: {gene1.get_complexity()}")
    
    # 方法2: 创建均线金叉信号
    gene2 = create_crossover_signal(fast_period=20, slow_period=60)
    print(f"\n方法2 - 均线金叉信号:")
    print(f"  Formula: {gene2.to_formula()}")
    
    # 方法3: 手动构建复杂基因
    root = OperatorNode(Operator.AND)
    
    # 条件1: RSI < 30
    rsi = IndicatorNode(IndicatorType.RSI, {"period": 14})
    threshold1 = ConstantNode(30)
    cond1 = OperatorNode(Operator.LT)
    cond1.add_child(rsi)
    cond1.add_child(threshold1)
    
    # 条件2: 成交量 > 100万
    volume = VariableNode("volume")
    threshold2 = ConstantNode(1000000)
    cond2 = OperatorNode(Operator.GT)
    cond2.add_child(volume)
    cond2.add_child(threshold2)
    
    root.add_child(cond1)
    root.add_child(cond2)
    
    gene3 = GeneExpression(root=root, gene_id="custom_001")
    print(f"\n方法3 - 复合条件基因:")
    print(f"  Formula: {gene3.to_formula()}")
    
    return gene1, gene2, gene3


def example_2_evolution():
    """示例2: 进化优化基因"""
    print("\n" + "=" * 60)
    print("示例2: 进化优化基因")
    print("=" * 60)
    
    # 创建初始种群
    config = GEPConfig(
        mutation_rate=0.1,
        crossover_rate=0.7,
        max_depth=8
    )
    
    algo = GEPAlgorithm(config)
    
    # 种子基因
    seed = create_buy_signal(IndicatorType.RSI, 30)
    population = algo.initialize_population(size=20, seed_genes=[seed])
    
    print(f"\n初始种群大小: {len(population)}")
    print(f"种子基因深度: {seed.get_depth()}")
    
    # 模拟适应度函数
    def fitness_fn(gene) -> FitnessResult:
        """模拟适应度评估 (实际应使用回测)"""
        # 基于基因复杂度计算模拟适应度
        complexity = gene.get_complexity()
        depth = gene.get_depth()
        
        # 模拟: 适中复杂度的基因更好
        fitness = 1.0 / (1 + abs(complexity - 10))
        
        return FitnessResult(
            fitness=fitness,
            sharpe_ratio=fitness * 2,
            max_drawdown=-0.1 * depth,
            annual_return=fitness * 0.5
        )
    
    # 执行进化
    print("\n执行进化...")
    final_pop, history = algo.evolve(
        population=population,
        fitness_fn=fitness_fn,
        generations=10,
        callback=lambda s: print(f"  Gen {s.generation}: best={s.best_fitness:.4f}, avg={s.avg_fitness:.4f}")
    )
    
    # 获取最优基因
    final_fitness = [fitness_fn(g).fitness for g in final_pop]
    best_idx = final_fitness.index(max(final_fitness))
    best_gene = final_pop[best_idx]
    
    print(f"\n进化完成!")
    print(f"最优基因: {best_gene.to_formula()}")
    print(f"适应度: {max(final_fitness):.4f}")
    
    return best_gene


def example_3_backtest():
    """示例3: 回测基因"""
    print("\n" + "=" * 60)
    print("示例3: 回测基因")
    print("=" * 60)
    
    # 创建测试基因
    gene = create_buy_signal(IndicatorType.RSI, 30)
    
    # 执行快速回测
    print("\n执行回测...")
    result = quick_backtest(
        gene=gene,
        symbol="BTC-USDT",
        market_type=MarketType.CRYPTO,
        timeframe=TimeFrame.H1
    )
    
    print(f"\n回测结果:")
    print(f"  总交易数: {result.total_trades}")
    print(f"  胜率: {result.win_rate:.2%}")
    print(f"  年化收益: {result.annual_return:.2%}")
    print(f"  最大回撤: {result.max_drawdown:.2%}")
    print(f"  夏普比率: {result.sharpe_ratio:.2f}")
    print(f"  盈亏比: {result.profit_factor:.2f}")
    
    return result


def example_4_protocol():
    """示例4: 协议序列化"""
    print("\n" + "=" * 60)
    print("示例4: 协议序列化")
    print("=" * 60)
    
    # 创建基因
    gene = create_crossover_signal(20, 60)
    gene.gene_id = "test_gene_001"
    gene.generation = 5
    
    # 序列化为Quant-GEP格式
    payload = serialize_gene(
        gene=gene,
        validation=ValidationInfo(
            status=ValidationStatus.VALIDATED,
            sharpe_ratio=1.85,
            max_drawdown=-0.12,
            annual_return=0.35,
            win_rate=0.62,
            total_trades=150
        ),
        meta=Metadata(
            author="QuantClaw-AI",
            source=GeneSource.CROSSOVER,
            tags=["sma", "trend_following", "crypto"],
            description="20/60日均线金叉策略，经GEP进化优化"
        )
    )
    
    print("\n序列化后的Quant-GEP格式:")
    print(gene_to_json(gene))
    
    # 反序列化
    restored = deserialize_gene(payload)
    print(f"\n反序列化成功!")
    print(f"  基因ID: {restored.gene_id}")
    print(f"  代数: {restored.generation}")
    print(f"  公式: {restored.to_formula()}")
    
    return payload


def example_5_complete_workflow():
    """示例5: 完整工作流"""
    print("\n" + "=" * 60)
    print("示例5: 完整工作流 - 发现→进化→回测→保存")
    print("=" * 60)
    
    # 1. 发现初始策略
    print("\n1. 发现初始策略...")
    seed = create_buy_signal(IndicatorType.RSI, 30)
    
    # 2. 进化优化
    print("2. 进化优化...")
    config = GEPConfig(mutation_rate=0.15, generations=20)
    algo = GEPAlgorithm(config)
    
    def fitness_fn(gene):
        # 这里应调用真实回测，使用模拟数据
        return FitnessResult(
            fitness=0.5 + 0.1 * gene.generation,
            sharpe_ratio=1.5,
            max_drawdown=-0.15
        )
    
    population = algo.initialize_population(30, [seed])
    final_pop, history = algo.evolve(population, fitness_fn, generations=5)
    
    best = max(final_pop, key=lambda g: fitness_fn(g).fitness)
    print(f"   最优策略: {best.to_formula()}")
    
    # 3. 回测验证
    print("3. 回测验证...")
    result = quick_backtest(best, symbol="BTC-USDT")
    print(f"   夏普比率: {result.sharpe_ratio:.2f}")
    
    # 4. 保存到协议格式
    print("4. 保存到协议格式...")
    payload = serialize_gene(
        best,
        validation=ValidationInfo(
            status=ValidationStatus.VALIDATED,
            sharpe_ratio=result.sharpe_ratio,
            max_drawdown=result.max_drawdown,
            annual_return=result.annual_return,
            win_rate=result.win_rate
        )
    )
    
    # 保存到文件
    filename = f"strategy_{best.gene_id}.json"
    with open(filename, 'w') as f:
        json.dump(payload, f, indent=2)
    
    print(f"   已保存到: {filename}")
    
    return best, result


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("Quant-GEP 完整示例")
    print(f"协议版本: quant-gep-v1")
    print("=" * 60)
    
    # 运行所有示例
    example_1_create_gene()
    example_2_evolution()
    example_3_backtest()
    example_4_protocol()
    example_5_complete_workflow()
    
    print("\n" + "=" * 60)
    print("所有示例运行完成!")
    print("=" * 60)

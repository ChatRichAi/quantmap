#!/usr/bin/env python3
"""
更新可视化数据 - 从进化数据库导出为可视化JSON
"""

import sqlite3
import json
from datetime import datetime

DB_PATH = "/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db"
OUTPUT_PATH = "/Users/oneday/.openclaw/workspace/quantclaw/ecosystem_data.json"

def export_ecosystem_data():
    """导出基因池数据为可视化格式"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 读取所有基因
    cursor.execute('SELECT * FROM genes')
    gene_rows = cursor.fetchall()
    
    nodes = []
    links = []
    
    # 颜色配置
    colors = {
        'strategy': "#e94560",
        'factor': "#0ea5e9",
        'paper': "#10b981",
        'agent': "#f59e0b",
        'asset': "#8b5cf6"
    }
    
    # 为每个基因创建节点
    for row in gene_rows:
        gene_id = row[0]
        name = row[1]
        formula = row[3]
        generation = row[8]
        parent_id = row[7]
        
        # 根据代数调整节点大小
        radius = 15 + generation * 3
        
        node = {
            "id": gene_id,
            "name": name[:30],
            "type": "factor",
            "formula": formula[:50],
            "generation": generation,
            "category": "evolved" if generation > 0 else "seed",
            "radius": min(radius, 35)
        }
        nodes.append(node)
        
        # 如果有父基因，创建连接
        if parent_id and '+' not in parent_id:  # 单父代
            links.append({
                "source": parent_id,
                "target": gene_id,
                "type": "evolved_from"
            })
        elif parent_id and '+' in parent_id:  # 交叉
            parents = parent_id.split('+')
            for p in parents[:2]:  # 最多两个父代
                links.append({
                    "source": p,
                    "target": gene_id,
                    "type": "crossover"
                })
    
    # 添加策略节点 (模拟)
    strategies = [
        {"id": "strategy_001", "name": "EntropyMomentum Pro", "type": "strategy", "sharpe": 1.8, "radius": 28},
        {"id": "strategy_002", "name": "RSI Mean Reversion", "type": "strategy", "sharpe": 1.5, "radius": 25},
        {"id": "strategy_003", "name": "Complex Hybrid v2", "type": "strategy", "sharpe": 2.1, "radius": 30},
    ]
    nodes.extend(strategies)
    
    # 策略使用因子的连接
    for i, s in enumerate(strategies):
        # 随机连接到2-3个基因
        import random
        if gene_rows:
            targets = random.sample([g[0] for g in gene_rows], min(3, len(gene_rows)))
            for t in targets:
                links.append({
                    "source": s["id"],
                    "target": t,
                    "type": "uses"
                })
    
    # 添加Agent节点
    agents = [
        {"id": "agent_evolution", "name": "Evolution Engine", "type": "agent", "reputation": 95, "radius": 22},
        {"id": "agent_miner", "name": "Genetic Miner", "type": "agent", "reputation": 88, "radius": 20},
    ]
    nodes.extend(agents)
    
    # Agent创建基因的连接
    for g in gene_rows:
        if g[6] == "evolution_engine":  # author
            links.append({
                "source": "agent_evolution",
                "target": g[0],
                "type": "created"
            })
    
    data = {
        "nodes": nodes,
        "links": links,
        "stats": {
            "total_genes": len(gene_rows),
            "seed_genes": sum(1 for g in gene_rows if g[8] == 0),
            "evolved_genes": sum(1 for g in gene_rows if g[8] > 0),
            "max_generation": max((g[8] for g in gene_rows), default=0),
            "timestamp": datetime.now().isoformat()
        }
    }
    
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Exported {len(nodes)} nodes, {len(links)} links")
    print(f"   Genes: {data['stats']['total_genes']} (Seed: {data['stats']['seed_genes']}, Evolved: {data['stats']['evolved_genes']})")
    print(f"   Max Generation: {data['stats']['max_generation']}")
    print(f"   Output: {OUTPUT_PATH}")
    
    conn.close()
    return data

if __name__ == "__main__":
    export_ecosystem_data()

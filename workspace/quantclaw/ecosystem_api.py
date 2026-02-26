#!/usr/bin/env python3
"""
QuantClaw Ecosystem API Server
生态数据API服务器 - 为可视化提供实时数据
"""

import json
import sqlite3
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
from collections import Counter
from math import log

DB_PATH = "/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db"


def get_ecosystem_data():
    """从数据库获取最新生态数据"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    nodes = []
    links = []
    gene_map = {}
    
    # 颜色配置
    type_colors = {
        'strategy': "#e94560",
        'factor': "#0ea5e9", 
        'paper': "#10b981",
        'validated': "#10b981",
        'agent': "#f59e0b",
        'asset': "#8b5cf6"
    }
    
    # 首先尝试从 genes 表获取
    cursor.execute('SELECT * FROM genes ORDER BY created_at DESC')
    gene_rows = cursor.fetchall()
    
    # 如果 genes 表为空，从 backtest_results 聚合数据
    if not gene_rows:
        cursor.execute('''
            SELECT gene_id, 
                   MAX(sharpe_ratio) as best_sharpe,
                   AVG(sharpe_ratio) as avg_sharpe,
                   MAX(total_return) as best_return,
                   AVG(win_rate) as avg_win_rate,
                   MAX(max_drawdown) as max_dd,
                   COUNT(*) as test_count,
                   MAX(timestamp) as last_test
            FROM backtest_results 
            GROUP BY gene_id
            ORDER BY best_sharpe DESC
            LIMIT 200
        ''')
        bt_rows = cursor.fetchall()
        
        for i, row in enumerate(bt_rows):
            gene_id = row[0]
            best_sharpe = row[1] or 0
            avg_sharpe = row[2] or 0
            best_return = row[3] or 0
            avg_win_rate = row[4] or 0
            max_dd = row[5] or 0
            test_count = row[6] or 1
            
            # 确定状态
            if best_sharpe > 1.0:
                status = 'validated'
                node_type = 'validated'
            elif best_sharpe > 0:
                status = 'tested'
                node_type = 'strategy'
            else:
                status = 'failed'
                node_type = 'factor'
            
            # 模拟代数 (基于测试次数)
            generation = min(test_count // 3, 5)
            radius = min(12 + generation * 2 + (best_sharpe * 3 if best_sharpe > 0 else 0), 30)
            
            node = {
                "id": gene_id,
                "name": f"Gene_{gene_id[:8]}",
                "type": node_type,
                "formula": f"Backtest Score: {best_sharpe:.2f}",
                "generation": generation,
                "radius": radius,
                "color": type_colors.get(node_type, "#0ea5e9"),
                "score": best_sharpe,
                "status": status,
                "win_rate": avg_win_rate,
                "max_drawdown": max_dd,
                "test_count": test_count
            }
            nodes.append(node)
            gene_map[gene_id] = i
        
        # 创建伪链接 (基于相似性能分组)
        sorted_nodes = sorted(nodes, key=lambda x: x.get('score', 0), reverse=True)
        for i in range(1, min(len(sorted_nodes), 50)):
            if sorted_nodes[i-1]['score'] > 0 and sorted_nodes[i]['score'] > 0:
                links.append({
                    "source": sorted_nodes[i-1]['id'],
                    "target": sorted_nodes[i]['id'],
                    "type": "similarity",
                    "shared_count": 1
                })
    else:
        # 原始逻辑: 从 genes 表获取
        for i, row in enumerate(gene_rows):
            gene_id = row[0]
            name = row[1]
            formula = row[3] if len(row) > 3 else ""
            generation = row[8] if len(row) > 8 else 0
            parent_id = row[7] if len(row) > 7 else None
            
            if generation == 0:
                node_type = 'paper' if 'paper' in str(row[5] if len(row) > 5 else '') else 'factor'
            elif 'RSI' in str(formula) or 'MACD' in str(formula) or 'SMA' in str(formula):
                node_type = 'strategy'
            else:
                node_type = 'factor'
            
            radius = min(15 + (generation or 0) * 2, 30)
            
            node = {
                "id": gene_id,
                "name": str(name)[:30] if name else gene_id[:8],
                "type": node_type,
                "formula": str(formula)[:50] if formula else "",
                "generation": generation or 0,
                "radius": radius,
                "color": type_colors.get(node_type, "#0ea5e9"),
                "status": "active"
            }
            nodes.append(node)
            gene_map[gene_id] = i
            
            if parent_id and '+' not in str(parent_id):
                links.append({
                    "source": parent_id,
                    "target": gene_id,
                    "type": "evolved_from"
                })
            elif parent_id and '+' in str(parent_id):
                parents = str(parent_id).split('+')[:2]
                for p in parents:
                    links.append({
                        "source": p,
                        "target": gene_id,
                        "type": "crossover"
                    })
    
    # 链路共享计数，用于可视化信任/复用强度
    parent_usage = Counter(link["source"] for link in links if link.get("source"))
    for link in links:
        link["shared_count"] = parent_usage.get(link["source"], 1)

    # 获取统计信息
    cursor.execute('SELECT COUNT(*) FROM genes')
    total_genes = cursor.fetchone()[0]
    
    cursor.execute('SELECT COUNT(DISTINCT parent_gene_id) FROM genes WHERE parent_gene_id IS NOT NULL')
    unique_parents = cursor.fetchone()[0]
    
    # 信任分（如果已启用 agent_reputation）
    top_agent_score = 0.0
    try:
        cursor.execute('SELECT MAX(score) FROM agent_reputation')
        top_agent_score = cursor.fetchone()[0] or 0.0
    except sqlite3.OperationalError:
        top_agent_score = 0.0

    conn.close()
    
    # 限制显示数量，并确保 links 只引用存在的节点
    display_nodes = nodes[:100]
    node_ids = {n["id"] for n in display_nodes}
    
    # 过滤 links，确保 source 和 target 都存在于 node_ids 中
    valid_links = [
        link for link in links 
        if link["source"] in node_ids and link["target"] in node_ids
    ]
    
    # Shannon 多样性（用于 Negentropy 指标）
    formula_counter = Counter(n["formula"] for n in display_nodes if n.get("formula"))
    shannon_diversity = 0.0
    total_formula = sum(formula_counter.values())
    if total_formula > 0:
        for count in formula_counter.values():
            p = count / total_formula
            shannon_diversity -= p * log(p) if p > 0 else 0.0

    return {
        "nodes": display_nodes,
        "links": valid_links[:200],
        "stats": {
            "total_genes": total_genes,
            "total_nodes": len(display_nodes),
            "total_links": len(valid_links),
            "unique_lineages": unique_parents,
            "negentropy_saved_compute": len(valid_links),
            "shannon_diversity": shannon_diversity,
            "top_agent_score": top_agent_score,
            "timestamp": datetime.now().isoformat()
        }
    }


class APIHandler(BaseHTTPRequestHandler):
    """API请求处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/api/ecosystem':
            # 获取生态数据
            data = get_ecosystem_data()
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            
        elif self.path == '/api/stats':
            # 获取统计数据
            data = get_ecosystem_data()['stats']
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
            
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """静默日志"""
        pass


def start_api_server(port=8889):
    """启动API服务器"""
    server = HTTPServer(('localhost', port), APIHandler)
    print(f"🌐 Ecosystem API Server started at http://localhost:{port}")
    print(f"   Endpoints:")
    print(f"   - GET /api/ecosystem  (完整生态数据)")
    print(f"   - GET /api/stats      (统计数据)")
    server.serve_forever()


if __name__ == "__main__":
    start_api_server()

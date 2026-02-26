#!/usr/bin/env python3
"""
报告生成器 - 生成 Markdown 和 HTML 分析报告
"""

import json
from datetime import datetime
from pathlib import Path

def generate_markdown_report(stock_data, analysis_result, output_path=None):
    """
    生成 Markdown 分析报告
    
    Args:
        stock_data: 股票基础数据
        analysis_result: 分析结果字典
        output_path: 输出路径（可选）
    """
    code = stock_data.get('code', '')
    name = stock_data.get('name', '')
    score = analysis_result.get('total_score', 0)
    
    # 评分颜色
    score_color = "🟢" if score >= 7 else "🟡" if score >= 5 else "🔴"
    
    report = f"""# {score_color} 股票狙击手分析报告

## {name} ({code})

**分析时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**综合评分**: {score}/10

---

## 📊 基础数据

| 指标 | 数值 |
|------|------|
| 当前价格 | ¥{stock_data.get('price', 'N/A')} |
| 涨跌幅 | {stock_data.get('change_pct', 'N/A')}% |
| 成交额 | {stock_data.get('amount', 'N/A')} |
| 异动类型 | {stock_data.get('type', 'N/A')} |

---

## 一、指数环境分析

{analysis_result.get('index_analysis', '待分析')}

---

## 二、题材热点分析

{analysis_result.get('theme_analysis', '待分析')}

---

## 三、技术分析 (TradingView)

### 多周期图表
- 5分钟图: {analysis_result.get('tv_5m_summary', 'N/A')}
- 15分钟图: {analysis_result.get('tv_15m_summary', 'N/A')}
- 1小时图: {analysis_result.get('tv_1h_summary', 'N/A')}

### 关键价位
- 支撑位: {analysis_result.get('support_levels', 'N/A')}
- 阻力位: {analysis_result.get('resistance_levels', 'N/A')}

### 订单流分析
{analysis_result.get('order_flow_analysis', '待分析')}

---

## 四、资金流向

{analysis_result.get('fund_flow_analysis', '待分析')}

---

## 五、舆情情绪

{analysis_result.get('sentiment_analysis', '待分析')}

---

## 六、超短六要素评分

| 要素 | 评分 | 说明 |
|------|------|------|
| 指数环境 | {analysis_result.get('score_index', 'N/A')}/10 | {analysis_result.get('note_index', '')} |
| 主线题材 | {analysis_result.get('score_theme', 'N/A')}/10 | {analysis_result.get('note_theme', '')} |
| 情绪周期 | {analysis_result.get('score_emotion', 'N/A')}/10 | {analysis_result.get('note_emotion', '')} |
| 个股定位 | {analysis_result.get('score_stock', 'N/A')}/10 | {analysis_result.get('note_stock', '')} |
| 风偏识别 | {analysis_result.get('score_style', 'N/A')}/10 | {analysis_result.get('note_style', '')} |
| 联动关系 | {analysis_result.get('score_correlation', 'N/A')}/10 | {analysis_result.get('note_correlation', '')} |

---

## 🎯 交易建议

### 操作评级: {analysis_result.get('action_rating', '观望')}

| 项目 | 建议 |
|------|------|
| 操作建议 | {analysis_result.get('suggestion_action', '观望')} |
| 入场价位 | {analysis_result.get('entry_price', '等待信号')} |
| 止损价位 | {analysis_result.get('stop_loss', '待确认')} |
| 目标价位 | {analysis_result.get('target_price', '待确认')} |
| 仓位建议 | {analysis_result.get('position_size', '轻仓试错')} |
| 持股周期 | {analysis_result.get('hold_period', '超短（1-3天）')} |

### 风险提示
{analysis_result.get('risk_warning', '市场有风险，投资需谨慎。本分析仅供参考，不构成投资建议。')}

---

*报告生成 by 股票狙击手*  
*基于超短策略框架分析*
"""
    
    if output_path:
        Path(output_path).write_text(report, encoding='utf-8')
        print(f"✅ Markdown 报告已保存: {output_path}")
    
    return report

def generate_html_report(stock_data, analysis_result, output_path=None):
    """生成 HTML 可视化报告"""
    
    code = stock_data.get('code', '')
    name = stock_data.get('name', '')
    score = analysis_result.get('total_score', 0)
    
    # 评分颜色类
    score_class = "high" if score >= 7 else "medium" if score >= 5 else "low"
    
    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>股票狙击手 - {name} ({code}) 分析报告</title>
    <link rel="stylesheet" href="chart_styles.css">
    <style>
        :root {{
            --bg-dark: #0d1117;
            --bg-card: #161b22;
            --bg-hover: #21262d;
            --text-primary: #e6edf3;
            --text-secondary: #8b949e;
            --accent-green: #238636;
            --accent-red: #da3633;
            --accent-yellow: #d29922;
            --border: #30363d;
        }}
        
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans SC', sans-serif;
            background: var(--bg-dark);
            color: var(--text-primary);
            line-height: 1.6;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            padding: 30px 0;
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }}
        
        .header h1 {{
            font-size: 2em;
            margin-bottom: 10px;
            background: linear-gradient(90deg, #58a6ff, #a371f7);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .stock-info {{
            font-size: 1.3em;
            color: var(--text-secondary);
        }}
        
        .score-card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 30px;
            text-align: center;
            margin-bottom: 30px;
            border: 1px solid var(--border);
        }}
        
        .score-value {{
            font-size: 4em;
            font-weight: bold;
            margin: 20px 0;
        }}
        
        .score-value.high {{ color: var(--accent-green); }}
        .score-value.medium {{ color: var(--accent-yellow); }}
        .score-value.low {{ color: var(--accent-red); }}
        
        .grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .card {{
            background: var(--bg-card);
            border-radius: 12px;
            padding: 20px;
            border: 1px solid var(--border);
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,0,0,0.3);
        }}
        
        .card h3 {{
            color: #58a6ff;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 8px;
        }}
        
        .data-table {{
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }}
        
        .data-table th,
        .data-table td {{
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid var(--border);
        }}
        
        .data-table th {{
            color: var(--text-secondary);
            font-weight: 500;
        }}
        
        .badge {{
            display: inline-block;
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 0.85em;
            font-weight: 500;
        }}
        
        .badge-buy {{
            background: rgba(35, 134, 54, 0.2);
            color: #3fb950;
        }}
        
        .badge-hold {{
            background: rgba(210, 153, 34, 0.2);
            color: #d29922;
        }}
        
        .badge-sell {{
            background: rgba(218, 54, 51, 0.2);
            color: #f85149;
        }}
        
        .chart-placeholder {{
            background: var(--bg-hover);
            border-radius: 8px;
            height: 300px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--text-secondary);
            margin-top: 15px;
        }}
        
        .action-section {{
            background: linear-gradient(135deg, #1f2937 0%, #111827 100%);
            border-radius: 12px;
            padding: 30px;
            margin-top: 30px;
        }}
        
        .action-section h2 {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .action-grid {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 20px;
            margin-top: 20px;
        }}
        
        .action-item {{
            text-align: center;
            padding: 20px;
            background: var(--bg-card);
            border-radius: 8px;
        }}
        
        .action-item .label {{
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-bottom: 8px;
        }}
        
        .action-item .value {{
            font-size: 1.4em;
            font-weight: bold;
            color: #58a6ff;
        }}
        
        .risk-warning {{
            background: rgba(218, 54, 51, 0.1);
            border-left: 4px solid var(--accent-red);
            padding: 15px 20px;
            border-radius: 0 8px 8px 0;
            margin-top: 30px;
            color: var(--text-secondary);
        }}
        
        .timestamp {{
            text-align: center;
            color: var(--text-secondary);
            font-size: 0.9em;
            margin-top: 30px;
        }}
        
        @media (max-width: 768px) {{
            .action-grid {{
                grid-template-columns: 1fr;
            }}
            .grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎯 股票狙击手</h1>
            <div class="stock-info">{name} ({code}) 分析报告</div>
            <div class="timestamp">生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</div>
        </div>
        
        <div class="score-card">
            <div>综合评分</div>
            <div class="score-value {score_class}">{score}</div>
            <div>满分 10 分</div>
        </div>
        
        <div class="grid">
            <div class="card">
                <h3>📈 基础数据</h3>
                <table class="data-table">
                    <tr><td>当前价格</td><td>¥{stock_data.get('price', 'N/A')}</td></tr>
                    <tr><td>涨跌幅</td><td>{stock_data.get('change_pct', 'N/A')}%</td></tr>
                    <tr><td>成交额</td><td>{stock_data.get('amount', 'N/A')}</td></tr>
                    <tr><td>异动类型</td><td><span class="badge badge-buy">{stock_data.get('type', 'N/A')}</span></td></tr>
                </table>
            </div>
            
            <div class="card">
                <h3>🎯 题材热点</h3>
                <p>{analysis_result.get('theme_analysis', '待分析')[:200]}...</p>
            </div>
            
            <div class="card">
                <h3>📊 技术分析</h3>
                <p><strong>支撑位:</strong> {analysis_result.get('support_levels', 'N/A')}</p>
                <p><strong>阻力位:</strong> {analysis_result.get('resistance_levels', 'N/A')}</p>
                <div class="chart-placeholder">
                    TradingView 图表区域
                </div>
            </div>
            
            <div class="card">
                <h3>💰 资金流向</h3>
                <p>{analysis_result.get('fund_flow_analysis', '待分析')[:200]}...</p>
            </div>
            
            <div class="card">
                <h3>😊 舆情情绪</h3>
                <p>{analysis_result.get('sentiment_analysis', '待分析')[:200]}...</p>
            </div>
            
            <div class="card">
                <h3>⚡ 六要素评分</h3>
                <table class="data-table">
                    <tr><td>指数环境</td><td>{analysis_result.get('score_index', 'N/A')}/10</td></tr>
                    <tr><td>主线题材</td><td>{analysis_result.get('score_theme', 'N/A')}/10</td></tr>
                    <tr><td>情绪周期</td><td>{analysis_result.get('score_emotion', 'N/A')}/10</td></tr>
                    <tr><td>个股定位</td><td>{analysis_result.get('score_stock', 'N/A')}/10</td></tr>
                    <tr><td>风偏识别</td><td>{analysis_result.get('score_style', 'N/A')}/10</td></tr>
                    <tr><td>联动关系</td><td>{analysis_result.get('score_correlation', 'N/A')}/10</td></tr>
                </table>
            </div>
        </div>
        
        <div class="action-section">
            <h2>🎯 交易建议</h2>
            <div style="text-align: center; margin-bottom: 20px;">
                <span class="badge {analysis_result.get('action_badge_class', 'badge-hold')}" style="font-size: 1.2em; padding: 8px 20px;">
                    {analysis_result.get('action_rating', '观望')}
                </span>
            </div>
            <div class="action-grid">
                <div class="action-item">
                    <div class="label">入场价位</div>
                    <div class="value">{analysis_result.get('entry_price', '等待信号')}</div>
                </div>
                <div class="action-item">
                    <div class="label">止损价位</div>
                    <div class="value">{analysis_result.get('stop_loss', '待确认')}</div>
                </div>
                <div class="action-item">
                    <div class="label">目标价位</div>
                    <div class="value">{analysis_result.get('target_price', '待确认')}</div>
                </div>
            </div>
        </div>
        
        <div class="risk-warning">
            <strong>⚠️ 风险提示</strong><br>
            {analysis_result.get('risk_warning', '市场有风险，投资需谨慎。本分析仅供参考，不构成投资建议。')}
        </div>
        
        <div class="timestamp">
            报告生成 by 股票狙击手 | 基于超短策略框架
        </div>
    </div>
</body>
</html>'''
    
    if output_path:
        Path(output_path).write_text(html, encoding='utf-8')
        print(f"✅ HTML 报告已保存: {output_path}")
    
    return html

if __name__ == "__main__":
    # 测试
    test_stock = {'code': '000001', 'name': '平安银行', 'price': 12.5, 'change_pct': 5.2, 'amount': '1.2亿', 'type': '快速拉升'}
    test_analysis = {
        'total_score': 7.5,
        'action_rating': '关注',
        'action_badge_class': 'badge-hold',
        'support_levels': '12.00',
        'resistance_levels': '13.50',
        'score_index': 7, 'score_theme': 8, 'score_emotion': 7,
        'score_stock': 8, 'score_style': 7, 'score_correlation': 7,
    }
    print(generate_markdown_report(test_stock, test_analysis))

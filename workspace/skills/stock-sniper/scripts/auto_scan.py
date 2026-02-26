#!/usr/bin/env python3
"""
股票狙击手 - 自动运行脚本
用于定时任务调用
"""

import sys
import json
from pathlib import Path
from datetime import datetime

# 确保能导入脚本
sys.path.insert(0, str(Path(__file__).parent))

from stock_sniper import StockSniper

def auto_scan():
    """
    自动扫描市场 - 供定时任务调用
    """
    print(f"\n{'='*60}")
    print(f"🤖 股票狙击手自动扫描启动")
    print(f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}\n")
    
    sniper = StockSniper()
    
    try:
        # 扫描并分析前8只异动股票
        results = sniper.scan_and_analyze(top_n=8)
        
        # 筛选高分股票 (>6分)
        good_stocks = [r for r in results if r['score'] >= 6]
        
        # 输出摘要（用于通知）
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_analyzed': len(results),
            'good_stocks_count': len(good_stocks),
            'good_stocks': [
                {
                    'code': r['stock_code'],
                    'name': r['stock_name'],
                    'score': r['score'],
                    'rating': r['rating']
                }
                for r in good_stocks
            ]
        }
        
        print(f"\n{'='*60}")
        print(f"📊 扫描完成摘要")
        print(f"{'='*60}")
        print(f"分析股票数: {summary['total_analyzed']}")
        print(f"高分股票数: {summary['good_stocks_count']}")
        
        if good_stocks:
            print(f"\n值得关注:")
            for s in summary['good_stocks']:
                print(f"  🟢 {s['name']}({s['code']}) - {s['score']}分 - {s['rating']}")
        
        # 保存摘要
        output_dir = Path(__file__).parent.parent / 'output'
        summary_path = output_dir / f"scan_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
        
        return summary
        
    except Exception as e:
        print(f"❌ 自动扫描失败: {e}")
        import traceback
        traceback.print_exc()
        return {'error': str(e)}

if __name__ == "__main__":
    auto_scan()

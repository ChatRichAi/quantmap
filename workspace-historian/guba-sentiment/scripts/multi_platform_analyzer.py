#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三平台情绪分析整合工具
整合: 东方财富 + 雪球 + 淘股吧
"""

import sys
import json
import argparse
from datetime import datetime

# 导入各平台接口
sys.path.insert(0, '.')
from scripts.sentiment_analyzer import fetch_real_data, calculate_sentiment_from_data
from scripts.xueqiu_api import analyze_xueqiu_sentiment
from scripts.taoguba_api import analyze_taoguba_sentiment


def analyze_all_platforms(code, demo_mode=False):
    """
    分析所有三个平台的情绪数据
    """
    print(f"\n{'='*65}")
    print(f"🔍 三平台情绪综合分析: {code}")
    print(f"{'='*65}")
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # 1. 东方财富
    print("【1/3】东方财富数据...")
    try:
        eastmoney_data = fetch_real_data(code)
        if eastmoney_data['basic']:
            eastmoney_sentiment = calculate_sentiment_from_data(eastmoney_data)
            results['eastmoney'] = {
                'platform': '东方财富',
                'data': eastmoney_data,
                'sentiment': eastmoney_sentiment,
                'status': 'success',
            }
            print(f"  ✅ 获取成功 | 情绪指数: {eastmoney_sentiment['sentiment_index']:+.1f}")
        else:
            results['eastmoney'] = {'status': 'failed', 'error': '无数据'}
            print("  ❌ 获取失败")
    except Exception as e:
        results['eastmoney'] = {'status': 'failed', 'error': str(e)}
        print(f"  ❌ 错误: {e}")
    
    # 2. 雪球
    print("\n【2/3】雪球数据...")
    try:
        xueqiu_result = analyze_xueqiu_sentiment(code, use_demo=demo_mode)
        results['xueqiu'] = xueqiu_result
        if demo_mode:
            print(f"  🎮 演示模式 | 情绪指数: {xueqiu_result['sentiment']['index']:+.1f}")
        else:
            print(f"  {'✅' if 'data' in xueqiu_result else '⚠️'} 情绪指数: {xueqiu_result['sentiment']['index']:+.1f}")
    except Exception as e:
        results['xueqiu'] = {'status': 'failed', 'error': str(e)}
        print(f"  ❌ 错误: {e}")
    
    # 3. 淘股吧
    print("\n【3/3】淘股吧数据...")
    try:
        taoguba_result = analyze_taoguba_sentiment(code, use_demo=True)  # 淘股吧暂时只能用演示
        results['taoguba'] = taoguba_result
        print(f"  🎮 演示模式 | 情绪指数: {taoguba_result['sentiment']['index']:+.1f}")
    except Exception as e:
        results['taoguba'] = {'status': 'failed', 'error': str(e)}
        print(f"  ❌ 错误: {e}")
    
    return results


def calculate_composite_sentiment(results):
    """
    计算综合情绪指数
    权重: 东方财富 40%, 雪球 35%, 淘股吧 25%
    """
    weights = {
        'eastmoney': 0.40,
        'xueqiu': 0.35,
        'taoguba': 0.25,
    }
    
    composite_index = 0
    valid_platforms = 0
    
    for platform, weight in weights.items():
        if platform in results and 'sentiment' in results[platform]:
            sentiment_data = results[platform]['sentiment']
            if 'sentiment_index' in sentiment_data:
                composite_index += sentiment_data['sentiment_index'] * weight
                valid_platforms += 1
            elif 'index' in sentiment_data:
                composite_index += sentiment_data['index'] * weight
                valid_platforms += 1
    
    # 如果没有有效数据，返回0
    if valid_platforms == 0:
        return {'index': 0, 'label': '未知', 'confidence': 0}
    
    # 标准化到 -50 ~ +50
    composite_index = max(-50, min(50, composite_index))
    
    # 情绪标签
    if composite_index > 40:
        label = '🔥 极度乐观'
    elif composite_index > 20:
        label = '📈 乐观'
    elif composite_index > 5:
        label = '↗️ 偏多'
    elif composite_index < -40:
        label = '❄️ 极度悲观'
    elif composite_index < -20:
        label = '📉 悲观'
    elif composite_index < -5:
        label = '↘️ 偏空'
    else:
        label = '😐 中性'
    
    return {
        'index': round(composite_index, 1),
        'label': label,
        'confidence': min(100, valid_platforms * 33 + 1),
    }


def print_composite_report(code, results, composite):
    """打印综合报告"""
    print("\n" + "=" * 65)
    print(f"📊 {code} - 三平台情绪综合分析报告")
    print("=" * 65)
    
    # 各平台数据
    print("\n【各平台情绪指数】")
    print("-" * 50)
    
    platforms = [
        ('eastmoney', '东方财富', '40%'),
        ('xueqiu', '雪球', '35%'),
        ('taoguba', '淘股吧', '25%'),
    ]
    
    for key, name, weight in platforms:
        if key in results and 'sentiment' in results[key]:
            sentiment = results[key]['sentiment']
            index = sentiment.get('sentiment_index') or sentiment.get('index', 0)
            label = sentiment.get('sentiment_label', '未知')
            
            # 可视化条
            bar_len = int(abs(index))
            bar = "█" * bar_len + "░" * (25 - bar_len)
            if index >= 0:
                bar_display = f"[+{bar} ]"
            else:
                bar_display = f"[{bar}+]"
            
            print(f"  {name:8} (权重{weight}): {index:+6.1f} | {label:8} {bar_display}")
        else:
            print(f"  {name:8} (权重{weight}):  无数据")
    
    # 综合情绪
    print("\n" + "=" * 50)
    print("【综合情绪指数】")
    print("-" * 50)
    
    idx = composite['index']
    bar_len = int(abs(idx))
    bar = "█" * bar_len + "░" * (50 - bar_len)
    if idx >= 0:
        print(f"  [-50░░░░░░░░░░░░░░░░░░] {bar[:25]} [+50]")
    else:
        print(f"  [-50] {bar[:25]} [░░░░░░░░░░░░░░░░░░+50]")
    
    print(f"\n  综合指数: {idx:+.1f}")
    print(f"  情绪判断: {composite['label']}")
    print(f"  数据可信度: {composite['confidence']}%")
    
    # 交易建议
    print("\n【交易参考】")
    print("-" * 50)
    
    if idx > 40:
        print("  ⚠️ 三平台情绪极度乐观，警惕过热反转")
        print("  💡 建议: 考虑分批减仓，不追高")
        print("  📍 适合: 持有者兑现利润，空仓者观望")
    elif idx > 20:
        print("  ✅ 情绪整体乐观，趋势向好")
        print("  💡 建议: 持有为主，新仓轻仓试探")
        print("  📍 适合: 趋势跟踪，设置移动止损")
    elif idx > 5:
        print("  ↗️ 情绪轻度偏多，可谨慎参与")
        print("  💡 建议: 关注量能，严格止损")
        print("  📍 适合: 低吸高抛，快进快出")
    elif idx < -40:
        print("  🎯 情绪极度悲观，可能物极必反")
        print("  💡 建议: 关注超跌反弹机会，但需等企稳")
        print("  📍 适合: 左侧交易者关注，右侧等待信号")
    elif idx < -20:
        print("  ⚠️ 情绪整体偏空，注意风险")
        print("  💡 建议: 控制仓位，减仓避险")
        print("  📍 适合: 空仓观望或轻仓试错")
    elif idx < -5:
        print("  ↘️ 情绪轻度偏空，谨慎操作")
        print("  💡 建议: 多看少动，等待情绪修复")
        print("  📍 适合: 观望为主")
    else:
        print("  😐 情绪中性，方向不明")
        print("  💡 建议: 等待明确信号，不盲目操作")
        print("  📍 适合: 观望或极轻仓试错")
    
    # 平台特色分析
    print("\n【平台特色观察】")
    print("-" * 50)
    
    if 'eastmoney' in results and 'sentiment' in results['eastmoney']:
        em_idx = results['eastmoney']['sentiment'].get('sentiment_index', 0)
        if em_idx > 30:
            print("  📍 东财: 散户关注度高，人气旺盛")
        elif em_idx < -30:
            print("  📍 东财: 散户情绪低落，需注意风险")
    
    if 'xueqiu' in results and 'sentiment' in results['xueqiu']:
        xq_idx = results['xueqiu']['sentiment'].get('index', 0)
        if xq_idx > 20:
            print("  📍 雪球: 专业投资者看多，基本面受认可")
        elif xq_idx < -20:
            print("  📍 雪球: 专业投资者谨慎，关注基本面风险")
    
    if 'taoguba' in results and 'sentiment' in results['taoguba']:
        tgb_idx = results['taoguba']['sentiment'].get('index', 0)
        if tgb_idx > 20:
            print("  📍 淘股吧: 超短资金活跃，关注连板机会")
        elif tgb_idx < -20:
            print("  📍 淘股吧: 短线资金谨慎，注意炸板风险")
    
    print("\n" + "=" * 65)
    print("⚠️ 免责声明: 情绪数据仅供参考，不构成投资建议")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(description='三平台情绪综合分析')
    parser.add_argument('--code', '-c', default='600875', help='股票代码')
    parser.add_argument('--demo', '-d', action='store_true', help='全部使用演示数据')
    parser.add_argument('--output', '-o', help='输出文件')
    
    args = parser.parse_args()
    
    # 分析所有平台
    results = analyze_all_platforms(args.code, demo_mode=args.demo)
    
    # 计算综合情绪
    composite = calculate_composite_sentiment(results)
    
    # 打印报告
    print_composite_report(args.code, results, composite)
    
    # 保存结果
    if args.output:
        output_data = {
            'code': args.code,
            'analysis_time': datetime.now().isoformat(),
            'composite_sentiment': composite,
            'platform_results': results,
        }
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ 结果已保存: {args.output}")


if __name__ == '__main__':
    main()

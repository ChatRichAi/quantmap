#!/usr/bin/env python3
"""
QuantMap Seed Library Importer
多源因子种子库批量导入器

来源：
  1. WorldQuant 101 Alphas（内置，无需网络）
  2. arXiv 批量采集（复用 arxiv_gene_extractor.py）
  3. Quantocracy RSS（实战博主策略因子）

Usage:
    python3 seed_library_importer.py --source all
    python3 seed_library_importer.py --source worldquant
    python3 seed_library_importer.py --source arxiv --limit 100
    python3 seed_library_importer.py --source quantocracy
    python3 seed_library_importer.py --source all --dry-run
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
from urllib import request as urllib_request
from urllib.error import URLError
from xml.etree import ElementTree as ET

DB_PATH = "/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db"
sys.path.insert(0, "/Users/oneday/.openclaw/workspace/quantclaw")

from evolution_ecosystem import Gene, QuantClawEvolutionHub


# ── WorldQuant 101 Alphas ─────────────────────────────────────────────────────
# 精选 35 个可直接表达为价量公式的 Alpha，来源：
# "101 Formulaic Alphas" (Zura Kakushadze, 2016)
# https://arxiv.org/abs/1601.00991

WORLDQUANT_ALPHAS: List[Dict[str, Any]] = [
    {
        "name": "alpha001_signed_power",
        "formula": "rank(ts_argmax(signed_power(close, 2), 5)) - 0.5",
        "description": "Signed power of close price ranked over 5-day argmax window",
        "category": "momentum",
        "params": {"window": 5},
    },
    {
        "name": "alpha002_vol_price_corr",
        "formula": "-corr(rank(delta(log(volume), 2)), rank((close - open) / open), 6)",
        "description": "Negative correlation between volume changes and intraday returns",
        "category": "volume",
        "params": {"window": 6},
    },
    {
        "name": "alpha003_open_vol_corr",
        "formula": "-corr(rank(open), rank(volume), 10)",
        "description": "Negative rank correlation between open price and volume",
        "category": "volume",
        "params": {"window": 10},
    },
    {
        "name": "alpha004_ts_rank_low",
        "formula": "-ts_rank(rank(low), 9)",
        "description": "Negative time-series rank of cross-sectional rank of low price",
        "category": "reversal",
        "params": {"window": 9},
    },
    {
        "name": "alpha005_open_vwap",
        "formula": "rank(open - ts_sum(vwap, 10) / 10) * -abs(rank(close - vwap))",
        "description": "Open price deviation from VWAP weighted by close-VWAP spread",
        "category": "mean_reversion",
        "params": {"window": 10},
    },
    {
        "name": "alpha006_open_vol_corr",
        "formula": "-corr(open, volume, 10)",
        "description": "Negative correlation between open price and volume over 10 days",
        "category": "volume",
        "params": {"window": 10},
    },
    {
        "name": "alpha007_adv20_delta",
        "formula": "sign(delta(close, 7)) * -ts_rank(abs(delta(close, 7)), 60)",
        "description": "Signed delta of close price scaled by its 60-day rank",
        "category": "momentum",
        "params": {"delta_window": 7, "rank_window": 60},
    },
    {
        "name": "alpha008_open_ret",
        "formula": "-rank(ts_sum(open, 5) * ts_sum(returns, 5) - ts_lag(ts_sum(open, 5) * ts_sum(returns, 5), 10))",
        "description": "Momentum of open-weighted returns over 5-day windows",
        "category": "momentum",
        "params": {"window": 5},
    },
    {
        "name": "alpha009_delta_close",
        "formula": "0 < ts_min(delta(close, 1), 5) if ts_min(delta(close, 1), 5) > 0 else (ts_max(delta(close, 1), 5) < 0 if ts_max(delta(close, 1), 5) < 0 else -delta(close, 1))",
        "description": "Directional close delta with trend confirmation",
        "category": "momentum",
        "params": {"window": 5},
    },
    {
        "name": "alpha010_close_delta_rank",
        "formula": "rank(0 < ts_min(delta(close, 1), 4) if ts_min(delta(close, 1), 4) > 0 else (ts_max(delta(close, 1), 4) < 0 if ts_max(delta(close, 1), 4) < 0 else -delta(close, 1)))",
        "description": "Ranked directional close delta over 4 days",
        "category": "momentum",
        "params": {"window": 4},
    },
    {
        "name": "alpha012_vol_price_sign",
        "formula": "sign(delta(volume, 1)) * -delta(close, 1)",
        "description": "Volume direction multiplied by negative price change",
        "category": "reversal",
        "params": {},
    },
    {
        "name": "alpha013_cov_vol_close",
        "formula": "-rank(covariance(rank(close), rank(volume), 5))",
        "description": "Negative rank of covariance between close and volume ranks",
        "category": "volume",
        "params": {"window": 5},
    },
    {
        "name": "alpha014_open_ret_corr",
        "formula": "-rank(delta(returns, 3)) * corr(open, volume, 10)",
        "description": "Return momentum scaled by open-volume correlation",
        "category": "momentum",
        "params": {"delta": 3, "corr_window": 10},
    },
    {
        "name": "alpha015_high_vol_corr",
        "formula": "-ts_sum(rank(corr(rank(high), rank(volume), 3)), 3)",
        "description": "Accumulated rank of high-volume correlation",
        "category": "volume",
        "params": {"corr_window": 3, "sum_window": 3},
    },
    {
        "name": "alpha016_high_vol_cov",
        "formula": "-rank(covariance(rank(high), rank(volume), 5))",
        "description": "Negative rank of high-volume covariance",
        "category": "volume",
        "params": {"window": 5},
    },
    {
        "name": "alpha017_close_vol",
        "formula": "-rank(ts_rank(close, 10)) * rank(delta(delta(close, 1), 1)) * rank(ts_rank(volume / adv20, 5))",
        "description": "Multi-factor: price trend, acceleration, and volume relative to ADV",
        "category": "momentum",
        "params": {"price_window": 10, "vol_window": 5},
    },
    {
        "name": "alpha018_corr_close_open",
        "formula": "-rank(ts_std(abs(close - open), 5) + close - open + corr(close, open, 10))",
        "description": "Intraday range volatility combined with close-open correlation",
        "category": "volatility",
        "params": {"std_window": 5, "corr_window": 10},
    },
    {
        "name": "alpha019_close_ret",
        "formula": "-sign(close - ts_lag(close, 7) + delta(close, 7)) * (1 + rank(1 + ts_sum(returns, 250)))",
        "description": "Contrarian signal based on 7-day lag weighted by 250-day return rank",
        "category": "reversal",
        "params": {"lag": 7, "return_window": 250},
    },
    {
        "name": "alpha020_open_high_low",
        "formula": "-rank(open - ts_lag(high, 1)) * rank(open - ts_lag(close, 1)) * rank(open - ts_lag(low, 1))",
        "description": "Open gap product across high, close, and low benchmarks",
        "category": "momentum",
        "params": {},
    },
    {
        "name": "alpha021_close_vol_mean",
        "formula": "(ts_sum(close, 8) / 8 + ts_std(close, 8) < ts_sum(close, 2) / 2) if (ts_sum(close, 8) / 8 + ts_std(close, 8) < ts_sum(close, 2) / 2) else (-1 if ts_sum(close, 2) / 2 < ts_sum(close, 8) / 8 - ts_std(close, 8) else 1)",
        "description": "Mean-reversion signal comparing short vs long-term price averages",
        "category": "mean_reversion",
        "params": {"short_window": 2, "long_window": 8},
    },
    {
        "name": "alpha022_high_corr_delta",
        "formula": "-delta(corr(high, volume, 5), 5) * rank(ts_std(close, 20))",
        "description": "Change in high-volume correlation scaled by price volatility",
        "category": "volume",
        "params": {"corr_window": 5, "std_window": 20},
    },
    {
        "name": "alpha023_high_delta",
        "formula": "-delta(high, 2) if ts_sum(high, 20) / 20 < high else 0",
        "description": "Downward pressure when price exceeds 20-day high average",
        "category": "mean_reversion",
        "params": {"window": 20, "delta_window": 2},
    },
    {
        "name": "alpha024_close_lag",
        "formula": "-delta(close, 100) / ts_lag(close, 100) if delta(ts_mean(close, 100), 100) / ts_lag(close, 100) < 0.05 else -delta(close, 3)",
        "description": "Long-term momentum with regime switching at 5% threshold",
        "category": "momentum",
        "params": {"long_window": 100, "short_window": 3, "threshold": 0.05},
    },
    {
        "name": "alpha025_adv20_ret",
        "formula": "rank(-returns * adv20 * vwap * (high - close))",
        "description": "Return-volume-vwap composite factor",
        "category": "volume",
        "params": {},
    },
    {
        "name": "alpha026_vol_high_corr",
        "formula": "-ts_max(corr(ts_rank(volume, 5), ts_rank(high, 5), 5), 3)",
        "description": "Max correlation between volume and high rank over rolling window",
        "category": "volume",
        "params": {"rank_window": 5, "corr_window": 5, "max_window": 3},
    },
    {
        "name": "alpha028_adv20_high_low",
        "formula": "scale(corr(adv20, low, 5) + (high + low) / 2 - close)",
        "description": "ADV-low correlation combined with midpoint deviation",
        "category": "volume",
        "params": {"window": 5},
    },
    {
        "name": "alpha029_close_ret_rank",
        "formula": "min(rank(rank(scale(log(ts_sum(rank(rank(-rank(delta(close - 1, 5)))), 2))))), 5) + ts_rank(ts_lag(-returns, 6), 5)",
        "description": "Multi-rank log-scaled delta with lagged return rank",
        "category": "momentum",
        "params": {"delta_window": 5, "lag": 6},
    },
    {
        "name": "alpha033_open_close_rank",
        "formula": "rank(-1 + open / close)",
        "description": "Ranked open-to-close ratio minus 1",
        "category": "mean_reversion",
        "params": {},
    },
    {
        "name": "alpha034_std_returns",
        "formula": "rank(rank(returns) / rank(ts_std(returns, 2) / ts_std(returns, 5)))",
        "description": "Return rank normalized by short vs long volatility",
        "category": "volatility",
        "params": {"short_std": 2, "long_std": 5},
    },
    {
        "name": "alpha040_high_vol_corr",
        "formula": "-rank(ts_std(high, 10)) * corr(high, volume, 10)",
        "description": "Negative high-price volatility times high-volume correlation",
        "category": "volatility",
        "params": {"window": 10},
    },
    {
        "name": "alpha041_high_low_vwap",
        "formula": "pow(high * low, 0.5) - vwap",
        "description": "Geometric mean of high-low vs VWAP spread",
        "category": "mean_reversion",
        "params": {},
    },
    {
        "name": "alpha043_adv20_close",
        "formula": "ts_rank(volume / adv20, 20) * ts_rank(-delta(close, 7), 8)",
        "description": "Volume relative to ADV times negative close delta rank",
        "category": "volume",
        "params": {"vol_window": 20, "delta": 7, "rank_window": 8},
    },
    {
        "name": "alpha054_open_close_range",
        "formula": "-pow(low - close, 2) * pow(open - close, 3)",
        "description": "Negative product of downside gap and upside gap powers",
        "category": "reversal",
        "params": {},
    },
    {
        "name": "alpha101_open_close_rank",
        "formula": "(close - open) / ((high - low) + 0.001)",
        "description": "Intraday return normalized by high-low range",
        "category": "momentum",
        "params": {"smoothing": 0.001},
    },
]


# ── 经典 Fama-French + AQR 风格因子 ──────────────────────────────────────────

CLASSIC_FACTORS: List[Dict[str, Any]] = [
    {
        "name": "ff_momentum_12m1m",
        "formula": "returns_12m_lag1 = (close[-21] / close[-252]) - 1",
        "description": "Fama-French momentum: 12-month return skipping most recent month",
        "category": "momentum",
        "params": {"lookback": 252, "skip": 21},
    },
    {
        "name": "ff_short_term_reversal",
        "formula": "-(close / close[-21] - 1)",
        "description": "Jegadeesh (1990) short-term reversal: negative 1-month return",
        "category": "reversal",
        "params": {"window": 21},
    },
    {
        "name": "aqr_bab_beta",
        "formula": "covariance(returns, market_returns, 252) / variance(market_returns, 252)",
        "description": "AQR Betting Against Beta: market beta over trailing year",
        "category": "low_beta",
        "params": {"window": 252},
    },
    {
        "name": "aqr_qmj_profitability",
        "formula": "gross_profit / total_assets",
        "description": "AQR Quality Minus Junk: Novy-Marx (2013) gross profitability factor",
        "category": "quality",
        "params": {},
    },
    {
        "name": "ff_size_log_mktcap",
        "formula": "log(price * shares_outstanding)",
        "description": "Fama-French SMB: log market capitalization (smaller = higher factor)",
        "category": "size",
        "params": {},
    },
    {
        "name": "amihud_illiquidity",
        "formula": "mean(abs(returns) / (volume * close), 21)",
        "description": "Amihud (2002) illiquidity ratio: price impact per dollar volume",
        "category": "liquidity",
        "params": {"window": 21},
    },
    {
        "name": "tsmom_12m",
        "formula": "sign(returns_12m) * (target_vol / realized_vol_1m)",
        "description": "Moskowitz/Ooi/Pedersen (2012) Time-Series Momentum with vol scaling",
        "category": "momentum",
        "params": {"lookback": 252, "vol_window": 21, "target_vol": 0.4},
    },
    {
        "name": "idiosyncratic_vol",
        "formula": "ts_std(returns - beta * market_returns, 252)",
        "description": "Ang et al. (2006) idiosyncratic volatility anomaly",
        "category": "volatility",
        "params": {"window": 252},
    },
    {
        "name": "accruals_sloan",
        "formula": "(delta_current_assets - delta_cash) - (delta_current_liabilities - delta_short_term_debt) - depreciation",
        "description": "Sloan (1996) accruals anomaly: accounting vs cash earnings",
        "category": "quality",
        "params": {},
    },
    {
        "name": "net_stock_issuance",
        "formula": "log(shares_outstanding / shares_outstanding[-252])",
        "description": "Pontiff & Woodgate (2008) net stock issuance anomaly",
        "category": "quality",
        "params": {"window": 252},
    },
]


# ── arXiv 批量搜索关键词 ───────────────────────────────────────────────────────

ARXIV_QUERIES = [
    "momentum factor stock returns cross-section",
    "mean reversion equity trading strategy",
    "volatility factor anomaly stock market",
    "value investing factor book-to-market",
    "quality factor profitability equity",
    "low beta anomaly stock returns",
    "technical indicator alpha generation trading",
    "time series momentum systematic strategy",
    "machine learning stock return prediction factor",
    "intraday price pattern high frequency alpha",
]


# ── Quantocracy 关键词 → 因子映射 ─────────────────────────────────────────────

QUANTOCRACY_FACTOR_MAP: Dict[str, Dict[str, Any]] = {
    "momentum": {
        "formula": "close / close[-63] - 1",
        "description": "3-month price momentum",
        "category": "momentum",
        "params": {"window": 63},
    },
    "trend following": {
        "formula": "close > sma(close, 200)",
        "description": "Price above 200-day moving average trend filter",
        "category": "momentum",
        "params": {"window": 200},
    },
    "mean reversion": {
        "formula": "(close - sma(close, 20)) / ts_std(close, 20) * -1",
        "description": "Negative z-score: buy when price is below 20-day average",
        "category": "mean_reversion",
        "params": {"window": 20},
    },
    "breakout": {
        "formula": "close > ts_max(high, 20) and volume > sma(volume, 20) * 1.5",
        "description": "20-day high breakout confirmed by volume surge",
        "category": "momentum",
        "params": {"price_window": 20, "vol_mult": 1.5},
    },
    "low volatility": {
        "formula": "1 / ts_std(returns, 20)",
        "description": "Inverse realized volatility: low-vol anomaly",
        "category": "volatility",
        "params": {"window": 20},
    },
    "carry": {
        "formula": "dividend_yield - risk_free_rate",
        "description": "Equity carry: dividend yield minus risk-free rate",
        "category": "value",
        "params": {},
    },
    "dual momentum": {
        "formula": "close / close[-252] - 1 if close > sma(close, 10) else 0",
        "description": "Antonacci dual momentum: absolute + relative momentum combined",
        "category": "momentum",
        "params": {"abs_window": 252, "rel_window": 10},
    },
    "rsi oversold": {
        "formula": "rsi(close, 14) < 30",
        "description": "RSI below 30 oversold signal for mean-reversion entries",
        "category": "mean_reversion",
        "params": {"period": 14, "threshold": 30},
    },
    "golden cross": {
        "formula": "sma(close, 50) > sma(close, 200)",
        "description": "50-day SMA crosses above 200-day SMA bullish signal",
        "category": "momentum",
        "params": {"fast": 50, "slow": 200},
    },
    "volume spike": {
        "formula": "volume / sma(volume, 20) > 2.0",
        "description": "Volume spike: current volume exceeds 2x 20-day average",
        "category": "volume",
        "params": {"window": 20, "threshold": 2.0},
    },
}


# ── 核心导入逻辑 ──────────────────────────────────────────────────────────────

def _make_gene(name: str, formula: str, description: str, source: str, category: str, params: Dict) -> Gene:
    gene = Gene(
        gene_id="",
        name=name,
        description=description,
        formula=formula,
        parameters={"category": category, **params},
        source=source,
        author="seed_importer",
        created_at=datetime.now(),
        parent_gene_id=None,
        generation=0,
    )
    gene.gene_id = gene.compute_id()
    return gene


def import_worldquant(hub: QuantClawEvolutionHub, dry_run: bool = False) -> int:
    """导入 WorldQuant 101 Alphas + 经典因子。"""
    all_factors = WORLDQUANT_ALPHAS + CLASSIC_FACTORS
    count = 0
    for alpha in all_factors:
        source = f"worldquant_101" if alpha in WORLDQUANT_ALPHAS else "classic_factors"
        gene = _make_gene(
            name=alpha["name"],
            formula=alpha["formula"],
            description=alpha["description"],
            source=source,
            category=alpha["category"],
            params=alpha.get("params", {}),
        )
        if dry_run:
            print(f"  [DRY] {gene.name}: {gene.formula[:60]}...")
            count += 1
            continue
        try:
            hub.publish_gene(gene)
            print(f"  ✓ {gene.name}")
            count += 1
        except Exception as e:
            print(f"  ✗ {gene.name}: {e}")
    return count


def import_arxiv(hub: QuantClawEvolutionHub, limit: int = 100, dry_run: bool = False) -> int:
    """通过 arXiv API 采集量化论文并提取因子。"""
    try:
        from arxiv_gene_extractor import ArxivGenePipeline
    except ImportError:
        print("  ✗ arxiv_gene_extractor.py not found, skipping arXiv import")
        return 0

    count = 0
    per_query = max(10, limit // len(ARXIV_QUERIES))
    pipeline = ArxivGenePipeline(db_path=DB_PATH)

    for query in ARXIV_QUERIES:
        print(f"\n  → Searching arXiv: '{query}' (limit={per_query})")
        try:
            result = pipeline.run(query=query, limit=per_query, dry_run=dry_run, min_confidence=0.4)
            injected = result.get("injected", 0)
            count += injected
            print(f"    ✓ {injected} factors injected")
            time.sleep(1)  # arXiv API 礼貌延迟
        except Exception as e:
            print(f"    ✗ Error: {e}")

    return count


def _fetch_rss(url: str, timeout: int = 10) -> str:
    """安全获取 RSS 内容。"""
    try:
        req = urllib_request.Request(url, headers={"User-Agent": "QuantMap/1.0 (research)"})
        with urllib_request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="ignore")
    except URLError as e:
        print(f"  ✗ RSS fetch failed: {e}")
        return ""


def import_quantocracy(hub: QuantClawEvolutionHub, dry_run: bool = False) -> int:
    """从 Quantocracy RSS 提取实战策略因子。"""
    RSS_URL = "https://quantocracy.com/feed/"
    print(f"  → Fetching Quantocracy RSS: {RSS_URL}")
    content = _fetch_rss(RSS_URL)

    if not content:
        print("  ✗ Could not fetch RSS, using keyword map directly")
        # 直接用预定义关键词因子作为备选
        count = 0
        for keyword, factor in QUANTOCRACY_FACTOR_MAP.items():
            gene = _make_gene(
                name=f"quantocracy_{keyword.replace(' ', '_')}",
                formula=factor["formula"],
                description=factor["description"],
                source="quantocracy_rss",
                category=factor["category"],
                params=factor.get("params", {}),
            )
            if dry_run:
                print(f"  [DRY] {gene.name}: {gene.formula[:60]}...")
                count += 1
                continue
            try:
                hub.publish_gene(gene)
                print(f"  ✓ {gene.name}")
                count += 1
            except Exception as e:
                print(f"  ✗ {gene.name}: {e}")
        return count

    # 解析 RSS XML
    matched_keywords: set = set()
    try:
        root = ET.fromstring(content)
        items = root.findall(".//item")
        print(f"  → Found {len(items)} RSS items")
        for item in items:
            title_el = item.find("title")
            desc_el = item.find("description")
            text = ""
            if title_el is not None and title_el.text:
                text += title_el.text.lower() + " "
            if desc_el is not None and desc_el.text:
                text += desc_el.text.lower()

            for keyword in QUANTOCRACY_FACTOR_MAP:
                if keyword in text:
                    matched_keywords.add(keyword)
    except ET.ParseError:
        print("  ✗ RSS parse error, using all keyword factors")
        matched_keywords = set(QUANTOCRACY_FACTOR_MAP.keys())

    if not matched_keywords:
        matched_keywords = set(QUANTOCRACY_FACTOR_MAP.keys())

    count = 0
    for keyword in matched_keywords:
        factor = QUANTOCRACY_FACTOR_MAP[keyword]
        gene = _make_gene(
            name=f"quantocracy_{keyword.replace(' ', '_')}",
            formula=factor["formula"],
            description=factor["description"],
            source="quantocracy_rss",
            category=factor["category"],
            params=factor.get("params", {}),
        )
        if dry_run:
            print(f"  [DRY] {gene.name}: {gene.formula[:60]}...")
            count += 1
            continue
        try:
            hub.publish_gene(gene)
            print(f"  ✓ {gene.name}")
            count += 1
        except Exception as e:
            print(f"  ✗ {gene.name}: {e}")

    return count


def count_genes(hub: QuantClawEvolutionHub) -> int:
    """查询当前基因总数。"""
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT COUNT(*) FROM genes").fetchone()
    conn.close()
    return row[0] if row else 0


# ── CLI 入口 ──────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="QuantMap Seed Library Importer")
    parser.add_argument(
        "--source",
        choices=["all", "worldquant", "arxiv", "quantocracy"],
        default="all",
        help="Import source (default: all)",
    )
    parser.add_argument("--limit", type=int, default=100, help="Max papers for arXiv source")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to DB")
    args = parser.parse_args()

    print("\n" + "═" * 60)
    print("  QuantMap Seed Library Importer")
    print("  多源因子种子库批量导入器")
    print("═" * 60)

    hub = QuantClawEvolutionHub(DB_PATH)
    before = count_genes(hub)
    print(f"\n  当前基因数：{before}")

    if args.dry_run:
        print("  ⚠️  DRY RUN 模式：预览不写入数据库\n")

    total = 0

    if args.source in ("all", "worldquant"):
        print(f"\n{'─' * 50}")
        print(f"  [1/3] WorldQuant 101 Alphas + 经典因子")
        print(f"{'─' * 50}")
        n = import_worldquant(hub, dry_run=args.dry_run)
        print(f"\n  → 导入 {n} 个因子")
        total += n

    if args.source in ("all", "arxiv"):
        print(f"\n{'─' * 50}")
        print(f"  [2/3] arXiv 批量采集（limit={args.limit}）")
        print(f"{'─' * 50}")
        n = import_arxiv(hub, limit=args.limit, dry_run=args.dry_run)
        print(f"\n  → 采集 {n} 个因子")
        total += n

    if args.source in ("all", "quantocracy"):
        print(f"\n{'─' * 50}")
        print(f"  [3/3] Quantocracy RSS 实战因子")
        print(f"{'─' * 50}")
        n = import_quantocracy(hub, dry_run=args.dry_run)
        print(f"\n  → 导入 {n} 个因子")
        total += n

    after = count_genes(hub)
    print(f"\n{'═' * 60}")
    print(f"  完成！总计处理 {total} 个因子")
    if not args.dry_run:
        print(f"  基因库：{before} → {after} 个（新增 {after - before} 个）")
    print(f"{'═' * 60}\n")


if __name__ == "__main__":
    main()

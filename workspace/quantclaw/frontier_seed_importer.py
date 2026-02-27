#!/usr/bin/env python3
"""
QuantMap Frontier Seed Importer
2024-2025 前沿因子种子库导入器

来源：
  - arXiv 2024-2025 年最新 q-fin 论文（按时间倒序）
  - 内置精选前沿因子（基于最新论文归纳）
  - 可选：通过 Kimi API（OpenAI 兼容）动态解析论文 abstract 生成新因子

Usage:
    python3 frontier_seed_importer.py                         # 导入内置前沿因子
    python3 frontier_seed_importer.py --arxiv                 # 同时采集最新 arXiv
    python3 frontier_seed_importer.py --arxiv --llm           # LLM 解析 abstract（需 KIMI_API_KEY）
    python3 frontier_seed_importer.py --test-kimi             # 测试 Kimi API 连接
    python3 frontier_seed_importer.py --dry-run               # 预览

Kimi API Key 配置（任选其一）：
    export KIMI_API_KEY=sk-kimi-xxx
    python3 frontier_seed_importer.py --api-key sk-kimi-xxx --test-kimi
"""

from __future__ import annotations

import argparse
import json
import os
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


# ── 2024-2025 前沿因子库（按方向分类）───────────────────────────────────────────

# 每个因子标注：论文来源 / 年份 / 方向
FRONTIER_FACTORS: List[Dict[str, Any]] = [

    # ── 1. LLM 情感因子（2024-2025）──────────────────────────────────────────────
    {
        "name": "llm_news_sentiment_causal",
        "formula": "causal_sentiment_score(news_embedding_t, lag=1)",
        "description": "CausalStock (NeurIPS 2024): LLM-denoised news causal discovery factor. "
                       "Temporal causal graph models time-lagged news→price dependencies.",
        "category": "nlp_sentiment",
        "source": "arxiv:2411.06391",
        "params": {"lag": 1, "llm": "encoder"},
        "year": 2024,
    },
    {
        "name": "finllm_sentiment_intensity",
        "formula": "llm_sentiment_polarity(text) * llm_sentiment_intensity(text)",
        "description": "FinLlama (ACM CAIIF 2024): LLM sentiment polarity × intensity product. "
                       "Generator-discriminator scheme classifies both direction and magnitude.",
        "category": "nlp_sentiment",
        "source": "arxiv:2024_finllama",
        "params": {"model": "llama2_7b_finetuned", "lora_rank": 16},
        "year": 2024,
    },
    {
        "name": "news_attention_momentum",
        "formula": "ts_sum(news_volume * abs(sentiment_score), 5) / ts_sum(news_volume, 5)",
        "description": "News attention-weighted sentiment momentum: volume-weighted sentiment "
                       "intensity over 5 days. Strong when sentiment volume spikes.",
        "category": "nlp_sentiment",
        "source": "research:2024_news_factor",
        "params": {"window": 5},
        "year": 2024,
    },
    {
        "name": "earnings_call_tone_drift",
        "formula": "sentiment_drift(earnings_call_t, earnings_call_t_minus_1)",
        "description": "Earnings call tone change factor: positive drift signals "
                       "management confidence increase, negative signals deterioration.",
        "category": "nlp_sentiment",
        "source": "research:2024_earnings_nlp",
        "params": {"model": "finbert"},
        "year": 2024,
    },

    # ── 2. 图神经网络 / 关系网络因子（2024-2025）─────────────────────────────────
    {
        "name": "gnn_sector_momentum",
        "formula": "gnn_aggregate(sector_graph, returns, depth=2)",
        "description": "GNN-based sector momentum: aggregates neighbor stock returns "
                       "through 2-hop sector graph adjacency. Captures spillover effects.",
        "category": "graph_factor",
        "source": "research:2024_gnn_sector",
        "params": {"hops": 2, "aggregation": "mean"},
        "year": 2024,
    },
    {
        "name": "magnet_hypergraph_momentum",
        "formula": "hypergraph_attention(price_series, causal_edges) * temporal_decay",
        "description": "MaGNet (2024-2025): Mamba dual-hypergraph network momentum. "
                       "CSI300 +22%, DJIA +20%, max drawdown <5%.",
        "category": "graph_factor",
        "source": "research:2024_magnet",
        "params": {"decay": 0.9, "hyperedge_threshold": 0.6},
        "year": 2024,
    },
    {
        "name": "supply_chain_graph_factor",
        "formula": "gnn_aggregate(supply_chain_graph, revenue_surprise, depth=3)",
        "description": "Supply chain propagation factor: upstream/downstream revenue "
                       "surprise propagation through supply chain graph edges.",
        "category": "graph_factor",
        "source": "research:2024_supply_chain_gnn",
        "params": {"hops": 3, "weight": "revenue_exposure"},
        "year": 2024,
    },

    # ── 3. 订单簿微观结构因子（2024-2025 LOB 研究）───────────────────────────────
    {
        "name": "lob_order_flow_imbalance",
        "formula": "(bid_qty_L1 - ask_qty_L1) / (bid_qty_L1 + ask_qty_L1)",
        "description": "Order flow imbalance at L1: signed bid-ask quantity ratio. "
                       "Predicts short-term price direction (TLOB, arXiv 2502.15757).",
        "category": "microstructure",
        "source": "arxiv:2502.15757",
        "params": {"depth": 1},
        "year": 2025,
    },
    {
        "name": "lob_depth_weighted_pressure",
        "formula": "ts_sum((bid_qty_Li * bid_price_Li - ask_qty_Li * ask_price_Li) / i, 10) for i in [1..10]",
        "description": "HLOB (2024): Depth-weighted order book pressure across 10 price levels. "
                       "Captures hidden liquidity using topological filtration.",
        "category": "microstructure",
        "source": "research:2024_hlob",
        "params": {"levels": 10},
        "year": 2024,
    },
    {
        "name": "lob_trade_sign_momentum",
        "formula": "ts_sum(sign(trade_price - midprice) * trade_volume, 20) / adv20",
        "description": "Trade-sign momentum: buy vs sell initiative ratio relative to ADV. "
                       "Captures informed order flow direction.",
        "category": "microstructure",
        "source": "research:2024_lob_microstructure",
        "params": {"window": 20},
        "year": 2024,
    },
    {
        "name": "realized_spread_factor",
        "formula": "2 * sign(trade_direction) * (trade_price - midprice_5min_later) / midprice",
        "description": "Realized spread: measures informed trading component of bid-ask spread. "
                       "Negative = market maker profit, Positive = informed trader advantage.",
        "category": "microstructure",
        "source": "research:2024_realized_spread",
        "params": {"horizon_min": 5},
        "year": 2024,
    },

    # ── 4. 期权隐含信息因子（2024-2025）──────────────────────────────────────────
    {
        "name": "iv_skew_factor",
        "formula": "iv(strike=0.95 * spot, maturity=30d) - iv(strike=1.05 * spot, maturity=30d)",
        "description": "Implied volatility skew: left tail premium over right tail. "
                       "High skew = bearish sentiment, tends to predict negative returns.",
        "category": "options_implied",
        "source": "research:2024_iv_skew",
        "params": {"moneyness_range": 0.05, "maturity_days": 30},
        "year": 2024,
    },
    {
        "name": "option_pcr_sentiment",
        "formula": "put_volume / call_volume",
        "description": "Put-Call Ratio sentiment factor: high PCR signals bearish positioning. "
                       "CSI1000 long-short timing effect strongest (2024 China research).",
        "category": "options_implied",
        "source": "research:2024_pcr_china",
        "params": {"aggregation": "30d_rolling_avg"},
        "year": 2024,
    },
    {
        "name": "forward_variance_risk_premium",
        "formula": "iv_squared_30d - realized_vol_squared_30d",
        "description": "Variance risk premium: implied minus realized variance. "
                       "Positive VRP compensates variance sellers, predicts future returns.",
        "category": "options_implied",
        "source": "research:2024_vrp_factor",
        "params": {"window": 30},
        "year": 2024,
    },
    {
        "name": "iv_term_structure_slope",
        "formula": "iv(maturity=60d) / iv(maturity=30d) - 1",
        "description": "IV term structure slope: contango vs backwardation signal. "
                       "Upward slope = near-term calm, downward = near-term stress.",
        "category": "options_implied",
        "source": "research:2024_iv_term_structure",
        "params": {"short_mat": 30, "long_mat": 60},
        "year": 2024,
    },

    # ── 5. 深度学习 / Transformer 价量因子（2024-2025）───────────────────────────
    {
        "name": "transformer_price_pattern",
        "formula": "tlob_transformer_score(ohlcv_10day_sequence)",
        "description": "TLOB (arXiv 2502.15757): Transformer with dual attention on 10-day "
                       "OHLCV sequence. Outperforms DeepLOB on mid-price trend prediction.",
        "category": "deep_learning",
        "source": "arxiv:2502.15757",
        "params": {"seq_len": 10, "attention_heads": 8},
        "year": 2025,
    },
    {
        "name": "temporal_fusion_alpha",
        "formula": "tft_prediction(ohlcv, macro_features, sector_embedding, horizon=5)",
        "description": "Temporal Fusion Transformer alpha: dynamic feature selection "
                       "across multiple time scales. Outperforms LSTM on multi-horizon forecasting.",
        "category": "deep_learning",
        "source": "research:2024_tft_alpha",
        "params": {"horizon": 5, "lstm_hidden": 128},
        "year": 2024,
    },
    {
        "name": "diffusion_vol_forecast",
        "formula": "armd_volatility_prediction(returns_sequence, horizon=5)",
        "description": "ARMD (AAAI 2025): Auto-Regressive Moving Diffusion treats volatility "
                       "as continuous diffusion process, aligning temporal evolution.",
        "category": "deep_learning",
        "source": "research:2025_armd_aaai",
        "params": {"diffusion_steps": 100, "horizon": 5},
        "year": 2025,
    },

    # ── 6. 另类数据因子（2024-2025）───────────────────────────────────────────────
    {
        "name": "satellite_poi_density_change",
        "formula": "delta(satellite_car_count(parking_lot), 30) / baseline_car_count",
        "description": "Satellite imagery POI activity: parking lot car count change "
                       "proxies retail/commercial activity before earnings.",
        "category": "alternative_data",
        "source": "research:2024_satellite_alt_data",
        "params": {"lookback": 30, "location": "retail_poi"},
        "year": 2024,
    },
    {
        "name": "credit_card_spending_momentum",
        "formula": "delta(sector_credit_spending_index, 30) / ts_std(sector_credit_spending_index, 90)",
        "description": "Credit card spending z-score momentum: abnormal spending growth "
                       "in sector predicts revenue surprise direction.",
        "category": "alternative_data",
        "source": "research:2024_cc_spending",
        "params": {"short_window": 30, "long_window": 90},
        "year": 2024,
    },
    {
        "name": "web_search_interest_factor",
        "formula": "zscore(search_volume_index(ticker), 20) - zscore(search_volume_index(ticker), 60)",
        "description": "Google Trends search interest momentum: short vs long-term attention "
                       "anomaly. Sudden interest spike = retail attention surge.",
        "category": "alternative_data",
        "source": "research:2024_web_search_factor",
        "params": {"short": 20, "long": 60},
        "year": 2024,
    },
    {
        "name": "social_media_attention_factor",
        "formula": "log(1 + social_mention_count) * sign(social_sentiment_score)",
        "description": "Social media attention factor: log-scaled mention count weighted "
                       "by sentiment sign. Captures retail investor attention effects.",
        "category": "alternative_data",
        "source": "research:2024_social_media_factor",
        "params": {"platform": "combined"},
        "year": 2024,
    },

    # ── 7. ESG / 气候因子（2024-2025）─────────────────────────────────────────────
    {
        "name": "carbon_intensity_discount",
        "formula": "-(carbon_emissions / revenue) * carbon_price_sensitivity",
        "description": "Carbon intensity discount factor: high carbon intensity + rising "
                       "carbon price → negative alpha. Stranded asset risk premium.",
        "category": "esg",
        "source": "research:2024_climate_finance",
        "params": {"carbon_price_growth": 0.1},
        "year": 2024,
    },
    {
        "name": "esg_momentum_factor",
        "formula": "delta(esg_score, 252) / ts_std(esg_score, 252)",
        "description": "ESG score momentum: improving ESG trajectory predicts positive "
                       "abnormal returns through institutional flow effects.",
        "category": "esg",
        "source": "research:2024_esg_momentum",
        "params": {"window": 252},
        "year": 2024,
    },

    # ── 8. 因子组合 / 动态权重（2024-2025）────────────────────────────────────────
    {
        "name": "comfort_zone_dynamic_weight",
        "formula": "quantile_diff(factor, upper_q=0.8, lower_q=0.2) * regime_confidence",
        "description": "华安证券因子舒适区 (2025): Quantile deviation weighted by regime "
                       "confidence. CSI1000 enhanced +12.8% annualized excess return, IR=2.40.",
        "category": "composite",
        "source": "research:2025_comfort_zone_hua_an",
        "params": {"upper_q": 0.8, "lower_q": 0.2},
        "year": 2025,
    },
    {
        "name": "end_to_end_dynamic_alpha",
        "formula": "e2e_factor_optimizer(factor_zoo, portfolio_objective='sharpe', horizon=20)",
        "description": "端到端动态Alpha (2025): Joint factor mining + portfolio optimization. "
                       "Shifts from static market-wide ranking to dynamic stock-specific scope.",
        "category": "composite",
        "source": "research:2025_e2e_dynamic_alpha",
        "params": {"horizon": 20, "objective": "sharpe"},
        "year": 2025,
    },
    {
        "name": "causal_factor_selection",
        "formula": "causal_discovery(factor_zoo, target=returns, method='NOTEARS')",
        "description": "Causal factor selection via NOTEARS algorithm: identifies truly "
                       "causal factors vs spurious correlations. Reduces overfitting.",
        "category": "composite",
        "source": "research:2024_causal_factor",
        "params": {"lambda_l1": 0.1, "max_iter": 100},
        "year": 2024,
    },

    # ── 9. 粗糙波动率 / 分形因子（2024）──────────────────────────────────────────
    {
        "name": "rough_hurst_exponent",
        "formula": "hurst_exponent(realized_vol_series, method='rough', window=252)",
        "description": "Rough volatility Hurst exponent (2024 review): H≈0.1 in equity markets "
                       "indicates rough/anti-persistent volatility dynamics.",
        "category": "volatility",
        "source": "research:2024_rough_vol_review",
        "params": {"window": 252, "method": "rough"},
        "year": 2024,
    },
    {
        "name": "physics_vol_surface_factor",
        "formula": "pinn_vol_surface_residual(strike_grid, maturity_grid)",
        "description": "Physics-informed NN volatility surface factor (2024): "
                       "arbitrage-free surface residual as cross-sectional signal.",
        "category": "volatility",
        "source": "research:2024_pinn_vol_surface",
        "params": {"arch": "conv_transformer"},
        "year": 2024,
    },
]


# ── arXiv 最新论文采集（按时间倒序）─────────────────────────────────────────────

FRONTIER_ARXIV_QUERIES = [
    "cat:q-fin.TR AND (factor OR alpha OR anomaly)",
    "cat:q-fin.PM AND (machine learning OR deep learning OR LLM)",
    "cat:q-fin.ST AND (cross-section OR factor OR momentum)",
    "cat:q-fin.TR AND (order book OR microstructure OR high frequency)",
    "cat:q-fin.PM AND (graph neural OR knowledge graph OR network)",
]

ARXIV_BASE = "http://export.arxiv.org/api/query"


def _arxiv_recent(query: str, max_results: int = 15, since_year: int = 2024) -> List[Dict]:
    """按时间倒序抓取最新 arXiv 论文，过滤 since_year 年之前的。"""
    import urllib.parse
    params = urllib.parse.urlencode({
        "search_query": query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": 0,
        "max_results": max_results,
    })
    url = f"{ARXIV_BASE}?{params}"
    try:
        req = urllib_request.Request(url, headers={"User-Agent": "QuantMap/1.0 (research)"})
        with urllib_request.urlopen(req, timeout=20) as resp:
            xml = resp.read().decode("utf-8")
    except URLError as e:
        print(f"    ✗ arXiv fetch failed: {e}")
        return []

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(xml)
    papers = []
    for entry in root.findall("atom:entry", ns):
        pub = entry.find("atom:published", ns)
        if pub is None or int(pub.text[:4]) < since_year:
            continue
        papers.append({
            "id": entry.find("atom:id", ns).text.split("/")[-1],
            "title": entry.find("atom:title", ns).text.strip().replace("\n", " "),
            "abstract": entry.find("atom:summary", ns).text.strip()[:500] if entry.find("atom:summary", ns) is not None else "",
            "published": pub.text[:10],
        })
    return papers


KIMI_BASE_URL = "https://api.moonshot.cn/v1"
KIMI_MODEL = "moonshot-v1-8k"


def _kimi_client(api_key: str):
    """创建 Kimi API 客户端（使用 openai 兼容接口）。"""
    try:
        from openai import OpenAI
        return OpenAI(api_key=api_key, base_url=KIMI_BASE_URL)
    except ImportError:
        raise RuntimeError("需要安装 openai 库：pip install openai")


def test_kimi_api(api_key: str) -> bool:
    """测试 Kimi API 连接是否正常。"""
    print("\n" + "─" * 60)
    print("  测试 Kimi API 连接...")
    print(f"  Base URL: {KIMI_BASE_URL}")
    print(f"  Model   : {KIMI_MODEL}")
    print(f"  API Key : {api_key[:12]}...{api_key[-6:]}")
    print("─" * 60)

    try:
        client = _kimi_client(api_key)
        resp = client.chat.completions.create(
            model=KIMI_MODEL,
            max_tokens=50,
            messages=[
                {"role": "system", "content": "You are Kimi, a helpful AI assistant."},
                {"role": "user", "content": "请用一句话介绍你自己，用中文。"},
            ],
        )
        answer = resp.choices[0].message.content.strip()
        print(f"\n  ✅ Kimi API 连接成功！")
        print(f"  模型响应: {answer}")
        print(f"  Token 用量: {resp.usage.total_tokens}")
        print("─" * 60 + "\n")
        return True
    except Exception as e:
        print(f"\n  ✗ Kimi API 连接失败: {e}")
        print("─" * 60 + "\n")
        return False


def _llm_extract_factor(paper: Dict, api_key: str) -> Optional[Dict]:
    """用 Kimi API 从论文 abstract 提取因子公式（OpenAI 兼容接口）。"""
    prompt = f"""You are a quantitative finance expert. Given this arXiv paper abstract, extract a tradeable factor signal.

Paper: {paper['title']}
Published: {paper['published']}
Abstract: {paper['abstract']}

If this paper proposes a quantifiable trading factor or signal:
1. Name it (snake_case, max 40 chars)
2. Write a pseudo-code formula (using: close, open, high, low, volume, returns, and standard functions like ts_rank, delta, corr, std, mean, etc.)
3. Describe it in one sentence
4. Classify: momentum | reversal | volatility | value | quality | microstructure | nlp_sentiment | graph_factor | alternative_data | other

Respond ONLY with JSON (no markdown):
{{"name": "...", "formula": "...", "description": "...", "category": "..."}}

If the paper has no quantifiable factor, respond with: {{"name": null}}"""

    try:
        client = _kimi_client(api_key)
        resp = client.chat.completions.create(
            model=KIMI_MODEL,
            max_tokens=300,
            messages=[
                {"role": "system", "content": "You are a quantitative finance expert. Always respond with valid JSON only."},
                {"role": "user", "content": prompt},
            ],
        )
        text = resp.choices[0].message.content.strip()
        # 去掉可能的 markdown 代码块包裹
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        result = json.loads(text.strip())
        if result.get("name"):
            return result
    except Exception as e:
        print(f"    ✗ Kimi LLM extract failed: {e}")
    return None


def import_frontier_builtin(hub: QuantClawEvolutionHub, dry_run: bool = False) -> int:
    """导入内置的 2024-2025 前沿因子。"""
    count = 0
    for f in FRONTIER_FACTORS:
        gene = Gene(
            gene_id="",
            name=f["name"],
            description=f["description"],
            formula=f["formula"],
            parameters={"category": f["category"], "year": f["year"], **f.get("params", {})},
            source=f["source"],
            author="frontier_importer_2025",
            created_at=datetime.now(),
            parent_gene_id=None,
            generation=0,
        )
        gene.gene_id = gene.compute_id()

        if dry_run:
            print(f"  [DRY] [{f['year']}] {gene.name}")
            count += 1
            continue
        try:
            hub.publish_gene(gene)
            print(f"  ✓ [{f['year']}] {gene.name}")
            count += 1
        except Exception as e:
            print(f"  ✗ {gene.name}: {e}")
    return count


def import_frontier_arxiv(hub: QuantClawEvolutionHub, api_key: Optional[str] = None,
                           dry_run: bool = False) -> int:
    """从 arXiv 最新论文采集并（可选）用 LLM 提取因子。"""
    use_llm = bool(api_key)
    count = 0
    seen_ids: set = set()

    for query in FRONTIER_ARXIV_QUERIES:
        print(f"\n  → arXiv: '{query}'")
        papers = _arxiv_recent(query, max_results=15, since_year=2024)
        print(f"    Found {len(papers)} papers from 2024+")
        time.sleep(3)  # arXiv 礼貌延迟

        for paper in papers:
            pid = paper["id"]
            if pid in seen_ids:
                continue
            seen_ids.add(pid)

            if use_llm:
                factor = _llm_extract_factor(paper, api_key)
                if not factor:
                    continue

                gene = Gene(
                    gene_id="",
                    name=f"arxiv_{factor['name']}",
                    description=f"[{paper['published']}] {factor['description']} | {paper['title'][:60]}",
                    formula=factor["formula"],
                    parameters={"category": factor["category"], "year": int(paper["published"][:4])},
                    source=f"arxiv:{pid}",
                    author="frontier_llm_extractor",
                    created_at=datetime.now(),
                    parent_gene_id=None,
                    generation=0,
                )
                gene.gene_id = gene.compute_id()

                if dry_run:
                    print(f"  [DRY] [{paper['published']}] {gene.name}: {gene.formula[:50]}...")
                    count += 1
                else:
                    try:
                        hub.publish_gene(gene)
                        print(f"  ✓ [{paper['published']}] {gene.name}")
                        count += 1
                    except Exception as e:
                        print(f"  ✗ {gene.name}: {e}")
                time.sleep(0.5)  # Claude API 礼貌延迟
            else:
                # 无 LLM：只打印论文标题供参考
                print(f"    [{paper['published']}] {paper['title'][:70]}")

    return count


def count_genes() -> int:
    import sqlite3
    conn = sqlite3.connect(DB_PATH)
    row = conn.execute("SELECT COUNT(*) FROM genes").fetchone()
    conn.close()
    return row[0] if row else 0


def main() -> None:
    parser = argparse.ArgumentParser(description="QuantMap Frontier Seed Importer 2024-2025")
    parser.add_argument("--arxiv", action="store_true", help="Also fetch latest arXiv papers")
    parser.add_argument("--llm", action="store_true", help="Use Kimi API to extract factors from abstracts")
    parser.add_argument("--api-key", type=str,
                        default=os.environ.get("KIMI_API_KEY", os.environ.get("ANTHROPIC_API_KEY", "")),
                        help="Kimi API key (or set KIMI_API_KEY env var)")
    parser.add_argument("--test-kimi", action="store_true", help="Test Kimi API connection and exit")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing to DB")
    args = parser.parse_args()

    # 测试 Kimi API 连接
    if args.test_kimi:
        if not args.api_key:
            print("  ✗ 需要提供 API key：--api-key sk-kimi-xxx 或设置 KIMI_API_KEY 环境变量")
            sys.exit(1)
        ok = test_kimi_api(args.api_key)
        sys.exit(0 if ok else 1)

    print("\n" + "═" * 64)
    print("  QuantMap Frontier Seed Importer  ·  2024-2025 前沿因子")
    print("═" * 64)

    before = count_genes()
    print(f"\n  当前基因数：{before}")

    hub = QuantClawEvolutionHub(DB_PATH)
    if args.dry_run:
        print("  ⚠️  DRY RUN 模式：预览不写入数据库\n")

    # Step 1: 内置前沿因子
    print(f"\n{'─' * 60}")
    print(f"  [1] 内置 2024-2025 前沿因子（{len(FRONTIER_FACTORS)} 个）")
    print(f"{'─' * 60}")

    cats: Dict[str, int] = {}
    for f in FRONTIER_FACTORS:
        cats[f["category"]] = cats.get(f["category"], 0) + 1
    for c, n in sorted(cats.items()):
        print(f"    {c}: {n} 个")
    print()

    n1 = import_frontier_builtin(hub, dry_run=args.dry_run)
    print(f"\n  → 导入 {n1} 个前沿因子")

    # Step 2: arXiv 最新论文（可选）
    n2 = 0
    if args.arxiv:
        print(f"\n{'─' * 60}")
        api_key = args.api_key if args.llm else None
        if args.llm and not api_key:
            print("  ⚠️  --llm 需要 KIMI_API_KEY，跳过 LLM 提取（仅展示论文列表）")
        mode = "LLM 解析" if (args.llm and api_key) else "仅展示"
        print(f"  [2] arXiv 最新论文采集（{mode}）")
        print(f"{'─' * 60}")
        n2 = import_frontier_arxiv(hub, api_key=api_key if args.llm else None, dry_run=args.dry_run)
        if args.llm and api_key:
            print(f"\n  → LLM 提取 {n2} 个新因子")

    after = count_genes()
    print(f"\n{'═' * 64}")
    print(f"  完成！新增因子：{n1 + n2} 个")
    if not args.dry_run:
        print(f"  基因库：{before} → {after} 个")
    print()
    print("  前沿方向覆盖：")
    print("    ✓ LLM 情感 / NLP 因子（CausalStock NeurIPS 2024）")
    print("    ✓ 图神经网络关系因子（MaGNet 超图网络 2024）")
    print("    ✓ 订单簿微观结构（TLOB arXiv 2502.15757）")
    print("    ✓ 期权隐含信息（IV Skew / PCR / VRP 2024）")
    print("    ✓ 另类数据（卫星图像 / 信用卡 / 社交媒体 2024）")
    print("    ✓ ESG / 气候因子（2024 碳强度折价）")
    print("    ✓ 端到端动态Alpha（华安舒适区 2025）")
    print("    ✓ 粗糙波动率 / PINN 波动率曲面（2024）")
    print(f"{'═' * 64}\n")

    if not args.llm:
        print("  💡 添加 --arxiv --llm --api-key sk-kimi-xxx 可用 Kimi AI 自动从最新论文提取因子")
        print("  💡 测试连接：python3 frontier_seed_importer.py --test-kimi --api-key sk-kimi-xxx")


if __name__ == "__main__":
    main()

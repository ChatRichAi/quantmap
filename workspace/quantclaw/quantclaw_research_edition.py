"""
QuantClaw Pro Research Edition - 研究增强版
集成学术论文成果的完整系统
"""

import sys
sys.path.insert(0, '/Users/oneday/.openclaw/workspace/quantclaw')

from quantclaw_pro import QuantClawPro
from research.advanced_features import EnhancedPerceptionLayer
from research.arxiv_crawler import ArxivPaperCrawler
from research.ab_testing_framework import PaperValidationFramework
from perception_layer import PerceptionLayer
from cognition_layer import CognitionLayer
from decision_layer import DecisionLayer

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ResearchEnhancementConfig:
    """研究增强配置"""
    use_advanced_features: bool = True
    use_paper_crawler: bool = False
    enable_auto_update: bool = False
    feature_mode: str = "hybrid"  # basic/hybrid/full_research


class QuantClawProResearch(QuantClawPro):
    """
    QuantClaw Pro 研究增强版
    集成学术论文成果的高级功能
    """
    
    def __init__(self, config: ResearchEnhancementConfig = None):
        """
        初始化研究增强版
        
        Args:
            config: 研究增强配置
        """
        self.config = config or ResearchEnhancementConfig()
        
        # 初始化基础组件
        if self.config.feature_mode == "hybrid":
            # 混合模式：基础32维 + 高级研究特征
            self.perception = EnhancedPerceptionLayer(use_advanced_features=True)
            logger.info("Using Enhanced Perception (32 basic + 12 advanced features)")
        elif self.config.feature_mode == "full_research":
            # 纯研究模式：仅使用论文特征
            from research.advanced_features import AdvancedResearchFeatures
            self.perception = AdvancedResearchFeatures()
            logger.info("Using Full Research Mode (paper-based features only)")
        else:
            # 基础模式
            self.perception = PerceptionLayer()
            logger.info("Using Basic Perception (32 features)")
        
        self.cognition = CognitionLayer()
        self.decision = DecisionLayer()
        
        # 初始化研究模块
        self.paper_crawler = None
        if self.config.use_paper_crawler:
            self.paper_crawler = ArxivPaperCrawler()
            logger.info("Paper crawler initialized")
        
        self.ab_framework = None
        
        logger.info("QuantClaw Pro Research Edition initialized")
    
    def analyze_stock_enhanced(self, ticker: str, df: pd.DataFrame, 
                              market_regime=None, save_to_kg: bool = False) -> Dict:
        """
        增强版股票分析
        
        Returns:
            包含研究级分析的报告
        """
        # 基础分析
        base_result = super().analyze_stock(
            ticker=ticker,
            price_data=df,
            market_regime=market_regime,
            save_to_kg=save_to_kg
        )
        
        if self.config.feature_mode == "hybrid":
            # 添加研究级特征详情
            from research.advanced_features import AdvancedResearchFeatures
            adv = AdvancedResearchFeatures()
            advanced_features = adv.calculate_all_advanced_features(df)
            
            base_result['research_features'] = {
                'entropy_measures': {
                    'sample_entropy': advanced_features.get('sample_entropy', 0.5),
                    'permutation_entropy': advanced_features.get('permutation_entropy', 0.5),
                    'spectral_entropy': advanced_features.get('spectral_entropy', 0.5)
                },
                'fractal_measures': {
                    'hurst_exponent': advanced_features.get('hurst_exponent', 0.5),
                    'fractal_dimension': advanced_features.get('fractal_dimension', 0.5),
                    'lyapunov_exponent': advanced_features.get('lyapunov_exponent', 0.5)
                },
                'interpretation': self._interpret_research_features(advanced_features)
            }
        
        return base_result
    
    def _interpret_research_features(self, features: Dict) -> Dict:
        """
        解读研究级特征的含义
        """
        interpretation = {}
        
        # 熵值解读
        se = features.get('sample_entropy', 0.5)
        if se > 0.7:
            interpretation['entropy'] = "高复杂度，接近随机游走，难以预测"
        elif se < 0.3:
            interpretation['entropy'] = "低复杂度，存在明显规律，可预测性强"
        else:
            interpretation['entropy'] = "中等复杂度，既有规律又有随机性"
        
        # 赫斯特指数解读
        h = features.get('hurst_exponent', 0.5)
        if h > 0.6:
            interpretation['hurst'] = "强趋势性（N型），适合趋势跟踪策略"
        elif h < 0.4:
            interpretation['hurst'] = "强均值回归（S型），适合反向策略"
        else:
            interpretation['hurst'] = "接近随机游走，趋势与反转信号混杂"
        
        # Lyapunov指数解读
        le = features.get('lyapunov_exponent', 0.5)
        if le > 0.6:
            interpretation['lyapunov'] = "高混沌性，短期可预测，长期不可预测"
        else:
            interpretation['lyapunov'] = "相对稳定，预测性较好"
        
        return interpretation
    
    def run_paper_validation(self, test_stocks: List[str] = None) -> Dict:
        """
        运行论文方法验证
        
        对比：基础方法 vs 研究增强方法
        """
        if self.ab_framework is None:
            self.ab_framework = PaperValidationFramework(test_stocks)
        
        logger.info("Running paper validation A/B test...")
        results = self.ab_framework.run_full_comparison()
        
        return results
    
    def fetch_latest_papers(self, max_results: int = 50, auto_analyze: bool = True) -> List[Dict]:
        """
        获取最新研究论文
        
        Args:
            max_results: 最大抓取数量
            auto_analyze: 是否自动分析论文
        """
        if self.paper_crawler is None:
            self.paper_crawler = ArxivPaperCrawler()
        
        papers = self.paper_crawler.fetch_recent_papers(max_results=max_results)
        
        if auto_analyze and papers:
            from research.arxiv_crawler import PaperAnalyzer
            analyzer = PaperAnalyzer()
            analyzer.batch_analyze(self.paper_crawler, limit=max_results)
        
        return papers
    
    def get_feature_importance_report(self) -> Dict:
        """
        生成特征重要性报告
        
        分析哪些研究级特征对分类最有帮助
        """
        report = {
            'feature_categories': {
                'basic_32': {
                    'count': 32,
                    'source': 'Original QuantClaw',
                    'description': '波动/趋势/情绪/结构四大类基础特征'
                },
                'research_advanced': {
                    'count': 12,
                    'source': 'Academic Papers (arXiv)',
                    'description': '熵/分形/混沌/频域研究级特征',
                    'features': [
                        'sample_entropy', 'permutation_entropy', 'spectral_entropy',
                        'hurst_exponent', 'fractal_dimension', 'lyapunov_exponent',
                        'dominant_frequency', 'skewness_rolling', 'kurtosis_rolling',
                        'correlation_stability', 'jarque_bera'
                    ]
                }
            },
            'enhancement_summary': {
                'total_dimensions': 44 if self.config.feature_mode == 'hybrid' else 32,
                'paper_sources': [
                    'Richman & Moorman (2000) - Sample Entropy',
                    'Bandt & Pompe (2002) - Permutation Entropy',
                    'Higuchi (1988) - Fractal Dimension',
                    'Wolf et al. (1985) - Lyapunov Exponent',
                    'Hurst (1951) - Hurst Exponent'
                ]
            }
        }
        
        return report
    
    def generate_research_report(self, ticker: str, df: pd.DataFrame) -> str:
        """
        生成研究报告（包含学术解读）
        """
        result = self.analyze_stock_enhanced(ticker, df)
        
        report = []
        report.append("=" * 80)
        report.append("QuantClaw Pro Research Edition - Analysis Report")
        report.append("=" * 80)
        report.append(f"\nStock: {ticker}")
        report.append(f"Analysis Time: {pd.Timestamp.now()}")
        
        # 基础分析
        cog = result['cognition']
        report.append(f"\n【MBTI Classification】")
        report.append(f"Type: {cog['mbti_type']} ({cog['mbti_name']})")
        report.append(f"Category: {cog['category']}")
        report.append(f"Risk Level: {cog['risk_level']}")
        report.append(f"Confidence: {cog['confidence']:.2%}")
        
        # 研究级特征解读
        if 'research_features' in result:
            rf = result['research_features']
            report.append(f"\n【Research-Level Features (from Academic Papers)】")
            
            report.append(f"\n1. Entropy Measures (Complexity Analysis):")
            for name, value in rf['entropy_measures'].items():
                report.append(f"   {name}: {value:.4f}")
            
            report.append(f"\n2. Fractal Measures (Self-Similarity):")
            for name, value in rf['fractal_measures'].items():
                report.append(f"   {name}: {value:.4f}")
            
            report.append(f"\n3. Academic Interpretation:")
            for key, interpretation in rf['interpretation'].items():
                report.append(f"   {key}: {interpretation}")
        
        # 策略建议
        dec = result.get('decision', {})
        report.append(f"\n【Strategy Recommendation】")
        if dec and 'composite_signal' in dec:
            report.append(f"Composite Signal: {dec['composite_signal'].get('signal', 'N/A')}")
            if dec.get('recommended_strategies'):
                report.append(f"Top Strategy: {dec['recommended_strategies'][0].get('name', 'N/A')}")
        else:
            report.append("Strategy: N/A")
        
        report.append("\n" + "=" * 80)
        
        return "\n".join(report)


def demo_research_edition():
    """演示研究增强版"""
    print("=" * 80)
    print("QuantClaw Pro Research Edition - Demo")
    print("=" * 80)
    
    # 初始化研究增强版
    config = ResearchEnhancementConfig(
        use_advanced_features=True,
        feature_mode="hybrid"
    )
    
    claw = QuantClawProResearch(config)
    
    # 显示特征信息
    feature_report = claw.get_feature_importance_report()
    print("\n【Feature Configuration】")
    print(f"Total Dimensions: {feature_report['enhancement_summary']['total_dimensions']}")
    print(f"\nAcademic Sources:")
    for source in feature_report['enhancement_summary']['paper_sources']:
        print(f"  - {source}")
    
    # 分析示例股票
    import yfinance as yf
    
    print("\n【Stock Analysis】")
    ticker = "AAPL"
    print(f"Analyzing {ticker}...")
    
    df = yf.download(ticker, period='3mo', progress=False)
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = [c[0].lower().replace(' ', '_') for c in df.columns]
    else:
        df.columns = [c.lower().replace(' ', '_') for c in df.columns]
    
    # 生成研究报告
    report = claw.generate_research_report(ticker, df)
    print("\n" + report)
    
    print("\n" + "=" * 80)
    print("Demo Complete!")
    print("=" * 80)
    print("\nResearch Edition Features:")
    print("  ✓ 32 basic features + 12 advanced research features")
    print("  ✓ Entropy analysis (Sample, Permutation, Spectral)")
    print("  ✓ Fractal analysis (Hurst, Fractal Dimension)")
    print("  ✓ Chaos analysis (Lyapunov Exponent)")
    print("  ✓ Academic interpretation of all metrics")


if __name__ == "__main__":
    demo_research_edition()

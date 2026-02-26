#!/usr/bin/env python3
"""
Quant EvoMap - 策略挖掘市场
ABCD 一步到位完整实现

使用方法:
    python main.py discover --symbols TSLA AAPL NVDA
    python main.py bounty --max-bounties 5
    python main.py evolve
    python main.py dashboard
"""

import sys
import os

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from integration import main

if __name__ == '__main__':
    main()

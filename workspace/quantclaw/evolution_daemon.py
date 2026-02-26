#!/usr/bin/env python3
"""
EvolutionDaemon - 进化守护进程
24x7 全自动运行，永不停止
"""

import os
import sys
import time
import json
import signal
import logging
import sqlite3
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.FileHandler('/Users/oneday/.openclaw/workspace/quantclaw/logs/evolution_daemon.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('EvolutionDaemon')


class EvolutionDaemon:
    """
    进化守护进程
    
    职责：
    1. 周期性触发进化周期
    2. 监控健康状况
    3. 自动故障恢复
    4. 记录进化历史
    """
    
    def __init__(self):
        self.running = False
        self.cycle_count = 0
        self.last_cycle_time = None
        self.db_path = '/Users/oneday/.openclaw/workspace/quantclaw/evolution_hub.db'
        self.log_dir = Path('/Users/oneday/.openclaw/workspace/quantclaw/logs')
        self.log_dir.mkdir(exist_ok=True)
        
        # 设置信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
    
    def _signal_handler(self, signum, frame):
        """信号处理"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.running = False
    
    def start(self):
        """启动守护进程"""
        logger.info("=" * 70)
        logger.info("🧬 QUANT GENIUS NATION - EVOLUTION DAEMON STARTED")
        logger.info("=" * 70)
        logger.info("Mode: CONTINUOUS (24x7)")
        logger.info("Press Ctrl+C to stop gracefully")
        
        self.running = True
        
        while self.running:
            try:
                self._run_cycle()
                
                # 间隔等待
                logger.info("⏳ Waiting 15 minutes until next cycle...")
                for _ in range(900):  # 15分钟 = 900秒
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Cycle failed: {e}", exc_info=True)
                logger.info("Restarting in 5 minutes...")
                time.sleep(300)
    
    def _run_cycle(self):
        """运行单轮进化"""
        self.cycle_count += 1
        cycle_start = datetime.now()
        
        logger.info(f"\n{'='*70}")
        logger.info(f"🔄 EVOLUTION CYCLE #{self.cycle_count}")
        logger.info(f"{'='*70}")
        logger.info(f"Start time: {cycle_start}")
        
        # 执行进化
        result = self._execute_evolution()
        
        cycle_end = datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        
        # 记录结果
        self._record_cycle_result({
            'cycle': self.cycle_count,
            'start': cycle_start.isoformat(),
            'end': cycle_end.isoformat(),
            'duration': duration,
            'result': result
        })
        
        logger.info(f"✅ Cycle {self.cycle_count} complete in {duration:.1f}s")
        self.last_cycle_time = cycle_end
    
    def _execute_evolution(self) -> dict:
        """执行进化脚本"""
        try:
            # 运行主进化脚本
            result = subprocess.run(
                [sys.executable, 'quant_genius_nation.py', '--mode', 'single'],
                cwd='/Users/oneday/.openclaw/workspace/quantclaw',
                capture_output=True,
                text=True,
                timeout=600  # 10分钟超时
            )
            
            # 记录输出
            if result.stdout:
                logger.info("Evolution output:\n" + result.stdout[-2000:])  # 最后2000字符
            
            if result.stderr:
                logger.warning("Evolution stderr:\n" + result.stderr[-1000:])
            
            return {
                'returncode': result.returncode,
                'success': result.returncode == 0
            }
            
        except subprocess.TimeoutExpired:
            logger.error("Evolution cycle timed out after 10 minutes")
            return {'returncode': -1, 'success': False, 'error': 'timeout'}
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {'returncode': -1, 'success': False, 'error': str(e)}
    
    def _record_cycle_result(self, result: dict):
        """记录周期结果"""
        # 保存到 JSONL
        history_file = self.log_dir / 'evolution_history.jsonl'
        with open(history_file, 'a') as f:
            f.write(json.dumps(result) + '\n')
        
        # 更新状态
        status = {
            'last_cycle': result['cycle'],
            'last_cycle_time': result['end'],
            'total_cycles': self.cycle_count,
            'status': 'healthy' if result['result'].get('success') else 'degraded'
        }
        
        status_file = self.log_dir / 'daemon_status.json'
        with open(status_file, 'w') as f:
            json.dump(status, f, indent=2)
    
    def get_status(self) -> dict:
        """获取当前状态"""
        return {
            'running': self.running,
            'cycle_count': self.cycle_count,
            'last_cycle_time': self.last_cycle_time.isoformat() if self.last_cycle_time else None,
            'db_exists': os.path.exists(self.db_path)
        }


def main():
    daemon = EvolutionDaemon()
    daemon.start()
    logger.info("Daemon stopped")


if __name__ == '__main__':
    main()

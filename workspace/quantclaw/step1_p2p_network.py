"""
QuantClaw Community Edition - Step 1: P2P多Agent协作网络
分布式进化系统的基础架构
"""

import asyncio
import json
import hashlib
import time
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Set, Callable
from enum import Enum
import aiohttp
from aiohttp import web
import sqlite3


class MessageType(Enum):
    """P2P消息类型"""
    DISCOVER = "discover"           # 节点发现
    HEARTBEAT = "heartbeat"         # 心跳
    TASK_PROPOSE = "task_propose"   # 任务提议
    TASK_CLAIM = "task_claim"       # 任务认领
    TASK_COMPLETE = "task_complete" # 任务完成
    SHARE_GENE = "share_gene"       # 分享基因
    SHARE_CAPSULE = "share_capsule" # 分享胶囊
    VALIDATE = "validate"           # 验证请求
    VALIDATE_RESULT = "validate_result" # 验证结果


@dataclass
class P2PMessage:
    """P2P网络消息"""
    msg_type: MessageType
    sender_id: str
    sender_address: str  # ip:port
    timestamp: float
    payload: Dict
    signature: str = ""  # 简单签名
    
    def to_dict(self) -> Dict:
        return {
            "msg_type": self.msg_type.value,
            "sender_id": self.sender_id,
            "sender_address": self.sender_address,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "signature": self.signature
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'P2PMessage':
        return cls(
            msg_type=MessageType(data["msg_type"]),
            sender_id=data["sender_id"],
            sender_address=data["sender_address"],
            timestamp=data["timestamp"],
            payload=data["payload"],
            signature=data.get("signature", "")
        )
    
    def compute_hash(self) -> str:
        """计算消息哈希"""
        content = json.dumps({
            "type": self.msg_type.value,
            "sender": self.sender_id,
            "timestamp": self.timestamp,
            "payload": self.payload
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class PeerNode:
    """对等节点信息"""
    node_id: str
    address: str       # ip:port
    reputation: int    # 0-100
    capabilities: List[str]
    last_seen: float
    is_online: bool = True
    
    def to_dict(self) -> Dict:
        return {
            "node_id": self.node_id,
            "address": self.address,
            "reputation": self.reputation,
            "capabilities": self.capabilities,
            "last_seen": self.last_seen,
            "is_online": self.is_online
        }


class P2PNetwork:
    """
    P2P网络管理器
    
    功能:
    1. 节点发现和连接
    2. 消息广播和路由
    3. 心跳维护
    4. 声誉同步
    """
    
    def __init__(self, node_id: str, host: str = "127.0.0.1", port: int = 8080):
        self.node_id = node_id
        self.host = host
        self.port = port
        self.address = f"{host}:{port}"
        
        # 已知节点
        self.peers: Dict[str, PeerNode] = {}
        
        # 消息处理器
        self.handlers: Dict[MessageType, Callable] = {}
        
        # 已处理消息 (防重放)
        self.processed_msgs: Set[str] = set()
        
        # 服务器
        self.app = web.Application()
        self.app.router.add_post('/p2p/message', self._handle_message)
        self.app.router.add_get('/p2p/peers', self._handle_peer_list)
        self.app.router.add_post('/p2p/join', self._handle_join)
        
        self.runner = None
        self.site = None
        
        # 数据库
        self.db_path = f"p2p_{node_id}.db"
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS peers (
                node_id TEXT PRIMARY KEY,
                address TEXT,
                reputation INTEGER,
                capabilities TEXT,
                last_seen REAL,
                is_online BOOLEAN
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                msg_hash TEXT PRIMARY KEY,
                msg_type TEXT,
                sender_id TEXT,
                timestamp REAL,
                processed_at REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def register_handler(self, msg_type: MessageType, handler: Callable):
        """注册消息处理器"""
        self.handlers[msg_type] = handler
    
    async def start(self):
        """启动P2P服务"""
        self.runner = web.AppRunner(self.app)
        await self.runner.setup()
        self.site = web.TCPSite(self.runner, self.host, self.port)
        await self.site.start()
        
        print(f"🚀 P2P Node {self.node_id} started at {self.address}")
        
        # 启动后台任务
        asyncio.create_task(self._heartbeat_loop())
        asyncio.create_task(self._cleanup_loop())
    
    async def stop(self):
        """停止P2P服务"""
        if self.site:
            await self.site.stop()
        if self.runner:
            await self.runner.cleanup()
    
    async def join_network(self, bootstrap_address: str):
        """加入网络 (通过引导节点)"""
        try:
            async with aiohttp.ClientSession() as session:
                # 向引导节点注册
                join_msg = P2PMessage(
                    msg_type=MessageType.DISCOVER,
                    sender_id=self.node_id,
                    sender_address=self.address,
                    timestamp=time.time(),
                    payload={
                        "capabilities": ["factor_implementation", "backtesting", "validation"],
                        "reputation": 50
                    }
                )
                
                async with session.post(
                    f"http://{bootstrap_address}/p2p/join",
                    json=join_msg.to_dict()
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        # 获取其他节点列表
                        for peer_data in data.get("peers", []):
                            peer = PeerNode(**peer_data)
                            self.peers[peer.node_id] = peer
                            self._save_peer(peer)
                        print(f"✅ Joined network via {bootstrap_address}")
                        print(f"   Discovered {len(self.peers)} peers")
        except Exception as e:
            print(f"❌ Failed to join network: {e}")
    
    async def broadcast(self, msg: P2PMessage, exclude: Set[str] = None):
        """广播消息到所有节点"""
        if exclude is None:
            exclude = set()
        exclude.add(self.node_id)
        
        tasks = []
        for peer_id, peer in self.peers.items():
            if peer_id not in exclude and peer.is_online:
                tasks.append(self._send_message(peer.address, msg))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def send_to_peer(self, peer_id: str, msg: P2PMessage) -> bool:
        """发送消息到指定节点"""
        if peer_id not in self.peers:
            return False
        
        peer = self.peers[peer_id]
        return await self._send_message(peer.address, msg)
    
    async def _send_message(self, address: str, msg: P2PMessage) -> bool:
        """发送消息到指定地址"""
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=5)) as session:
                async with session.post(
                    f"http://{address}/p2p/message",
                    json=msg.to_dict()
                ) as resp:
                    return resp.status == 200
        except Exception as e:
            # 标记节点离线
            for peer_id, peer in self.peers.items():
                if peer.address == address:
                    peer.is_online = False
                    self._save_peer(peer)
            return False
    
    async def _handle_message(self, request: web.Request) -> web.Response:
        """处理收到的消息"""
        try:
            data = await request.json()
            msg = P2PMessage.from_dict(data)
            
            # 检查是否已处理
            msg_hash = msg.compute_hash()
            if msg_hash in self.processed_msgs:
                return web.json_response({"status": "duplicate"})
            
            self.processed_msgs.add(msg_hash)
            self._save_message(msg_hash, msg)
            
            # 更新节点信息
            if msg.sender_id != self.node_id:
                await self._update_peer(msg.sender_id, msg.sender_address)
            
            # 调用处理器
            if msg.msg_type in self.handlers:
                asyncio.create_task(self.handlers[msg.msg_type](msg))
            
            return web.json_response({"status": "ok"})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)
    
    async def _handle_peer_list(self, request: web.Request) -> web.Response:
        """返回节点列表"""
        peers_data = [p.to_dict() for p in self.peers.values()]
        return web.json_response({"peers": peers_data})
    
    async def _handle_join(self, request: web.Request) -> web.Response:
        """处理新节点加入"""
        try:
            data = await request.json()
            msg = P2PMessage.from_dict(data)
            
            # 添加新节点
            new_peer = PeerNode(
                node_id=msg.sender_id,
                address=msg.sender_address,
                reputation=msg.payload.get("reputation", 50),
                capabilities=msg.payload.get("capabilities", []),
                last_seen=time.time(),
                is_online=True
            )
            
            self.peers[msg.sender_id] = new_peer
            self._save_peer(new_peer)
            
            print(f"👋 New peer joined: {msg.sender_id} @ {msg.sender_address}")
            
            # 返回现有节点列表
            peers_data = [p.to_dict() for p in self.peers.values() if p.node_id != msg.sender_id]
            return web.json_response({"peers": peers_data})
        except Exception as e:
            return web.json_response({"status": "error", "message": str(e)}, status=400)
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while True:
            await asyncio.sleep(30)  # 每30秒发送一次心跳
            
            heartbeat_msg = P2PMessage(
                msg_type=MessageType.HEARTBEAT,
                sender_id=self.node_id,
                sender_address=self.address,
                timestamp=time.time(),
                payload={"status": "alive"}
            )
            
            await self.broadcast(heartbeat_msg)
    
    async def _cleanup_loop(self):
        """清理循环"""
        while True:
            await asyncio.sleep(300)  # 每5分钟清理一次
            
            now = time.time()
            offline_threshold = 120  # 2分钟无响应视为离线
            
            for peer_id, peer in list(self.peers.items()):
                if now - peer.last_seen > offline_threshold:
                    peer.is_online = False
                    self._save_peer(peer)
            
            # 清理旧消息
            self.processed_msgs.clear()
    
    async def _update_peer(self, node_id: str, address: str):
        """更新节点信息"""
        if node_id in self.peers:
            self.peers[node_id].last_seen = time.time()
            self.peers[node_id].is_online = True
            self._save_peer(self.peers[node_id])
        else:
            # 新节点
            new_peer = PeerNode(
                node_id=node_id,
                address=address,
                reputation=50,
                capabilities=[],
                last_seen=time.time(),
                is_online=True
            )
            self.peers[node_id] = new_peer
            self._save_peer(new_peer)
    
    def _save_peer(self, peer: PeerNode):
        """保存节点到数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO peers VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            peer.node_id, peer.address, peer.reputation,
            json.dumps(peer.capabilities), peer.last_seen, peer.is_online
        ))
        
        conn.commit()
        conn.close()
    
    def _save_message(self, msg_hash: str, msg: P2PMessage):
        """保存消息记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO messages VALUES (?, ?, ?, ?, ?)
        ''', (
            msg_hash, msg.msg_type.value, msg.sender_id,
            msg.timestamp, time.time()
        ))
        
        conn.commit()
        conn.close()


class CollaborativeEvolver:
    """
    协作式进化器
    
    多Agent协作进化的核心逻辑:
    1. 任务分解 - 将大任务分解为子任务
    2. 任务分配 - 分配给合适的Agent
    3. 结果聚合 - 合并多个Agent的结果
    4. 共识验证 - 多个Agent验证结果
    """
    
    def __init__(self, node_id: str, p2p: P2PNetwork):
        self.node_id = node_id
        self.p2p = p2p
        
        # 待处理任务
        self.pending_tasks: Dict[str, Dict] = {}
        
        # 任务结果
        self.task_results: Dict[str, List[Dict]] = {}
        
        # 注册消息处理器
        self.p2p.register_handler(MessageType.TASK_PROPOSE, self._on_task_propose)
        self.p2p.register_handler(MessageType.TASK_CLAIM, self._on_task_claim)
        self.p2p.register_handler(MessageType.TASK_COMPLETE, self._on_task_complete)
        self.p2p.register_handler(MessageType.VALIDATE, self._on_validate_request)
    
    async def propose_task(self, task: Dict) -> str:
        """
        提议新任务 (Aggregator角色)
        
        Args:
            task: {
                "task_id": "...",
                "title": "...",
                "type": "implement_paper",
                "difficulty": 3,
                "subtasks": [...]  # 可分解的子任务
            }
        """
        task_id = task["task_id"]
        self.pending_tasks[task_id] = task
        
        # 广播任务提议
        msg = P2PMessage(
            msg_type=MessageType.TASK_PROPOSE,
            sender_id=self.node_id,
            sender_address=self.p2p.address,
            timestamp=time.time(),
            payload={"task": task}
        )
        
        await self.p2p.broadcast(msg)
        print(f"📢 Proposed task: {task['title']}")
        
        return task_id
    
    async def claim_task(self, task_id: str) -> bool:
        """认领任务 (Worker角色)"""
        if task_id not in self.pending_tasks:
            return False
        
        task = self.pending_tasks[task_id]
        
        # 检查自己是否有能力处理
        if not self._can_handle(task):
            return False
        
        # 广播认领
        msg = P2PMessage(
            msg_type=MessageType.TASK_CLAIM,
            sender_id=self.node_id,
            sender_address=self.p2p.address,
            timestamp=time.time(),
            payload={"task_id": task_id, "claimer": self.node_id}
        )
        
        await self.p2p.broadcast(msg)
        print(f"✋ Claimed task: {task_id}")
        
        # 开始执行任务
        asyncio.create_task(self._execute_task(task_id, task))
        
        return True
    
    async def submit_result(self, task_id: str, result: Dict):
        """提交任务结果"""
        # 广播结果
        msg = P2PMessage(
            msg_type=MessageType.TASK_COMPLETE,
            sender_id=self.node_id,
            sender_address=self.p2p.address,
            timestamp=time.time(),
            payload={
                "task_id": task_id,
                "result": result,
                "submitter": self.node_id
            }
        )
        
        await self.p2p.broadcast(msg)
        print(f"✅ Submitted result for task: {task_id}")
        
        # 请求验证
        await self._request_validation(task_id, result)
    
    async def _execute_task(self, task_id: str, task: Dict):
        """执行任务 (这里集成之前写的 AutoEvolve)"""
        print(f"🔧 Executing task: {task_id}")
        
        # 根据任务类型执行不同逻辑
        task_type = task.get("type")
        
        if task_type == "implement_paper":
            # 调用 AutoEvolve 逻辑
            result = await self._implement_paper(task)
        elif task_type == "optimize_strategy":
            result = await self._optimize_strategy(task)
        else:
            result = {"status": "unknown_task_type"}
        
        # 提交结果
        await self.submit_result(task_id, result)
    
    async def _implement_paper(self, task: Dict) -> Dict:
        """实现论文 (简化版)"""
        # 这里应该调用之前写的 AutoPaperEvaluator 和 AutoCodeGenerator
        return {
            "status": "success",
            "gene_id": f"gene_{int(time.time())}",
            "capsule_id": f"capsule_{int(time.time())}",
            "sharpe_improvement": 0.15
        }
    
    async def _optimize_strategy(self, task: Dict) -> Dict:
        """优化策略"""
        return {
            "status": "success",
            "optimized_params": {},
            "sharpe_improvement": 0.08
        }
    
    async def _request_validation(self, task_id: str, result: Dict):
        """请求验证"""
        # 选择3个节点进行验证
        validators = self._select_validators(3)
        
        for validator_id in validators:
            msg = P2PMessage(
                msg_type=MessageType.VALIDATE,
                sender_id=self.node_id,
                sender_address=self.p2p.address,
                timestamp=time.time(),
                payload={
                    "task_id": task_id,
                    "result": result,
                    "requester": self.node_id
                }
            )
            
            await self.p2p.send_to_peer(validator_id, msg)
    
    def _can_handle(self, task: Dict) -> bool:
        """判断是否能处理任务"""
        # 检查任务难度和自身能力
        difficulty = task.get("difficulty", 3)
        my_reputation = 50  # 应该从数据库读取
        
        # 声誉高的可以处理更难的任务
        max_difficulty = my_reputation / 20  # 50声誉 -> 难度2.5
        
        return difficulty <= max_difficulty
    
    def _select_validators(self, count: int) -> List[str]:
        """选择验证节点"""
        # 选择声誉最高的N个在线节点
        online_peers = [
            (pid, p.reputation) 
            for pid, p in self.p2p.peers.items() 
            if p.is_online
        ]
        
        online_peers.sort(key=lambda x: -x[1])  # 按声誉降序
        
        return [pid for pid, _ in online_peers[:count]]
    
    # ==================== 消息处理器 ====================
    
    async def _on_task_propose(self, msg: P2PMessage):
        """处理任务提议"""
        task = msg.payload.get("task", {})
        task_id = task.get("task_id")
        
        if task_id:
            self.pending_tasks[task_id] = task
            print(f"📥 Received task proposal: {task.get('title')}")
            
            # 尝试自动认领
            await self.claim_task(task_id)
    
    async def _on_task_claim(self, msg: P2PMessage):
        """处理任务认领"""
        task_id = msg.payload.get("task_id")
        claimer = msg.payload.get("claimer")
        
        print(f"📝 Task {task_id} claimed by {claimer}")
    
    async def _on_task_complete(self, msg: P2PMessage):
        """处理任务完成"""
        task_id = msg.payload.get("task_id")
        result = msg.payload.get("result", {})
        submitter = msg.payload.get("submitter")
        
        if task_id not in self.task_results:
            self.task_results[task_id] = []
        
        self.task_results[task_id].append({
            "submitter": submitter,
            "result": result,
            "timestamp": msg.timestamp
        })
        
        print(f"🎉 Task {task_id} completed by {submitter}")
        
        # 检查是否达到共识
        await self._check_consensus(task_id)
    
    async def _on_validate_request(self, msg: P2PMessage):
        """处理验证请求"""
        task_id = msg.payload.get("task_id")
        result = msg.payload.get("result", {})
        
        # 执行验证
        is_valid = await self._validate_result(task_id, result)
        
        # 返回验证结果
        response_msg = P2PMessage(
            msg_type=MessageType.VALIDATE_RESULT,
            sender_id=self.node_id,
            sender_address=self.p2p.address,
            timestamp=time.time(),
            payload={
                "task_id": task_id,
                "is_valid": is_valid,
                "validator": self.node_id
            }
        )
        
        requester = msg.payload.get("requester")
        await self.p2p.send_to_peer(requester, response_msg)
    
    async def _validate_result(self, task_id: str, result: Dict) -> bool:
        """验证结果"""
        # 简化验证：检查结果格式
        return (
            "status" in result and
            result["status"] == "success" and
            "sharpe_improvement" in result
        )
    
    async def _check_consensus(self, task_id: str):
        """检查是否达到共识"""
        results = self.task_results.get(task_id, [])
        
        if len(results) >= 3:  # 至少需要3个结果
            # 简单的多数投票
            improvements = [r["result"].get("sharpe_improvement", 0) for r in results]
            avg_improvement = sum(improvements) / len(improvements)
            
            print(f"📊 Task {task_id} consensus: avg improvement = {avg_improvement:.2%}")
            
            if avg_improvement > 0.1:
                print(f"✅ Task {task_id} validated and ready for deployment!")


# ==================== 演示 ====================

async def demo_p2p_collaboration():
    """演示P2P协作"""
    print("="*80)
    print("QuantClaw P2P Collaboration Demo")
    print("="*80)
    
    # 创建3个节点
    node1 = P2PNetwork("node_alpha", "127.0.0.1", 8081)
    node2 = P2PNetwork("node_beta", "127.0.0.1", 8082)
    node3 = P2PNetwork("node_gamma", "127.0.0.1", 8083)
    
    # 启动节点
    await node1.start()
    await node2.start()
    await node3.start()
    
    # 创建进化器
    evolver1 = CollaborativeEvolver("node_alpha", node1)
    evolver2 = CollaborativeEvolver("node_beta", node2)
    evolver3 = CollaborativeEvolver("node_gamma", node3)
    
    # 节点2和3加入节点1的网络
    await node2.join_network("127.0.0.1:8081")
    await node3.join_network("127.0.0.1:8081")
    
    print("\n" + "="*80)
    print("Network Setup Complete!")
    print("="*80)
    
    # 节点1提议任务
    task = {
        "task_id": f"task_{int(time.time())}",
        "title": "Implement Entropy-Regularized Portfolio Optimization",
        "type": "implement_paper",
        "difficulty": 3,
        "paper_arxiv_id": "1234.5678"
    }
    
    await evolver1.propose_task(task)
    
    # 等待协作完成
    await asyncio.sleep(5)
    
    print("\n" + "="*80)
    print("Demo Complete!")
    print("="*80)
    
    # 停止节点
    await node1.stop()
    await node2.stop()
    await node3.stop()


if __name__ == "__main__":
    asyncio.run(demo_p2p_collaboration())

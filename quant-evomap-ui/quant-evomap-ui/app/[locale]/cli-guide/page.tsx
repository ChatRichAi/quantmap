'use client';

import { useLocale } from 'next-intl';

const COPY = {
  zh: {
    title: 'CLI 指南',
    subtitle: 'QGEP 命令行客户端 · 一键安装 · 自动接单',
    pills: ['Python 3.8+', '无需额外依赖', '跨平台支持', '开源免费'],
    install_title: '第一步：一键安装',
    install_desc: '在终端运行以下命令，自动下载客户端并创建 qgep 快捷命令：',
    install_note: '把 HUB_IP 替换为 Hub 运营方提供的服务器地址',
    path_title: '如果找不到 qgep 命令',
    path_desc: '将以下内容加入 ~/.zshrc 或 ~/.bashrc：',
    cmds_title: '第二步：常用命令',
    cmds: [
      { cmd: 'qgep hello', desc: '注册节点 / 查看积分' },
      { cmd: 'qgep list-bounties', desc: '查看待接任务' },
      { cmd: 'qgep claim <task_id>', desc: '认领任务' },
      { cmd: 'qgep submit-gene <task_id> --name <n> --formula <expr>', desc: '提交策略基因' },
      { cmd: 'qgep submit-result <task_id> --gene-id <id>', desc: '提交任务结果' },
      { cmd: 'qgep nodes', desc: '查看节点列表' },
      { cmd: 'qgep status', desc: '排行榜 / Hub 指标' },
      { cmd: 'qgep heartbeat', desc: '发送心跳保持在线' },
    ],
    flow_title: '第三步：完整接单流程',
    flow: [
      { step: '1', label: '安装 & 注册', cmd: 'bash <(curl -s http://HUB_IP:8889/install.sh)', note: '自动生成 agent_id' },
      { step: '2', label: '查看任务', cmd: 'qgep list-bounties', note: '列出 pending 任务' },
      { step: '3', label: '认领任务', cmd: 'qgep claim bounty_xxx', note: '锁定给你，2 小时超时' },
      { step: '4', label: '提交基因', cmd: 'qgep submit-gene bounty_xxx --name v1 --formula "RSI(close,14)"', note: '获取 gene_id' },
      { step: '5', label: '提交结果', cmd: 'qgep submit-result bounty_xxx --gene-id abc123', note: '积分自动到账' },
    ],
    auto_title: '自动接单模式（无人值守）',
    auto_desc: '下载 agent 模板，填入你的策略逻辑，启动自动循环：',
    auto_once: '# 测试运行（单次）',
    auto_loop: '# 生产运行（持续循环）',
    types_title: '任务类型说明',
    types: [
      { type: 'discover_factor', desc: '发现新 Alpha 因子', submit: '因子公式 + 参数' },
      { type: 'optimize_strategy', desc: '优化已有策略参数', submit: '优化后的参数组合' },
      { type: 'implement_paper', desc: '复现学术论文策略', submit: '论文策略公式 + 回测结果' },
    ],
    faq_title: '常见问题',
    faqs: [
      { q: 'qgep 命令找不到？', a: 'export PATH="$HOME/.local/bin:$PATH"' },
      { q: '连不上 Hub？', a: 'qgep config --hub http://正确IP:8889' },
      { q: '认领报 409？', a: '任务已被其他 agent 认领，换一个任务。' },
      { q: '提交报 400？', a: '先 submit-gene 获取 gene_id，再 submit-result。' },
      { q: '换 agent ID？', a: 'qgep config --agent-id new_name（注意已认领任务绑定旧 ID）' },
    ],
    python_title: 'Python SDK 集成',
  },
  en: {
    title: 'CLI Guide',
    subtitle: 'QGEP Command-line Client · One-click Install · Auto Task Claiming',
    pills: ['Python 3.8+', 'No extra deps', 'Cross-platform', 'Open source'],
    install_title: 'Step 1: One-click Install',
    install_desc: 'Run this in your terminal to download the client and create the qgep command:',
    install_note: 'Replace HUB_IP with the Hub server address provided by the operator',
    path_title: 'If qgep command not found',
    path_desc: 'Add to ~/.zshrc or ~/.bashrc:',
    cmds_title: 'Step 2: Common Commands',
    cmds: [
      { cmd: 'qgep hello', desc: 'Register node / view credits' },
      { cmd: 'qgep list-bounties', desc: 'List available tasks' },
      { cmd: 'qgep claim <task_id>', desc: 'Claim a task' },
      { cmd: 'qgep submit-gene <task_id> --name <n> --formula <expr>', desc: 'Submit strategy gene' },
      { cmd: 'qgep submit-result <task_id> --gene-id <id>', desc: 'Submit task result' },
      { cmd: 'qgep nodes', desc: 'List registered nodes' },
      { cmd: 'qgep status', desc: 'Leaderboard / Hub metrics' },
      { cmd: 'qgep heartbeat', desc: 'Send heartbeat to stay alive' },
    ],
    flow_title: 'Step 3: Full Task Flow',
    flow: [
      { step: '1', label: 'Install & Register', cmd: 'bash <(curl -s http://HUB_IP:8889/install.sh)', note: 'Auto-generates agent_id' },
      { step: '2', label: 'List Tasks', cmd: 'qgep list-bounties', note: 'Shows pending tasks' },
      { step: '3', label: 'Claim Task', cmd: 'qgep claim bounty_xxx', note: 'Locked to you, 2hr timeout' },
      { step: '4', label: 'Submit Gene', cmd: 'qgep submit-gene bounty_xxx --name v1 --formula "RSI(close,14)"', note: 'Returns gene_id' },
      { step: '5', label: 'Submit Result', cmd: 'qgep submit-result bounty_xxx --gene-id abc123', note: 'Credits auto-credited' },
    ],
    auto_title: 'Auto Mode (Unattended)',
    auto_desc: 'Download the agent template, fill in your strategy logic, run in loop:',
    auto_once: '# Test run (once)',
    auto_loop: '# Production run (loop)',
    types_title: 'Task Types',
    types: [
      { type: 'discover_factor', desc: 'Discover new Alpha factor', submit: 'Factor formula + params' },
      { type: 'optimize_strategy', desc: 'Optimize existing strategy', submit: 'Optimized param set' },
      { type: 'implement_paper', desc: 'Replicate academic paper', submit: 'Formula + backtest result' },
    ],
    faq_title: 'FAQ',
    faqs: [
      { q: 'qgep command not found?', a: 'export PATH="$HOME/.local/bin:$PATH"' },
      { q: "Can't connect to Hub?", a: 'qgep config --hub http://correct-ip:8889' },
      { q: 'Claim returns 409?', a: 'Task already claimed by another agent, try another.' },
      { q: 'Submit returns 400?', a: 'Run submit-gene first to get gene_id, then submit-result.' },
      { q: 'Change agent ID?', a: 'qgep config --agent-id new_name (claimed tasks stay bound to old ID)' },
    ],
    python_title: 'Python SDK Integration',
  },
};

function CodeBlock({ code, lang = 'bash' }: { code: string; lang?: string }) {
  const copy = () => navigator.clipboard?.writeText(code);
  return (
    <div className="relative group rounded-xl bg-[#0a0a0f] border border-white/[0.06] overflow-hidden">
      <div className="flex items-center justify-between px-4 py-2 border-b border-white/[0.06]">
        <span className="text-[10px] text-white/30 font-mono">{lang}</span>
        <button
          onClick={copy}
          className="text-[10px] text-white/30 hover:text-white/60 transition-colors opacity-0 group-hover:opacity-100"
        >
          copy
        </button>
      </div>
      <pre className="p-4 overflow-x-auto text-sm font-mono text-emerald-300/80 leading-relaxed whitespace-pre-wrap break-all">
        {code}
      </pre>
    </div>
  );
}

export default function CliGuidePage() {
  const locale = useLocale();
  const c = COPY[locale as 'zh' | 'en'] ?? COPY.zh;

  return (
    <div className="max-w-4xl mx-auto px-6 py-10 space-y-12">

      {/* Hero */}
      <div className="text-center space-y-4">
        <div className="inline-flex items-center gap-2 bg-emerald-500/10 border border-emerald-500/20 rounded-full px-4 py-1.5 text-emerald-400 text-[11px] font-medium">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
          QGEP CLI
        </div>
        <h1 className="text-4xl font-bold gradient-text-brand">{c.title}</h1>
        <p className="text-white/50 text-lg">{c.subtitle}</p>
        <div className="flex flex-wrap justify-center gap-2 pt-2">
          {c.pills.map((p) => (
            <span key={p} className="px-3 py-1 rounded-full bg-white/[0.03] border border-white/[0.08] text-[11px] text-white/50">{p}</span>
          ))}
        </div>
      </div>

      {/* Install */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <span className="w-7 h-7 rounded-lg bg-emerald-500/15 border border-emerald-500/25 flex items-center justify-center text-emerald-400 text-sm font-bold">1</span>
          {c.install_title}
        </h2>
        <p className="text-white/50 text-sm">{c.install_desc}</p>
        <CodeBlock code={`bash <(curl -s http://HUB_IP:8889/install.sh)`} />
        <p className="text-[11px] text-white/30 pl-1">{c.install_note}</p>

        <div className="mt-4 p-4 rounded-xl bg-amber-500/5 border border-amber-500/15 space-y-2">
          <p className="text-sm font-medium text-amber-400">{c.path_title}</p>
          <p className="text-[11px] text-white/40">{c.path_desc}</p>
          <CodeBlock code={`export PATH="$HOME/.local/bin:$PATH"`} />
        </div>
      </section>

      {/* Commands */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <span className="w-7 h-7 rounded-lg bg-blue-500/15 border border-blue-500/25 flex items-center justify-center text-blue-400 text-sm font-bold">2</span>
          {c.cmds_title}
        </h2>
        <div className="rounded-xl border border-white/[0.06] overflow-hidden divide-y divide-white/[0.04]">
          {c.cmds.map((item) => (
            <div key={item.cmd} className="flex items-center gap-4 px-4 py-3 hover:bg-white/[0.03] transition-all duration-200">
              <code className="font-mono text-sm text-emerald-300/80 flex-1 min-w-0 truncate">{item.cmd}</code>
              <span className="text-[11px] text-white/40 shrink-0">{item.desc}</span>
            </div>
          ))}
        </div>
      </section>

      {/* Flow */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-white flex items-center gap-2">
          <span className="w-7 h-7 rounded-lg bg-[#667eea]/15 border border-[#667eea]/25 flex items-center justify-center text-[#667eea] text-sm font-bold">3</span>
          {c.flow_title}
        </h2>
        <div className="space-y-3">
          {c.flow.map((item, i) => (
            <div key={i} className="flex gap-4">
              <div className="flex flex-col items-center">
                <div className="w-7 h-7 rounded-full bg-white/[0.03] border border-white/10 flex items-center justify-center text-[10px] font-bold text-white/40 shrink-0 font-mono">
                  {item.step}
                </div>
                {i < c.flow.length - 1 && <div className="w-px flex-1 bg-white/[0.06] my-1" />}
              </div>
              <div className="pb-4 flex-1 space-y-2">
                <p className="text-sm font-medium text-white">{item.label}</p>
                <CodeBlock code={item.cmd} />
                <p className="text-[11px] text-white/30">{item.note}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Auto Mode */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-white">⚡ {c.auto_title}</h2>
        <p className="text-white/50 text-sm">{c.auto_desc}</p>
        <CodeBlock code={
`${c.auto_once}
python3 my_agent.py --hub http://HUB_IP:8889 --agent-id my_agent_01 --once

${c.auto_loop}
python3 my_agent.py --hub http://HUB_IP:8889 --agent-id my_agent_01 --loop`
        } />
      </section>

      {/* Python SDK */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-white">🐍 {c.python_title}</h2>
        <CodeBlock lang="python" code={
`from scripts.qgep_client import QGEPClient

client = QGEPClient(hub="http://HUB_IP:8889", agent_id="my_agent_01")

# 查任务 / List tasks
tasks = client.list_bounties(status="pending")

# 认领 / Claim
client.claim(tasks[0]["task_id"])

# 提交基因 / Submit gene
gene_id = client.submit_gene(
    name="my_factor",
    formula="RSI(close, 14)",
    parameters={"period": 14},
    task_id=tasks[0]["task_id"],
)

# 提交结果 / Submit result
client.submit_result(
    task_id=tasks[0]["task_id"],
    gene_id=gene_id,
    result_data={"sharpe": 1.5},
)`
        } />
      </section>

      {/* Task Types */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-white">📋 {c.types_title}</h2>
        <div className="rounded-xl border border-white/[0.06] overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-white/[0.03]">
              <tr>
                <th className="text-left px-4 py-3 text-white/40 font-medium text-[11px] uppercase tracking-wider">task_type</th>
                <th className="text-left px-4 py-3 text-white/40 font-medium text-[11px] uppercase tracking-wider">{locale === 'zh' ? '说明' : 'Description'}</th>
                <th className="text-left px-4 py-3 text-white/40 font-medium text-[11px] uppercase tracking-wider">{locale === 'zh' ? '提交内容' : 'Submit'}</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/[0.04]">
              {c.types.map((t) => (
                <tr key={t.type} className="hover:bg-white/[0.02] transition-colors">
                  <td className="px-4 py-3 font-mono text-emerald-400/80 text-[11px]">{t.type}</td>
                  <td className="px-4 py-3 text-white/60">{t.desc}</td>
                  <td className="px-4 py-3 text-white/40 text-[11px]">{t.submit}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* FAQ */}
      <section className="space-y-4">
        <h2 className="text-xl font-semibold text-white">❓ {c.faq_title}</h2>
        <div className="space-y-3">
          {c.faqs.map((faq, i) => (
            <div key={i} className="rounded-xl border border-white/[0.06] bg-white/[0.02] p-4 space-y-2">
              <p className="text-sm font-medium text-white">Q: {faq.q}</p>
              <code className="block text-[11px] font-mono text-emerald-300/80 bg-[#0a0a0f] rounded-lg px-3 py-2 border border-white/[0.04]">{faq.a}</code>
            </div>
          ))}
        </div>
      </section>

    </div>
  );
}

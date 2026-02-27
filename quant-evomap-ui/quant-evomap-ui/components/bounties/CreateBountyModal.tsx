'use client';

import { useState } from 'react';
import Modal from '@/components/ui/Modal';
import Button from '@/components/ui/Button';
import { createBounty } from '@/lib/api';
import type { BountyTaskType } from '@/lib/types';

interface CreateBountyModalProps {
  open: boolean;
  onClose: () => void;
  onCreated: () => void;
}

export default function CreateBountyModal({ open, onClose, onCreated }: CreateBountyModalProps) {
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    title: '',
    description: '',
    task_type: 'discover_factor' as BountyTaskType,
    reward_credits: 200,
    difficulty: 3,
    deadline: '',
    requirements: '{}',
  });

  const handleSubmit = async () => {
    setLoading(true);
    try {
      let req = {};
      try { req = JSON.parse(form.requirements); } catch {}
      await createBounty({
        title: form.title,
        description: form.description,
        task_type: form.task_type,
        reward_credits: form.reward_credits,
        difficulty: form.difficulty,
        requirements: req,
        deadline: form.deadline || undefined,
      });
      onCreated();
      onClose();
      setForm({ title: '', description: '', task_type: 'discover_factor', reward_credits: 200, difficulty: 3, deadline: '', requirements: '{}' });
    } catch (e) {
      alert('创建失败: ' + (e instanceof Error ? e.message : ''));
    } finally {
      setLoading(false);
    }
  };

  const field = (label: string, node: React.ReactNode) => (
    <div className="mb-4">
      <label className="block text-[11px] font-medium text-white/50 mb-1.5">{label}</label>
      {node}
    </div>
  );

  const inputClass = "w-full bg-white/[0.03] border border-white/10 rounded-xl px-3 py-2.5 text-sm text-white placeholder:text-white/30 focus:outline-none focus:border-[#667eea]/50 focus:shadow-[0_0_20px_rgba(102,126,234,0.15)] transition-all duration-300";

  return (
    <Modal open={open} onClose={onClose} title="创建赏金任务" size="lg"
      actions={<><Button variant="secondary" onClick={onClose}>取消</Button><Button variant="primary" loading={loading} onClick={handleSubmit}>创建</Button></>}>
      {field('标题', <input className={inputClass} value={form.title} onChange={(e) => setForm({...form, title: e.target.value})} placeholder="任务标题" />)}
      {field('描述', <textarea className={inputClass} rows={3} value={form.description} onChange={(e) => setForm({...form, description: e.target.value})} placeholder="详细描述..." />)}
      {field('任务类型', (
        <select className={inputClass} value={form.task_type} onChange={(e) => setForm({...form, task_type: e.target.value as BountyTaskType})}>
          <option value="discover_factor">发现因子</option>
          <option value="optimize_strategy">优化策略</option>
          <option value="implement_paper">实现论文</option>
        </select>
      ))}
      <div className="grid grid-cols-2 gap-4">
        {field('奖励积分', <input type="number" className={inputClass} value={form.reward_credits} onChange={(e) => setForm({...form, reward_credits: Number(e.target.value)})} />)}
        {field('难度 (1-5)', <input type="number" min={1} max={5} className={inputClass} value={form.difficulty} onChange={(e) => setForm({...form, difficulty: Number(e.target.value)})} />)}
      </div>
      {field('截止日期（可选）', <input type="datetime-local" className={inputClass} value={form.deadline} onChange={(e) => setForm({...form, deadline: e.target.value})} />)}
      {field('要求 (JSON)', <textarea className={`${inputClass} font-mono text-[11px]`} rows={3} value={form.requirements} onChange={(e) => setForm({...form, requirements: e.target.value})} />)}
    </Modal>
  );
}

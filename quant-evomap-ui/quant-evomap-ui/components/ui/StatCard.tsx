interface StatCardProps {
  label: string;
  value: string | number;
  icon?: string;
  sub?: string;
}

export default function StatCard({ label, value, icon, sub }: StatCardProps) {
  return (
    <div className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-5 transition-all duration-200 hover:bg-white/[0.05] hover:border-white/10 group">
      <div className="flex items-start justify-between">
        <div>
          <p className="text-[11px] text-white/50 uppercase tracking-wider mb-2">{label}</p>
          <p className="text-2xl font-bold font-mono text-white">{value}</p>
          {sub && <p className="text-[11px] text-white/40 mt-1.5">{sub}</p>}
        </div>
        {icon && (
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-[#667eea]/20 to-[#764ba2]/20 border border-[#667eea]/20 flex items-center justify-center text-lg group-hover:shadow-glow-xs transition-all duration-200">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}

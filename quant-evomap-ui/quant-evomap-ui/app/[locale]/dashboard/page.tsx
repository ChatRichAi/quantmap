import PageHeader from '@/components/layout/PageHeader';
import Card from '@/components/ui/Card';
import StatsGrid from '@/components/dashboard/StatsGrid';
import RecentActivity from '@/components/dashboard/RecentActivity';
import SystemHealth from '@/components/dashboard/SystemHealth';
import QuickActions from '@/components/dashboard/QuickActions';

export default function DashboardPage() {
  return (
    <div className="p-8">
      <PageHeader title="控制台总览" subtitle="QGEP 策略基因进化生态系统" />
      <StatsGrid />
      <div className="grid grid-cols-3 gap-6 mt-6">
        <div className="col-span-2">
          <Card title="最近活动">
            <RecentActivity />
          </Card>
        </div>
        <div className="space-y-6">
          <Card title="系统健康">
            <SystemHealth />
          </Card>
          <Card title="快捷操作">
            <QuickActions />
          </Card>
        </div>
      </div>
    </div>
  );
}

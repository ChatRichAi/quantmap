interface EmptyStateProps {
  icon?: string;
  title: string;
  description?: string;
}

export default function EmptyState({ icon = '📭', title, description }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center py-16 text-center">
      <div className="text-4xl mb-4">{icon}</div>
      <p className="text-text-primary font-medium mb-1">{title}</p>
      {description && <p className="text-text-secondary text-sm">{description}</p>}
    </div>
  );
}

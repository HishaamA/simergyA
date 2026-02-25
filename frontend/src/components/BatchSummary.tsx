import { CheckmarkFilled, WarningFilled, Close } from '@carbon/icons-react';
import type { BatchPredictionResponse } from '../types';

interface BatchSummaryProps {
  response: BatchPredictionResponse;
}

export function BatchSummary({ response }: BatchSummaryProps) {
  const stableCount = response.results.filter(r => r.is_stable).length;
  const unstableCount = response.results.filter(r => !r.is_stable).length;
  
  return (
    <div className="batch-summary">
      <div className="batch-summary__stat">
        <div className="batch-summary__stat-value">{response.total_files}</div>
        <div className="batch-summary__stat-label">Total Files</div>
      </div>
      
      <div className="batch-summary__stat">
        <div className="batch-summary__stat-value" style={{ color: 'var(--simer-success)' }}>
          {response.successful}
        </div>
        <div className="batch-summary__stat-label">Processed</div>
      </div>
      
      <div className="batch-summary__stat">
        <div className="batch-summary__stat-value" style={{ color: 'var(--simer-error)' }}>
          {response.failed}
        </div>
        <div className="batch-summary__stat-label">Failed</div>
      </div>
      
      <div style={{ borderLeft: '1px solid var(--simer-border)', paddingLeft: '2rem', marginLeft: '1rem' }}>
        <div className="batch-summary__stat">
          <div className="batch-summary__stat-value" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <CheckmarkFilled size={24} style={{ color: 'var(--simer-success)' }} />
            {stableCount}
          </div>
          <div className="batch-summary__stat-label">Stable</div>
        </div>
      </div>
      
      <div className="batch-summary__stat">
        <div className="batch-summary__stat-value" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <WarningFilled size={24} style={{ color: 'var(--simer-warning)' }} />
          {unstableCount}
        </div>
        <div className="batch-summary__stat-label">Unstable</div>
      </div>
    </div>
  );
}

interface ErrorListProps {
  errors: Array<{ filename: string; error: string }>;
}

export function ErrorList({ errors }: ErrorListProps) {
  if (errors.length === 0) return null;
  
  return (
    <div className="simer-card" style={{ borderColor: 'var(--simer-error)' }}>
      <h4 style={{ color: 'var(--simer-error)', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <Close size={20} />
        Failed Files ({errors.length})
      </h4>
      <ul className="file-list">
        {errors.map((error, index) => (
          <li key={index} className="file-list__item" style={{ background: 'rgba(218, 30, 40, 0.05)' }}>
            <span className="file-list__name">{error.filename}</span>
            <span style={{ color: 'var(--simer-error)', fontSize: '0.875rem' }}>{error.error}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}

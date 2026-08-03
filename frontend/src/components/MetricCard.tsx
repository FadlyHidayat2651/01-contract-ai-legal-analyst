import React from 'react';
import { Tile } from '@carbon/react';
import { ArrowUp, ArrowDown } from '@carbon/icons-react';
import './MetricCard.scss';

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: number;
  subtitle?: string;
  icon?: React.ReactNode;
}

const MetricCard: React.FC<MetricCardProps> = ({
  title,
  value,
  change,
  subtitle,
  icon,
}) => {
  const isPositive = change !== undefined && change >= 0;
  const hasChange = change !== undefined && change !== 0;

  return (
    <Tile className="metric-card">
      <div className="metric-card-header">
        <div className="metric-card-title">{title}</div>
        {icon && <div className="metric-card-icon">{icon}</div>}
      </div>
      
      <div className="metric-card-value">{value}</div>
      
      {hasChange && (
        <div className={`metric-card-change ${isPositive ? 'positive' : 'negative'}`}>
          {isPositive ? <ArrowUp size={16} /> : <ArrowDown size={16} />}
          <span>{Math.abs(change)}%</span>
        </div>
      )}
      
      {subtitle && <div className="metric-card-subtitle">{subtitle}</div>}
    </Tile>
  );
};

export default MetricCard;

// Made with Bob

import { Tile } from '@carbon/react';
import { ArrowUp, ArrowDown } from '@carbon/icons-react';
import type { RiskDistribution } from '../types';
import './RiskGauge.scss';

interface Metric {
  label: string;
  value: number;
}

interface RiskGaugeProps {
  title: string;
  subtitle: string;
  score: number;
  total: number;
  change: number;
  metrics: Metric[];
  riskDistribution?: RiskDistribution[];
}

const RiskGauge = ({
  title,
  subtitle,
  score,
  total,
  change,
  metrics,
  riskDistribution,
}: RiskGaugeProps) => {
  const circumference = 2 * Math.PI * 45;
  const offset = circumference - (score / 100) * circumference;

  const getRiskColor = (level: string) => {
    switch (level) {
      case 'critical':
        return '#da1e28';
      case 'high':
        return '#ff832b';
      case 'medium':
        return '#f1c21b';
      case 'low':
        return '#24a148';
      default:
        return '#0f62fe';
    }
  };

  return (
    <Tile className="risk-gauge">
      <div className="risk-gauge-header">
        <div>
          <h3 className="risk-gauge-title">{title}</h3>
          <p className="risk-gauge-subtitle">{subtitle}</p>
        </div>
        <div className="risk-gauge-time">5m ago</div>
      </div>

      <div className="risk-gauge-content">
        <div className="risk-gauge-chart">
          <svg viewBox="0 0 100 100" className="circular-chart">
            {/* Background circles */}
            {riskDistribution && riskDistribution.length > 0 ? (
              riskDistribution.map((risk, index) => {
                const radius = 45 - index * 3;
                const circ = 2 * Math.PI * radius;
                const strokeOffset = circ - (risk.percentage / 100) * circ;
                return (
                  <circle
                    key={risk.risk_level}
                    className="circle-bg"
                    cx="50"
                    cy="50"
                    r={radius}
                    fill="none"
                    stroke={getRiskColor(risk.risk_level)}
                    strokeWidth="3"
                    strokeDasharray={circ}
                    strokeDashoffset={strokeOffset}
                    transform="rotate(-90 50 50)"
                  />
                );
              })
            ) : (
              <>
                <circle
                  className="circle-bg"
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="#393939"
                  strokeWidth="3"
                />
                <circle
                  className="circle-progress"
                  cx="50"
                  cy="50"
                  r="45"
                  fill="none"
                  stroke="#0f62fe"
                  strokeWidth="3"
                  strokeDasharray={circumference}
                  strokeDashoffset={offset}
                  transform="rotate(-90 50 50)"
                />
              </>
            )}
            <text
              x="50"
              y="45"
              className="circle-text-score"
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {score}%
            </text>
            <text
              x="50"
              y="58"
              className="circle-text-change"
              textAnchor="middle"
              dominantBaseline="middle"
            >
              {change > 0 ? '+' : ''}
              {change}
            </text>
          </svg>
          <div className="risk-gauge-label">Overall score</div>
        </div>

        <div className="risk-gauge-metrics">
          {metrics.map((metric, index) => (
            <div key={index} className="metric-item">
              <div className="metric-bar">
                <div
                  className="metric-bar-fill"
                  style={{
                    width: `${(metric.value / total) * 100}%`,
                    backgroundColor: riskDistribution
                      ? getRiskColor(riskDistribution[index]?.risk_level || 'low')
                      : '#0f62fe',
                  }}
                />
              </div>
              <div className="metric-label">{metric.label}</div>
            </div>
          ))}
        </div>
      </div>
    </Tile>
  );
};

export default RiskGauge;

// Made with Bob

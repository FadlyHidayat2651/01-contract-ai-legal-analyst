import { useEffect, useState } from 'react';
import {
  Grid,
  Column,
  Tile,
  Loading,
  InlineNotification,
} from '@carbon/react';
import { statsApi, contractApi, clauseApi } from '../services/api';
import type { ContractStats, RiskDistribution, Contract, Clause } from '../types';
import MetricCard from '../components/MetricCard';
import RiskGauge from '../components/RiskGauge';
import QuickStarters from '../components/QuickStarters';
import './Dashboard.scss';

const Dashboard = () => {
  const [stats, setStats] = useState<ContractStats | null>(null);
  const [riskDistribution, setRiskDistribution] = useState<RiskDistribution[]>([]);
  const [recentContracts, setRecentContracts] = useState<Contract[]>([]);
  const [highRiskClauses, setHighRiskClauses] = useState<Clause[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);

      const [statsData, riskData, contracts, clauses] = await Promise.all([
        statsApi.getContractStats(),
        statsApi.getRiskDistribution(),
        contractApi.getContracts({ limit: 5 }),
        clauseApi.getAllClauses({ risk_level: 'high', limit: 5 }),
      ]);

      setStats(statsData);
      setRiskDistribution(riskData);
      setRecentContracts(contracts);
      setHighRiskClauses(clauses);
    } catch (err) {
      setError('Failed to load dashboard data. Please try again.');
      console.error('Dashboard error:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="dashboard-loading">
        <Loading description="Loading dashboard..." withOverlay={false} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={error}
          onCloseButtonClick={() => setError(null)}
        />
      </div>
    );
  }

  const processedPercentage = stats
    ? Math.round((stats.processed_contracts / stats.total_contracts) * 100) || 0
    : 0;

  const riskScore = riskDistribution.length > 0
    ? Math.round(
        100 -
          (riskDistribution.find((r) => r.risk_level === 'critical')?.percentage || 0) -
          (riskDistribution.find((r) => r.risk_level === 'high')?.percentage || 0)
      )
    : 0;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1 className="dashboard-title">Contract Analysis Dashboard</h1>
        <p className="dashboard-subtitle">
          Monitor contract processing, risk assessment, and clause analysis
        </p>
      </div>

      <Grid className="dashboard-grid" narrow>
        {/* Main Metrics Row */}
        <Column lg={5} md={4} sm={4}>
          <RiskGauge
            title="Processing Status"
            subtitle="Contracts processed"
            score={processedPercentage}
            total={stats?.total_contracts || 0}
            change={stats?.processed_contracts || 0}
            metrics={[
              { label: 'Completed', value: stats?.processed_contracts || 0 },
              { label: 'Pending', value: stats?.pending_contracts || 0 },
            ]}
          />
        </Column>

        <Column lg={5} md={4} sm={4}>
          <RiskGauge
            title="Clause Analysis"
            subtitle="Total clauses extracted"
            score={85}
            total={stats?.total_clauses || 0}
            change={stats?.total_clauses || 0}
            metrics={[
              { label: 'Analyzed', value: stats?.total_clauses || 0 },
              { label: 'High Risk', value: stats?.high_risk_clauses || 0 },
            ]}
          />
        </Column>

        <Column lg={6} md={8} sm={4}>
          <RiskGauge
            title="Risk Assessment"
            subtitle="Overall risk score"
            score={riskScore}
            total={stats?.total_clauses || 0}
            change={stats?.critical_risk_clauses || 0}
            metrics={[
              {
                label: 'Critical',
                value: riskDistribution.find((r) => r.risk_level === 'critical')?.count || 0,
              },
              {
                label: 'High',
                value: riskDistribution.find((r) => r.risk_level === 'high')?.count || 0,
              },
              {
                label: 'Medium',
                value: riskDistribution.find((r) => r.risk_level === 'medium')?.count || 0,
              },
            ]}
            riskDistribution={riskDistribution}
          />
        </Column>

        {/* Secondary Metrics Row */}
        <Column lg={4} md={4} sm={4}>
          <MetricCard
            title="Total Contracts"
            value={stats?.total_contracts || 0}
            subtitle="Documents uploaded"
            trend="up"
            trendValue={stats?.processed_contracts || 0}
          />
        </Column>

        <Column lg={4} md={4} sm={4}>
          <MetricCard
            title="High Risk Clauses"
            value={stats?.high_risk_clauses || 0}
            subtitle="Requiring review"
            trend="down"
            trendValue={stats?.critical_risk_clauses || 0}
          />
        </Column>

        <Column lg={4} md={4} sm={4}>
          <MetricCard
            title="Critical Issues"
            value={stats?.critical_risk_clauses || 0}
            subtitle="Immediate attention needed"
            trend={stats?.critical_risk_clauses ? 'up' : 'neutral'}
            trendValue={stats?.critical_risk_clauses || 0}
          />
        </Column>

        <Column lg={4} md={4} sm={4}>
          <MetricCard
            title="Processing Rate"
            value={`${processedPercentage}%`}
            subtitle="Completion rate"
            trend="up"
            trendValue={processedPercentage}
          />
        </Column>

        {/* Quick Starters */}
        <Column lg={16} md={8} sm={4}>
          <QuickStarters
            recentContracts={recentContracts}
            highRiskClauses={highRiskClauses}
          />
        </Column>
      </Grid>
    </div>
  );
};

export default Dashboard;

// Made with Bob

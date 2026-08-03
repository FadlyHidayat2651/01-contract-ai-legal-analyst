import React from 'react';
import { Tile, Tag } from '@carbon/react';
import { useNavigate } from 'react-router-dom';
import { Contract, Clause } from '../types';
import './QuickStarters.scss';

interface QuickStartersProps {
  title: string;
  contracts?: Contract[];
  clauses?: Clause[];
  type: 'contracts' | 'clauses';
}

const QuickStarters: React.FC<QuickStartersProps> = ({
  title,
  contracts,
  clauses,
  type,
}) => {
  const navigate = useNavigate();

  const getRiskColor = (riskLevel?: string) => {
    switch (riskLevel?.toLowerCase()) {
      case 'critical':
        return 'red';
      case 'high':
        return 'magenta';
      case 'medium':
        return 'warm-gray';
      case 'low':
        return 'green';
      default:
        return 'gray';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed':
        return 'green';
      case 'processing':
        return 'blue';
      case 'failed':
        return 'red';
      default:
        return 'gray';
    }
  };

  const handleContractClick = (contractId: number) => {
    navigate(`/contracts/${contractId}`);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    });
  };

  return (
    <Tile className="quick-starters">
      <div className="quick-starters-header">
        <h3 className="quick-starters-title">{title}</h3>
      </div>

      <div className="quick-starters-list">
        {type === 'contracts' && contracts && contracts.length > 0 ? (
          contracts.map((contract) => (
            <div
              key={contract.id}
              className="quick-starter-item"
              onClick={() => handleContractClick(contract.id)}
            >
              <div className="item-content">
                <div className="item-title">{contract.title}</div>
                <div className="item-meta">
                  <span className="item-date">
                    {formatDate(contract.created_at)}
                  </span>
                  <Tag type={getStatusColor(contract.processing_status)} size="sm">
                    {contract.processing_status}
                  </Tag>
                  {contract.risk_level && (
                    <Tag type={getRiskColor(contract.risk_level)} size="sm">
                      {contract.risk_level}
                    </Tag>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : type === 'clauses' && clauses && clauses.length > 0 ? (
          clauses.map((clause) => (
            <div
              key={clause.id}
              className="quick-starter-item"
              onClick={() => handleContractClick(clause.contract_id)}
            >
              <div className="item-content">
                <div className="item-title">{clause.title}</div>
                <div className="item-meta">
                  <Tag type={getRiskColor(clause.risk_level)} size="sm">
                    {clause.risk_level}
                  </Tag>
                  {clause.clause_type && (
                    <span className="item-type">{clause.clause_type}</span>
                  )}
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="quick-starters-empty">
            <p>No {type} available</p>
          </div>
        )}
      </div>
    </Tile>
  );
};

export default QuickStarters;

// Made with Bob

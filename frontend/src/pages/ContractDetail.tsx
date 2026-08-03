import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Breadcrumb,
  BreadcrumbItem,
  Button,
  Tabs,
  TabList,
  Tab,
  TabPanels,
  TabPanel,
  Tag,
  Loading,
  InlineNotification,
  Tile,
  Grid,
  Column,
} from '@carbon/react';
import { ArrowLeft, Download, TrashCan } from '@carbon/icons-react';
import { contractApi, clauseApi, sectionApi } from '../services/api';
import { Contract, Clause, DocumentSection } from '../types';
import './ContractDetail.scss';

const ContractDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [contract, setContract] = useState<Contract | null>(null);
  const [clauses, setClauses] = useState<Clause[]>([]);
  const [sections, setSections] = useState<DocumentSection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      fetchContractDetails(Number(id));
    }
  }, [id]);

  const fetchContractDetails = async (contractId: number) => {
    try {
      setLoading(true);
      setError(null);
      const [contractData, clausesData, sectionsData] = await Promise.all([
        contractApi.getContract(contractId),
        clauseApi.getClauses(contractId),
        sectionApi.getSections(contractId),
      ]);
      setContract(contractData);
      setClauses(clausesData);
      setSections(sectionsData);
    } catch (err) {
      setError('Failed to load contract details. Please try again.');
      console.error('Error fetching contract details:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!contract) return;
    if (window.confirm('Are you sure you want to delete this contract?')) {
      try {
        await contractApi.deleteContract(contract.id);
        navigate('/contracts');
      } catch (err) {
        setError('Failed to delete contract. Please try again.');
        console.error('Error deleting contract:', err);
      }
    }
  };

  const handleDownload = () => {
    if (contract?.file_path) {
      window.open(`/api${contract.file_path}`, '_blank');
    }
  };

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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  if (loading) {
    return (
      <div className="contract-detail-loading">
        <Loading description="Loading contract details..." withOverlay={false} />
      </div>
    );
  }

  if (!contract) {
    return (
      <div className="contract-detail-error">
        <InlineNotification
          kind="error"
          title="Contract not found"
          subtitle="The requested contract could not be found."
          lowContrast
        />
        <Button onClick={() => navigate('/contracts')}>
          Back to Contracts
        </Button>
      </div>
    );
  }

  return (
    <div className="contract-detail">
      <Breadcrumb>
        <BreadcrumbItem href="/dashboard">Dashboard</BreadcrumbItem>
        <BreadcrumbItem href="/contracts">Contracts</BreadcrumbItem>
        <BreadcrumbItem isCurrentPage>{contract.title}</BreadcrumbItem>
      </Breadcrumb>

      <div className="contract-detail-header">
        <div className="header-left">
          <Button
            kind="ghost"
            renderIcon={ArrowLeft}
            onClick={() => navigate('/contracts')}
          >
            Back
          </Button>
          <h1>{contract.title}</h1>
        </div>
        <div className="header-actions">
          <Button
            kind="tertiary"
            renderIcon={Download}
            onClick={handleDownload}
          >
            Download
          </Button>
          <Button
            kind="danger--tertiary"
            renderIcon={TrashCan}
            onClick={handleDelete}
          >
            Delete
          </Button>
        </div>
      </div>

      {error && (
        <InlineNotification
          kind="error"
          title="Error"
          subtitle={error}
          onCloseButtonClick={() => setError(null)}
          lowContrast
        />
      )}

      <Grid className="contract-detail-info">
        <Column lg={4} md={4} sm={4}>
          <Tile>
            <div className="info-item">
              <span className="info-label">Status</span>
              <Tag type={getStatusColor(contract.processing_status)} size="md">
                {contract.processing_status}
              </Tag>
            </div>
          </Tile>
        </Column>
        <Column lg={4} md={4} sm={4}>
          <Tile>
            <div className="info-item">
              <span className="info-label">Risk Level</span>
              {contract.risk_level ? (
                <Tag type={getRiskColor(contract.risk_level)} size="md">
                  {contract.risk_level}
                </Tag>
              ) : (
                <span className="text-secondary">Not assessed</span>
              )}
            </div>
          </Tile>
        </Column>
        <Column lg={4} md={4} sm={4}>
          <Tile>
            <div className="info-item">
              <span className="info-label">Created</span>
              <span className="info-value">{formatDate(contract.created_at)}</span>
            </div>
          </Tile>
        </Column>
        <Column lg={4} md={4} sm={4}>
          <Tile>
            <div className="info-item">
              <span className="info-label">Last Updated</span>
              <span className="info-value">{formatDate(contract.updated_at)}</span>
            </div>
          </Tile>
        </Column>
      </Grid>

      <Tabs>
        <TabList aria-label="Contract details tabs">
          <Tab>Clauses ({clauses.length})</Tab>
          <Tab>Document Sections ({sections.length})</Tab>
        </TabList>
        <TabPanels>
          <TabPanel>
            <div className="clauses-panel">
              {clauses.length > 0 ? (
                <div className="clauses-list">
                  {clauses.map((clause) => (
                    <Tile key={clause.id} className="clause-item">
                      <div className="clause-header">
                        <h4>{clause.title}</h4>
                        <div className="clause-tags">
                          <Tag type={getRiskColor(clause.risk_level)} size="sm">
                            {clause.risk_level}
                          </Tag>
                          {clause.clause_type && (
                            <Tag type="gray" size="sm">
                              {clause.clause_type}
                            </Tag>
                          )}
                        </div>
                      </div>
                      <p className="clause-content">{clause.content}</p>
                      {clause.analysis && (
                        <div className="clause-analysis">
                          <strong>Analysis:</strong>
                          <p>{clause.analysis}</p>
                        </div>
                      )}
                    </Tile>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <p>No clauses extracted yet.</p>
                </div>
              )}
            </div>
          </TabPanel>
          <TabPanel>
            <div className="sections-panel">
              {sections.length > 0 ? (
                <div className="sections-list">
                  {sections.map((section) => (
                    <Tile key={section.id} className="section-item">
                      <div className="section-header">
                        <h4>{section.title}</h4>
                        <Tag type="gray" size="sm">
                          {section.section_type}
                        </Tag>
                      </div>
                      <p className="section-content">{section.content}</p>
                      <div className="section-meta">
                        <span>Page: {section.page_number}</span>
                        {section.confidence_score && (
                          <span>
                            Confidence: {(section.confidence_score * 100).toFixed(1)}%
                          </span>
                        )}
                      </div>
                    </Tile>
                  ))}
                </div>
              ) : (
                <div className="empty-state">
                  <p>No document sections available.</p>
                </div>
              )}
            </div>
          </TabPanel>
        </TabPanels>
      </Tabs>
    </div>
  );
};

export default ContractDetail;

// Made with Bob

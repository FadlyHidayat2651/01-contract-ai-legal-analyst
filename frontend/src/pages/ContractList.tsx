import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  DataTable,
  Table,
  TableHead,
  TableRow,
  TableHeader,
  TableBody,
  TableCell,
  TableContainer,
  TableToolbar,
  TableToolbarContent,
  TableToolbarSearch,
  Button,
  Tag,
  Pagination,
  Loading,
  InlineNotification,
} from '@carbon/react';
import { Add, TrashCan, View } from '@carbon/icons-react';
import { contractApi } from '../services/api';
import { Contract } from '../types';
import './ContractList.scss';

const ContractList: React.FC = () => {
  const navigate = useNavigate();
  const [contracts, setContracts] = useState<Contract[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  useEffect(() => {
    fetchContracts();
  }, []);

  const fetchContracts = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await contractApi.getContracts();
      setContracts(data);
    } catch (err) {
      setError('Failed to load contracts. Please try again.');
      console.error('Error fetching contracts:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (window.confirm('Are you sure you want to delete this contract?')) {
      try {
        await contractApi.deleteContract(id);
        setContracts(contracts.filter((c) => c.id !== id));
      } catch (err) {
        setError('Failed to delete contract. Please try again.');
        console.error('Error deleting contract:', err);
      }
    }
  };

  const handleView = (id: number) => {
    navigate(`/contracts/${id}`);
  };

  const handleUpload = () => {
    navigate('/upload');
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
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  const filteredContracts = contracts.filter((contract) =>
    (contract.title || contract.filename).toLowerCase().includes(searchQuery.toLowerCase())
  );

  const paginatedContracts = filteredContracts.slice(
    (page - 1) * pageSize,
    page * pageSize
  );

  const headers = [
    { key: 'title', header: 'Contract Title' },
    { key: 'status', header: 'Status' },
    { key: 'risk_level', header: 'Risk Level' },
    { key: 'created_at', header: 'Created' },
    { key: 'actions', header: 'Actions' },
  ];

  const rows = paginatedContracts.map((contract) => ({
    id: contract.id.toString(),
    title: contract.title || contract.filename,
    status: contract.processing_status,
    risk_level: contract.risk_level || 'N/A',
    created_at: formatDate(contract.created_at),
    actions: contract.id,
  }));

  if (loading) {
    return (
      <div className="contract-list-loading">
        <Loading description="Loading contracts..." withOverlay={false} />
      </div>
    );
  }

  return (
    <div className="contract-list">
      <div className="contract-list-header">
        <h1>Contracts</h1>
        <Button
          renderIcon={Add}
          onClick={handleUpload}
          kind="primary"
        >
          Upload Contract
        </Button>
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

      <DataTable rows={rows} headers={headers}>
        {({
          rows,
          headers,
          getTableProps,
          getHeaderProps,
          getRowProps,
          getTableContainerProps,
        }) => (
          <TableContainer
            title=""
            description=""
            {...getTableContainerProps()}
          >
            <TableToolbar>
              <TableToolbarContent>
                <TableToolbarSearch
                  placeholder="Search contracts..."
                  onChange={(e: any) => setSearchQuery(e.target?.value || e)}
                />
              </TableToolbarContent>
            </TableToolbar>
            <Table {...getTableProps()}>
              <TableHead>
                <TableRow>
                  {headers.map((header) => (
                    <TableHeader {...getHeaderProps({ header })}>
                      {header.header}
                    </TableHeader>
                  ))}
                </TableRow>
              </TableHead>
              <TableBody>
                {rows.map((row) => {
                  const contract = paginatedContracts.find(
                    (c) => c.id.toString() === row.id
                  );
                  return (
                    <TableRow {...getRowProps({ row })}>
                      {row.cells.map((cell) => {
                        if (cell.info.header === 'status') {
                          return (
                            <TableCell key={cell.id}>
                              <Tag
                                type={getStatusColor(cell.value)}
                                size="sm"
                              >
                                {cell.value}
                              </Tag>
                            </TableCell>
                          );
                        }
                        if (cell.info.header === 'risk_level') {
                          return (
                            <TableCell key={cell.id}>
                              {cell.value !== 'N/A' ? (
                                <Tag
                                  type={getRiskColor(cell.value)}
                                  size="sm"
                                >
                                  {cell.value}
                                </Tag>
                              ) : (
                                <span className="text-secondary">N/A</span>
                              )}
                            </TableCell>
                          );
                        }
                        if (cell.info.header === 'actions') {
                          return (
                            <TableCell key={cell.id}>
                              <div className="action-buttons">
                                <Button
                                  kind="ghost"
                                  size="sm"
                                  renderIcon={View}
                                  iconDescription="View"
                                  hasIconOnly
                                  onClick={() => handleView(Number(cell.value))}
                                />
                                <Button
                                  kind="ghost"
                                  size="sm"
                                  renderIcon={TrashCan}
                                  iconDescription="Delete"
                                  hasIconOnly
                                  onClick={() => handleDelete(Number(cell.value))}
                                />
                              </div>
                            </TableCell>
                          );
                        }
                        return <TableCell key={cell.id}>{cell.value}</TableCell>;
                      })}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        )}
      </DataTable>

      {filteredContracts.length > pageSize && (
        <Pagination
          totalItems={filteredContracts.length}
          pageSize={pageSize}
          pageSizes={[10, 20, 30, 40, 50]}
          page={page}
          onChange={({ page, pageSize }) => {
            setPage(page);
            setPageSize(pageSize);
          }}
        />
      )}
    </div>
  );
};

export default ContractList;

// Made with Bob

import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { Theme } from '@carbon/react';
import Dashboard from './pages/Dashboard';
import ContractList from './pages/ContractList';
import ContractDetail from './pages/ContractDetail';
import ContractUpload from './pages/ContractUpload';
import Layout from './components/Layout';
import './App.scss';

function App() {
  return (
    <Theme theme="g100">
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/contracts" element={<ContractList />} />
            <Route path="/contracts/:id" element={<ContractDetail />} />
            <Route path="/upload" element={<ContractUpload />} />
          </Routes>
        </Layout>
      </Router>
    </Theme>
  );
}

export default App;

// Made with Bob

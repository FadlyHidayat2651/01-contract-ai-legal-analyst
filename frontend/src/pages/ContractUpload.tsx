import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  FileUploader,
  Button,
  InlineNotification,
  ProgressBar,
  Tile,
} from '@carbon/react';
import { Upload, CheckmarkFilled } from '@carbon/icons-react';
import { contractApi } from '../services/api';
import { Contract } from '../types';
import './ContractUpload.scss';

const ContractUpload: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [uploadedContract, setUploadedContract] = useState<Contract | null>(null);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files && files.length > 0) {
      const selectedFile = files[0];
      
      // Validate file type
      const allowedTypes = [
        'application/pdf',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
      ];
      
      if (!allowedTypes.includes(selectedFile.type)) {
        setError('Please upload a PDF or Word document (.pdf, .doc, .docx)');
        setFile(null);
        return;
      }

      // Validate file size (max 50MB)
      const maxSize = 50 * 1024 * 1024; // 50MB in bytes
      if (selectedFile.size > maxSize) {
        setError('File size must be less than 50MB');
        setFile(null);
        return;
      }

      setFile(selectedFile);
      setError(null);
      setUploadedContract(null);
    }
  };

  const handleUpload = async () => {
    if (!file) {
      setError('Please select a file to upload');
      return;
    }

    try {
      setUploading(true);
      setError(null);
      setUploadProgress(0);

      // Simulate progress (since we don't have real progress tracking)
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          if (prev >= 90) {
            clearInterval(progressInterval);
            return 90;
          }
          return prev + 10;
        });
      }, 200);

      const contract = await contractApi.uploadContract(file);
      
      clearInterval(progressInterval);
      setUploadProgress(100);
      setUploadedContract(contract);
      
      // Auto-redirect after 2 seconds
      setTimeout(() => {
        navigate(`/contracts/${contract.id}`);
      }, 2000);
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        'Failed to upload contract. Please try again.'
      );
      console.error('Error uploading contract:', err);
      setUploadProgress(0);
    } finally {
      setUploading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setUploadedContract(null);
    setError(null);
    setUploadProgress(0);
  };

  return (
    <div className="contract-upload">
      <div className="upload-header">
        <h1>Upload Contract</h1>
        <p>Upload a contract document for analysis and clause extraction</p>
      </div>

      {error && (
        <InlineNotification
          kind="error"
          title="Upload Error"
          subtitle={error}
          onCloseButtonClick={() => setError(null)}
          lowContrast
        />
      )}

      {uploadedContract ? (
        <Tile className="upload-success">
          <div className="success-content">
            <CheckmarkFilled size={48} className="success-icon" />
            <h2>Upload Successful!</h2>
            <p>
              Your contract "{uploadedContract.title}" has been uploaded and is
              being processed.
            </p>
            <div className="success-actions">
              <Button
                kind="primary"
                onClick={() => navigate(`/contracts/${uploadedContract.id}`)}
              >
                View Contract
              </Button>
              <Button kind="secondary" onClick={handleReset}>
                Upload Another
              </Button>
            </div>
          </div>
        </Tile>
      ) : (
        <Tile className="upload-container">
          <div className="upload-area">
            <FileUploader
              labelTitle="Upload file"
              labelDescription="Max file size is 50MB. Supported formats: PDF, DOC, DOCX"
              buttonLabel="Select file"
              buttonKind="primary"
              size="lg"
              filenameStatus="edit"
              accept={['.pdf', '.doc', '.docx']}
              multiple={false}
              disabled={uploading}
              onChange={handleFileChange}
              iconDescription="Upload file"
            />

            {file && (
              <div className="file-info">
                <div className="file-details">
                  <strong>Selected file:</strong>
                  <span>{file.name}</span>
                  <span className="file-size">
                    ({(file.size / 1024 / 1024).toFixed(2)} MB)
                  </span>
                </div>
              </div>
            )}

            {uploading && (
              <div className="upload-progress">
                <ProgressBar
                  label="Uploading contract..."
                  value={uploadProgress}
                  max={100}
                />
                <p className="progress-text">
                  {uploadProgress < 100
                    ? 'Uploading and processing document...'
                    : 'Processing complete!'}
                </p>
              </div>
            )}

            <div className="upload-actions">
              <Button
                kind="primary"
                renderIcon={Upload}
                onClick={handleUpload}
                disabled={!file || uploading}
              >
                {uploading ? 'Uploading...' : 'Upload Contract'}
              </Button>
              {file && !uploading && (
                <Button kind="secondary" onClick={handleReset}>
                  Clear
                </Button>
              )}
            </div>
          </div>

          <div className="upload-info">
            <h3>Upload Guidelines</h3>
            <ul>
              <li>Supported formats: PDF, DOC, DOCX</li>
              <li>Maximum file size: 50MB</li>
              <li>Documents will be automatically processed using IBM Docling</li>
              <li>Clauses and sections will be extracted and analyzed</li>
              <li>Processing may take a few minutes depending on document size</li>
            </ul>
          </div>
        </Tile>
      )}
    </div>
  );
};

export default ContractUpload;

// Made with Bob

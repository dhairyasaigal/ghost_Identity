import React, { useState } from 'react';
import { Row, Col, Card, Form, Button, Alert, ProgressBar, Tab, Tabs, Table, Badge, Modal } from 'react-bootstrap';

function TrustedContactPortal() {
  const [uploadStatus, setUploadStatus] = useState('idle'); // idle, uploading, processing, success, error
  const [verificationResult, setVerificationResult] = useState(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  
  // Mock policy execution data
  const [policyExecutions] = useState([
    {
      id: 1,
      platform: 'Gmail',
      accountId: 'john.doe@gmail.com',
      actionType: 'delete',
      status: 'completed',
      executedAt: '2024-01-07 11:00:00',
      response: 'Account deletion request submitted successfully',
      confidence: 0.95
    },
    {
      id: 2,
      platform: 'Facebook',
      accountId: 'facebook.com/johndoe',
      actionType: 'memorialize',
      status: 'in_progress',
      executedAt: '2024-01-07 11:05:00',
      response: 'Memorialization request sent, awaiting platform response',
      confidence: 0.88
    },
    {
      id: 3,
      platform: 'Chase Bank',
      accountId: '****1234',
      actionType: 'lock',
      status: 'pending',
      executedAt: null,
      response: 'Waiting for manual review due to high-value account',
      confidence: null
    }
  ]);

  const [verificationHistory] = useState([
    {
      id: 1,
      fileName: 'death_certificate_john_doe.pdf',
      uploadedAt: '2024-01-07 10:30:00',
      status: 'verified',
      extractedName: 'John Doe',
      dateOfDeath: '2024-01-15',
      confidence: 0.95
    }
  ]);

  const handleFileSelect = (e) => {
    const file = e.target.files[0];
    setSelectedFile(file);
    setUploadStatus('idle');
    setVerificationResult(null);
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files[0];
    if (file && isValidFileType(file)) {
      setSelectedFile(file);
      setUploadStatus('idle');
      setVerificationResult(null);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = (e) => {
    e.preventDefault();
    setDragOver(false);
  };

  const isValidFileType = (file) => {
    const validTypes = ['application/pdf', 'image/jpeg', 'image/jpg', 'image/png', 'image/tiff'];
    return validTypes.includes(file.type);
  };

  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploadStatus('uploading');
    
    // Simulate file upload and processing
    setTimeout(() => {
      setUploadStatus('processing');
      
      // Simulate Azure AI Vision processing
      setTimeout(() => {
        setUploadStatus('success');
        setVerificationResult({
          extractedName: 'John Doe',
          dateOfDeath: '2024-01-15',
          certificateId: 'DC-2024-001234',
          confidence: 0.95,
          status: 'verified'
        });
        setShowUploadModal(false);
      }, 3000);
    }, 1000);
  };

  const getStatusMessage = () => {
    switch (uploadStatus) {
      case 'uploading':
        return 'Uploading death certificate to secure servers...';
      case 'processing':
        return 'Azure AI Vision is analyzing the document and extracting key information...';
      case 'success':
        return 'Death certificate verified successfully!';
      case 'error':
        return 'Error processing death certificate. Please try again.';
      default:
        return '';
    }
  };

  const getStatusBadgeColor = (status) => {
    const colors = {
      completed: 'success',
      in_progress: 'primary',
      pending: 'warning',
      failed: 'danger'
    };
    return colors[status] || 'secondary';
  };

  const getActionBadgeColor = (action) => {
    const colors = {
      delete: 'danger',
      memorialize: 'warning',
      transfer: 'success',
      lock: 'secondary'
    };
    return colors[action] || 'secondary';
  };

  return (
    <div className="fade-in">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="mb-2">Trusted Contact Portal</h2>
          <p className="text-muted mb-0">
            Verify death events and monitor AI-powered policy execution with complete transparency
          </p>
        </div>
        <Button variant="primary" onClick={() => setShowUploadModal(true)}>
          Upload Certificate
        </Button>
      </div>

      {/* Security Notice */}
      <Alert variant="info" className="mb-4">
        <div className="d-flex align-items-center">
          <div className="feature-icon me-3" style={{ width: '32px', height: '32px', fontSize: '1rem' }}>🔐</div>
          <div>
            <strong>Secure Verification:</strong> All death certificates are processed using Azure AI Vision with 
            bank-level security. Only authorized trusted contacts can access this portal.
          </div>
        </div>
      </Alert>
      
      <Tabs defaultActiveKey="verification" className="mb-4">
        <Tab eventKey="verification" title="Death Verification">
          <Row>
            <Col lg={8}>
              {/* Verification Results */}
              {verificationResult && (
                <Card className="dashboard-card mb-4">
                  <Card.Header className="bg-success text-white">
                    <h5 className="mb-0">
                      Verification Complete
                    </h5>
                  </Card.Header>
                  <Card.Body>
                    <Row>
                      <Col md={6}>
                        <div className="mb-3">
                          <strong>Extracted Name:</strong><br />
                          <span className="h5">{verificationResult.extractedName}</span>
                        </div>
                        <div className="mb-3">
                          <strong>Date of Death:</strong><br />
                          <span className="h6">{verificationResult.dateOfDeath}</span>
                        </div>
                      </Col>
                      <Col md={6}>
                        <div className="mb-3">
                          <strong>Certificate ID:</strong><br />
                          <code>{verificationResult.certificateId}</code>
                        </div>
                        <div className="mb-3">
                          <strong>AI Confidence:</strong><br />
                          <div className="d-flex align-items-center">
                            <ProgressBar 
                              now={verificationResult.confidence * 100} 
                              className="flex-grow-1 me-2"
                              variant="success"
                            />
                            <span className="fw-bold">{(verificationResult.confidence * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      </Col>
                    </Row>
                    
                    <Alert variant="success" className="mb-0">
                      <strong>Automatic Processing Initiated:</strong><br />
                      Digital assets have been secured and AI policy execution has begun. 
                      Monitor progress in the Policy Execution tab.
                    </Alert>
                  </Card.Body>
                </Card>
              )}

              {/* Processing Status */}
              {uploadStatus !== 'idle' && uploadStatus !== 'success' && (
                <Card className="dashboard-card mb-4">
                  <Card.Body>
                    <div className="text-center">
                      <div className="feature-icon mx-auto mb-3">
                        {uploadStatus === 'uploading' ? 'Upload' : 'AI'}
                      </div>
                      <h5>{getStatusMessage()}</h5>
                      <ProgressBar 
                        animated 
                        now={uploadStatus === 'uploading' ? 30 : 70} 
                        className="mb-3"
                      />
                      <p className="text-muted">
                        {uploadStatus === 'uploading' 
                          ? 'Securely transferring document to Azure servers...'
                          : 'AI is extracting name, date of death, and certificate details...'
                        }
                      </p>
                    </div>
                  </Card.Body>
                </Card>
              )}

              {/* Verification History */}
              <Card className="dashboard-card">
                <Card.Header>
                  <h5 className="mb-0">
                    Verification History
                  </h5>
                </Card.Header>
                <Card.Body>
                  {verificationHistory.length === 0 ? (
                    <div className="text-center py-4">
                      <div className="feature-icon mx-auto mb-3">Doc</div>
                      <h6>No Previous Verifications</h6>
                      <p className="text-muted">Upload your first death certificate to begin the verification process.</p>
                    </div>
                  ) : (
                    <Table responsive hover>
                      <thead>
                        <tr>
                          <th>Document</th>
                          <th>Extracted Data</th>
                          <th>Status</th>
                          <th>Confidence</th>
                          <th>Date</th>
                        </tr>
                      </thead>
                      <tbody>
                        {verificationHistory.map((record) => (
                          <tr key={record.id}>
                            <td>
                              <div className="d-flex align-items-center">
                                <div className="feature-icon me-2" style={{ width: '24px', height: '24px', fontSize: '0.75rem' }}>PDF</div>
                                <div>
                                  <strong>{record.fileName}</strong><br />
                                  <small className="text-muted">PDF Document</small>
                                </div>
                              </div>
                            </td>
                            <td>
                              <div>
                                <strong>{record.extractedName}</strong><br />
                                <small className="text-muted">DOD: {record.dateOfDeath}</small>
                              </div>
                            </td>
                            <td>
                              <Badge bg={record.status === 'verified' ? 'success' : 'warning'}>
                                {record.status}
                              </Badge>
                            </td>
                            <td>
                              <div className="d-flex align-items-center">
                                <ProgressBar 
                                  now={record.confidence * 100} 
                                  className="flex-grow-1 me-2" 
                                  style={{ width: '60px', height: '8px' }}
                                  variant="success"
                                />
                                <small>{(record.confidence * 100).toFixed(1)}%</small>
                              </div>
                            </td>
                            <td>
                              <small>{record.uploadedAt}</small>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  )}
                </Card.Body>
              </Card>
            </Col>
            
            <Col lg={4}>
              {/* Quick Upload Card */}
              <Card className="dashboard-card mb-4">
                <Card.Header>
                  <h6 className="mb-0">
                    Quick Upload
                  </h6>
                </Card.Header>
                <Card.Body>
                  <div 
                    className={`upload-area ${dragOver ? 'dragover' : ''}`}
                    onDrop={handleDrop}
                    onDragOver={handleDragOver}
                    onDragLeave={handleDragLeave}
                    onClick={() => setShowUploadModal(true)}
                  >
                    <div className="text-center">
                      <div className="feature-icon mx-auto mb-3">Doc</div>
                      <p className="mb-2"><strong>Drop certificate here</strong></p>
                      <p className="text-muted small mb-0">or click to browse</p>
                    </div>
                  </div>
                  <div className="mt-3">
                    <small className="text-muted">
                      <strong>Supported:</strong> PDF, JPG, PNG, TIFF<br />
                      <strong>Max size:</strong> 10MB
                    </small>
                  </div>
                </Card.Body>
              </Card>

              {/* How It Works */}
              <Card className="dashboard-card">
                <Card.Header>
                  <h6 className="mb-0">
                    Verification Process
                  </h6>
                </Card.Header>
                <Card.Body>
                  <div className="d-flex flex-column gap-3">
                    <div className="d-flex align-items-start">
                      <div className="step-number me-3" style={{ width: '30px', height: '30px', fontSize: '0.8rem' }}>1</div>
                      <div>
                        <strong>Upload</strong><br />
                        <small className="text-muted">Submit death certificate document</small>
                      </div>
                    </div>
                    <div className="d-flex align-items-start">
                      <div className="step-number me-3" style={{ width: '30px', height: '30px', fontSize: '0.8rem' }}>2</div>
                      <div>
                        <strong>AI Analysis</strong><br />
                        <small className="text-muted">Azure AI Vision extracts key information</small>
                      </div>
                    </div>
                    <div className="d-flex align-items-start">
                      <div className="step-number me-3" style={{ width: '30px', height: '30px', fontSize: '0.8rem' }}>3</div>
                      <div>
                        <strong>Verification</strong><br />
                        <small className="text-muted">System validates against user records</small>
                      </div>
                    </div>
                    <div className="d-flex align-items-start">
                      <div className="step-number me-3" style={{ width: '30px', height: '30px', fontSize: '0.8rem' }}>4</div>
                      <div>
                        <strong>Execution</strong><br />
                        <small className="text-muted">AI interprets and executes policies</small>
                      </div>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="monitoring" title="Policy Execution">
          <Row>
            <Col>
              <Card className="dashboard-card">
                <Card.Header>
                  <h5 className="mb-0">
                    AI Policy Execution Status
                  </h5>
                </Card.Header>
                <Card.Body>
                  <Alert variant="info" className="mb-4">
                    <div className="d-flex align-items-center">
                      <div className="feature-icon me-3" style={{ width: '32px', height: '32px', fontSize: '1rem' }}>AI</div>
                      <div>
                        <strong>Automated Processing:</strong> Azure OpenAI is interpreting user policies and generating 
                        platform-specific notifications. All actions are logged and auditable.
                      </div>
                    </div>
                  </Alert>
                  
                  <Table responsive hover>
                    <thead>
                      <tr>
                        <th>Platform</th>
                        <th>Account</th>
                        <th>Action</th>
                        <th>Status</th>
                        <th>AI Confidence</th>
                        <th>Executed</th>
                        <th>Response</th>
                      </tr>
                    </thead>
                    <tbody>
                      {policyExecutions.map((execution) => (
                        <tr key={execution.id}>
                          <td>
                            <div className="d-flex align-items-center">
                              <div className="feature-icon me-2" style={{ width: '24px', height: '24px', fontSize: '0.75rem' }}>Web</div>
                              <strong>{execution.platform}</strong>
                            </div>
                          </td>
                          <td>
                            <code>{execution.accountId}</code>
                          </td>
                          <td>
                            <Badge bg={getActionBadgeColor(execution.actionType)}>
                              {execution.actionType}
                            </Badge>
                          </td>
                          <td>
                            <Badge bg={getStatusBadgeColor(execution.status)}>
                              {execution.status.replace('_', ' ')}
                            </Badge>
                          </td>
                          <td>
                            {execution.confidence ? (
                              <div className="d-flex align-items-center">
                                <ProgressBar 
                                  now={execution.confidence * 100} 
                                  className="flex-grow-1 me-2" 
                                  style={{ width: '50px', height: '6px' }}
                                  variant="success"
                                />
                                <small>{(execution.confidence * 100).toFixed(0)}%</small>
                              </div>
                            ) : (
                              <span className="text-muted">-</span>
                            )}
                          </td>
                          <td>
                            {execution.executedAt ? (
                              <small>{execution.executedAt}</small>
                            ) : (
                              <span className="text-muted">Pending</span>
                            )}
                          </td>
                          <td>
                            <small className="text-muted">{execution.response}</small>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                  
                  <Alert variant="secondary" className="mt-4">
                    <h6>Status Legend:</h6>
                    <div className="d-flex flex-wrap gap-3 mt-2">
                      <div><Badge bg="success">Completed</Badge> - Action successfully executed</div>
                      <div><Badge bg="primary">In Progress</Badge> - Notification sent, awaiting response</div>
                      <div><Badge bg="warning">Pending</Badge> - Waiting for manual review</div>
                      <div><Badge bg="danger">Failed</Badge> - Execution failed, intervention required</div>
                    </div>
                  </Alert>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="dashboard" title="Status Dashboard">
          <Row>
            {/* Statistics Cards */}
            <Col md={3}>
              <div className="stat-card">
                <div className="stat-number text-success">1</div>
                <div className="stat-label">Verified Deaths</div>
              </div>
            </Col>
            <Col md={3}>
              <div className="stat-card">
                <div className="stat-number text-primary">3</div>
                <div className="stat-label">Total Policies</div>
              </div>
            </Col>
            <Col md={3}>
              <div className="stat-card">
                <div className="stat-number text-success">1</div>
                <div className="stat-label">Completed</div>
              </div>
            </Col>
            <Col md={3}>
              <div className="stat-card">
                <div className="stat-number text-warning">2</div>
                <div className="stat-label">In Progress</div>
              </div>
            </Col>
          </Row>
          
          <Row className="mt-4">
            <Col>
              <Card className="dashboard-card">
                <Card.Header>
                  <h5 className="mb-0">
                    Recent Activity Timeline
                  </h5>
                </Card.Header>
                <Card.Body>
                  <div className="timeline">
                    <div className="d-flex mb-4">
                      <div className="feature-icon me-3" style={{ width: '40px', height: '40px', fontSize: '1rem' }}>✓</div>
                      <div className="flex-grow-1">
                        <div className="d-flex justify-content-between align-items-start">
                          <div>
                            <strong>Death Certificate Verified</strong><br />
                            <small className="text-muted">John Doe certificate processed with 95% confidence</small>
                          </div>
                          <small className="text-muted">2024-01-07 10:30:00</small>
                        </div>
                      </div>
                    </div>
                    
                    <div className="d-flex mb-4">
                      <div className="feature-icon me-3" style={{ width: '40px', height: '40px', fontSize: '1rem' }}>🔒</div>
                      <div className="flex-grow-1">
                        <div className="d-flex justify-content-between align-items-start">
                          <div>
                            <strong>Digital Assets Secured</strong><br />
                            <small className="text-muted">All registered assets frozen automatically</small>
                          </div>
                          <small className="text-muted">2024-01-07 10:31:00</small>
                        </div>
                      </div>
                    </div>
                    
                    <div className="d-flex mb-4">
                      <div className="feature-icon me-3" style={{ width: '40px', height: '40px', fontSize: '1rem' }}>AI</div>
                      <div className="flex-grow-1">
                        <div className="d-flex justify-content-between align-items-start">
                          <div>
                            <strong>AI Policy Interpretation Started</strong><br />
                            <small className="text-muted">Azure OpenAI processing user policies</small>
                          </div>
                          <small className="text-muted">2024-01-07 10:32:00</small>
                        </div>
                      </div>
                    </div>
                    
                    <div className="d-flex mb-4">
                      <div className="feature-icon me-3" style={{ width: '40px', height: '40px', fontSize: '1rem' }}>Mail</div>
                      <div className="flex-grow-1">
                        <div className="d-flex justify-content-between align-items-start">
                          <div>
                            <strong>Gmail Deletion Request Sent</strong><br />
                            <small className="text-muted">Professional notification generated and delivered</small>
                          </div>
                          <small className="text-muted">2024-01-07 11:00:00</small>
                        </div>
                      </div>
                    </div>
                    
                    <div className="d-flex">
                      <div className="feature-icon me-3" style={{ width: '40px', height: '40px', fontSize: '1rem' }}>Social</div>
                      <div className="flex-grow-1">
                        <div className="d-flex justify-content-between align-items-start">
                          <div>
                            <strong>Facebook Memorialization Request Sent</strong><br />
                            <small className="text-muted">Awaiting platform response</small>
                          </div>
                          <small className="text-muted">2024-01-07 11:05:00</small>
                        </div>
                      </div>
                    </div>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
      </Tabs>

      {/* Upload Modal */}
      <Modal show={showUploadModal} onHide={() => setShowUploadModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>
            Upload Death Certificate
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="warning" className="mb-4">
            <strong>Authorization Required:</strong> Only authorized trusted contacts can upload death certificates. 
            Ensure you have proper authorization before proceeding.
          </Alert>
          
          <Form onSubmit={handleUpload}>
            <div 
              className={`upload-area ${dragOver ? 'dragover' : ''} mb-4`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
            >
              <div className="text-center">
                <div className="feature-icon mx-auto mb-3">Doc</div>
                <h5>Drop death certificate here</h5>
                <p className="text-muted mb-3">or click to browse files</p>
                <input
                  type="file"
                  accept=".pdf,.jpg,.jpeg,.png,.tiff"
                  onChange={handleFileSelect}
                  style={{ display: 'none' }}
                  id="certificate-upload"
                />
                <label htmlFor="certificate-upload" className="btn btn-outline-primary">
                  Choose File
                </label>
              </div>
            </div>
            
            {selectedFile && (
              <Alert variant="info" className="mb-4">
                <div className="d-flex justify-content-between align-items-center">
                  <div>
                    <strong>Selected:</strong> {selectedFile.name}<br />
                    <small>Size: {formatFileSize(selectedFile.size)} | Type: {selectedFile.type}</small>
                  </div>
                  <Button 
                    variant="outline-danger" 
                    size="sm"
                    onClick={() => setSelectedFile(null)}
                  >
                    Remove
                  </Button>
                </div>
              </Alert>
            )}
            
            <div className="text-muted mb-4">
              <strong>Supported formats:</strong> PDF, JPG, PNG, TIFF<br />
              <strong>Maximum file size:</strong> 10MB<br />
              <strong>Processing:</strong> Azure AI Vision with bank-level security
            </div>
            
            <div className="d-flex gap-2 justify-content-end">
              <Button variant="outline-secondary" onClick={() => setShowUploadModal(false)}>
                Cancel
              </Button>
              <Button 
                type="submit" 
                variant="primary"
                disabled={!selectedFile || uploadStatus === 'uploading' || uploadStatus === 'processing'}
              >
                {uploadStatus === 'uploading' || uploadStatus === 'processing' ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Processing...
                  </>
                ) : (
                  'Verify Certificate'
                )}
              </Button>
            </div>
          </Form>
        </Modal.Body>
      </Modal>
    </div>
  );
}

export default TrustedContactPortal;
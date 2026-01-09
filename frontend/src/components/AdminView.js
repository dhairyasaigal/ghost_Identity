import React, { useState } from 'react';
import { Row, Col, Card, Table, Badge, Tab, Tabs, Alert, ProgressBar } from 'react-bootstrap';

function AdminView() {
  const [auditLogs] = useState([
    {
      id: 1,
      timestamp: '2024-01-07 10:30:00',
      eventType: 'death_verification',
      description: 'Death certificate processed for John Doe',
      aiService: 'azure_vision',
      status: 'success',
      confidence: 0.95,
      inputData: { fileName: 'death_cert_john_doe.pdf', fileSize: '2.3MB' },
      outputData: { 
        extractedName: 'John Doe', 
        dateOfDeath: '2024-01-15', 
        certificateId: 'DC-2024-001234',
        confidence: 0.95
      }
    },
    {
      id: 2,
      timestamp: '2024-01-07 10:31:15',
      description: 'Policy interpretation for Gmail account',
      eventType: 'policy_execution',
      aiService: 'azure_openai',
      status: 'success',
      confidence: 0.88,
      inputData: { 
        policy: 'Please delete my Gmail account completely and permanently. Do not memorialize it.',
        platform: 'Gmail',
        actionType: 'delete'
      },
      outputData: {
        interpretedAction: 'delete',
        generatedNotification: 'Professional account deletion request',
        confidence: 0.88
      }
    },
    {
      id: 3,
      timestamp: '2024-01-07 10:32:30',
      eventType: 'asset_freeze',
      description: 'Digital assets frozen for user John Doe',
      aiService: null,
      status: 'success',
      confidence: null,
      inputData: { userId: 'user_123', assetCount: 5 },
      outputData: { frozenAssets: 5, freezeTime: '2024-01-07 10:32:30' }
    }
  ]);

  const [systemMetrics] = useState({
    totalUsers: 1247,
    activeAssets: 3891,
    verifiedDeaths: 23,
    policiesExecuted: 156,
    aiAccuracy: 94.2,
    systemUptime: 99.8,
    avgProcessingTime: 2.3
  });

  // Before/After state comparison data
  const [beforeAfterData] = useState({
    before: {
      userStatus: 'active',
      assetsCount: 5,
      assets: [
        { platform: 'Gmail', status: 'active', lastAccess: '2024-01-14 09:30:00' },
        { platform: 'Facebook', status: 'active', lastAccess: '2024-01-13 15:45:00' },
        { platform: 'Chase Bank', status: 'active', lastAccess: '2024-01-14 12:00:00' },
        { platform: 'LinkedIn', status: 'active', lastAccess: '2024-01-12 08:20:00' },
        { platform: 'Twitter', status: 'active', lastAccess: '2024-01-14 16:10:00' }
      ],
      trustedContacts: 2,
      policies: 5
    },
    after: {
      userStatus: 'deceased',
      assetsCount: 5,
      assets: [
        { platform: 'Gmail', status: 'deletion_requested', lastAccess: '2024-01-14 09:30:00', actionTaken: 'Delete request sent' },
        { platform: 'Facebook', status: 'memorialized', lastAccess: '2024-01-13 15:45:00', actionTaken: 'Memorialization request sent' },
        { platform: 'Chase Bank', status: 'frozen', lastAccess: '2024-01-14 12:00:00', actionTaken: 'Account frozen pending review' },
        { platform: 'LinkedIn', status: 'deletion_requested', lastAccess: '2024-01-12 08:20:00', actionTaken: 'Delete request sent' },
        { platform: 'Twitter', status: 'frozen', lastAccess: '2024-01-14 16:10:00', actionTaken: 'Account frozen' }
      ],
      trustedContacts: 2,
      policies: 5,
      executionTime: '2024-01-07 10:30:00 - 11:15:00'
    }
  });

  const [selectedLog, setSelectedLog] = useState(null);

  return (
    <div className="fade-in">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="mb-2">System Administration & Demonstration</h2>
          <p className="text-muted mb-0">
            Comprehensive view of system operations, AI decision processes, and before/after state comparisons 
            for technical evaluation and demonstration purposes.
          </p>
        </div>
      </div>
      
      <Row className="mb-4">
        <Col md={2}>
          <Card className="dashboard-card text-center">
            <Card.Body>
              <h3 className="text-primary">{systemMetrics.totalUsers}</h3>
              <p className="mb-0">Total Users</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card className="dashboard-card text-center">
            <Card.Body>
              <h3 className="text-info">{systemMetrics.activeAssets}</h3>
              <p className="mb-0">Active Assets</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card className="dashboard-card text-center">
            <Card.Body>
              <h3 className="text-warning">{systemMetrics.verifiedDeaths}</h3>
              <p className="mb-0">Verified Deaths</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card className="dashboard-card text-center">
            <Card.Body>
              <h3 className="text-success">{systemMetrics.policiesExecuted}</h3>
              <p className="mb-0">Policies Executed</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card className="dashboard-card text-center">
            <Card.Body>
              <h3 className="text-primary">{systemMetrics.aiAccuracy}%</h3>
              <p className="mb-0">AI Accuracy</p>
            </Card.Body>
          </Card>
        </Col>
        <Col md={2}>
          <Card className="dashboard-card text-center">
            <Card.Body>
              <h3 className="text-success">{systemMetrics.systemUptime}%</h3>
              <p className="mb-0">System Uptime</p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      <Tabs defaultActiveKey="before-after" className="mb-3">
        <Tab eventKey="before-after" title="Before/After State Comparison">
          <Alert variant="info">
            <strong>Demonstration View:</strong> This shows the complete transformation of digital assets 
            from active state to secured/executed state after death verification.
          </Alert>
          
          <Row>
            <Col md={6}>
              <Card className="dashboard-card">
                <Card.Header className="bg-light">
                  <h5 className="mb-0">BEFORE - Active User State</h5>
                  <small className="text-muted">State before death verification</small>
                </Card.Header>
                <Card.Body>
                  <Table size="sm">
                    <tbody>
                      <tr>
                        <td><strong>User Status:</strong></td>
                        <td>
                          <Badge bg="success">{beforeAfterData.before.userStatus}</Badge>
                        </td>
                      </tr>
                      <tr>
                        <td><strong>Digital Assets:</strong></td>
                        <td>{beforeAfterData.before.assetsCount} registered</td>
                      </tr>
                      <tr>
                        <td><strong>Trusted Contacts:</strong></td>
                        <td>{beforeAfterData.before.trustedContacts} verified</td>
                      </tr>
                      <tr>
                        <td><strong>Action Policies:</strong></td>
                        <td>{beforeAfterData.before.policies} configured</td>
                      </tr>
                    </tbody>
                  </Table>
                  
                  <h6 className="mt-3">Asset Status:</h6>
                  <Table size="sm">
                    <thead>
                      <tr>
                        <th>Platform</th>
                        <th>Status</th>
                        <th>Last Access</th>
                      </tr>
                    </thead>
                    <tbody>
                      {beforeAfterData.before.assets.map((asset, index) => (
                        <tr key={index}>
                          <td>{asset.platform}</td>
                          <td>
                            <Badge bg="success">{asset.status}</Badge>
                          </td>
                          <td><small>{asset.lastAccess}</small></td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
            
            <Col md={6}>
              <Card className="dashboard-card">
                <Card.Header className="bg-warning">
                  <h5 className="mb-0">AFTER - Secured/Executed State</h5>
                  <small className="text-muted">State after AI-powered policy execution</small>
                </Card.Header>
                <Card.Body>
                  <Table size="sm">
                    <tbody>
                      <tr>
                        <td><strong>User Status:</strong></td>
                        <td>
                          <Badge bg="danger">{beforeAfterData.after.userStatus}</Badge>
                        </td>
                      </tr>
                      <tr>
                        <td><strong>Digital Assets:</strong></td>
                        <td>{beforeAfterData.after.assetsCount} secured/processed</td>
                      </tr>
                      <tr>
                        <td><strong>Execution Time:</strong></td>
                        <td><small>{beforeAfterData.after.executionTime}</small></td>
                      </tr>
                      <tr>
                        <td><strong>Processing Duration:</strong></td>
                        <td>45 minutes (automated)</td>
                      </tr>
                    </tbody>
                  </Table>
                  
                  <h6 className="mt-3">Asset Status After Execution:</h6>
                  <Table size="sm">
                    <thead>
                      <tr>
                        <th>Platform</th>
                        <th>Status</th>
                        <th>Action Taken</th>
                      </tr>
                    </thead>
                    <tbody>
                      {beforeAfterData.after.assets.map((asset, index) => (
                        <tr key={index}>
                          <td>{asset.platform}</td>
                          <td>
                            <Badge bg={
                              asset.status === 'deletion_requested' ? 'danger' :
                              asset.status === 'memorialized' ? 'warning' :
                              asset.status === 'frozen' ? 'secondary' : 'success'
                            }>
                              {asset.status.replace('_', ' ')}
                            </Badge>
                          </td>
                          <td><small>{asset.actionTaken}</small></td>
                        </tr>
                      ))}
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
          </Row>
          
          <Row className="mt-4">
            <Col>
              <Card className="dashboard-card">
                <Card.Header>
                  <h5 className="mb-0">Transformation Summary</h5>
                </Card.Header>
                <Card.Body>
                  <Row>
                    <Col md={3}>
                      <div className="text-center">
                        <h4 className="text-success">100%</h4>
                        <p>Assets Secured</p>
                      </div>
                    </Col>
                    <Col md={3}>
                      <div className="text-center">
                        <h4 className="text-primary">45min</h4>
                        <p>Total Processing Time</p>
                      </div>
                    </Col>
                    <Col md={3}>
                      <div className="text-center">
                        <h4 className="text-warning">5</h4>
                        <p>Policies Executed</p>
                      </div>
                    </Col>
                    <Col md={3}>
                      <div className="text-center">
                        <h4 className="text-info">0</h4>
                        <p>Manual Interventions</p>
                      </div>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="ai-decisions" title="AI Decision Trail">
          <Alert variant="primary">
            <strong>AI Processing Transparency:</strong> Detailed view of how Microsoft AI services 
            (Azure AI Vision and Azure OpenAI) processed death verification and policy execution.
          </Alert>
          
          <Row>
            <Col md={6}>
              <Card className="dashboard-card">
                <Card.Header>
                  <h5 className="mb-0">Azure AI Vision - Death Certificate Analysis</h5>
                </Card.Header>
                <Card.Body>
                  <div className="mb-3">
                    <strong>Processing Pipeline:</strong>
                    <ProgressBar className="mt-2">
                      <ProgressBar variant="success" now={25} label="OCR Extraction" />
                      <ProgressBar variant="info" now={25} label="Text Analysis" />
                      <ProgressBar variant="warning" now={25} label="Field Mapping" />
                      <ProgressBar variant="primary" now={25} label="Validation" />
                    </ProgressBar>
                  </div>
                  
                  <Table size="sm">
                    <tbody>
                      <tr>
                        <td><strong>Input Document:</strong></td>
                        <td>death_cert_john_doe.pdf (2.3MB)</td>
                      </tr>
                      <tr>
                        <td><strong>OCR Confidence:</strong></td>
                        <td>98.7%</td>
                      </tr>
                      <tr>
                        <td><strong>Extracted Fields:</strong></td>
                        <td>
                          <ul className="mb-0">
                            <li>Name: John Doe (confidence: 99.2%)</li>
                            <li>Date of Death: 2024-01-15 (confidence: 97.8%)</li>
                            <li>Certificate ID: DC-2024-001234 (confidence: 95.1%)</li>
                          </ul>
                        </td>
                      </tr>
                      <tr>
                        <td><strong>Validation Result:</strong></td>
                        <td><Badge bg="success">VERIFIED</Badge></td>
                      </tr>
                      <tr>
                        <td><strong>Processing Time:</strong></td>
                        <td>3.2 seconds</td>
                      </tr>
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
            
            <Col md={6}>
              <Card className="dashboard-card">
                <Card.Header>
                  <h5 className="mb-0">Azure OpenAI - Policy Interpretation</h5>
                </Card.Header>
                <Card.Body>
                  <div className="mb-3">
                    <strong>Processing Pipeline:</strong>
                    <ProgressBar className="mt-2">
                      <ProgressBar variant="success" now={33} label="Policy Analysis" />
                      <ProgressBar variant="info" now={33} label="Intent Recognition" />
                      <ProgressBar variant="warning" now={34} label="Notification Generation" />
                    </ProgressBar>
                  </div>
                  
                  <Table size="sm">
                    <tbody>
                      <tr>
                        <td><strong>Input Policy:</strong></td>
                        <td>"Please delete my Gmail account completely..."</td>
                      </tr>
                      <tr>
                        <td><strong>Interpreted Action:</strong></td>
                        <td><Badge bg="danger">DELETE</Badge></td>
                      </tr>
                      <tr>
                        <td><strong>Confidence Score:</strong></td>
                        <td>88.7%</td>
                      </tr>
                      <tr>
                        <td><strong>Generated Notification:</strong></td>
                        <td>Professional deletion request with legal documentation</td>
                      </tr>
                      <tr>
                        <td><strong>Platform Compliance:</strong></td>
                        <td><Badge bg="success">COMPLIANT</Badge></td>
                      </tr>
                      <tr>
                        <td><strong>Processing Time:</strong></td>
                        <td>1.8 seconds</td>
                      </tr>
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
          </Row>
          
          <Row className="mt-4">
            <Col>
              <Card className="dashboard-card">
                <Card.Header>
                  <h5 className="mb-0">AI Decision Accuracy Metrics</h5>
                </Card.Header>
                <Card.Body>
                  <Row>
                    <Col md={4}>
                      <div className="text-center">
                        <h4 className="text-success">95.2%</h4>
                        <p>OCR Accuracy</p>
                        <small className="text-muted">Azure AI Vision</small>
                      </div>
                    </Col>
                    <Col md={4}>
                      <div className="text-center">
                        <h4 className="text-primary">88.7%</h4>
                        <p>Policy Interpretation</p>
                        <small className="text-muted">Azure OpenAI</small>
                      </div>
                    </Col>
                    <Col md={4}>
                      <div className="text-center">
                        <h4 className="text-warning">100%</h4>
                        <p>Platform Compliance</p>
                        <small className="text-muted">Generated Notifications</small>
                      </div>
                    </Col>
                  </Row>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="audit" title="Comprehensive Audit Logs">
          <Card className="dashboard-card">
            <Card.Header>
              <h5 className="mb-0">Tamper-Proof System Audit Trail</h5>
            </Card.Header>
            <Card.Body>
              <Alert variant="secondary">
                <strong>Audit Log Integrity:</strong> All entries are cryptographically signed and tamper-proof. 
                Hash verification ensures complete audit trail integrity.
              </Alert>
              
              <Table responsive>
                <thead>
                  <tr>
                    <th>Timestamp</th>
                    <th>Event Type</th>
                    <th>Description</th>
                    <th>AI Service</th>
                    <th>Status</th>
                    <th>Confidence</th>
                    <th>Details</th>
                  </tr>
                </thead>
                <tbody>
                  {auditLogs.map((log) => (
                    <tr key={log.id}>
                      <td><small>{log.timestamp}</small></td>
                      <td>
                        <Badge bg="secondary">
                          {log.eventType.replace('_', ' ')}
                        </Badge>
                      </td>
                      <td>{log.description}</td>
                      <td>
                        {log.aiService ? (
                          <Badge bg="info">{log.aiService}</Badge>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                      <td>
                        <Badge bg={log.status === 'success' ? 'success' : 'danger'}>
                          {log.status}
                        </Badge>
                      </td>
                      <td>
                        {log.confidence ? `${(log.confidence * 100).toFixed(1)}%` : '-'}
                      </td>
                      <td>
                        <button 
                          className="btn btn-sm btn-outline-primary"
                          onClick={() => setSelectedLog(log)}
                        >
                          View Details
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </Table>
              
              {selectedLog && (
                <Card className="dashboard-card mt-3">
                  <Card.Header>
                    <h6 className="mb-0">Audit Log Details - {selectedLog.eventType}</h6>
                  </Card.Header>
                  <Card.Body>
                    <Row>
                      <Col md={6}>
                        <h6>Input Data:</h6>
                        <pre className="bg-light p-2" style={{fontSize: '0.8em'}}>
                          {JSON.stringify(selectedLog.inputData, null, 2)}
                        </pre>
                      </Col>
                      <Col md={6}>
                        <h6>Output Data:</h6>
                        <pre className="bg-light p-2" style={{fontSize: '0.8em'}}>
                          {JSON.stringify(selectedLog.outputData, null, 2)}
                        </pre>
                      </Col>
                    </Row>
                  </Card.Body>
                </Card>
              )}
            </Card.Body>
          </Card>
        </Tab>
        
        <Tab eventKey="system-health" title="System Health & Performance">
          <Row>
            <Col md={6}>
              <Card className="dashboard-card">
                <Card.Header>
                  <h5 className="mb-0">Performance Metrics</h5>
                </Card.Header>
                <Card.Body>
                  <Table>
                    <tbody>
                      <tr>
                        <td><strong>Average Processing Time:</strong></td>
                        <td>{systemMetrics.avgProcessingTime} seconds</td>
                      </tr>
                      <tr>
                        <td><strong>System Uptime:</strong></td>
                        <td>{systemMetrics.systemUptime}%</td>
                      </tr>
                      <tr>
                        <td><strong>AI Service Availability:</strong></td>
                        <td>
                          <Badge bg="success">Azure AI Vision: 99.9%</Badge><br />
                          <Badge bg="success">Azure OpenAI: 99.7%</Badge>
                        </td>
                      </tr>
                      <tr>
                        <td><strong>Database Performance:</strong></td>
                        <td>Query time: 0.12ms avg</td>
                      </tr>
                      <tr>
                        <td><strong>Security Events:</strong></td>
                        <td>0 incidents in last 30 days</td>
                      </tr>
                    </tbody>
                  </Table>
                </Card.Body>
              </Card>
            </Col>
            
            <Col md={6}>
              <Card className="dashboard-card">
                <Card.Header>
                  <h5 className="mb-0">Service Status</h5>
                </Card.Header>
                <Card.Body>
                  <div className="mb-3">
                    <div className="d-flex justify-content-between">
                      <span>Azure AI Vision</span>
                      <Badge bg="success">Operational</Badge>
                    </div>
                    <ProgressBar variant="success" now={100} className="mt-1" />
                  </div>
                  
                  <div className="mb-3">
                    <div className="d-flex justify-content-between">
                      <span>Azure OpenAI</span>
                      <Badge bg="success">Operational</Badge>
                    </div>
                    <ProgressBar variant="success" now={100} className="mt-1" />
                  </div>
                  
                  <div className="mb-3">
                    <div className="d-flex justify-content-between">
                      <span>Database</span>
                      <Badge bg="success">Operational</Badge>
                    </div>
                    <ProgressBar variant="success" now={100} className="mt-1" />
                  </div>
                  
                  <div className="mb-3">
                    <div className="d-flex justify-content-between">
                      <span>Encryption Service</span>
                      <Badge bg="success">Operational</Badge>
                    </div>
                    <ProgressBar variant="success" now={100} className="mt-1" />
                  </div>
                  
                  <div className="mb-3">
                    <div className="d-flex justify-content-between">
                      <span>Audit Logging</span>
                      <Badge bg="success">Operational</Badge>
                    </div>
                    <ProgressBar variant="success" now={100} className="mt-1" />
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Tab>
      </Tabs>
    </div>
  );
}

export default AdminView;
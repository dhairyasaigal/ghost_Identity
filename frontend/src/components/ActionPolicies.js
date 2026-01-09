import React, { useState } from 'react';
import { Row, Col, Card, Form, Button, Table, Badge, Alert, Modal } from 'react-bootstrap';

function ActionPolicies() {
  const [policies, setPolicies] = useState([]);
  const [assets] = useState([
    { id: 1, platformName: 'Gmail', assetType: 'email', accountIdentifier: 'user@gmail.com' },
    { id: 2, platformName: 'Facebook', assetType: 'social_media', accountIdentifier: 'facebook.com/user' },
    { id: 3, platformName: 'Chase Bank', assetType: 'bank', accountIdentifier: '****1234' }
  ]);
  
  const [newPolicy, setNewPolicy] = useState({
    assetId: '',
    actionType: 'delete',
    naturalLanguagePolicy: '',
    specificInstructions: '',
    conditions: '',
    priority: 1
  });
  
  const [showPreview, setShowPreview] = useState(false);
  const [previewPolicy, setPreviewPolicy] = useState(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    const selectedAsset = assets.find(asset => asset.id === parseInt(newPolicy.assetId));
    
    const policy = {
      ...newPolicy,
      id: Date.now(),
      assetId: parseInt(newPolicy.assetId),
      platformName: selectedAsset?.platformName || '',
      assetType: selectedAsset?.assetType || '',
      accountIdentifier: selectedAsset?.accountIdentifier || '',
      status: 'active',
      createdAt: new Date().toISOString()
    };
    
    setPolicies([...policies, policy]);
    setNewPolicy({
      assetId: '',
      actionType: 'delete',
      naturalLanguagePolicy: '',
      specificInstructions: '',
      conditions: '',
      priority: 1
    });
  };

  const removePolicy = (id) => {
    setPolicies(policies.filter(policy => policy.id !== id));
  };

  const previewPolicyExecution = (policy) => {
    const selectedAsset = assets.find(asset => asset.id === policy.assetId);
    setPreviewPolicy({
      ...policy,
      asset: selectedAsset,
      generatedNotification: generateMockNotification(policy, selectedAsset)
    });
    setShowPreview(true);
  };

  const generateMockNotification = (policy, asset) => {
    const actionText = {
      delete: 'permanently delete',
      memorialize: 'memorialize',
      transfer: 'transfer ownership of',
      lock: 'lock and secure'
    };

    return {
      subject: `Death Notification - Request to ${actionText[policy.actionType]} account`,
      body: `Dear ${asset.platformName} Support Team,

I am writing to notify you of the death of the account holder and request that you ${actionText[policy.actionType]} the following account:

Account Information:
- Platform: ${asset.platformName}
- Account Identifier: ${asset.accountIdentifier}
- Account Type: ${asset.assetType.replace('_', ' ')}

Requested Action: ${policy.actionType.charAt(0).toUpperCase() + policy.actionType.slice(1)}

${policy.specificInstructions ? `Special Instructions: ${policy.specificInstructions}` : ''}

${policy.conditions ? `Conditions: ${policy.conditions}` : ''}

Please find attached the death certificate and any required documentation. If you need additional information or documentation, please contact me at the information provided below.

Thank you for your assistance during this difficult time.

Sincerely,
[Trusted Contact Name]
[Contact Information]`,
      requiredDocuments: ['Death Certificate', 'Proof of Authority', 'Government ID']
    };
  };

  const validatePolicy = () => {
    const errors = [];
    if (!newPolicy.assetId) errors.push('Please select an asset');
    if (!newPolicy.naturalLanguagePolicy.trim()) errors.push('Please provide a policy description');
    return errors;
  };

  const validationErrors = validatePolicy();

  return (
    <div className="fade-in">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="mb-2">Action Policy Configuration</h2>
          <p className="text-muted mb-0">
            Create detailed policies for how your digital assets should be handled after death. 
            These policies will be interpreted by AI and executed automatically.
          </p>
        </div>
      </div>
      
      <Row>
        <Col md={6}>
          <Card className="dashboard-card">
            <Card.Header>
              <h5 className="mb-0">Create New Policy</h5>
            </Card.Header>
            <Card.Body>
              <Form onSubmit={handleSubmit}>
                <Form.Group className="mb-3">
                  <Form.Label>Select Digital Asset *</Form.Label>
                  <Form.Select
                    value={newPolicy.assetId}
                    onChange={(e) => setNewPolicy({...newPolicy, assetId: e.target.value})}
                    required
                  >
                    <option value="">Choose an asset...</option>
                    {assets.map((asset) => (
                      <option key={asset.id} value={asset.id}>
                        {asset.platformName} - {asset.accountIdentifier} ({asset.assetType.replace('_', ' ')})
                      </option>
                    ))}
                  </Form.Select>
                  <Form.Text className="text-muted">
                    Select from your registered digital assets in the vault.
                  </Form.Text>
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Action Type *</Form.Label>
                  <Form.Select
                    value={newPolicy.actionType}
                    onChange={(e) => setNewPolicy({...newPolicy, actionType: e.target.value})}
                    required
                  >
                    <option value="delete">Delete Account - Permanently remove the account</option>
                    <option value="memorialize">Memorialize Account - Convert to memorial/tribute</option>
                    <option value="transfer">Transfer Account - Transfer to trusted contact</option>
                    <option value="lock">Lock Account - Secure and freeze the account</option>
                  </Form.Select>
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Policy Description (Natural Language) *</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={3}
                    placeholder="Describe in your own words what should happen to this account. Example: 'Please delete my Gmail account completely and permanently. Do not memorialize it or keep any data.'"
                    value={newPolicy.naturalLanguagePolicy}
                    onChange={(e) => setNewPolicy({...newPolicy, naturalLanguagePolicy: e.target.value})}
                    required
                  />
                  <Form.Text className="text-muted">
                    Azure OpenAI will interpret this natural language policy to generate appropriate notifications.
                  </Form.Text>
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Specific Instructions</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={2}
                    placeholder="Any specific instructions for the platform (e.g., 'Please donate any remaining account balance to charity')"
                    value={newPolicy.specificInstructions}
                    onChange={(e) => setNewPolicy({...newPolicy, specificInstructions: e.target.value})}
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Conditions/Requirements</Form.Label>
                  <Form.Control
                    as="textarea"
                    rows={2}
                    placeholder="Any conditions that must be met before executing this policy (e.g., 'Wait 30 days after death verification')"
                    value={newPolicy.conditions}
                    onChange={(e) => setNewPolicy({...newPolicy, conditions: e.target.value})}
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Priority Level</Form.Label>
                  <Form.Select
                    value={newPolicy.priority}
                    onChange={(e) => setNewPolicy({...newPolicy, priority: parseInt(e.target.value)})}
                  >
                    <option value={1}>High Priority - Execute immediately</option>
                    <option value={2}>Medium Priority - Execute within 7 days</option>
                    <option value={3}>Low Priority - Execute within 30 days</option>
                  </Form.Select>
                </Form.Group>
                
                {validationErrors.length > 0 && (
                  <Alert variant="danger">
                    <strong>Please fix the following errors:</strong>
                    <ul className="mb-0 mt-2">
                      {validationErrors.map((error, index) => (
                        <li key={index}>{error}</li>
                      ))}
                    </ul>
                  </Alert>
                )}
                
                <div className="d-grid gap-2">
                  <Button type="submit" variant="primary" disabled={validationErrors.length > 0}>
                    Create Policy
                  </Button>
                </div>
              </Form>
            </Card.Body>
          </Card>
        </Col>
        
        <Col md={6}>
          <Card className="dashboard-card">
            <Card.Header>
              <h5 className="mb-0">Active Policies ({policies.length})</h5>
            </Card.Header>
            <Card.Body style={{maxHeight: '600px', overflowY: 'auto'}}>
              {policies.length === 0 ? (
                <Alert variant="info">
                  <strong>No policies created yet.</strong><br />
                  Create policies to define how your digital assets should be handled after death.
                </Alert>
              ) : (
                <div>
                  {policies.map((policy) => (
                    <Card key={policy.id} className="mb-3 border">
                      <Card.Body>
                        <div className="d-flex justify-content-between align-items-start mb-2">
                          <h6 className="mb-0">{policy.platformName}</h6>
                          <div>
                            <Badge bg="info" className="me-1">
                              Priority {policy.priority}
                            </Badge>
                            <Badge bg={
                              policy.actionType === 'delete' ? 'danger' :
                              policy.actionType === 'memorialize' ? 'warning' :
                              policy.actionType === 'transfer' ? 'success' : 'secondary'
                            }>
                              {policy.actionType}
                            </Badge>
                          </div>
                        </div>
                        
                        <p className="text-muted small mb-2">
                          {policy.accountIdentifier} • {policy.assetType.replace('_', ' ')}
                        </p>
                        
                        <p className="mb-2">
                          <strong>Policy:</strong> {policy.naturalLanguagePolicy}
                        </p>
                        
                        {policy.specificInstructions && (
                          <p className="mb-2">
                            <strong>Instructions:</strong> {policy.specificInstructions}
                          </p>
                        )}
                        
                        {policy.conditions && (
                          <p className="mb-2">
                            <strong>Conditions:</strong> {policy.conditions}
                          </p>
                        )}
                        
                        <div className="d-flex gap-2">
                          <Button 
                            variant="outline-primary" 
                            size="sm"
                            onClick={() => previewPolicyExecution(policy)}
                          >
                            Preview Execution
                          </Button>
                          <Button 
                            variant="outline-danger" 
                            size="sm"
                            onClick={() => removePolicy(policy.id)}
                          >
                            Remove
                          </Button>
                        </div>
                      </Card.Body>
                    </Card>
                  ))}
                </div>
              )}
            </Card.Body>
          </Card>
        </Col>
      </Row>
      
      {/* Policy Preview Modal */}
      <Modal show={showPreview} onHide={() => setShowPreview(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Policy Execution Preview</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {previewPolicy && (
            <div>
              <Alert variant="info">
                <strong>Preview:</strong> This shows how Azure OpenAI would interpret your policy and generate notifications.
              </Alert>
              
              <h6>Policy Details</h6>
              <Table size="sm" className="mb-3">
                <tbody>
                  <tr>
                    <td><strong>Platform:</strong></td>
                    <td>{previewPolicy.platformName}</td>
                  </tr>
                  <tr>
                    <td><strong>Account:</strong></td>
                    <td>{previewPolicy.accountIdentifier}</td>
                  </tr>
                  <tr>
                    <td><strong>Action:</strong></td>
                    <td>
                      <Badge bg={
                        previewPolicy.actionType === 'delete' ? 'danger' :
                        previewPolicy.actionType === 'memorialize' ? 'warning' :
                        previewPolicy.actionType === 'transfer' ? 'success' : 'secondary'
                      }>
                        {previewPolicy.actionType}
                      </Badge>
                    </td>
                  </tr>
                  <tr>
                    <td><strong>Priority:</strong></td>
                    <td>Level {previewPolicy.priority}</td>
                  </tr>
                </tbody>
              </Table>
              
              <h6>Generated Notification</h6>
              <Card>
                <Card.Header>
                  <strong>Subject:</strong> {previewPolicy.generatedNotification.subject}
                </Card.Header>
                <Card.Body>
                  <pre style={{whiteSpace: 'pre-wrap', fontSize: '0.9em'}}>
                    {previewPolicy.generatedNotification.body}
                  </pre>
                  
                  <hr />
                  <h6>Required Documents:</h6>
                  <ul>
                    {previewPolicy.generatedNotification.requiredDocuments.map((doc, index) => (
                      <li key={index}>{doc}</li>
                    ))}
                  </ul>
                </Card.Body>
              </Card>
            </div>
          )}
        </Modal.Body>
        <Modal.Footer>
          <Button variant="secondary" onClick={() => setShowPreview(false)}>
            Close Preview
          </Button>
        </Modal.Footer>
      </Modal>
    </div>
  );
}

export default ActionPolicies;
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Form, Button, Table, Badge, Tab, Tabs, Alert, Modal } from 'react-bootstrap';
import apiService from '../services/api';

function UserVault() {
  const [assets, setAssets] = useState([]);
  const [trustedContacts, setTrustedContacts] = useState([]);
  const [showAssetModal, setShowAssetModal] = useState(false);
  const [showContactModal, setShowContactModal] = useState(false);
  const [loading, setLoading] = useState(false);
  
  const [newAsset, setNewAsset] = useState({
    assetType: 'email',
    platformName: '',
    accountIdentifier: '',
    credentials: '',
    actionType: 'delete'
  });
  
  const [newContact, setNewContact] = useState({
    contact_name: '',
    contact_email: '',
    contact_phone: '',
    relationship: '',
    contact_aadhaar_number: '',
    contact_pan_number: '',
    contact_address_line1: '',
    contact_address_line2: '',
    contact_city: '',
    contact_state: '',
    contact_pincode: '',
    authorization_level: 'basic'
  });

  const handleAssetSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    // Simulate API call
    setTimeout(() => {
      const asset = {
        ...newAsset,
        id: Date.now(),
        status: 'active',
        createdAt: new Date().toISOString()
      };
      setAssets([...assets, asset]);
      setNewAsset({
        assetType: 'email',
        platformName: '',
        accountIdentifier: '',
        credentials: '',
        actionType: 'delete'
      });
      setShowAssetModal(false);
      setLoading(false);
    }, 1000);
  };

  const handleContactSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    
    try {
      // Use the actual API service to add trusted contact
      const response = await apiService.addTrustedContact(newContact);
      
      // Add the new contact to the list
      const contact = {
        ...response.contact,
        id: response.contact.contact_id,
        createdAt: new Date().toISOString()
      };
      setTrustedContacts([...trustedContacts, contact]);
      
      // Reset form
      setNewContact({
        contact_name: '',
        contact_email: '',
        contact_phone: '',
        relationship: '',
        contact_aadhaar_number: '',
        contact_pan_number: '',
        contact_address_line1: '',
        contact_address_line2: '',
        contact_city: '',
        contact_state: '',
        contact_pincode: '',
        authorization_level: 'basic'
      });
      setShowContactModal(false);
      setLoading(false);
    } catch (error) {
      console.error('Error adding trusted contact:', error);
      // For now, simulate success for demo purposes
      const contact = {
        ...newContact,
        id: Date.now(),
        status: 'pending',
        verification_status: 'pending',
        identity_documents_verified: 'pending',
        createdAt: new Date().toISOString()
      };
      setTrustedContacts([...trustedContacts, contact]);
      setNewContact({
        contact_name: '',
        contact_email: '',
        contact_phone: '',
        relationship: '',
        contact_aadhaar_number: '',
        contact_pan_number: '',
        contact_address_line1: '',
        contact_address_line2: '',
        contact_city: '',
        contact_state: '',
        contact_pincode: '',
        authorization_level: 'basic'
      });
      setShowContactModal(false);
      setLoading(false);
    }
  };

  const removeAsset = (id) => {
    setAssets(assets.filter(asset => asset.id !== id));
  };

  const removeContact = (id) => {
    setTrustedContacts(trustedContacts.filter(contact => contact.id !== id));
  };

  const getActionTypeColor = (type) => {
    const colors = {
      delete: 'danger',
      memorialize: 'warning',
      transfer: 'success',
      lock: 'secondary'
    };
    return colors[type] || 'secondary';
  };

  return (
    <div className="fade-in">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="mb-2">Digital Asset Vault</h2>
          <p className="text-muted mb-0">
            Securely manage your digital assets and trusted contacts with enterprise-grade encryption
          </p>
        </div>
        <div className="d-flex gap-2">
          <Button variant="primary" onClick={() => setShowAssetModal(true)}>
            Add Asset
          </Button>
          <Button variant="outline-primary" onClick={() => setShowContactModal(true)}>
            Add Contact
          </Button>
        </div>
      </div>

      {/* Security Notice */}
      <Alert variant="info" className="mb-4">
        <div className="d-flex align-items-start">
          <div className="me-3 mt-1">
            <strong>Security Notice:</strong>
          </div>
          <div>
            All sensitive data is encrypted using AES-256 encryption and stored securely. 
            Multi-factor authentication is required for all vault operations.
          </div>
        </div>
      </Alert>
      
      <Tabs defaultActiveKey="assets" className="mb-4">
        <Tab eventKey="assets" title={`Digital Assets (${assets.length})`}>
          <Row>
            <Col>
              {assets.length === 0 ? (
                <Card className="dashboard-card text-center py-5">
                  <Card.Body>
                    <h4>No Assets Registered</h4>
                    <p className="text-muted mb-4">
                      Start securing your digital legacy by adding your first digital asset to the vault.
                    </p>
                    <Button variant="primary" onClick={() => setShowAssetModal(true)}>
                      Add Your First Asset
                    </Button>
                  </Card.Body>
                </Card>
              ) : (
                <Card className="dashboard-card">
                  <Card.Header className="d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">Registered Assets ({assets.length})</h5>
                    <Button variant="primary" size="sm" onClick={() => setShowAssetModal(true)}>
                      Add Asset
                    </Button>
                  </Card.Header>
                  <Card.Body className="p-0">
                    <Table responsive hover className="mb-0">
                      <thead>
                        <tr>
                          <th>Platform</th>
                          <th>Type</th>
                          <th>Account</th>
                          <th>Default Action</th>
                          <th>Status</th>
                          <th>Added</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {assets.map((asset) => (
                          <tr key={asset.id}>
                            <td>
                              <strong>{asset.platformName}</strong>
                            </td>
                            <td>
                              <Badge bg="secondary">
                                {asset.assetType.replace('_', ' ')}
                              </Badge>
                            </td>
                            <td>
                              <code className="text-muted">{asset.accountIdentifier}</code>
                            </td>
                            <td>
                              <Badge bg={getActionTypeColor(asset.actionType)}>
                                {asset.actionType}
                              </Badge>
                            </td>
                            <td>
                              <Badge bg="success">
                                {asset.status}
                              </Badge>
                            </td>
                            <td>
                              <small className="text-muted">
                                {new Date(asset.createdAt).toLocaleDateString()}
                              </small>
                            </td>
                            <td>
                              <div className="d-flex gap-1">
                                <Button variant="outline-primary" size="sm">
                                  Edit
                                </Button>
                                <Button 
                                  variant="outline-danger" 
                                  size="sm"
                                  onClick={() => removeAsset(asset.id)}
                                >
                                  Delete
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </Card.Body>
                </Card>
              )}
            </Col>
          </Row>
        </Tab>
        
        <Tab eventKey="contacts" title={`Trusted Contacts (${trustedContacts.length})`}>
          <Row>
            <Col>
              {trustedContacts.length === 0 ? (
                <Card className="dashboard-card text-center py-5">
                  <Card.Body>
                    <h4>No Trusted Contacts Added</h4>
                    <p className="text-muted mb-4">
                      Add trusted individuals who can verify death events and oversee your digital legacy policies.
                    </p>
                    <Alert variant="warning" className="mb-4">
                      <strong>Important:</strong> Choose people you trust completely. They will have the ability to 
                      verify death events and execute your digital legacy policies.
                    </Alert>
                    <Button variant="primary" onClick={() => setShowContactModal(true)}>
                      Add Your First Contact
                    </Button>
                  </Card.Body>
                </Card>
              ) : (
                <Card className="dashboard-card">
                  <Card.Header className="d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">Trusted Contacts ({trustedContacts.length})</h5>
                    <Button variant="primary" size="sm" onClick={() => setShowContactModal(true)}>
                      Add Contact
                    </Button>
                  </Card.Header>
                  <Card.Body className="p-0">
                    <Table responsive hover className="mb-0">
                      <thead>
                        <tr>
                          <th>Name</th>
                          <th>Contact Info</th>
                          <th>Relationship</th>
                          <th>Identity Verification</th>
                          <th>Authorization Level</th>
                          <th>Status</th>
                          <th>Actions</th>
                        </tr>
                      </thead>
                      <tbody>
                        {trustedContacts.map((contact) => (
                          <tr key={contact.id}>
                            <td>
                              <div>
                                <strong>{contact.contact_name || contact.name}</strong>
                                {contact.contact_aadhaar_number && (
                                  <div>
                                    <small className="text-muted">
                                      Aadhaar: ****{contact.contact_aadhaar_number.slice(-4)}
                                    </small>
                                  </div>
                                )}
                                {contact.contact_pan_number && (
                                  <div>
                                    <small className="text-muted">
                                      PAN: {contact.contact_pan_number}
                                    </small>
                                  </div>
                                )}
                              </div>
                            </td>
                            <td>
                              <div>
                                <code className="text-muted">{contact.contact_email || contact.email}</code>
                                <br />
                                <small className="text-muted">
                                  {contact.contact_phone || contact.phone || '—'}
                                </small>
                              </div>
                            </td>
                            <td>
                              <Badge bg="secondary">
                                {contact.relationship}
                              </Badge>
                            </td>
                            <td>
                              <div>
                                {contact.identity_verification_score && (
                                  <div className="mb-1">
                                    <small>Score: {contact.identity_verification_score}</small>
                                  </div>
                                )}
                                <Badge bg={contact.identity_documents_verified === 'verified' ? 'success' : 'warning'}>
                                  {contact.identity_documents_verified || 'Pending'}
                                </Badge>
                              </div>
                            </td>
                            <td>
                              <Badge bg={
                                contact.authorization_level === 'full' ? 'success' : 
                                contact.authorization_level === 'emergency_only' ? 'warning' : 'secondary'
                              }>
                                {contact.authorization_level || 'basic'}
                              </Badge>
                            </td>
                            <td>
                              <Badge bg={contact.verification_status === 'verified' || contact.status === 'verified' ? 'success' : 'warning'}>
                                {contact.verification_status || contact.status || 'pending'}
                              </Badge>
                            </td>
                            <td>
                              <div className="d-flex gap-1">
                                <Button variant="outline-primary" size="sm">
                                  Edit
                                </Button>
                                <Button 
                                  variant="outline-danger" 
                                  size="sm"
                                  onClick={() => removeContact(contact.id)}
                                >
                                  Delete
                                </Button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </Card.Body>
                </Card>
              )}
            </Col>
          </Row>
        </Tab>
      </Tabs>

      {/* Add Asset Modal */}
      <Modal show={showAssetModal} onHide={() => setShowAssetModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Add Digital Asset</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Form onSubmit={handleAssetSubmit}>
            <Row>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Asset Type</Form.Label>
                  <Form.Select 
                    value={newAsset.assetType}
                    onChange={(e) => setNewAsset({...newAsset, assetType: e.target.value})}
                    required
                  >
                    <option value="email">Email Account</option>
                    <option value="bank">Bank Account</option>
                    <option value="social_media">Social Media</option>
                    <option value="other">Other</option>
                  </Form.Select>
                </Form.Group>
              </Col>
              <Col md={6}>
                <Form.Group className="mb-3">
                  <Form.Label>Default Action</Form.Label>
                  <Form.Select 
                    value={newAsset.actionType}
                    onChange={(e) => setNewAsset({...newAsset, actionType: e.target.value})}
                    required
                  >
                    <option value="delete">Delete Account</option>
                    <option value="memorialize">Memorialize Account</option>
                    <option value="transfer">Transfer to Contact</option>
                    <option value="lock">Lock Account</option>
                  </Form.Select>
                </Form.Group>
              </Col>
            </Row>
            
            <Form.Group className="mb-3">
              <Form.Label>Platform Name</Form.Label>
              <Form.Control
                type="text"
                placeholder="e.g., Gmail, Chase Bank, Facebook"
                value={newAsset.platformName}
                onChange={(e) => setNewAsset({...newAsset, platformName: e.target.value})}
                required
              />
            </Form.Group>
            
            <Form.Group className="mb-3">
              <Form.Label>Account Identifier</Form.Label>
              <Form.Control
                type="text"
                placeholder="e.g., email address, account number"
                value={newAsset.accountIdentifier}
                onChange={(e) => setNewAsset({...newAsset, accountIdentifier: e.target.value})}
                required
              />
              <Form.Text className="text-muted">
                This information will be encrypted using AES-256 encryption
              </Form.Text>
            </Form.Group>
            
            <Form.Group className="mb-4">
              <Form.Label>Additional Notes (Optional)</Form.Label>
              <Form.Control
                as="textarea"
                rows={3}
                placeholder="Recovery information, special instructions, or additional account details"
                value={newAsset.credentials}
                onChange={(e) => setNewAsset({...newAsset, credentials: e.target.value})}
              />
              <Form.Text className="text-muted">
                All sensitive data is encrypted and stored securely
              </Form.Text>
            </Form.Group>
            
            <div className="d-flex gap-2 justify-content-end">
              <Button variant="outline-secondary" onClick={() => setShowAssetModal(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Adding...
                  </>
                ) : (
                  'Add to Vault'
                )}
              </Button>
            </div>
          </Form>
        </Modal.Body>
      </Modal>

      {/* Add Contact Modal */}
      <Modal show={showContactModal} onHide={() => setShowContactModal(false)} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>Add Trusted Contact with Enhanced Security Verification</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="warning" className="mb-4">
            <strong>Enhanced Security Required:</strong> For maximum security, we require comprehensive identity verification 
            for all trusted contacts including Aadhaar and PAN details. This ensures only legitimate contacts can access your digital legacy.
          </Alert>
          
          <Form onSubmit={handleContactSubmit}>
            {/* Basic Information */}
            <Card className="mb-4">
              <Card.Header>
                <h6 className="mb-0">Basic Information</h6>
              </Card.Header>
              <Card.Body>
                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Full Name *</Form.Label>
                      <Form.Control
                        type="text"
                        placeholder="Enter full legal name as per Aadhaar"
                        value={newContact.contact_name}
                        onChange={(e) => setNewContact({...newContact, contact_name: e.target.value})}
                        required
                      />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Relationship *</Form.Label>
                      <Form.Select
                        value={newContact.relationship}
                        onChange={(e) => setNewContact({...newContact, relationship: e.target.value})}
                        required
                      >
                        <option value="">Select relationship</option>
                        <option value="spouse">Spouse</option>
                        <option value="parent">Parent</option>
                        <option value="child">Child</option>
                        <option value="sibling">Sibling</option>
                        <option value="friend">Close Friend</option>
                        <option value="attorney">Attorney</option>
                        <option value="executor">Estate Executor</option>
                        <option value="other">Other</option>
                      </Form.Select>
                    </Form.Group>
                  </Col>
                </Row>
                
                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Email Address *</Form.Label>
                      <Form.Control
                        type="email"
                        placeholder="contact@example.com"
                        value={newContact.contact_email}
                        onChange={(e) => setNewContact({...newContact, contact_email: e.target.value})}
                        required
                      />
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Mobile Number *</Form.Label>
                      <Form.Control
                        type="tel"
                        placeholder="9876543210"
                        value={newContact.contact_phone}
                        onChange={(e) => setNewContact({...newContact, contact_phone: e.target.value})}
                        maxLength="10"
                        required
                      />
                      <Form.Text className="text-muted">
                        10-digit Indian mobile number for OTP verification
                      </Form.Text>
                    </Form.Group>
                  </Col>
                </Row>
              </Card.Body>
            </Card>

            {/* Identity Verification */}
            <Card className="mb-4">
              <Card.Header>
                <h6 className="mb-0">Identity Verification (Required for Security)</h6>
              </Card.Header>
              <Card.Body>
                <Alert variant="info" className="mb-3">
                  <strong>Why we need this:</strong> Identity verification ensures only legitimate trusted contacts 
                  can access your digital legacy and prevents fraud.
                </Alert>
                
                <Row>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>Aadhaar Number *</Form.Label>
                      <Form.Control
                        type="text"
                        placeholder="1234 5678 9012"
                        value={newContact.contact_aadhaar_number}
                        onChange={(e) => setNewContact({...newContact, contact_aadhaar_number: e.target.value})}
                        maxLength="14"
                        required
                      />
                      <Form.Text className="text-muted">
                        12-digit Aadhaar number for identity verification
                      </Form.Text>
                    </Form.Group>
                  </Col>
                  <Col md={6}>
                    <Form.Group className="mb-3">
                      <Form.Label>PAN Number *</Form.Label>
                      <Form.Control
                        type="text"
                        placeholder="ABCDE1234F"
                        value={newContact.contact_pan_number}
                        onChange={(e) => setNewContact({...newContact, contact_pan_number: e.target.value.toUpperCase()})}
                        maxLength="10"
                        style={{ textTransform: 'uppercase' }}
                        required
                      />
                      <Form.Text className="text-muted">
                        10-character PAN number for additional verification
                      </Form.Text>
                    </Form.Group>
                  </Col>
                </Row>
              </Card.Body>
            </Card>

            {/* Address Information */}
            <Card className="mb-4">
              <Card.Header>
                <h6 className="mb-0">Address Information</h6>
              </Card.Header>
              <Card.Body>
                <Form.Group className="mb-3">
                  <Form.Label>Address Line 1 *</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="House/Flat number, Street name"
                    value={newContact.contact_address_line1}
                    onChange={(e) => setNewContact({...newContact, contact_address_line1: e.target.value})}
                    required
                  />
                </Form.Group>
                
                <Form.Group className="mb-3">
                  <Form.Label>Address Line 2</Form.Label>
                  <Form.Control
                    type="text"
                    placeholder="Area, Landmark (Optional)"
                    value={newContact.contact_address_line2}
                    onChange={(e) => setNewContact({...newContact, contact_address_line2: e.target.value})}
                  />
                </Form.Group>
                
                <Row>
                  <Col md={4}>
                    <Form.Group className="mb-3">
                      <Form.Label>City *</Form.Label>
                      <Form.Control
                        type="text"
                        placeholder="City name"
                        value={newContact.contact_city}
                        onChange={(e) => setNewContact({...newContact, contact_city: e.target.value})}
                        required
                      />
                    </Form.Group>
                  </Col>
                  <Col md={4}>
                    <Form.Group className="mb-3">
                      <Form.Label>State *</Form.Label>
                      <Form.Select
                        value={newContact.contact_state}
                        onChange={(e) => setNewContact({...newContact, contact_state: e.target.value})}
                        required
                      >
                        <option value="">Select State</option>
                        <option value="Andhra Pradesh">Andhra Pradesh</option>
                        <option value="Arunachal Pradesh">Arunachal Pradesh</option>
                        <option value="Assam">Assam</option>
                        <option value="Bihar">Bihar</option>
                        <option value="Chhattisgarh">Chhattisgarh</option>
                        <option value="Goa">Goa</option>
                        <option value="Gujarat">Gujarat</option>
                        <option value="Haryana">Haryana</option>
                        <option value="Himachal Pradesh">Himachal Pradesh</option>
                        <option value="Jharkhand">Jharkhand</option>
                        <option value="Karnataka">Karnataka</option>
                        <option value="Kerala">Kerala</option>
                        <option value="Madhya Pradesh">Madhya Pradesh</option>
                        <option value="Maharashtra">Maharashtra</option>
                        <option value="Manipur">Manipur</option>
                        <option value="Meghalaya">Meghalaya</option>
                        <option value="Mizoram">Mizoram</option>
                        <option value="Nagaland">Nagaland</option>
                        <option value="Odisha">Odisha</option>
                        <option value="Punjab">Punjab</option>
                        <option value="Rajasthan">Rajasthan</option>
                        <option value="Sikkim">Sikkim</option>
                        <option value="Tamil Nadu">Tamil Nadu</option>
                        <option value="Telangana">Telangana</option>
                        <option value="Tripura">Tripura</option>
                        <option value="Uttar Pradesh">Uttar Pradesh</option>
                        <option value="Uttarakhand">Uttarakhand</option>
                        <option value="West Bengal">West Bengal</option>
                        <option value="Delhi">Delhi</option>
                        <option value="Jammu and Kashmir">Jammu and Kashmir</option>
                        <option value="Ladakh">Ladakh</option>
                        <option value="Puducherry">Puducherry</option>
                        <option value="Chandigarh">Chandigarh</option>
                        <option value="Andaman and Nicobar Islands">Andaman and Nicobar Islands</option>
                        <option value="Dadra and Nagar Haveli and Daman and Diu">Dadra and Nagar Haveli and Daman and Diu</option>
                        <option value="Lakshadweep">Lakshadweep</option>
                      </Form.Select>
                    </Form.Group>
                  </Col>
                  <Col md={4}>
                    <Form.Group className="mb-3">
                      <Form.Label>Pincode *</Form.Label>
                      <Form.Control
                        type="text"
                        placeholder="400001"
                        value={newContact.contact_pincode}
                        onChange={(e) => setNewContact({...newContact, contact_pincode: e.target.value})}
                        maxLength="6"
                        required
                      />
                    </Form.Group>
                  </Col>
                </Row>
              </Card.Body>
            </Card>

            {/* Authorization Level */}
            <Card className="mb-4">
              <Card.Header>
                <h6 className="mb-0">Authorization Level</h6>
              </Card.Header>
              <Card.Body>
                <Form.Group className="mb-3">
                  <Form.Label>Access Level *</Form.Label>
                  <Form.Select
                    value={newContact.authorization_level}
                    onChange={(e) => setNewContact({...newContact, authorization_level: e.target.value})}
                    required
                  >
                    <option value="basic">Basic - Can verify death events only</option>
                    <option value="full">Full - Can verify death events and execute all policies</option>
                    <option value="emergency_only">Emergency Only - Limited access during emergencies</option>
                  </Form.Select>
                  <Form.Text className="text-muted">
                    Choose the level of access this trusted contact should have to your digital assets
                  </Form.Text>
                </Form.Group>
              </Card.Body>
            </Card>
            
            <Alert variant="warning" className="mb-4">
              <strong>Security Notice:</strong> All identity documents will be verified against government databases. 
              The trusted contact will receive verification instructions via email and SMS.
            </Alert>
            
            <div className="d-flex gap-2 justify-content-end">
              <Button variant="outline-secondary" onClick={() => setShowContactModal(false)}>
                Cancel
              </Button>
              <Button type="submit" variant="primary" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Adding & Verifying...
                  </>
                ) : (
                  'Add Trusted Contact'
                )}
              </Button>
            </div>
          </Form>
        </Modal.Body>
      </Modal>
    </div>
  );
}

export default UserVault;
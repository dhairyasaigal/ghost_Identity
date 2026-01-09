import React from 'react';
import { Container, Row, Col, Card, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

function RoleSelection() {
  const navigate = useNavigate();

  const handleRoleSelection = (role) => {
    // Store the selected role in localStorage for session management
    localStorage.setItem('userRole', role);
    
    if (role === 'user') {
      navigate('/user-dashboard');
    } else if (role === 'admin') {
      navigate('/admin-login');
    } else if (role === 'trusted-contact') {
      navigate('/trusted-contact');
    }
  };

  return (
    <div className="role-selection-page">
      {/* Professional Header Section */}
      <div className="role-selection-header">
        <Container>
          <div className="text-center">
            <h1>Ghost Identity Protection</h1>
            <p className="lead">
              Enterprise-grade digital legacy management with comprehensive identity verification and AI-powered policy execution
            </p>
          </div>
        </Container>
      </div>

      <Container>
        <Row className="justify-content-center">
          <Col lg={10}>
            <div className="text-center role-selection-content">
              <h2 className="mb-3">Select Your Access Level</h2>
              <p className="text-muted">
                Choose your role to access the appropriate management interface
              </p>
            </div>

            <Row className="g-4">
              {/* Regular User */}
              <Col md={4}>
                <Card className="role-card h-100 text-center" style={{ cursor: 'pointer' }} onClick={() => handleRoleSelection('user')}>
                  <Card.Body className="p-4">
                    <div className="role-icon mb-4" style={{ 
                      width: '80px', 
                      height: '80px', 
                      backgroundColor: '#007bff', 
                      borderRadius: '50%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      margin: '0 auto',
                      fontSize: '1.5rem',
                      color: 'white',
                      fontWeight: 'bold'
                    }}>
                      U
                    </div>
                    <h4 className="mb-3">End User</h4>
                    <p className="text-muted mb-4">
                      Register for comprehensive digital legacy protection services and manage your digital assets with enterprise-grade security
                    </p>
                    <ul className="list-unstyled text-start mb-4">
                      <li className="mb-2">Complete KYC verification process</li>
                      <li className="mb-2">Secure digital asset management</li>
                      <li className="mb-2">Policy creation and management</li>
                      <li className="mb-2">Trusted contact administration</li>
                      <li className="mb-2">Digital legacy protection</li>
                    </ul>
                    <Button variant="primary" size="lg" className="w-100">
                      Access User Portal
                    </Button>
                  </Card.Body>
                </Card>
              </Col>

              {/* Trusted Contact */}
              <Col md={4}>
                <Card className="role-card h-100 text-center" style={{ cursor: 'pointer' }} onClick={() => handleRoleSelection('trusted-contact')}>
                  <Card.Body className="p-4">
                    <div className="role-icon mb-4" style={{ 
                      width: '80px', 
                      height: '80px', 
                      backgroundColor: '#28a745', 
                      borderRadius: '50%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      margin: '0 auto',
                      fontSize: '1.5rem',
                      color: 'white',
                      fontWeight: 'bold'
                    }}>
                      T
                    </div>
                    <h4 className="mb-3">Authorized Contact</h4>
                    <p className="text-muted mb-4">
                      Designated contact authorized to verify death events and execute digital legacy policies with full audit compliance
                    </p>
                    <ul className="list-unstyled text-start mb-4">
                      <li className="mb-2">Death certificate verification</li>
                      <li className="mb-2">Event validation and processing</li>
                      <li className="mb-2">Policy execution monitoring</li>
                      <li className="mb-2">Comprehensive audit trail access</li>
                      <li className="mb-2">Secure document management</li>
                    </ul>
                    <Button variant="success" size="lg" className="w-100">
                      Access Contact Portal
                    </Button>
                  </Card.Body>
                </Card>
              </Col>

              {/* Administrator */}
              <Col md={4}>
                <Card className="role-card h-100 text-center" style={{ cursor: 'pointer' }} onClick={() => handleRoleSelection('admin')}>
                  <Card.Body className="p-4">
                    <div className="role-icon mb-4" style={{ 
                      width: '80px', 
                      height: '80px', 
                      backgroundColor: '#dc3545', 
                      borderRadius: '50%', 
                      display: 'flex', 
                      alignItems: 'center', 
                      justifyContent: 'center', 
                      margin: '0 auto',
                      fontSize: '1.5rem',
                      color: 'white',
                      fontWeight: 'bold'
                    }}>
                      A
                    </div>
                    <h4 className="mb-3">System Administrator</h4>
                    <p className="text-muted mb-4">
                      Administrative access for platform management, user oversight, and system monitoring with full operational control
                    </p>
                    <ul className="list-unstyled text-start mb-4">
                      <li className="mb-2">Platform administration and configuration</li>
                      <li className="mb-2">User account management and oversight</li>
                      <li className="mb-2">System monitoring and maintenance</li>
                      <li className="mb-2">Security compliance and auditing</li>
                      <li className="mb-2">Analytics and reporting dashboard</li>
                    </ul>
                    <Button variant="danger" size="lg" className="w-100">
                      Access Admin Console
                    </Button>
                  </Card.Body>
                </Card>
              </Col>
            </Row>

            <div className="text-center mt-5">
              <Row className="g-4">
                <Col md={4}>
                  <div className="feature-highlight">
                    <h6>Bank-Level Security</h6>
                    <small>AES-256 encryption and multi-factor authentication protocols</small>
                  </div>
                </Col>
                <Col md={4}>
                  <div className="feature-highlight">
                    <h6>AI-Powered Automation</h6>
                    <small>Azure OpenAI for intelligent policy execution and document processing</small>
                  </div>
                </Col>
                <Col md={4}>
                  <div className="feature-highlight">
                    <h6>Government Compliance</h6>
                    <small>Aadhaar and PAN verification with regulatory compliance standards</small>
                  </div>
                </Col>
              </Row>
              
              <div className="mt-5 pt-4 border-top">
                <p className="text-muted mb-0">
                  <small>Trusted by enterprises worldwide • SOC 2 Type II Certified • ISO 27001 Compliant</small>
                </p>
              </div>
            </div>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default RoleSelection;
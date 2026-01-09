import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Button, Alert, Badge, ProgressBar } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

function UserDashboard() {
  const navigate = useNavigate();
  const [userStats, setUserStats] = useState({
    totalAssets: 0,
    trustedContacts: 0,
    activePolicies: 0,
    verificationStatus: 'pending'
  });

  useEffect(() => {
    // Check if user role is set
    const userRole = localStorage.getItem('userRole');
    if (userRole !== 'user') {
      navigate('/');
      return;
    }

    // Load user statistics (mock data for now)
    setUserStats({
      totalAssets: 3,
      trustedContacts: 2,
      activePolicies: 5,
      verificationStatus: 'verified'
    });
  }, [navigate]);

  const handleGetStarted = () => {
    navigate('/register');
  };

  const handleLogin = () => {
    navigate('/login');
  };

  return (
    <div className="fade-in">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="mb-2">Welcome to Ghost Identity Protection</h2>
          <p className="text-muted mb-0">
            Secure your digital legacy with comprehensive identity verification and AI-powered policy execution
          </p>
        </div>
        <div className="d-flex gap-2">
          <Button variant="outline-primary" onClick={handleLogin}>
            Sign In
          </Button>
          <Button variant="primary" onClick={handleGetStarted}>
            Get Started
          </Button>
        </div>
      </div>

      {/* Hero Section */}
      <Card className="dashboard-card mb-4" style={{ background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)', color: 'white' }}>
        <Card.Body className="p-5">
          <Row className="align-items-center">
            <Col lg={8}>
              <h1 className="display-5 mb-3">Protect Your Digital Legacy</h1>
              <p className="lead mb-4">
                Ensure your digital assets are handled according to your wishes with our AI-powered 
                digital legacy management platform. Complete with government-grade identity verification.
              </p>
              <div className="d-flex gap-3">
                <Button variant="light" size="lg" onClick={handleGetStarted}>
                  Start Registration
                </Button>
                <Button variant="outline-light" size="lg" onClick={handleLogin}>
                  Existing User? Sign In
                </Button>
              </div>
            </Col>
            <Col lg={4} className="text-center">
              <div style={{ fontSize: '6rem', opacity: 0.3 }}>🛡️</div>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Features Grid */}
      <Row className="g-4 mb-4">
        <Col md={4}>
          <Card className="dashboard-card h-100">
            <Card.Body className="text-center p-4">
              <div className="feature-icon mx-auto mb-3" style={{ backgroundColor: '#007bff' }}>🔐</div>
              <h5 className="mb-3">Enhanced KYC Verification</h5>
              <p className="text-muted mb-3">
                Complete identity verification using Aadhaar and PAN cards with government database validation
              </p>
              <ul className="list-unstyled text-start">
                <li>✓ Aadhaar number verification</li>
                <li>✓ PAN card validation</li>
                <li>✓ Multi-factor authentication</li>
                <li>✓ Biometric security</li>
              </ul>
            </Card.Body>
          </Card>
        </Col>

        <Col md={4}>
          <Card className="dashboard-card h-100">
            <Card.Body className="text-center p-4">
              <div className="feature-icon mx-auto mb-3" style={{ backgroundColor: '#28a745' }}>🤖</div>
              <h5 className="mb-3">AI-Powered Execution</h5>
              <p className="text-muted mb-3">
                Azure OpenAI interprets your policies and generates platform-specific notifications automatically
              </p>
              <ul className="list-unstyled text-start">
                <li>✓ Natural language processing</li>
                <li>✓ Smart policy interpretation</li>
                <li>✓ Automated notifications</li>
                <li>✓ Platform integration</li>
              </ul>
            </Card.Body>
          </Card>
        </Col>

        <Col md={4}>
          <Card className="dashboard-card h-100">
            <Card.Body className="text-center p-4">
              <div className="feature-icon mx-auto mb-3" style={{ backgroundColor: '#ffc107' }}>👥</div>
              <h5 className="mb-3">Trusted Contact Network</h5>
              <p className="text-muted mb-3">
                Secure verification system with enhanced identity checks for all trusted contacts
              </p>
              <ul className="list-unstyled text-start">
                <li>✓ Enhanced security verification</li>
                <li>✓ Background checks</li>
                <li>✓ Document verification</li>
                <li>✓ Authorization levels</li>
              </ul>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* How It Works */}
      <Card className="dashboard-card mb-4">
        <Card.Header>
          <h5 className="mb-0">How Ghost Identity Protection Works</h5>
        </Card.Header>
        <Card.Body>
          <Row className="g-4">
            <Col md={3} className="text-center">
              <div className="step-number mx-auto mb-3">1</div>
              <h6>Register & Verify</h6>
              <p className="text-muted small">
                Complete KYC verification with Aadhaar and PAN details for maximum security
              </p>
            </Col>
            <Col md={3} className="text-center">
              <div className="step-number mx-auto mb-3">2</div>
              <h6>Add Digital Assets</h6>
              <p className="text-muted small">
                Securely store information about your email accounts, social media, and financial assets
              </p>
            </Col>
            <Col md={3} className="text-center">
              <div className="step-number mx-auto mb-3">3</div>
              <h6>Create Policies</h6>
              <p className="text-muted small">
                Define what should happen to each asset using natural language instructions
              </p>
            </Col>
            <Col md={3} className="text-center">
              <div className="step-number mx-auto mb-3">4</div>
              <h6>AI Execution</h6>
              <p className="text-muted small">
                When needed, AI interprets your policies and executes them automatically
              </p>
            </Col>
          </Row>
        </Card.Body>
      </Card>

      {/* Security Features */}
      <Row className="g-4 mb-4">
        <Col lg={6}>
          <Card className="dashboard-card h-100">
            <Card.Header>
              <h6 className="mb-0">🔒 Security Features</h6>
            </Card.Header>
            <Card.Body>
              <div className="d-flex flex-column gap-3">
                <div className="d-flex align-items-center">
                  <Badge bg="success" className="me-3">✓</Badge>
                  <div>
                    <strong>AES-256 Encryption</strong><br />
                    <small className="text-muted">Military-grade encryption for all sensitive data</small>
                  </div>
                </div>
                <div className="d-flex align-items-center">
                  <Badge bg="success" className="me-3">✓</Badge>
                  <div>
                    <strong>Government Database Verification</strong><br />
                    <small className="text-muted">Real-time verification against UIDAI and Income Tax databases</small>
                  </div>
                </div>
                <div className="d-flex align-items-center">
                  <Badge bg="success" className="me-3">✓</Badge>
                  <div>
                    <strong>Multi-Factor Authentication</strong><br />
                    <small className="text-muted">SMS, email, and TOTP-based authentication</small>
                  </div>
                </div>
                <div className="d-flex align-items-center">
                  <Badge bg="success" className="me-3">✓</Badge>
                  <div>
                    <strong>Audit Trail</strong><br />
                    <small className="text-muted">Complete logging of all actions and access attempts</small>
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col lg={6}>
          <Card className="dashboard-card h-100">
            <Card.Header>
              <h6 className="mb-0">🤖 AI Capabilities</h6>
            </Card.Header>
            <Card.Body>
              <div className="d-flex flex-column gap-3">
                <div className="d-flex align-items-center">
                  <Badge bg="primary" className="me-3">AI</Badge>
                  <div>
                    <strong>Natural Language Processing</strong><br />
                    <small className="text-muted">Understands your policies written in plain English</small>
                  </div>
                </div>
                <div className="d-flex align-items-center">
                  <Badge bg="primary" className="me-3">AI</Badge>
                  <div>
                    <strong>Platform Integration</strong><br />
                    <small className="text-muted">Generates appropriate notifications for each platform</small>
                  </div>
                </div>
                <div className="d-flex align-items-center">
                  <Badge bg="primary" className="me-3">AI</Badge>
                  <div>
                    <strong>Document Analysis</strong><br />
                    <small className="text-muted">Azure AI Vision processes death certificates automatically</small>
                  </div>
                </div>
                <div className="d-flex align-items-center">
                  <Badge bg="primary" className="me-3">AI</Badge>
                  <div>
                    <strong>Smart Execution</strong><br />
                    <small className="text-muted">Intelligent policy execution with confidence scoring</small>
                  </div>
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Call to Action */}
      <Card className="dashboard-card text-center">
        <Card.Body className="p-5">
          <h3 className="mb-3">Ready to Secure Your Digital Legacy?</h3>
          <p className="lead text-muted mb-4">
            Join thousands of users who trust Ghost Identity Protection to manage their digital assets securely
          </p>
          <div className="d-flex justify-content-center gap-3">
            <Button variant="primary" size="lg" onClick={handleGetStarted}>
              Start Your Registration
            </Button>
            <Button variant="outline-primary" size="lg" onClick={handleLogin}>
              Sign In to Your Account
            </Button>
          </div>
        </Card.Body>
      </Card>
    </div>
  );
}

export default UserDashboard;
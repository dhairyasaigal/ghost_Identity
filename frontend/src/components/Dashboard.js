import React from 'react';
import { Row, Col, Card, Button, Container } from 'react-bootstrap';

function Dashboard() {
  return (
    <div className="fade-in">
      {/* Hero Section */}
      <div className="dashboard-hero">
        <Container>
          <div className="text-center">
            <h1>Ghost Identity Protection</h1>
            <p className="lead">
              Enterprise-grade digital legacy management with AI-powered automation and comprehensive security
            </p>
          </div>
        </Container>
      </div>

      {/* Main Features Grid */}
      <Container className="py-4">
        <div className="feature-grid">
          <div className="feature-card">
            <div className="feature-icon">AP</div>
            <h3 className="feature-title">Action Policies</h3>
            <p className="feature-description">
              Create intelligent policies using natural language to define exactly how your digital assets should be handled. 
              Our AI interprets your requirements and executes them automatically with full audit trails.
            </p>
            <Button variant="primary" href="/policies" className="mt-3">
              Manage Policies
            </Button>
          </div>

          <div className="feature-card">
            <div className="feature-icon">TC</div>
            <h3 className="feature-title">Trusted Contacts</h3>
            <p className="feature-description">
              Designate authorized individuals who can verify death events and oversee policy execution. 
              Multi-factor authentication and role-based access ensure complete security.
            </p>
            <Button variant="primary" href="/trusted-contact" className="mt-3">
              Contact Portal
            </Button>
          </div>

          <div className="feature-card">
            <div className="feature-icon">DV</div>
            <h3 className="feature-title">Digital Vault</h3>
            <p className="feature-description">
              Securely register and encrypt your digital assets including email accounts, financial accounts, 
              and social media profiles. Industry-standard AES-256 encryption protects all data.
            </p>
            <Button variant="outline-primary" href="/vault" className="mt-3">
              Manage Vault
            </Button>
          </div>

          <div className="feature-card">
            <div className="feature-icon">AI</div>
            <h3 className="feature-title">AI Administration</h3>
            <p className="feature-description">
              Monitor Azure AI services, view comprehensive audit logs, and track policy execution results. 
              Complete transparency and compliance reporting for all system operations.
            </p>
            <Button variant="outline-primary" href="/admin" className="mt-3">
              Admin Dashboard
            </Button>
          </div>
        </div>

        {/* Statistics Section */}
        <div className="stats-grid">
          <div className="stat-card">
            <div className="stat-number">256-bit</div>
            <div className="stat-label">Encryption</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">99.9%</div>
            <div className="stat-label">Uptime SLA</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">24/7</div>
            <div className="stat-label">Monitoring</div>
          </div>
          <div className="stat-card">
            <div className="stat-number">SOC 2</div>
            <div className="stat-label">Compliant</div>
          </div>
        </div>

        {/* Process Overview */}
        <Row className="mt-5">
          <Col>
            <Card className="dashboard-card">
              <Card.Body>
                <h3 className="text-center mb-4">How It Works</h3>
                <Row>
                  <Col md={3} className="text-center mb-4">
                    <div className="feature-icon mx-auto mb-3">1</div>
                    <h5>Register Assets</h5>
                    <p className="text-muted">
                      Add digital accounts to the encrypted vault with multi-factor authentication protection.
                    </p>
                  </Col>
                  <Col md={3} className="text-center mb-4">
                    <div className="feature-icon mx-auto mb-3">2</div>
                    <h5>Create Policies</h5>
                    <p className="text-muted">
                      Define natural language policies specifying delete, memorialize, transfer, or lock actions.
                    </p>
                  </Col>
                  <Col md={3} className="text-center mb-4">
                    <div className="feature-icon mx-auto mb-3">3</div>
                    <h5>Add Contacts</h5>
                    <p className="text-muted">
                      Designate trusted contacts who can verify death events with proper authorization.
                    </p>
                  </Col>
                  <Col md={3} className="text-center mb-4">
                    <div className="feature-icon mx-auto mb-3">4</div>
                    <h5>AI Execution</h5>
                    <p className="text-muted">
                      Azure AI services automatically process certificates and execute digital legacy policies.
                    </p>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Technology Integration */}
        <Row className="mt-4">
          <Col>
            <Card className="dashboard-card">
              <Card.Body>
                <h3 className="text-center mb-4">Powered by Microsoft Azure AI</h3>
                <Row>
                  <Col md={4} className="text-center mb-4">
                    <div className="feature-icon mx-auto mb-3">AV</div>
                    <h5>Azure AI Vision</h5>
                    <p className="text-muted">
                      Advanced OCR technology processes and verifies death certificates with high accuracy and confidence scoring.
                    </p>
                  </Col>
                  <Col md={4} className="text-center mb-4">
                    <div className="feature-icon mx-auto mb-3">AI</div>
                    <h5>Azure OpenAI</h5>
                    <p className="text-muted">
                      Natural language processing interprets policies and generates professional platform notifications.
                    </p>
                  </Col>
                  <Col md={4} className="text-center mb-4">
                    <div className="feature-icon mx-auto mb-3">ES</div>
                    <h5>Enterprise Security</h5>
                    <p className="text-muted">
                      Bank-level encryption, comprehensive audit logging, and compliance with industry security standards.
                    </p>
                  </Col>
                </Row>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Call to Action */}
        <Row className="mt-4">
          <Col className="text-center">
            <Card className="dashboard-card">
              <Card.Body className="py-4">
                <h3 className="mb-3">Ready to Secure Your Digital Legacy?</h3>
                <p className="text-muted mb-4">
                  Start by registering your digital assets and creating your first action policy.
                </p>
                <div className="d-flex gap-3 justify-content-center flex-wrap">
                  <Button variant="primary" size="lg" href="/vault">
                    Get Started
                  </Button>
                  <Button variant="outline-primary" size="lg" href="/admin">
                    View Demo
                  </Button>
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default Dashboard;
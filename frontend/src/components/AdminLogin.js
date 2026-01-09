import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';

function AdminLogin() {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState({
    username: '',
    password: '',
    adminKey: ''
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setCredentials(prev => ({
      ...prev,
      [name]: value
    }));
    setError('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      // Mock admin authentication - in production, this would call the backend
      if (credentials.username === 'admin' && 
          credentials.password === 'admin123' && 
          credentials.adminKey === 'GHOST_ADMIN_2024') {
        
        // Store admin session
        localStorage.setItem('userRole', 'admin');
        localStorage.setItem('adminAuthenticated', 'true');
        
        navigate('/admin');
      } else {
        setError('Invalid administrator credentials. Please check your username, password, and admin key.');
      }
    } catch (err) {
      setError('Authentication failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToRoleSelection = () => {
    localStorage.removeItem('userRole');
    navigate('/');
  };

  return (
    <div className="admin-login-page" style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
      <Container className="py-5">
        <Row className="justify-content-center">
          <Col lg={5} md={7}>
            <div className="text-center mb-4">
              <Button 
                variant="outline-secondary" 
                size="sm" 
                onClick={handleBackToRoleSelection}
                className="mb-3"
              >
                ← Back to Role Selection
              </Button>
              <h2 className="mb-2">Administrator Login</h2>
              <p className="text-muted">
                Secure access to Ghost Identity Protection administration panel
              </p>
            </div>

            <Card className="shadow">
              <Card.Body className="p-4">
                <Alert variant="warning" className="mb-4">
                  <div className="d-flex align-items-center">
                    <div className="me-3" style={{ fontSize: '1.5rem' }}>⚠️</div>
                    <div>
                      <strong>Restricted Access:</strong> This area is for authorized administrators only. 
                      All access attempts are logged and monitored.
                    </div>
                  </div>
                </Alert>

                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-3">
                    <Form.Label>Administrator Username</Form.Label>
                    <Form.Control
                      type="text"
                      name="username"
                      value={credentials.username}
                      onChange={handleInputChange}
                      placeholder="Enter admin username"
                      required
                    />
                  </Form.Group>

                  <Form.Group className="mb-3">
                    <Form.Label>Password</Form.Label>
                    <Form.Control
                      type="password"
                      name="password"
                      value={credentials.password}
                      onChange={handleInputChange}
                      placeholder="Enter admin password"
                      required
                    />
                  </Form.Group>

                  <Form.Group className="mb-4">
                    <Form.Label>Admin Access Key</Form.Label>
                    <Form.Control
                      type="password"
                      name="adminKey"
                      value={credentials.adminKey}
                      onChange={handleInputChange}
                      placeholder="Enter admin access key"
                      required
                    />
                    <Form.Text className="text-muted">
                      Special access key required for administrator authentication
                    </Form.Text>
                  </Form.Group>

                  {error && (
                    <Alert variant="danger" className="mb-3">
                      {error}
                    </Alert>
                  )}

                  <div className="d-grid">
                    <Button 
                      type="submit" 
                      variant="danger" 
                      size="lg"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2"></span>
                          Authenticating...
                        </>
                      ) : (
                        'Access Admin Panel'
                      )}
                    </Button>
                  </div>
                </Form>

                <div className="text-center mt-4">
                  <small className="text-muted">
                    For demo purposes:<br />
                    Username: <code>admin</code><br />
                    Password: <code>admin123</code><br />
                    Admin Key: <code>GHOST_ADMIN_2024</code>
                  </small>
                </div>
              </Card.Body>
            </Card>

            <div className="text-center mt-4">
              <div className="row">
                <div className="col-4">
                  <div className="text-center">
                    <div style={{ fontSize: '2rem' }}>🔐</div>
                    <small className="text-muted">Secure Access</small>
                  </div>
                </div>
                <div className="col-4">
                  <div className="text-center">
                    <div style={{ fontSize: '2rem' }}>📊</div>
                    <small className="text-muted">System Monitoring</small>
                  </div>
                </div>
                <div className="col-4">
                  <div className="text-center">
                    <div style={{ fontSize: '2rem' }}>⚙️</div>
                    <small className="text-muted">Platform Management</small>
                  </div>
                </div>
              </div>
            </div>
          </Col>
        </Row>
      </Container>
    </div>
  );
}

export default AdminLogin;
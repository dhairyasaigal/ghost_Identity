import React, { useState } from 'react';
import { Container, Row, Col, Card, Form, Button, Alert } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import apiService from '../services/api';

function UserLogin() {
  const navigate = useNavigate();
  const [credentials, setCredentials] = useState({
    login_id: '',
    password: ''
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
      const response = await apiService.login(credentials);
      
      // Store user session
      localStorage.setItem('userRole', 'user');
      localStorage.setItem('userAuthenticated', 'true');
      localStorage.setItem('userId', response.user.user_id);
      
      // Navigate to user vault
      navigate('/vault');
    } catch (err) {
      setError(err.data?.error || 'Login failed. Please check your credentials.');
    } finally {
      setLoading(false);
    }
  };

  const handleBackToRoleSelection = () => {
    localStorage.removeItem('userRole');
    navigate('/');
  };

  const handleRegister = () => {
    navigate('/register');
  };

  return (
    <div className="user-login-page" style={{ minHeight: '100vh', backgroundColor: '#f8f9fa' }}>
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
              <h2 className="mb-2">User Sign In</h2>
              <p className="text-muted">
                Access your Ghost Identity Protection account
              </p>
            </div>

            <Card className="shadow">
              <Card.Body className="p-4">
                <Form onSubmit={handleSubmit}>
                  <Form.Group className="mb-3">
                    <Form.Label>Email or Phone Number</Form.Label>
                    <Form.Control
                      type="text"
                      name="login_id"
                      value={credentials.login_id}
                      onChange={handleInputChange}
                      placeholder="Enter your email or phone number"
                      required
                    />
                    <Form.Text className="text-muted">
                      Use the email or phone number you registered with
                    </Form.Text>
                  </Form.Group>

                  <Form.Group className="mb-4">
                    <Form.Label>Password</Form.Label>
                    <Form.Control
                      type="password"
                      name="password"
                      value={credentials.password}
                      onChange={handleInputChange}
                      placeholder="Enter your password"
                      required
                    />
                  </Form.Group>

                  {error && (
                    <Alert variant="danger" className="mb-3">
                      {error}
                    </Alert>
                  )}

                  <div className="d-grid mb-3">
                    <Button 
                      type="submit" 
                      variant="primary" 
                      size="lg"
                      disabled={loading}
                    >
                      {loading ? (
                        <>
                          <span className="spinner-border spinner-border-sm me-2"></span>
                          Signing In...
                        </>
                      ) : (
                        'Sign In'
                      )}
                    </Button>
                  </div>

                  <div className="text-center">
                    <span className="text-muted">Don't have an account? </span>
                    <Button variant="link" className="p-0" onClick={handleRegister}>
                      Register here
                    </Button>
                  </div>
                </Form>
              </Card.Body>
            </Card>

            <Alert variant="info" className="mt-4">
              <div className="d-flex align-items-center">
                <div className="me-3" style={{ fontSize: '1.5rem' }}>🔒</div>
                <div>
                  <strong>Secure Login:</strong> Your credentials are protected with bank-level security. 
                  Multi-factor authentication may be required for sensitive operations.
                </div>
              </div>
            </Alert>

            <div className="text-center mt-4">
              <div className="row">
                <div className="col-4">
                  <div className="text-center">
                    <div style={{ fontSize: '2rem' }}>🛡️</div>
                    <small className="text-muted">Secure Access</small>
                  </div>
                </div>
                <div className="col-4">
                  <div className="text-center">
                    <div style={{ fontSize: '2rem' }}>🔐</div>
                    <small className="text-muted">Encrypted Data</small>
                  </div>
                </div>
                <div className="col-4">
                  <div className="text-center">
                    <div style={{ fontSize: '2rem' }}>✅</div>
                    <small className="text-muted">KYC Verified</small>
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

export default UserLogin;
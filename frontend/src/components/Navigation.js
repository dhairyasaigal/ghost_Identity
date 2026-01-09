import React, { useState, useEffect } from 'react';
import { Navbar, Nav, Container, Button } from 'react-bootstrap';
import { LinkContainer } from 'react-router-bootstrap';
import { useLocation, useNavigate } from 'react-router-dom';

function Navigation() {
  const location = useLocation();
  const navigate = useNavigate();
  const [userRole, setUserRole] = useState(null);

  useEffect(() => {
    const role = localStorage.getItem('userRole');
    setUserRole(role);
  }, [location]);

  const handleLogout = () => {
    localStorage.removeItem('userRole');
    localStorage.removeItem('userAuthenticated');
    localStorage.removeItem('adminAuthenticated');
    localStorage.removeItem('userId');
    navigate('/');
  };

  const handleRoleSwitch = () => {
    localStorage.removeItem('userRole');
    localStorage.removeItem('userAuthenticated');
    localStorage.removeItem('adminAuthenticated');
    localStorage.removeItem('userId');
    navigate('/');
  };

  // Don't show navigation on role selection page
  if (location.pathname === '/' || location.pathname === '/admin-login' || location.pathname === '/login') {
    return null;
  }

  return (
    <Navbar expand="lg" className="navbar">
      <Container>
        <Navbar.Brand href="/">
          Ghost Identity Protection
          {userRole && (
            <span className="badge bg-secondary ms-2" style={{ fontSize: '0.6rem' }}>
              {userRole === 'admin' ? 'ADMIN' : userRole === 'trusted-contact' ? 'TRUSTED CONTACT' : 'USER'}
            </span>
          )}
        </Navbar.Brand>
        <Navbar.Toggle aria-controls="basic-navbar-nav" />
        <Navbar.Collapse id="basic-navbar-nav">
          <Nav className="ms-auto">
            {userRole === 'user' && (
              <>
                <LinkContainer to="/user-dashboard">
                  <Nav.Link className={location.pathname === '/user-dashboard' ? 'active' : ''}>
                    Dashboard
                  </Nav.Link>
                </LinkContainer>
                <LinkContainer to="/register">
                  <Nav.Link className={location.pathname === '/register' ? 'active' : ''}>
                    Register
                  </Nav.Link>
                </LinkContainer>
                <LinkContainer to="/vault">
                  <Nav.Link className={location.pathname === '/vault' ? 'active' : ''}>
                    Digital Vault
                  </Nav.Link>
                </LinkContainer>
                <LinkContainer to="/policies">
                  <Nav.Link className={location.pathname === '/policies' ? 'active' : ''}>
                    Action Policies
                  </Nav.Link>
                </LinkContainer>
              </>
            )}
            
            {userRole === 'trusted-contact' && (
              <LinkContainer to="/trusted-contact">
                <Nav.Link className={location.pathname === '/trusted-contact' ? 'active' : ''}>
                  Verification Portal
                </Nav.Link>
              </LinkContainer>
            )}
            
            {userRole === 'admin' && (
              <LinkContainer to="/admin">
                <Nav.Link className={location.pathname === '/admin' ? 'active' : ''}>
                  Administration
                </Nav.Link>
              </LinkContainer>
            )}

            {userRole && (
              <Nav.Item className="d-flex align-items-center ms-3">
                <Button variant="outline-secondary" size="sm" onClick={handleRoleSwitch} className="me-2">
                  Switch Role
                </Button>
                <Button variant="outline-danger" size="sm" onClick={handleLogout}>
                  Logout
                </Button>
              </Nav.Item>
            )}
          </Nav>
        </Navbar.Collapse>
      </Container>
    </Navbar>
  );
}

export default Navigation;
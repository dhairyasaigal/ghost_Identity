import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Container } from 'react-bootstrap';
import Navigation from './components/Navigation';
import RoleSelection from './components/RoleSelection';
import UserDashboard from './components/UserDashboard';
import UserLogin from './components/UserLogin';
import AdminLogin from './components/AdminLogin';
import Dashboard from './components/Dashboard';
import UserVault from './components/UserVault';
import ActionPolicies from './components/ActionPolicies';
import TrustedContactPortal from './components/TrustedContactPortal';
import AdminView from './components/AdminView';
import Registration from './components/Registration';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <div className="main-content">
          <Navigation />
          <Container className="py-4">
            <Routes>
              {/* Role Selection - Landing Page */}
              <Route path="/" element={<RoleSelection />} />
              
              {/* User Routes */}
              <Route path="/user-dashboard" element={<UserDashboard />} />
              <Route path="/login" element={<UserLogin />} />
              <Route path="/register" element={<Registration />} />
              <Route path="/vault" element={<UserVault />} />
              <Route path="/policies" element={<ActionPolicies />} />
              
              {/* Trusted Contact Routes */}
              <Route path="/trusted-contact" element={<TrustedContactPortal />} />
              
              {/* Admin Routes */}
              <Route path="/admin-login" element={<AdminLogin />} />
              <Route path="/admin" element={<AdminView />} />
              
              {/* Legacy Routes (for backward compatibility) */}
              <Route path="/dashboard" element={<Dashboard />} />
            </Routes>
          </Container>
        </div>
      </div>
    </Router>
  );
}

export default App;
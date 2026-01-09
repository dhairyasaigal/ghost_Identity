import React, { useState } from 'react';
import { Row, Col, Card, Form, Button, Alert, ProgressBar, Modal } from 'react-bootstrap';
import apiService from '../services/api';

function Registration() {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    // Basic Information
    email: '',
    password: '',
    confirmPassword: '',
    phone_number: '',
    full_name: '',
    date_of_birth: '',
    
    // Identity Documents
    aadhaar_number: '',
    pan_number: '',
    
    // Address Information
    address_line1: '',
    address_line2: '',
    city: '',
    state: '',
    pincode: ''
  });
  
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const [registrationResult, setRegistrationResult] = useState(null);
  const [showOTPModal, setShowOTPModal] = useState(false);
  const [otpData, setOtpData] = useState({
    phone_otp: '',
    email_otp: '',
    user_id: ''
  });
  const [verificationStatus, setVerificationStatus] = useState({
    phone_verified: false,
    email_verified: false
  });

  const indianStates = [
    'Andhra Pradesh', 'Arunachal Pradesh', 'Assam', 'Bihar', 'Chhattisgarh',
    'Goa', 'Gujarat', 'Haryana', 'Himachal Pradesh', 'Jharkhand', 'Karnataka',
    'Kerala', 'Madhya Pradesh', 'Maharashtra', 'Manipur', 'Meghalaya', 'Mizoram',
    'Nagaland', 'Odisha', 'Punjab', 'Rajasthan', 'Sikkim', 'Tamil Nadu',
    'Telangana', 'Tripura', 'Uttar Pradesh', 'Uttarakhand', 'West Bengal',
    'Delhi', 'Jammu and Kashmir', 'Ladakh', 'Puducherry', 'Chandigarh',
    'Andaman and Nicobar Islands', 'Dadra and Nagar Haveli and Daman and Diu',
    'Lakshadweep'
  ];

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({
        ...prev,
        [name]: ''
      }));
    }
  };

  const validateStep = (step) => {
    const newErrors = {};
    
    if (step === 1) {
      // Basic Information Validation
      if (!formData.full_name.trim()) {
        newErrors.full_name = 'Full name is required';
      }
      
      if (!formData.email.trim()) {
        newErrors.email = 'Email is required';
      } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(formData.email)) {
        newErrors.email = 'Invalid email format';
      }
      
      if (!formData.phone_number.trim()) {
        newErrors.phone_number = 'Phone number is required';
      } else if (!/^[6-9]\d{9}$/.test(formData.phone_number.replace(/[\s\-\+]/g, ''))) {
        newErrors.phone_number = 'Invalid Indian mobile number';
      }
      
      if (!formData.date_of_birth) {
        newErrors.date_of_birth = 'Date of birth is required';
      }
      
      if (!formData.password) {
        newErrors.password = 'Password is required';
      } else if (formData.password.length < 8) {
        newErrors.password = 'Password must be at least 8 characters';
      }
      
      if (formData.password !== formData.confirmPassword) {
        newErrors.confirmPassword = 'Passwords do not match';
      }
    }
    
    if (step === 2) {
      // Identity Documents Validation
      if (!formData.aadhaar_number.trim()) {
        newErrors.aadhaar_number = 'Aadhaar number is required';
      } else {
        const aadhaar = formData.aadhaar_number.replace(/[\s\-]/g, '');
        if (!/^[2-9]{1}[0-9]{3}[0-9]{4}[0-9]{4}$/.test(aadhaar)) {
          newErrors.aadhaar_number = 'Invalid Aadhaar number format';
        }
      }
      
      if (!formData.pan_number.trim()) {
        newErrors.pan_number = 'PAN number is required';
      } else if (!/^[A-Z]{5}[0-9]{4}[A-Z]{1}$/.test(formData.pan_number.toUpperCase())) {
        newErrors.pan_number = 'Invalid PAN number format (ABCDE1234F)';
      }
    }
    
    if (step === 3) {
      // Address Information Validation
      if (!formData.address_line1.trim()) {
        newErrors.address_line1 = 'Address line 1 is required';
      }
      
      if (!formData.city.trim()) {
        newErrors.city = 'City is required';
      }
      
      if (!formData.state) {
        newErrors.state = 'State is required';
      }
      
      if (!formData.pincode.trim()) {
        newErrors.pincode = 'Pincode is required';
      } else if (!/^[1-9][0-9]{5}$/.test(formData.pincode)) {
        newErrors.pincode = 'Invalid pincode format';
      }
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(currentStep)) {
      setCurrentStep(prev => prev + 1);
    }
  };

  const handlePrevious = () => {
    setCurrentStep(prev => prev - 1);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!validateStep(3)) {
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await apiService.register(formData);
      setRegistrationResult(response);
      setOtpData(prev => ({
        ...prev,
        user_id: response.user_id
      }));
      setShowOTPModal(true);
    } catch (error) {
      setErrors({
        submit: error.data?.error || error.message || 'Registration failed'
      });
    } finally {
      setLoading(false);
    }
  };

  const handleOTPVerification = async (otpType) => {
    try {
      const otpValue = otpType === 'phone' ? otpData.phone_otp : otpData.email_otp;
      
      const response = await apiService.verifyOTP({
        user_id: otpData.user_id,
        otp_type: otpType,
        otp: otpValue
      });
      
      setVerificationStatus(prev => ({
        ...prev,
        [`${otpType}_verified`]: true
      }));
      
      // If both verifications are complete, close modal and show success
      if (verificationStatus.phone_verified && otpType === 'email' || 
          verificationStatus.email_verified && otpType === 'phone') {
        setShowOTPModal(false);
        setCurrentStep(4); // Success step
      }
      
    } catch (error) {
      setErrors({
        [`${otpType}_otp`]: error.data?.error || 'Invalid OTP'
      });
    }
  };

  const handleResendOTP = async (otpType) => {
    try {
      await apiService.resendOTP({
        user_id: otpData.user_id,
        otp_type: otpType
      });
      
      setErrors(prev => ({
        ...prev,
        [`${otpType}_otp`]: ''
      }));
      
    } catch (error) {
      setErrors({
        [`${otpType}_otp`]: error.data?.error || 'Failed to resend OTP'
      });
    }
  };

  const renderStep1 = () => (
    <Card className="dashboard-card">
      <Card.Header>
        <h5 className="mb-0">Step 1: Basic Information</h5>
      </Card.Header>
      <Card.Body>
        <Row>
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Full Name *</Form.Label>
              <Form.Control
                type="text"
                name="full_name"
                value={formData.full_name}
                onChange={handleInputChange}
                isInvalid={!!errors.full_name}
                placeholder="Enter your full name as per Aadhaar"
              />
              <Form.Control.Feedback type="invalid">
                {errors.full_name}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
          
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Date of Birth *</Form.Label>
              <Form.Control
                type="date"
                name="date_of_birth"
                value={formData.date_of_birth}
                onChange={handleInputChange}
                isInvalid={!!errors.date_of_birth}
              />
              <Form.Control.Feedback type="invalid">
                {errors.date_of_birth}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
        </Row>
        
        <Row>
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Email Address *</Form.Label>
              <Form.Control
                type="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                isInvalid={!!errors.email}
                placeholder="your.email@example.com"
              />
              <Form.Control.Feedback type="invalid">
                {errors.email}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
          
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Mobile Number *</Form.Label>
              <Form.Control
                type="tel"
                name="phone_number"
                value={formData.phone_number}
                onChange={handleInputChange}
                isInvalid={!!errors.phone_number}
                placeholder="9876543210"
                maxLength="10"
              />
              <Form.Control.Feedback type="invalid">
                {errors.phone_number}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
        </Row>
        
        <Row>
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Password *</Form.Label>
              <Form.Control
                type="password"
                name="password"
                value={formData.password}
                onChange={handleInputChange}
                isInvalid={!!errors.password}
                placeholder="Minimum 8 characters"
              />
              <Form.Control.Feedback type="invalid">
                {errors.password}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
          
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Confirm Password *</Form.Label>
              <Form.Control
                type="password"
                name="confirmPassword"
                value={formData.confirmPassword}
                onChange={handleInputChange}
                isInvalid={!!errors.confirmPassword}
                placeholder="Re-enter password"
              />
              <Form.Control.Feedback type="invalid">
                {errors.confirmPassword}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );

  const renderStep2 = () => (
    <Card className="dashboard-card">
      <Card.Header>
        <h5 className="mb-0">Step 2: Identity Verification</h5>
      </Card.Header>
      <Card.Body>
        <Alert variant="info" className="mb-4">
          <strong>Identity Verification Required:</strong> We need your Aadhaar and PAN details for secure identity verification. This information is encrypted and stored securely.
        </Alert>
        
        <Row>
          <Col md={6}>
            <Form.Group className="mb-3">
              <Form.Label>Aadhaar Number *</Form.Label>
              <Form.Control
                type="text"
                name="aadhaar_number"
                value={formData.aadhaar_number}
                onChange={handleInputChange}
                isInvalid={!!errors.aadhaar_number}
                placeholder="1234 5678 9012"
                maxLength="14"
              />
              <Form.Control.Feedback type="invalid">
                {errors.aadhaar_number}
              </Form.Control.Feedback>
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
                name="pan_number"
                value={formData.pan_number}
                onChange={handleInputChange}
                isInvalid={!!errors.pan_number}
                placeholder="ABCDE1234F"
                maxLength="10"
                style={{ textTransform: 'uppercase' }}
              />
              <Form.Control.Feedback type="invalid">
                {errors.pan_number}
              </Form.Control.Feedback>
              <Form.Text className="text-muted">
                10-character PAN number for additional verification
              </Form.Text>
            </Form.Group>
          </Col>
        </Row>
        
        <Alert variant="warning" className="mt-3">
          <strong>Security Notice:</strong> Your identity documents will be verified against government databases to ensure authenticity and prevent fraud.
        </Alert>
      </Card.Body>
    </Card>
  );

  const renderStep3 = () => (
    <Card className="dashboard-card">
      <Card.Header>
        <h5 className="mb-0">Step 3: Address Information</h5>
      </Card.Header>
      <Card.Body>
        <Form.Group className="mb-3">
          <Form.Label>Address Line 1 *</Form.Label>
          <Form.Control
            type="text"
            name="address_line1"
            value={formData.address_line1}
            onChange={handleInputChange}
            isInvalid={!!errors.address_line1}
            placeholder="House/Flat number, Street name"
          />
          <Form.Control.Feedback type="invalid">
            {errors.address_line1}
          </Form.Control.Feedback>
        </Form.Group>
        
        <Form.Group className="mb-3">
          <Form.Label>Address Line 2</Form.Label>
          <Form.Control
            type="text"
            name="address_line2"
            value={formData.address_line2}
            onChange={handleInputChange}
            placeholder="Area, Landmark (Optional)"
          />
        </Form.Group>
        
        <Row>
          <Col md={4}>
            <Form.Group className="mb-3">
              <Form.Label>City *</Form.Label>
              <Form.Control
                type="text"
                name="city"
                value={formData.city}
                onChange={handleInputChange}
                isInvalid={!!errors.city}
                placeholder="City name"
              />
              <Form.Control.Feedback type="invalid">
                {errors.city}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
          
          <Col md={4}>
            <Form.Group className="mb-3">
              <Form.Label>State *</Form.Label>
              <Form.Select
                name="state"
                value={formData.state}
                onChange={handleInputChange}
                isInvalid={!!errors.state}
              >
                <option value="">Select State</option>
                {indianStates.map(state => (
                  <option key={state} value={state}>{state}</option>
                ))}
              </Form.Select>
              <Form.Control.Feedback type="invalid">
                {errors.state}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
          
          <Col md={4}>
            <Form.Group className="mb-3">
              <Form.Label>Pincode *</Form.Label>
              <Form.Control
                type="text"
                name="pincode"
                value={formData.pincode}
                onChange={handleInputChange}
                isInvalid={!!errors.pincode}
                placeholder="400001"
                maxLength="6"
              />
              <Form.Control.Feedback type="invalid">
                {errors.pincode}
              </Form.Control.Feedback>
            </Form.Group>
          </Col>
        </Row>
      </Card.Body>
    </Card>
  );

  const renderStep4 = () => (
    <Card className="dashboard-card">
      <Card.Header className="bg-success text-white">
        <h5 className="mb-0">Registration Successful!</h5>
      </Card.Header>
      <Card.Body className="text-center">
        <div className="feature-icon mx-auto mb-3" style={{ backgroundColor: '#28a745' }}>✓</div>
        <h4>Welcome to Ghost Identity Protection</h4>
        <p className="lead">Your account has been created and verified successfully.</p>
        
        <Alert variant="success">
          <strong>Account Status:</strong> Fully Verified<br />
          <strong>KYC Status:</strong> {registrationResult?.kyc_status}<br />
          <strong>Identity Score:</strong> {registrationResult?.identity_verification_score}
        </Alert>
        
        <Button variant="primary" size="lg" href="/dashboard">
          Go to Dashboard
        </Button>
      </Card.Body>
    </Card>
  );

  return (
    <div className="fade-in">
      <div className="d-flex justify-content-between align-items-center mb-4">
        <div>
          <h2 className="mb-2">Create Your Account</h2>
          <p className="text-muted mb-0">
            Secure your digital legacy with comprehensive identity verification
          </p>
        </div>
      </div>

      {/* Progress Bar */}
      <Card className="dashboard-card mb-4">
        <Card.Body>
          <div className="d-flex justify-content-between align-items-center mb-3">
            <span>Registration Progress</span>
            <span>{currentStep}/4</span>
          </div>
          <ProgressBar now={(currentStep / 4) * 100} />
          <div className="d-flex justify-content-between mt-2">
            <small className={currentStep >= 1 ? 'text-primary' : 'text-muted'}>Basic Info</small>
            <small className={currentStep >= 2 ? 'text-primary' : 'text-muted'}>Identity</small>
            <small className={currentStep >= 3 ? 'text-primary' : 'text-muted'}>Address</small>
            <small className={currentStep >= 4 ? 'text-primary' : 'text-muted'}>Complete</small>
          </div>
        </Card.Body>
      </Card>

      <Form onSubmit={handleSubmit}>
        {currentStep === 1 && renderStep1()}
        {currentStep === 2 && renderStep2()}
        {currentStep === 3 && renderStep3()}
        {currentStep === 4 && renderStep4()}

        {errors.submit && (
          <Alert variant="danger" className="mt-3">
            {errors.submit}
          </Alert>
        )}

        {currentStep < 4 && (
          <div className="d-flex justify-content-between mt-4">
            <Button 
              variant="outline-secondary" 
              onClick={handlePrevious}
              disabled={currentStep === 1}
            >
              Previous
            </Button>
            
            {currentStep < 3 ? (
              <Button variant="primary" onClick={handleNext}>
                Next
              </Button>
            ) : (
              <Button 
                type="submit" 
                variant="success"
                disabled={loading}
              >
                {loading ? (
                  <>
                    <span className="spinner-border spinner-border-sm me-2"></span>
                    Creating Account...
                  </>
                ) : (
                  'Create Account'
                )}
              </Button>
            )}
          </div>
        )}
      </Form>

      {/* OTP Verification Modal */}
      <Modal show={showOTPModal} onHide={() => setShowOTPModal(false)} size="lg">
        <Modal.Header closeButton>
          <Modal.Title>Verify Your Contact Information</Modal.Title>
        </Modal.Header>
        <Modal.Body>
          <Alert variant="info">
            <strong>Verification Required:</strong> We've sent OTP codes to your phone and email. 
            Please enter both codes to complete your registration.
          </Alert>
          
          <Row>
            <Col md={6}>
              <Card className="border">
                <Card.Header>
                  <h6 className="mb-0">Phone Verification</h6>
                </Card.Header>
                <Card.Body>
                  <Form.Group className="mb-3">
                    <Form.Label>Enter SMS OTP</Form.Label>
                    <Form.Control
                      type="text"
                      value={otpData.phone_otp}
                      onChange={(e) => setOtpData(prev => ({...prev, phone_otp: e.target.value}))}
                      placeholder="6-digit code"
                      maxLength="6"
                      isInvalid={!!errors.phone_otp}
                    />
                    <Form.Control.Feedback type="invalid">
                      {errors.phone_otp}
                    </Form.Control.Feedback>
                  </Form.Group>
                  
                  <div className="d-grid gap-2">
                    <Button 
                      variant={verificationStatus.phone_verified ? "success" : "primary"}
                      onClick={() => handleOTPVerification('phone')}
                      disabled={verificationStatus.phone_verified || otpData.phone_otp.length !== 6}
                    >
                      {verificationStatus.phone_verified ? 'Verified ✓' : 'Verify Phone'}
                    </Button>
                    
                    <Button 
                      variant="outline-secondary" 
                      size="sm"
                      onClick={() => handleResendOTP('phone')}
                    >
                      Resend SMS
                    </Button>
                  </div>
                </Card.Body>
              </Card>
            </Col>
            
            <Col md={6}>
              <Card className="border">
                <Card.Header>
                  <h6 className="mb-0">Email Verification</h6>
                </Card.Header>
                <Card.Body>
                  <Form.Group className="mb-3">
                    <Form.Label>Enter Email OTP</Form.Label>
                    <Form.Control
                      type="text"
                      value={otpData.email_otp}
                      onChange={(e) => setOtpData(prev => ({...prev, email_otp: e.target.value}))}
                      placeholder="6-digit code"
                      maxLength="6"
                      isInvalid={!!errors.email_otp}
                    />
                    <Form.Control.Feedback type="invalid">
                      {errors.email_otp}
                    </Form.Control.Feedback>
                  </Form.Group>
                  
                  <div className="d-grid gap-2">
                    <Button 
                      variant={verificationStatus.email_verified ? "success" : "primary"}
                      onClick={() => handleOTPVerification('email')}
                      disabled={verificationStatus.email_verified || otpData.email_otp.length !== 6}
                    >
                      {verificationStatus.email_verified ? 'Verified ✓' : 'Verify Email'}
                    </Button>
                    
                    <Button 
                      variant="outline-secondary" 
                      size="sm"
                      onClick={() => handleResendOTP('email')}
                    >
                      Resend Email
                    </Button>
                  </div>
                </Card.Body>
              </Card>
            </Col>
          </Row>
        </Modal.Body>
      </Modal>
    </div>
  );
}

export default Registration;
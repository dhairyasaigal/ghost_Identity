/**
 * API Service Layer for Ghost Identity Protection System
 * Handles all HTTP requests to the backend API with error handling and authentication
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

class ApiError extends Error {
  constructor(message, status, data) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.data = data;
  }
}

class ApiService {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  /**
   * Make HTTP request with error handling
   */
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include', // Include cookies for session management
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      // Handle non-JSON responses
      const contentType = response.headers.get('content-type');
      let data;
      
      if (contentType && contentType.includes('application/json')) {
        data = await response.json();
      } else {
        data = { message: await response.text() };
      }

      if (!response.ok) {
        throw new ApiError(
          data.error || data.message || `HTTP ${response.status}`,
          response.status,
          data
        );
      }

      return data;
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      // Network or other errors
      throw new ApiError(
        error.message || 'Network error occurred',
        0,
        { originalError: error }
      );
    }
  }

  // Authentication API
  async register(userData) {
    return this.request('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async verifyOTP(otpData) {
    return this.request('/auth/verify-otp', {
      method: 'POST',
      body: JSON.stringify(otpData),
    });
  }

  async resendOTP(otpData) {
    return this.request('/auth/resend-otp', {
      method: 'POST',
      body: JSON.stringify(otpData),
    });
  }

  async login(credentials) {
    return this.request('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async logout() {
    return this.request('/auth/logout', {
      method: 'POST',
    });
  }

  async checkSession() {
    return this.request('/auth/session');
  }

  async setupMFA() {
    return this.request('/auth/mfa/setup');
  }

  async verifyMFA(token) {
    return this.request('/auth/mfa/verify', {
      method: 'POST',
      body: JSON.stringify({ token }),
    });
  }

  async getProfile() {
    return this.request('/auth/profile');
  }

  async updateProfile(profileData) {
    return this.request('/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  }

  async changePassword(passwordData) {
    return this.request('/auth/change-password', {
      method: 'POST',
      body: JSON.stringify(passwordData),
    });
  }

  // Digital Asset Management API
  async getDigitalAssets() {
    return this.request('/vault/assets');
  }

  async addDigitalAsset(assetData) {
    return this.request('/vault/assets', {
      method: 'POST',
      body: JSON.stringify(assetData),
    });
  }

  async getAssetsByType(assetType) {
    return this.request(`/vault/assets/${assetType}`);
  }

  // Trusted Contact Management API
  async getTrustedContacts() {
    return this.request('/vault/trusted-contacts');
  }

  async addTrustedContact(contactData) {
    return this.request('/vault/trusted-contacts', {
      method: 'POST',
      body: JSON.stringify(contactData),
    });
  }

  async updateTrustedContact(contactId, contactData) {
    return this.request(`/vault/trusted-contacts/${contactId}`, {
      method: 'PUT',
      body: JSON.stringify(contactData),
    });
  }

  async deleteTrustedContact(contactId) {
    return this.request(`/vault/trusted-contacts/${contactId}`, {
      method: 'DELETE',
    });
  }

  // Action Policy Management API
  async getActionPolicies() {
    return this.request('/vault/policies');
  }

  async createActionPolicy(policyData) {
    return this.request('/vault/policies', {
      method: 'POST',
      body: JSON.stringify(policyData),
    });
  }

  async updateActionPolicy(policyId, policyData) {
    return this.request(`/vault/policies/${policyId}`, {
      method: 'PUT',
      body: JSON.stringify(policyData),
    });
  }

  async deleteActionPolicy(policyId) {
    return this.request(`/vault/policies/${policyId}`, {
      method: 'DELETE',
    });
  }

  // Death Verification API
  async uploadDeathCertificate(formData) {
    return this.request('/verification/upload-certificate', {
      method: 'POST',
      headers: {}, // Don't set Content-Type for FormData
      body: formData,
    });
  }

  async getVerificationStatus(userEmail, contactEmail) {
    const params = new URLSearchParams({ contact_email: contactEmail });
    return this.request(`/verification/status/${userEmail}?${params}`);
  }

  async getUserPolicies(userEmail, contactEmail) {
    const params = new URLSearchParams({ contact_email: contactEmail });
    return this.request(`/verification/policies/${userEmail}?${params}`);
  }

  async manualPolicyExecution(userEmail, executionData) {
    return this.request(`/verification/execute-policies/${userEmail}`, {
      method: 'POST',
      body: JSON.stringify(executionData),
    });
  }

  async getAuditTrail(userEmail, params = {}) {
    const queryParams = new URLSearchParams(params);
    return this.request(`/verification/audit-trail/${userEmail}?${queryParams}`);
  }

  // Notification API
  async deliverNotification(notificationData) {
    return this.request('/notifications/deliver', {
      method: 'POST',
      body: JSON.stringify(notificationData),
    });
  }

  async deliverBatchNotifications(notificationsData) {
    return this.request('/notifications/deliver/batch', {
      method: 'POST',
      body: JSON.stringify(notificationsData),
    });
  }

  async getDeliveryStatus(notificationId) {
    return this.request(`/notifications/status/${notificationId}`);
  }

  async processRetryQueue(userData) {
    return this.request('/notifications/retry/process', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async getDeliveryStatistics() {
    return this.request('/notifications/statistics');
  }

  async getTemplate(platform, actionType, templateType = 'email') {
    const params = new URLSearchParams({ template_type: templateType });
    return this.request(`/notifications/templates/${platform}/${actionType}?${params}`);
  }

  async createCustomTemplate(templateData) {
    return this.request('/notifications/templates', {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  }

  async validateTemplate(templateData) {
    return this.request('/notifications/templates/validate', {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  }

  async generateNotificationFromTemplate(templateData) {
    return this.request('/notifications/templates/generate', {
      method: 'POST',
      body: JSON.stringify(templateData),
    });
  }

  async listAvailableTemplates(platform = null) {
    const params = platform ? new URLSearchParams({ platform }) : '';
    return this.request(`/notifications/templates/list?${params}`);
  }

  async getTemplateStatistics() {
    return this.request('/notifications/templates/statistics');
  }

  async getPlatformRequirements(platform) {
    return this.request(`/notifications/templates/requirements/${platform}`);
  }

  async executeNotificationPolicies(policyData) {
    return this.request('/notifications/execute-policies', {
      method: 'POST',
      body: JSON.stringify(policyData),
    });
  }
}

// Create singleton instance
const apiService = new ApiService();

export default apiService;
export { ApiError };
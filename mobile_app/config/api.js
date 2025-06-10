// config/api.js
// API Configuration for VMS Mobile App

// Update this IP address to match your Django server
export const API_CONFIG = {
  // Development - Update this to your Django server IP address
  BASE_URL: 'http://192.168.250.153:8000/api/v1',
  
  // Production - Update this to your production server URL
  // BASE_URL: 'https://your-domain.com/api/v1',
  
  TIMEOUT: 30000, // 30 seconds
  
  // API Endpoints
  ENDPOINTS: {
    // Authentication
    LOGIN: '/token-auth/',
    
    // User Management
    USERS: '/users/',
    USER_ME: '/users/me/',
    
    // Vehicle Management
    VEHICLES: '/vehicles/',
    VEHICLE_TYPES: '/vehicle-types/',
    
    // Trip Management
    TRIPS: '/trips/',
    
    // Maintenance
    MAINTENANCE: '/maintenance/',
    
    // Fuel Management
    FUEL: '/fuel/',
  }
};

// Helper function to get full API URL
export const getApiUrl = (endpoint) => {
  return `${API_CONFIG.BASE_URL}${endpoint}`;
};

// HTTP Headers
export const getHeaders = (token = null, contentType = 'application/json') => {
  const headers = {
    'Content-Type': contentType,
  };
  
  if (token) {
    headers['Authorization'] = `Token ${token}`;
  }
  
  return headers;
};

// HTTP Status Codes
export const HTTP_STATUS = {
  OK: 200,
  CREATED: 201,
  BAD_REQUEST: 400,
  UNAUTHORIZED: 401,
  FORBIDDEN: 403,
  NOT_FOUND: 404,
  INTERNAL_SERVER_ERROR: 500,
};

export default API_CONFIG;
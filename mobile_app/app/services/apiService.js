// services/apiService.js
import * as SecureStore from 'expo-secure-store';
import { API_CONFIG, getApiUrl, getHeaders, HTTP_STATUS } from '../config/api';

class ApiService {
  constructor() {
    this.baseURL = API_CONFIG.BASE_URL;
    this.timeout = API_CONFIG.TIMEOUT;
  }

  // Get stored token
  async getToken() {
    try {
      return await SecureStore.getItemAsync('userToken');
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  }

  // Store token
  async setToken(token) {
    try {
      await SecureStore.setItemAsync('userToken', token);
    } catch (error) {
      console.error('Error storing token:', error);
    }
  }

  // Remove token
  async removeToken() {
    try {
      await SecureStore.deleteItemAsync('userToken');
    } catch (error) {
      console.error('Error removing token:', error);
    }
  }

  // Generic API call method
  async apiCall(endpoint, options = {}) {
    try {
      const token = await this.getToken();
      const url = getApiUrl(endpoint);
      
      const config = {
        method: 'GET',
        headers: getHeaders(token),
        timeout: this.timeout,
        ...options,
      };

      console.log(`API Call: ${config.method} ${url}`);
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);
      
      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorText = await response.text();
        let errorMessage;
        
        try {
          const errorJson = JSON.parse(errorText);
          errorMessage = errorJson.detail || errorJson.message || errorJson.non_field_errors?.[0] || 'An error occurred';
        } catch {
          errorMessage = errorText || `HTTP ${response.status}`;
        }
        
        throw new Error(errorMessage);
      }

      const data = await response.json();
      console.log(`API Success: ${config.method} ${url}`);
      return data;
    } catch (error) {
      console.error('API Error:', error);
      
      if (error.name === 'AbortError') {
        throw new Error('Request timeout');
      }
      
      throw error;
    }
  }

  // Authentication methods
  async login(username, password) {
    try {
      const response = await fetch(getApiUrl(API_CONFIG.ENDPOINTS.LOGIN), {
        method: 'POST',
        headers: getHeaders(),
        body: JSON.stringify({ username, password }),
      });

      const data = await response.json();

      if (!response.ok) {
        const errorMessage = data.detail || data.non_field_errors?.[0] || 'Login failed';
        throw new Error(errorMessage);
      }

      if (data.token) {
        await this.setToken(data.token);
      }

      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async logout() {
    await this.removeToken();
  }

  // User methods
  async getUserInfo() {
    return this.apiCall(API_CONFIG.ENDPOINTS.USER_ME);
  }

  async getUsers() {
    return this.apiCall(API_CONFIG.ENDPOINTS.USERS);
  }

  // Vehicle methods
  async getVehicles() {
    return this.apiCall(API_CONFIG.ENDPOINTS.VEHICLES);
  }

  async getVehicle(id) {
    return this.apiCall(`${API_CONFIG.ENDPOINTS.VEHICLES}${id}/`);
  }

  async getVehicleTrips(vehicleId) {
    return this.apiCall(`${API_CONFIG.ENDPOINTS.VEHICLES}${vehicleId}/trips/`);
  }

  async getVehicleActiveTrip(vehicleId) {
    return this.apiCall(`${API_CONFIG.ENDPOINTS.VEHICLES}${vehicleId}/active_trip/`);
  }

  async getVehicleMaintenance(vehicleId) {
    return this.apiCall(`${API_CONFIG.ENDPOINTS.VEHICLES}${vehicleId}/maintenance/`);
  }

  async getVehicleFuel(vehicleId) {
    return this.apiCall(`${API_CONFIG.ENDPOINTS.VEHICLES}${vehicleId}/fuel/`);
  }

  // Trip methods
  async getTrips() {
    return this.apiCall(API_CONFIG.ENDPOINTS.TRIPS);
  }

  async getTrip(id) {
    return this.apiCall(`${API_CONFIG.ENDPOINTS.TRIPS}${id}/`);
  }

  async createTrip(tripData) {
    return this.apiCall(API_CONFIG.ENDPOINTS.TRIPS, {
      method: 'POST',
      body: JSON.stringify(tripData),
    });
  }

  async updateTrip(id, tripData) {
    return this.apiCall(`${API_CONFIG.ENDPOINTS.TRIPS}${id}/`, {
      method: 'PATCH',
      body: JSON.stringify(tripData),
    });
  }

  async endTrip(id, endOdometer, notes = '') {
    return this.apiCall(`${API_CONFIG.ENDPOINTS.TRIPS}${id}/end_trip/`, {
      method: 'POST',
      body: JSON.stringify({
        end_odometer: endOdometer,
        notes: notes,
      }),
    });
  }

  async cancelTrip(id, reason = '') {
    return this.apiCall(`${API_CONFIG.ENDPOINTS.TRIPS}${id}/cancel_trip/`, {
      method: 'POST',
      body: JSON.stringify({
        reason: reason,
      }),
    });
  }

  // Fuel methods
  async getFuelTransactions() {
    return this.apiCall(API_CONFIG.ENDPOINTS.FUEL);
  }

  async createFuelTransaction(fuelData) {
    return this.apiCall(API_CONFIG.ENDPOINTS.FUEL, {
      method: 'POST',
      body: JSON.stringify(fuelData),
    });
  }

  // Maintenance methods
  async getMaintenance() {
    return this.apiCall(API_CONFIG.ENDPOINTS.MAINTENANCE);
  }

  async createMaintenance(maintenanceData) {
    return this.apiCall(API_CONFIG.ENDPOINTS.MAINTENANCE, {
      method: 'POST',
      body: JSON.stringify(maintenanceData),
    });
  }

  // Vehicle Types
  async getVehicleTypes() {
    return this.apiCall(API_CONFIG.ENDPOINTS.VEHICLE_TYPES);
  }

  // Check if user is authenticated
  async isAuthenticated() {
    try {
      const token = await this.getToken();
      if (!token) return false;
      
      // Try to get user info to validate token
      await this.getUserInfo();
      return true;
    } catch (error) {
      // If token is invalid, remove it
      await this.removeToken();
      return false;
    }
  }
}

// Export singleton instance
export default new ApiService();
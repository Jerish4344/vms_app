import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
  Text,
  TextInput,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import * as SecureStore from 'expo-secure-store';

// API Configuration
const API_BASE_URL = 'http://192.168.250.153:8000/api/v1'; // Update this to your Django server IP
const API_ENDPOINTS = {
  LOGIN: `${API_BASE_URL}/token-auth/`,
  USER_ME: `${API_BASE_URL}/users/me/`,
  VEHICLES: `${API_BASE_URL}/vehicles/`,
  TRIPS: `${API_BASE_URL}/trips/`,
};

// API Helper functions
const apiCall = async (endpoint, options = {}) => {
  try {
    const token = await SecureStore.getItemAsync('userToken');
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };
    
    if (token) {
      headers['Authorization'] = `Token ${token}`;
    }

    const response = await fetch(endpoint, {
      ...options,
      headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    return await response.json();
  } catch (error) {
    console.error('API Error:', error);
    throw error;
  }
};

export default function App() {
  const [isLoading, setIsLoading] = useState(true);
  const [userToken, setUserToken] = useState(null);
  const [userInfo, setUserInfo] = useState(null);
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginLoading, setLoginLoading] = useState(false);
  const [error, setError] = useState('');

  // Authentication functions
  const signIn = async (token) => {
    setIsLoading(true);
    try {
      await SecureStore.setItemAsync('userToken', token);
      setUserToken(token);
      
      // Fetch user info after successful login
      await fetchUserInfo(token);
    } catch (e) {
      console.error('Error signing in:', e);
      Alert.alert('Error', 'Failed to save login credentials');
    }
    setIsLoading(false);
  };

  const signOut = async () => {
    setIsLoading(true);
    try {
      await SecureStore.deleteItemAsync('userToken');
      setUserToken(null);
      setUserInfo(null);
    } catch (e) {
      console.error('Error signing out:', e);
    }
    setIsLoading(false);
  };

  const fetchUserInfo = async (token = null) => {
    try {
      const currentToken = token || userToken;
      if (!currentToken) return;

      const userData = await apiCall(API_ENDPOINTS.USER_ME);
      setUserInfo(userData);
    } catch (error) {
      console.error('Error fetching user info:', error);
      // If token is invalid, sign out
      if (error.message.includes('401') || error.message.includes('403')) {
        await signOut();
      }
    }
  };

  // Load token on app start
  useEffect(() => {
    const bootstrapAsync = async () => {
      let userToken;
      try {
        userToken = await SecureStore.getItemAsync('userToken');
        if (userToken) {
          setUserToken(userToken);
          await fetchUserInfo(userToken);
        }
      } catch (e) {
        console.error('Error restoring token:', e);
      }
      setIsLoading(false);
    };

    bootstrapAsync();
  }, []);

  // Handle login
  const handleLogin = async () => {
    if (!username || !password) {
      setError('Username and password are required');
      return;
    }

    setLoginLoading(true);
    setError('');

    try {
      const response = await fetch(API_ENDPOINTS.LOGIN, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          username: username.trim(),
          password: password,
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || data.non_field_errors?.[0] || 'Login failed');
      }

      if (data.token) {
        await signIn(data.token);
        setUsername('');
        setPassword('');
      } else {
        throw new Error('No token received from server');
      }
    } catch (err) {
      console.error('Login error:', err);
      setError(err.message || 'Login failed. Please check your credentials.');
      Alert.alert('Login Failed', err.message || 'Please check your credentials and try again.');
    } finally {
      setLoginLoading(false);
    }
  };

  // Loading screen
  if (isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#1976D2" />
        <Text style={styles.loadingText}>Loading...</Text>
      </View>
    );
  }

  // Main app
  return (
    <SafeAreaProvider>
      <StatusBar style="dark" />
      {userToken ? (
        // Home screen (when logged in)
        <SafeAreaView style={styles.container}>
          <View style={styles.homeContainer}>
            <Text style={styles.welcomeText}>Welcome to VMS Mobile!</Text>
            {userInfo && (
              <View style={styles.userInfoContainer}>
                <Text style={styles.userInfoText}>
                  Hello, {userInfo.full_name || userInfo.username}
                </Text>
                <Text style={styles.userRoleText}>
                  Role: {userInfo.user_type}
                </Text>
                {userInfo.email && (
                  <Text style={styles.userEmailText}>
                    Email: {userInfo.email}
                  </Text>
                )}
              </View>
            )}
            <Text style={styles.subtitle}>You are logged in and connected to the VMS system.</Text>
            
            <View style={styles.quickActions}>
              <TouchableOpacity style={styles.actionButton}>
                <Text style={styles.actionButtonText}>View Vehicles</Text>
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.actionButton}>
                <Text style={styles.actionButtonText}>Start Trip</Text>
              </TouchableOpacity>
              
              <TouchableOpacity style={styles.actionButton}>
                <Text style={styles.actionButtonText}>My Trips</Text>
              </TouchableOpacity>
            </View>
            
            <TouchableOpacity
              style={styles.logoutButton}
              onPress={signOut}
            >
              <Text style={styles.buttonText}>Logout</Text>
            </TouchableOpacity>
          </View>
        </SafeAreaView>
      ) : (
        // Login screen
        <SafeAreaView style={styles.container}>
          <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.keyboardAvoidView}
          >
            <ScrollView contentContainerStyle={styles.scrollView}>
              <View style={styles.logoContainer}>
                <View style={styles.logoPlaceholder}>
                  <Text style={styles.logoText}>VMS</Text>
                </View>
                <Text style={styles.appName}>Vehicle Management System</Text>
              </View>
              
              <View style={styles.formContainer}>
                <Text style={styles.title}>Login</Text>
                
                {error ? (
                  <View style={styles.errorContainer}>
                    <Text style={styles.errorText}>{error}</Text>
                  </View>
                ) : null}
                
                <View style={styles.form}>
                  <TextInput
                    placeholder="Username or Email"
                    value={username}
                    onChangeText={setUsername}
                    style={styles.input}
                    autoCapitalize="none"
                    autoCorrect={false}
                    editable={!loginLoading}
                  />
                  
                  <TextInput
                    placeholder="Password"
                    value={password}
                    onChangeText={setPassword}
                    secureTextEntry
                    style={styles.input}
                    editable={!loginLoading}
                  />
                  
                  <TouchableOpacity
                    onPress={handleLogin}
                    style={[styles.loginButton, loginLoading && styles.disabledButton]}
                    disabled={loginLoading}
                  >
                    {loginLoading ? (
                      <ActivityIndicator color="#fff" />
                    ) : (
                      <Text style={styles.buttonText}>Login</Text>
                    )}
                  </TouchableOpacity>
                </View>
                
                <TouchableOpacity
                  style={styles.forgotPassword}
                  disabled={loginLoading}
                  onPress={() => Alert.alert('Forgot Password', 'Please contact your administrator to reset your password.')}
                >
                  <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
                </TouchableOpacity>
              </View>
              
              <View style={styles.footer}>
                <Text style={styles.footerText}>
                  Vehicle Management System © {new Date().getFullYear()}
                </Text>
                <Text style={styles.versionText}>
                  Version 1.0.0
                </Text>
              </View>
            </ScrollView>
          </KeyboardAvoidingView>
        </SafeAreaView>
      )}
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f5f5f5',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
    color: '#666',
  },
  keyboardAvoidView: {
    flex: 1,
  },
  scrollView: {
    flexGrow: 1,
    justifyContent: 'center',
    padding: 20,
  },
  logoContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  logoPlaceholder: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: '#1976D2',
    justifyContent: 'center',
    alignItems: 'center',
  },
  logoText: {
    color: '#fff',
    fontSize: 32,
    fontWeight: 'bold',
  },
  appName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 10,
    color: '#1976D2',
    textAlign: 'center',
  },
  formContainer: {
    padding: 20,
    borderRadius: 10,
    backgroundColor: '#fff',
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
    color: '#333',
  },
  form: {
    width: '100%',
  },
  input: {
    marginBottom: 15,
    padding: 15,
    borderWidth: 1,
    borderColor: '#ddd',
    borderRadius: 8,
    backgroundColor: '#f9f9f9',
    fontSize: 16,
  },
  loginButton: {
    backgroundColor: '#1976D2',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 10,
  },
  disabledButton: {
    backgroundColor: '#ccc',
  },
  buttonText: {
    color: '#fff',
    fontWeight: 'bold',
    fontSize: 16,
  },
  forgotPassword: {
    marginTop: 20,
    alignSelf: 'center',
  },
  forgotPasswordText: {
    color: '#1976D2',
    fontSize: 14,
  },
  errorContainer: {
    backgroundColor: '#ffebee',
    borderRadius: 5,
    padding: 10,
    marginBottom: 15,
    borderLeftWidth: 4,
    borderLeftColor: '#f44336',
  },
  errorText: {
    color: '#f44336',
    textAlign: 'center',
    fontSize: 14,
  },
  footer: {
    marginTop: 30,
    alignItems: 'center',
  },
  footerText: {
    color: '#666',
    fontSize: 12,
    textAlign: 'center',
  },
  versionText: {
    color: '#999',
    fontSize: 10,
    marginTop: 5,
  },
  homeContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 20,
  },
  welcomeText: {
    fontSize: 28,
    fontWeight: 'bold',
    marginBottom: 10,
    color: '#333',
    textAlign: 'center',
  },
  userInfoContainer: {
    backgroundColor: '#fff',
    borderRadius: 10,
    padding: 15,
    marginBottom: 20,
    width: '100%',
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  userInfoText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#333',
    marginBottom: 5,
  },
  userRoleText: {
    fontSize: 14,
    color: '#1976D2',
    fontWeight: '500',
  },
  userEmailText: {
    fontSize: 14,
    color: '#666',
    marginTop: 2,
  },
  subtitle: {
    fontSize: 16,
    color: '#666',
    marginBottom: 30,
    textAlign: 'center',
  },
  quickActions: {
    width: '100%',
    marginBottom: 30,
  },
  actionButton: {
    backgroundColor: '#1976D2',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  actionButtonText: {
    color: '#fff',
    fontWeight: '600',
    fontSize: 16,
  },
  logoutButton: {
    backgroundColor: '#f44336',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    width: '100%',
    maxWidth: 200,
  },
});
import React, { useState, useContext } from 'react';
import {
  View,
  StyleSheet,
  Image,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { TextInput, Button, Text, Surface, HelperText } from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Formik } from 'formik';
import * as Yup from 'yup';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { authAPI } from '../../services/apiService';
import { AuthContext } from '../../context/AuthContext';
import { NetworkContext } from '../../context/NetworkContext';

// Validation schema
const LoginSchema = Yup.object().shape({
  username: Yup.string().required('Username or email is required'),
  password: Yup.string().required('Password is required'),
});

const LoginScreen = ({ navigation }) => {
  const [loading, setLoading] = useState(false);
  const [hidePassword, setHidePassword] = useState(true);
  const [error, setError] = useState('');
  
  const { signIn } = useContext(AuthContext);
  const { isConnected } = useContext(NetworkContext);
  
  // Handle login submission
  const handleLogin = async (values) => {
    if (!isConnected) {
      Alert.alert(
        'No Internet Connection',
        'You need an internet connection to log in. Please check your connection and try again.',
        [{ text: 'OK' }]
      );
      return;
    }
    
    setLoading(true);
    setError('');
    
    try {
      const response = await authAPI.login(values.username, values.password);
      
      if (response.token) {
        // Call the signIn function from AuthContext to store the token
        await signIn(response.token);
      } else {
        setError('Login failed. Please check your credentials.');
      }
    } catch (err) {
      console.error('Login error:', err);
      
      // Handle different error scenarios
      if (err.response) {
        // The server responded with an error status
        if (err.response.status === 400) {
          setError('Invalid username or password');
        } else if (err.response.status === 401) {
          setError('Unauthorized. Please check your credentials.');
        } else {
          setError(`Server error: ${err.response.status}`);
        }
      } else if (err.request) {
        // The request was made but no response was received
        setError('No response from server. Please try again later.');
      } else {
        // Something else caused the error
        setError('An error occurred. Please try again.');
      }
    } finally {
      setLoading(false);
    }
  };
  
  return (
    <SafeAreaView style={styles.container}>
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardAvoidView}
      >
        <ScrollView contentContainerStyle={styles.scrollView}>
          <View style={styles.logoContainer}>
            <Image
              source={require('../../../assets/icon.png')}
              style={styles.logo}
              resizeMode="contain"
            />
            <Text style={styles.appName}>Vehicle Management System</Text>
          </View>
          
          <Surface style={styles.formContainer}>
            <Text style={styles.title}>Login</Text>
            
            {error ? (
              <HelperText type="error" visible={!!error} style={styles.errorText}>
                {error}
              </HelperText>
            ) : null}
            
            <Formik
              initialValues={{ username: '', password: '' }}
              validationSchema={LoginSchema}
              onSubmit={handleLogin}
            >
              {({ handleChange, handleBlur, handleSubmit, values, errors, touched }) => (
                <View style={styles.form}>
                  <TextInput
                    label="Username or Email"
                    value={values.username}
                    onChangeText={handleChange('username')}
                    onBlur={handleBlur('username')}
                    style={styles.input}
                    autoCapitalize="none"
                    left={<TextInput.Icon icon="account" />}
                    error={touched.username && errors.username}
                    disabled={loading}
                  />
                  {touched.username && errors.username ? (
                    <HelperText type="error" visible={touched.username && errors.username}>
                      {errors.username}
                    </HelperText>
                  ) : null}
                  
                  <TextInput
                    label="Password"
                    value={values.password}
                    onChangeText={handleChange('password')}
                    onBlur={handleBlur('password')}
                    secureTextEntry={hidePassword}
                    style={styles.input}
                    left={<TextInput.Icon icon="lock" />}
                    right={
                      <TextInput.Icon
                        icon={hidePassword ? 'eye' : 'eye-off'}
                        onPress={() => setHidePassword(!hidePassword)}
                      />
                    }
                    error={touched.password && errors.password}
                    disabled={loading}
                  />
                  {touched.password && errors.password ? (
                    <HelperText type="error" visible={touched.password && errors.password}>
                      {errors.password}
                    </HelperText>
                  ) : null}
                  
                  <Button
                    mode="contained"
                    onPress={handleSubmit}
                    style={styles.button}
                    loading={loading}
                    disabled={loading}
                  >
                    Login
                  </Button>
                </View>
              )}
            </Formik>
            
            <TouchableOpacity
              onPress={() => navigation.navigate('ForgotPassword')}
              style={styles.forgotPassword}
              disabled={loading}
            >
              <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
            </TouchableOpacity>
          </Surface>
          
          <View style={styles.footer}>
            <Text style={styles.footerText}>
              Vehicle Management System © {new Date().getFullYear()}
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
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
  logo: {
    width: 100,
    height: 100,
  },
  appName: {
    fontSize: 24,
    fontWeight: 'bold',
    marginTop: 10,
    color: '#1976D2',
  },
  formContainer: {
    padding: 20,
    borderRadius: 10,
    elevation: 4,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    marginBottom: 20,
    textAlign: 'center',
  },
  form: {
    width: '100%',
  },
  input: {
    marginBottom: 10,
  },
  button: {
    marginTop: 20,
    paddingVertical: 8,
  },
  forgotPassword: {
    marginTop: 20,
    alignSelf: 'center',
  },
  forgotPasswordText: {
    color: '#1976D2',
  },
  errorText: {
    textAlign: 'center',
    marginBottom: 10,
  },
  footer: {
    marginTop: 30,
    alignItems: 'center',
  },
  footerText: {
    color: '#666',
    fontSize: 12,
  },
});

export default LoginScreen;

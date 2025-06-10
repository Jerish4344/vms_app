import { createContext } from 'react';

/**
 * Authentication Context
 * 
 * Provides authentication state and functions throughout the app.
 * 
 * Available functions:
 * - signIn(token): Stores the authentication token and updates state
 * - signOut(): Removes the authentication token and updates state
 * - signUp(token): Similar to signIn, used after registration
 */
export const AuthContext = createContext({
  signIn: async (token) => {},
  signOut: async () => {},
  signUp: async (token) => {},
  // The actual implementation of these functions is in App.js
  // This just provides the shape of the context
});

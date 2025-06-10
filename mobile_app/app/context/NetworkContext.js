import { createContext } from 'react';

/**
 * Network Context
 * 
 * Provides network connectivity state throughout the app.
 * Used to handle offline scenarios and display appropriate UI.
 * 
 * Available properties:
 * - isConnected: Boolean indicating if the device has internet connectivity
 * 
 * Usage example:
 * ```
 * import { useContext } from 'react';
 * import { NetworkContext } from '../context/NetworkContext';
 * 
 * function MyComponent() {
 *   const { isConnected } = useContext(NetworkContext);
 *   
 *   if (!isConnected) {
 *     return <Text>You are offline. Some features may be unavailable.</Text>;
 *   }
 *   
 *   return <Text>Connected to the internet</Text>;
 * }
 * ```
 */
export const NetworkContext = createContext({
  isConnected: true,
  // The actual implementation updates this value in App.js
  // based on NetInfo.addEventListener results
});

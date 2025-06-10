import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { persistReducer, persistStore } from 'redux-persist';
import thunk from 'redux-thunk';

// Import slices
import authReducer from './slices/authSlice';
import vehiclesReducer from './slices/vehiclesSlice';
import tripsReducer from './slices/tripsSlice';
import maintenanceReducer from './slices/maintenanceSlice';
import fuelReducer from './slices/fuelSlice';
import uiReducer from './slices/uiSlice';
import offlineReducer from './slices/offlineSlice';

// Configure Redux Persist
const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  // Don't persist UI state or any sensitive auth data
  blacklist: ['ui'],
  // Optionally whitelist specific slices instead of blacklisting
  // whitelist: ['vehicles', 'trips', 'maintenance', 'fuel', 'offline'],
};

// Auth persistence config with separate storage
const authPersistConfig = {
  key: 'auth',
  storage: AsyncStorage,
  // Don't persist sensitive auth data like tokens (those are in SecureStore)
  blacklist: ['error', 'loading'],
};

// Combine all reducers
const rootReducer = combineReducers({
  auth: persistReducer(authPersistConfig, authReducer),
  vehicles: vehiclesReducer,
  trips: tripsReducer,
  maintenance: maintenanceReducer,
  fuel: fuelReducer,
  ui: uiReducer,
  offline: offlineReducer,
});

// Create persisted reducer
const persistedReducer = persistReducer(persistConfig, rootReducer);

// Custom middleware to handle API errors globally
const errorMiddleware = (store) => (next) => (action) => {
  // Check if the action is a rejected API call
  if (action.type?.endsWith('/rejected') && action.payload) {
    // Dispatch to UI slice to show error
    store.dispatch({
      type: 'ui/setError',
      payload: {
        message: action.payload.message || 'An error occurred',
        source: action.type.split('/')[0], // Get the slice name
      },
    });
  }
  return next(action);
};

// Configure the Redux store
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        // Ignore non-serializable values in these paths
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE'],
        ignoredPaths: ['offline.queue'],
      },
    }).concat(thunk, errorMiddleware),
  devTools: __DEV__, // Only enable Redux DevTools in development
});

// Create persistor
export const persistor = persistStore(store);

// Enable refetchOnFocus and refetchOnReconnect behaviors
// This sets up listeners for the store, which will refetch data when the app
// regains focus or reconnects to the network
setupListeners(store.dispatch);

// Export types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

export default { store, persistor };

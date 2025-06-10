import React, { useState, useEffect, useContext } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  RefreshControl,
  TouchableOpacity,
  Image,
  FlatList,
} from 'react-native';
import {
  Text,
  Card,
  Title,
  Paragraph,
  Button,
  Divider,
  Avatar,
  ActivityIndicator,
  Surface,
  useTheme,
  Badge,
  IconButton,
  List,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useSelector, useDispatch } from 'react-redux';
import { useFocusEffect } from '@react-navigation/native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import moment from 'moment';

// Import API services
import {
  vehiclesAPI,
  tripsAPI,
  maintenanceAPI,
  fuelAPI,
  authAPI,
} from '../../services/apiService';

// Import contexts
import { NetworkContext } from '../../context/NetworkContext';

const DashboardScreen = ({ navigation }) => {
  const theme = useTheme();
  const dispatch = useDispatch();
  const { isConnected } = useContext(NetworkContext);

  // State variables
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [summaryData, setSummaryData] = useState({
    totalVehicles: 0,
    availableVehicles: 0,
    activeTrips: 0,
    pendingMaintenance: 0,
    fuelTransactions: 0,
  });
  const [recentTrips, setRecentTrips] = useState([]);
  const [upcomingMaintenance, setUpcomingMaintenance] = useState([]);
  const [documentsExpiring, setDocumentsExpiring] = useState([]);
  const [userProfile, setUserProfile] = useState(null);
  const [error, setError] = useState(null);

  // Load dashboard data
  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch user profile
      const userResponse = await authAPI.getCurrentUser();
      setUserProfile(userResponse.data);

      // Fetch vehicles summary
      const vehiclesResponse = await vehiclesAPI.getAll();
      const vehicles = vehiclesResponse.data.results || [];
      
      // Calculate vehicle statistics
      const availableVehicles = vehicles.filter(v => v.status === 'available').length;
      
      // Fetch active trips
      const activeTripsResponse = await tripsAPI.getAll({ status: 'ongoing' });
      const activeTrips = activeTripsResponse.data.results || [];
      
      // Fetch recent trips (completed)
      const recentTripsResponse = await tripsAPI.getAll({ 
        status: 'completed',
        ordering: '-end_time',
        limit: 5 
      });
      setRecentTrips(recentTripsResponse.data.results || []);
      
      // Fetch pending maintenance
      const maintenanceResponse = await maintenanceAPI.getAll({ 
        status: 'scheduled',
        ordering: 'scheduled_date' 
      });
      const pendingMaintenance = maintenanceResponse.data.results || [];
      setUpcomingMaintenance(pendingMaintenance.slice(0, 3));
      
      // Fetch recent fuel transactions
      const fuelResponse = await fuelAPI.getAll({
        ordering: '-date',
        limit: 10
      });
      const fuelTransactions = fuelResponse.data.results || [];
      
      // Set summary data
      setSummaryData({
        totalVehicles: vehicles.length,
        availableVehicles,
        activeTrips: activeTrips.length,
        pendingMaintenance: pendingMaintenance.length,
        fuelTransactions: fuelTransactions.length,
      });

      // Check for expiring documents (simplified - would be better as a dedicated API endpoint)
      const expiringDocs = [];
      const today = new Date();
      const thirtyDaysFromNow = new Date();
      thirtyDaysFromNow.setDate(today.getDate() + 30);

      vehicles.forEach(vehicle => {
        const checkDate = (date, type, vehicleId, plate) => {
          if (!date) return;
          const expiryDate = new Date(date);
          if (expiryDate > today && expiryDate < thirtyDaysFromNow) {
            expiringDocs.push({
              id: `${vehicleId}-${type}`,
              vehicleId,
              licensePlate: plate,
              documentType: type,
              expiryDate: date,
              vehicleName: `${vehicle.make} ${vehicle.model}`
            });
          }
        };

        checkDate(vehicle.rc_valid_till, 'RC', vehicle.id, vehicle.license_plate);
        checkDate(vehicle.insurance_expiry_date, 'Insurance', vehicle.id, vehicle.license_plate);
        checkDate(vehicle.fitness_expiry, 'Fitness Certificate', vehicle.id, vehicle.license_plate);
        checkDate(vehicle.permit_expiry, 'Permit', vehicle.id, vehicle.license_plate);
        checkDate(vehicle.pollution_cert_expiry, 'Pollution Certificate', vehicle.id, vehicle.license_plate);
      });

      setDocumentsExpiring(expiringDocs);

    } catch (err) {
      console.error('Error loading dashboard data:', err);
      setError('Failed to load dashboard data. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Refresh data when screen is focused
  useFocusEffect(
    React.useCallback(() => {
      loadDashboardData();
      return () => {
        // Cleanup if needed
      };
    }, [])
  );

  // Handle manual refresh
  const onRefresh = () => {
    setRefreshing(true);
    loadDashboardData();
  };

  // Quick actions
  const quickActions = [
    {
      id: 'start-trip',
      title: 'Start Trip',
      icon: 'map-marker-path',
      color: theme.colors.primary,
      onPress: () => navigation.navigate('Trips', { screen: 'StartTrip' }),
    },
    {
      id: 'add-fuel',
      title: 'Add Fuel',
      icon: 'gas-station',
      color: '#4CAF50',
      onPress: () => navigation.navigate('Fuel', { screen: 'AddFuel' }),
    },
    {
      id: 'report-issue',
      title: 'Report Issue',
      icon: 'car-wrench',
      color: '#FF9800',
      onPress: () => navigation.navigate('Maintenance', { screen: 'MaintenanceList' }),
    },
    {
      id: 'view-vehicles',
      title: 'Vehicles',
      icon: 'car-multiple',
      color: '#2196F3',
      onPress: () => navigation.navigate('Vehicles', { screen: 'VehicleList' }),
    },
  ];

  // Render quick action button
  const renderQuickAction = ({ item }) => (
    <TouchableOpacity style={styles.quickActionButton} onPress={item.onPress}>
      <Surface style={[styles.quickActionIcon, { backgroundColor: item.color }]}>
        <MaterialCommunityIcons name={item.icon} size={24} color="#fff" />
      </Surface>
      <Text style={styles.quickActionText}>{item.title}</Text>
    </TouchableOpacity>
  );

  // Render loading state
  if (loading && !refreshing) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={theme.colors.primary} />
        <Text style={styles.loadingText}>Loading dashboard...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Offline warning */}
        {!isConnected && (
          <Card style={styles.offlineCard}>
            <Card.Content style={styles.offlineContent}>
              <MaterialCommunityIcons name="wifi-off" size={20} color="#fff" />
              <Text style={styles.offlineText}>
                You're offline. Some data may not be up to date.
              </Text>
            </Card.Content>
          </Card>
        )}

        {/* User greeting */}
        <View style={styles.userGreeting}>
          <View style={styles.greetingTextContainer}>
            <Text style={styles.greetingText}>
              Hello, {userProfile?.full_name || 'User'}
            </Text>
            <Text style={styles.dateText}>
              {moment().format('dddd, MMMM D, YYYY')}
            </Text>
          </View>
          <Avatar.Image
            size={50}
            source={
              userProfile?.profile_image
                ? { uri: userProfile.profile_image }
                : require('../../../assets/default-avatar.png')
            }
          />
        </View>

        {/* Error message */}
        {error && (
          <Card style={styles.errorCard}>
            <Card.Content>
              <Text style={styles.errorText}>{error}</Text>
              <Button mode="contained" onPress={loadDashboardData} style={styles.retryButton}>
                Retry
              </Button>
            </Card.Content>
          </Card>
        )}

        {/* Summary cards */}
        <View style={styles.summaryContainer}>
          <Card style={styles.summaryCard}>
            <Card.Content style={styles.summaryContent}>
              <MaterialCommunityIcons name="car" size={24} color={theme.colors.primary} />
              <View style={styles.summaryTextContainer}>
                <Text style={styles.summaryLabel}>Total Vehicles</Text>
                <Text style={styles.summaryValue}>{summaryData.totalVehicles}</Text>
              </View>
            </Card.Content>
          </Card>
          
          <Card style={styles.summaryCard}>
            <Card.Content style={styles.summaryContent}>
              <MaterialCommunityIcons name="car-key" size={24} color="#4CAF50" />
              <View style={styles.summaryTextContainer}>
                <Text style={styles.summaryLabel}>Available</Text>
                <Text style={styles.summaryValue}>{summaryData.availableVehicles}</Text>
              </View>
            </Card.Content>
          </Card>
          
          <Card style={styles.summaryCard}>
            <Card.Content style={styles.summaryContent}>
              <MaterialCommunityIcons name="map-marker-path" size={24} color="#FF9800" />
              <View style={styles.summaryTextContainer}>
                <Text style={styles.summaryLabel}>Active Trips</Text>
                <Text style={styles.summaryValue}>{summaryData.activeTrips}</Text>
              </View>
            </Card.Content>
          </Card>
          
          <Card style={styles.summaryCard}>
            <Card.Content style={styles.summaryContent}>
              <MaterialCommunityIcons name="wrench" size={24} color="#F44336" />
              <View style={styles.summaryTextContainer}>
                <Text style={styles.summaryLabel}>Maintenance</Text>
                <Text style={styles.summaryValue}>{summaryData.pendingMaintenance}</Text>
              </View>
            </Card.Content>
          </Card>
        </View>

        {/* Quick actions */}
        <Card style={styles.sectionCard}>
          <Card.Title title="Quick Actions" />
          <Card.Content>
            <FlatList
              data={quickActions}
              renderItem={renderQuickAction}
              keyExtractor={(item) => item.id}
              horizontal
              showsHorizontalScrollIndicator={false}
              contentContainerStyle={styles.quickActionsContainer}
            />
          </Card.Content>
        </Card>

        {/* Documents expiring soon */}
        {documentsExpiring.length > 0 && (
          <Card style={styles.sectionCard}>
            <Card.Title
              title="Documents Expiring Soon"
              left={(props) => (
                <Avatar.Icon {...props} icon="calendar-alert" style={{ backgroundColor: '#FF9800' }} />
              )}
              right={(props) => (
                <Badge {...props} style={styles.badgeStyle}>
                  {documentsExpiring.length}
                </Badge>
              )}
            />
            <Card.Content>
              {documentsExpiring.slice(0, 3).map((doc) => (
                <List.Item
                  key={doc.id}
                  title={doc.documentType}
                  description={`${doc.vehicleName} (${doc.licensePlate})`}
                  left={(props) => <List.Icon {...props} icon="file-document-outline" />}
                  right={(props) => (
                    <Text style={styles.expiryDate}>
                      Expires: {moment(doc.expiryDate).format('MMM D, YYYY')}
                    </Text>
                  )}
                  onPress={() => navigation.navigate('Vehicles', {
                    screen: 'VehicleDetail',
                    params: { vehicleId: doc.vehicleId }
                  })}
                />
              ))}
              {documentsExpiring.length > 3 && (
                <Button
                  mode="text"
                  onPress={() => navigation.navigate('Vehicles', { screen: 'VehicleList' })}
                >
                  View All ({documentsExpiring.length})
                </Button>
              )}
            </Card.Content>
          </Card>
        )}

        {/* Recent trips */}
        <Card style={styles.sectionCard}>
          <Card.Title
            title="Recent Trips"
            left={(props) => (
              <Avatar.Icon {...props} icon="map-marker-path" style={{ backgroundColor: theme.colors.primary }} />
            )}
          />
          <Card.Content>
            {recentTrips.length > 0 ? (
              recentTrips.map((trip) => (
                <TouchableOpacity
                  key={trip.id}
                  onPress={() => navigation.navigate('Trips', {
                    screen: 'TripDetail',
                    params: { tripId: trip.id }
                  })}
                >
                  <View style={styles.tripItem}>
                    <View style={styles.tripInfo}>
                      <Text style={styles.tripVehicle}>
                        {trip.vehicle.make} {trip.vehicle.model} ({trip.vehicle.license_plate})
                      </Text>
                      <Text style={styles.tripRoute}>
                        {trip.origin} → {trip.destination}
                      </Text>
                      <View style={styles.tripDetails}>
                        <Text style={styles.tripDate}>
                          {moment(trip.end_time).format('MMM D, YYYY')}
                        </Text>
                        <Text style={styles.tripDistance}>
                          {trip.distance} km
                        </Text>
                        <Text style={styles.tripDuration}>
                          {trip.duration_display}
                        </Text>
                      </View>
                    </View>
                    <IconButton
                      icon="chevron-right"
                      size={20}
                      onPress={() => navigation.navigate('Trips', {
                        screen: 'TripDetail',
                        params: { tripId: trip.id }
                      })}
                    />
                  </View>
                  <Divider />
                </TouchableOpacity>
              ))
            ) : (
              <Text style={styles.emptyListText}>No recent trips found</Text>
            )}
            <Button
              mode="text"
              onPress={() => navigation.navigate('Trips', { screen: 'TripList' })}
              style={styles.viewAllButton}
            >
              View All Trips
            </Button>
          </Card.Content>
        </Card>

        {/* Upcoming maintenance */}
        <Card style={styles.sectionCard}>
          <Card.Title
            title="Upcoming Maintenance"
            left={(props) => (
              <Avatar.Icon {...props} icon="wrench" style={{ backgroundColor: '#F44336' }} />
            )}
          />
          <Card.Content>
            {upcomingMaintenance.length > 0 ? (
              upcomingMaintenance.map((maintenance) => (
                <TouchableOpacity
                  key={maintenance.id}
                  onPress={() => navigation.navigate('Maintenance', {
                    screen: 'MaintenanceDetail',
                    params: { maintenanceId: maintenance.id }
                  })}
                >
                  <View style={styles.maintenanceItem}>
                    <View style={styles.maintenanceInfo}>
                      <Text style={styles.maintenanceType}>
                        {maintenance.maintenance_type}
                      </Text>
                      <Text style={styles.maintenanceVehicle}>
                        {maintenance.vehicle.make} {maintenance.vehicle.model} ({maintenance.vehicle.license_plate})
                      </Text>
                      <Text style={styles.maintenanceDate}>
                        Scheduled: {moment(maintenance.scheduled_date).format('MMM D, YYYY')}
                      </Text>
                    </View>
                    <IconButton
                      icon="chevron-right"
                      size={20}
                      onPress={() => navigation.navigate('Maintenance', {
                        screen: 'MaintenanceDetail',
                        params: { maintenanceId: maintenance.id }
                      })}
                    />
                  </View>
                  <Divider />
                </TouchableOpacity>
              ))
            ) : (
              <Text style={styles.emptyListText}>No upcoming maintenance scheduled</Text>
            )}
            <Button
              mode="text"
              onPress={() => navigation.navigate('Maintenance', { screen: 'MaintenanceList' })}
              style={styles.viewAllButton}
            >
              View All Maintenance
            </Button>
          </Card.Content>
        </Card>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollContent: {
    padding: 16,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 10,
    fontSize: 16,
  },
  offlineCard: {
    marginBottom: 16,
    backgroundColor: '#f44336',
  },
  offlineContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  offlineText: {
    color: '#fff',
    marginLeft: 8,
  },
  userGreeting: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 20,
  },
  greetingTextContainer: {
    flex: 1,
  },
  greetingText: {
    fontSize: 22,
    fontWeight: 'bold',
  },
  dateText: {
    fontSize: 14,
    color: '#666',
    marginTop: 4,
  },
  errorCard: {
    marginBottom: 16,
    backgroundColor: '#ffebee',
  },
  errorText: {
    color: '#d32f2f',
    marginBottom: 10,
  },
  retryButton: {
    marginTop: 10,
  },
  summaryContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  summaryCard: {
    width: '48%',
    marginBottom: 10,
  },
  summaryContent: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  summaryTextContainer: {
    marginLeft: 10,
  },
  summaryLabel: {
    fontSize: 14,
    color: '#666',
  },
  summaryValue: {
    fontSize: 20,
    fontWeight: 'bold',
  },
  sectionCard: {
    marginBottom: 16,
  },
  quickActionsContainer: {
    paddingVertical: 8,
  },
  quickActionButton: {
    alignItems: 'center',
    marginRight: 20,
    width: 80,
  },
  quickActionIcon: {
    width: 50,
    height: 50,
    borderRadius: 25,
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 8,
  },
  quickActionText: {
    fontSize: 12,
    textAlign: 'center',
  },
  badgeStyle: {
    marginRight: 16,
  },
  expiryDate: {
    fontSize: 12,
    color: '#F44336',
  },
  tripItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  tripInfo: {
    flex: 1,
  },
  tripVehicle: {
    fontWeight: 'bold',
  },
  tripRoute: {
    fontSize: 14,
    marginTop: 4,
  },
  tripDetails: {
    flexDirection: 'row',
    marginTop: 4,
  },
  tripDate: {
    fontSize: 12,
    color: '#666',
    marginRight: 10,
  },
  tripDistance: {
    fontSize: 12,
    color: '#666',
    marginRight: 10,
  },
  tripDuration: {
    fontSize: 12,
    color: '#666',
  },
  maintenanceItem: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingVertical: 10,
  },
  maintenanceInfo: {
    flex: 1,
  },
  maintenanceType: {
    fontWeight: 'bold',
  },
  maintenanceVehicle: {
    fontSize: 14,
    marginTop: 4,
  },
  maintenanceDate: {
    fontSize: 12,
    color: '#F44336',
    marginTop: 4,
  },
  emptyListText: {
    textAlign: 'center',
    color: '#666',
    fontStyle: 'italic',
    paddingVertical: 10,
  },
  viewAllButton: {
    marginTop: 10,
  },
});

export default DashboardScreen;

import React, { useState, useEffect, useContext } from 'react';
import {
  View,
  FlatList,
  StyleSheet,
  TouchableOpacity,
  RefreshControl,
  Image,
} from 'react-native';
import {
  Text,
  Searchbar,
  Chip,
  Card,
  Title,
  Paragraph,
  Badge,
  ActivityIndicator,
  Button,
  IconButton,
  Menu,
  Divider,
  useTheme,
  FAB,
} from 'react-native-paper';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from '@react-navigation/native';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import { vehiclesAPI } from '../../services/apiService';
import { NetworkContext } from '../../context/NetworkContext';

const VehicleListScreen = ({ navigation }) => {
  const theme = useTheme();
  const { isConnected } = useContext(NetworkContext);
  
  // State variables
  const [vehicles, setVehicles] = useState([]);
  const [filteredVehicles, setFilteredVehicles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [error, setError] = useState(null);
  const [filterMenuVisible, setFilterMenuVisible] = useState(false);
  const [activeFilters, setActiveFilters] = useState([]);
  const [sortOrder, setSortOrder] = useState('make_asc');
  
  // Filter options
  const filterOptions = [
    { key: 'status_available', label: 'Available', value: 'status=available' },
    { key: 'status_in_use', label: 'In Use', value: 'status=in_use' },
    { key: 'status_maintenance', label: 'Under Maintenance', value: 'status=maintenance' },
    { key: 'company_owned', label: 'Company Owned', value: 'company_owned=yes' },
    { key: 'not_company_owned', label: 'Not Company Owned', value: 'company_owned=no' },
  ];
  
  // Sort options
  const sortOptions = [
    { key: 'make_asc', label: 'Make (A-Z)', value: 'make' },
    { key: 'make_desc', label: 'Make (Z-A)', value: '-make' },
    { key: 'year_asc', label: 'Year (Oldest)', value: 'year' },
    { key: 'year_desc', label: 'Year (Newest)', value: '-year' },
    { key: 'license_plate', label: 'License Plate', value: 'license_plate' },
  ];
  
  // Load vehicles data
  const loadVehicles = async () => {
    setLoading(true);
    setError(null);
    
    try {
      // Build query parameters from active filters
      const params = {};
      
      // Add search query if exists
      if (searchQuery) {
        params.search = searchQuery;
      }
      
      // Add filters
      activeFilters.forEach(filter => {
        const [key, value] = filter.split('=');
        params[key] = value;
      });
      
      // Add sort order
      const sortOption = sortOptions.find(option => option.key === sortOrder);
      if (sortOption) {
        params.ordering = sortOption.value;
      }
      
      const response = await vehiclesAPI.getAll(params);
      setVehicles(response.data.results || []);
      setFilteredVehicles(response.data.results || []);
    } catch (err) {
      console.error('Error loading vehicles:', err);
      setError('Failed to load vehicles. Please try again.');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };
  
  // Load data when screen is focused
  useFocusEffect(
    React.useCallback(() => {
      loadVehicles();
      return () => {
        // Cleanup if needed
      };
    }, [searchQuery, activeFilters, sortOrder])
  );
  
  // Handle search
  const onChangeSearch = (query) => {
    setSearchQuery(query);
  };
  
  // Handle refresh
  const onRefresh = () => {
    setRefreshing(true);
    loadVehicles();
  };
  
  // Toggle filter
  const toggleFilter = (filterValue) => {
    if (activeFilters.includes(filterValue)) {
      setActiveFilters(activeFilters.filter(filter => filter !== filterValue));
    } else {
      setActiveFilters([...activeFilters, filterValue]);
    }
  };
  
  // Clear all filters
  const clearFilters = () => {
    setActiveFilters([]);
    setSearchQuery('');
  };
  
  // Get status color
  const getStatusColor = (status) => {
    switch (status) {
      case 'available':
        return '#4CAF50';
      case 'in_use':
        return '#2196F3';
      case 'maintenance':
        return '#FF9800';
      case 'retired':
        return '#9E9E9E';
      default:
        return '#9E9E9E';
    }
  };
  
  // Render vehicle item
  const renderVehicleItem = ({ item }) => (
    <TouchableOpacity
      onPress={() => navigation.navigate('VehicleDetail', { vehicleId: item.id })}
    >
      <Card style={styles.vehicleCard}>
        <Card.Content>
          <View style={styles.vehicleHeader}>
            <View style={styles.vehicleInfo}>
              <Title style={styles.vehicleTitle}>
                {item.make} {item.model} ({item.year})
              </Title>
              <Paragraph style={styles.licensePlate}>{item.license_plate}</Paragraph>
            </View>
            <Badge
              style={[
                styles.statusBadge,
                { backgroundColor: getStatusColor(item.status) }
              ]}
            >
              {item.status_display}
            </Badge>
          </View>
          
          <View style={styles.vehicleImageContainer}>
            {item.image_url ? (
              <Image
                source={{ uri: item.image_url }}
                style={styles.vehicleImage}
                resizeMode="cover"
              />
            ) : (
              <View style={styles.noImageContainer}>
                <MaterialCommunityIcons name="car" size={40} color="#ccc" />
                <Text style={styles.noImageText}>No Image</Text>
              </View>
            )}
          </View>
          
          <View style={styles.vehicleDetails}>
            <View style={styles.detailItem}>
              <MaterialCommunityIcons name="fuel" size={16} color="#666" />
              <Text style={styles.detailText}>{item.fuel_type || 'N/A'}</Text>
            </View>
            
            <View style={styles.detailItem}>
              <MaterialCommunityIcons name="account" size={16} color="#666" />
              <Text style={styles.detailText}>
                {item.assigned_driver || 'Unassigned'}
              </Text>
            </View>
            
            <View style={styles.detailItem}>
              <MaterialCommunityIcons name="gauge" size={16} color="#666" />
              <Text style={styles.detailText}>{item.current_odometer} km</Text>
            </View>
          </View>
          
          {item.current_driver && (
            <View style={styles.currentDriver}>
              <Text style={styles.currentDriverLabel}>Current Driver:</Text>
              <Text style={styles.currentDriverName}>
                {item.current_driver.full_name}
              </Text>
            </View>
          )}
          
          {!item.documents_valid && (
            <View style={styles.documentWarning}>
              <MaterialCommunityIcons name="alert-circle" size={16} color="#F44336" />
              <Text style={styles.documentWarningText}>
                Documents require attention
              </Text>
            </View>
          )}
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );
  
  // Render empty state
  const renderEmptyList = () => (
    <View style={styles.emptyContainer}>
      <MaterialCommunityIcons name="car-off" size={64} color="#ccc" />
      <Text style={styles.emptyText}>No vehicles found</Text>
      {(activeFilters.length > 0 || searchQuery) && (
        <Button mode="outlined" onPress={clearFilters} style={styles.clearButton}>
          Clear Filters
        </Button>
      )}
    </View>
  );
  
  // Render filter chips
  const renderFilterChips = () => {
    const activeFilterLabels = activeFilters.map(filterValue => {
      const filter = filterOptions.find(option => option.value === filterValue);
      return filter ? filter.label : filterValue;
    });
    
    if (activeFilterLabels.length === 0) {
      return null;
    }
    
    return (
      <View style={styles.filterChipsContainer}>
        <ScrollView horizontal showsHorizontalScrollIndicator={false}>
          {activeFilterLabels.map((label, index) => (
            <Chip
              key={index}
              onClose={() => toggleFilter(activeFilters[index])}
              style={styles.filterChip}
              mode="outlined"
            >
              {label}
            </Chip>
          ))}
          {activeFilterLabels.length > 0 && (
            <Chip
              onPress={clearFilters}
              style={styles.clearChip}
              mode="outlined"
            >
              Clear All
            </Chip>
          )}
        </ScrollView>
      </View>
    );
  };
  
  return (
    <SafeAreaView style={styles.container}>
      {/* Offline warning */}
      {!isConnected && (
        <View style={styles.offlineWarning}>
          <MaterialCommunityIcons name="wifi-off" size={16} color="#fff" />
          <Text style={styles.offlineText}>
            You're offline. Some features may be limited.
          </Text>
        </View>
      )}
      
      {/* Search and filter header */}
      <View style={styles.header}>
        <Searchbar
          placeholder="Search vehicles..."
          onChangeText={onChangeSearch}
          value={searchQuery}
          style={styles.searchBar}
          onSubmitEditing={loadVehicles}
        />
        
        <View style={styles.filterContainer}>
          <Menu
            visible={filterMenuVisible}
            onDismiss={() => setFilterMenuVisible(false)}
            anchor={
              <IconButton
                icon="filter-variant"
                size={24}
                onPress={() => setFilterMenuVisible(true)}
              />
            }
          >
            <Menu.Item
              title="Sort By"
              disabled
              titleStyle={{ fontWeight: 'bold' }}
            />
            <Divider />
            {sortOptions.map((option) => (
              <Menu.Item
                key={option.key}
                title={option.label}
                onPress={() => {
                  setSortOrder(option.key);
                  setFilterMenuVisible(false);
                }}
                leadingIcon={sortOrder === option.key ? 'check' : undefined}
              />
            ))}
            <Divider />
            <Menu.Item
              title="Filter By"
              disabled
              titleStyle={{ fontWeight: 'bold' }}
            />
            <Divider />
            {filterOptions.map((option) => (
              <Menu.Item
                key={option.key}
                title={option.label}
                onPress={() => {
                  toggleFilter(option.value);
                  setFilterMenuVisible(false);
                }}
                leadingIcon={
                  activeFilters.includes(option.value) ? 'check' : undefined
                }
              />
            ))}
            <Divider />
            <Menu.Item
              title="Clear All Filters"
              onPress={() => {
                clearFilters();
                setFilterMenuVisible(false);
              }}
              leadingIcon="filter-remove"
            />
          </Menu>
        </View>
      </View>
      
      {/* Active filters */}
      {renderFilterChips()}
      
      {/* Error message */}
      {error && (
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>{error}</Text>
          <Button mode="contained" onPress={loadVehicles} style={styles.retryButton}>
            Retry
          </Button>
        </View>
      )}
      
      {/* Vehicle list */}
      {loading && !refreshing ? (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={theme.colors.primary} />
          <Text style={styles.loadingText}>Loading vehicles...</Text>
        </View>
      ) : (
        <FlatList
          data={filteredVehicles}
          renderItem={renderVehicleItem}
          keyExtractor={(item) => item.id.toString()}
          contentContainerStyle={styles.listContent}
          ListEmptyComponent={renderEmptyList}
          refreshControl={
            <RefreshControl refreshing={refreshing} onPress={onRefresh} />
          }
        />
      )}
      
      {/* FAB for adding new vehicle (if user has permission) */}
      <FAB
        style={[styles.fab, { backgroundColor: theme.colors.primary }]}
        icon="plus"
        onPress={() => navigation.navigate('AddVehicle')}
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#fff',
  },
  searchBar: {
    flex: 1,
    marginRight: 8,
    elevation: 0,
    backgroundColor: '#f0f0f0',
  },
  filterContainer: {
    flexDirection: 'row',
  },
  filterChipsContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: '#eee',
  },
  filterChip: {
    marginRight: 8,
  },
  clearChip: {
    marginRight: 8,
    backgroundColor: '#ffebee',
  },
  listContent: {
    padding: 16,
    paddingBottom: 80, // Space for FAB
  },
  vehicleCard: {
    marginBottom: 16,
    elevation: 2,
  },
  vehicleHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
  },
  vehicleInfo: {
    flex: 1,
  },
  vehicleTitle: {
    fontSize: 16,
    fontWeight: 'bold',
  },
  licensePlate: {
    fontSize: 14,
    marginTop: 2,
  },
  statusBadge: {
    alignSelf: 'flex-start',
  },
  vehicleImageContainer: {
    height: 120,
    marginVertical: 10,
    borderRadius: 8,
    overflow: 'hidden',
    backgroundColor: '#f0f0f0',
  },
  vehicleImage: {
    width: '100%',
    height: '100%',
  },
  noImageContainer: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center',
  },
  noImageText: {
    color: '#999',
    marginTop: 8,
  },
  vehicleDetails: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginTop: 8,
  },
  detailItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  detailText: {
    marginLeft: 4,
    fontSize: 14,
    color: '#666',
  },
  currentDriver: {
    flexDirection: 'row',
    marginTop: 8,
    padding: 8,
    backgroundColor: '#e3f2fd',
    borderRadius: 4,
  },
  currentDriverLabel: {
    fontWeight: 'bold',
    marginRight: 4,
  },
  currentDriverName: {
    flex: 1,
  },
  documentWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
    padding: 8,
    backgroundColor: '#ffebee',
    borderRadius: 4,
  },
  documentWarningText: {
    marginLeft: 4,
    color: '#F44336',
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
  emptyContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    padding: 20,
  },
  emptyText: {
    fontSize: 16,
    color: '#666',
    marginTop: 10,
    marginBottom: 20,
  },
  clearButton: {
    marginTop: 10,
  },
  errorContainer: {
    padding: 16,
    backgroundColor: '#ffebee',
    margin: 16,
    borderRadius: 8,
  },
  errorText: {
    color: '#d32f2f',
    marginBottom: 10,
  },
  retryButton: {
    marginTop: 10,
  },
  offlineWarning: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#f44336',
    padding: 8,
    justifyContent: 'center',
  },
  offlineText: {
    color: '#fff',
    marginLeft: 8,
  },
  fab: {
    position: 'absolute',
    margin: 16,
    right: 0,
    bottom: 0,
  },
});

export default VehicleListScreen;

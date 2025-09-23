import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  ScrollView,
  TouchableOpacity,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TextInput } from '../components/TextInput';
import { LoadingButton } from '../components/LoadingButton';

interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  profile?: {
    university?: string;
    course?: string;
    destination_country?: string;
    destination_city?: string;
    origin_country?: string;
    origin_city?: string;
  };
}

export default function SearchScreen() {
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedFilters, setSelectedFilters] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<User[]>([]);
  const [loading, setLoading] = useState(false);

  const filterOptions = [
    { id: 'country', label: 'Country', icon: 'flag-outline' },
    { id: 'city', label: 'City', icon: 'location-outline' },
    { id: 'university', label: 'University', icon: 'school-outline' },
    { id: 'course', label: 'Course', icon: 'book-outline' },
    { id: 'origin_country', label: 'Origin Country', icon: 'globe-outline' },
  ];

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      Alert.alert('Search Error', 'Please enter a search term');
      return;
    }

    setLoading(true);
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const params = new URLSearchParams();
      if (selectedFilters.includes('country')) params.append('country', searchQuery);
      if (selectedFilters.includes('city')) params.append('city', searchQuery);
      if (selectedFilters.includes('university')) params.append('university', searchQuery);
      if (selectedFilters.includes('course')) params.append('course', searchQuery);
      if (selectedFilters.includes('origin_country')) params.append('origin_country', searchQuery);

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/users/search?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Search failed');
      }

      setSearchResults(result.users || []);
    } catch (error) {
      console.error('Search error:', error);
      Alert.alert(
        'Search Error',
        error instanceof Error ? error.message : 'Something went wrong'
      );
    } finally {
      setLoading(false);
    }
  };

  const toggleFilter = (filterId: string) => {
    setSelectedFilters(prev => 
      prev.includes(filterId)
        ? prev.filter(id => id !== filterId)
        : [...prev, filterId]
    );
  };

  const sendConnectionRequest = async (userId: string) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/connections/request`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ to_user_id: userId }),
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to send connection request');
      }

      Alert.alert('Success', 'Connection request sent!');
    } catch (error) {
      console.error('Connection request error:', error);
      Alert.alert(
        'Error',
        error instanceof Error ? error.message : 'Failed to send connection request'
      );
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Find Students</Text>
        <TouchableOpacity style={styles.headerButton}>
          <Ionicons name="filter-outline" size={24} color="#ffffff" />
        </TouchableOpacity>
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Search Section */}
        <View style={styles.searchSection}>
          <TextInput
            placeholder="Search by name, university, course..."
            value={searchQuery}
            onChangeText={setSearchQuery}
            leftIcon="search-outline"
            style={styles.searchInput}
          />

          {/* Filter Chips */}
          <ScrollView 
            horizontal 
            showsHorizontalScrollIndicator={false}
            style={styles.filtersContainer}
          >
            {filterOptions.map((filter) => (
              <TouchableOpacity
                key={filter.id}
                style={[
                  styles.filterChip,
                  selectedFilters.includes(filter.id) && styles.filterChipActive
                ]}
                onPress={() => toggleFilter(filter.id)}
                activeOpacity={0.8}
              >
                <Ionicons 
                  name={filter.icon as keyof typeof Ionicons.glyphMap} 
                  size={16} 
                  color={selectedFilters.includes(filter.id) ? '#ffffff' : '#a0a0a0'} 
                />
                <Text 
                  style={[
                    styles.filterChipText,
                    selectedFilters.includes(filter.id) && styles.filterChipTextActive
                  ]}
                >
                  {filter.label}
                </Text>
              </TouchableOpacity>
            ))}
          </ScrollView>

          <LoadingButton
            title="Search"
            onPress={handleSearch}
            loading={loading}
            style={styles.searchButton}
          />
        </View>

        {/* Results Section */}
        {searchResults.length > 0 && (
          <View style={styles.resultsSection}>
            <Text style={styles.sectionTitle}>
              {searchResults.length} student{searchResults.length !== 1 ? 's' : ''} found
            </Text>

            {searchResults.map((user) => (
              <View key={user.id} style={styles.userCard}>
                <View style={styles.userInfo}>
                  <View style={styles.avatar}>
                    <Text style={styles.avatarText}>
                      {user.first_name[0]}{user.last_name[0]}
                    </Text>
                  </View>
                  
                  <View style={styles.userDetails}>
                    <Text style={styles.userName}>
                      {user.first_name} {user.last_name}
                    </Text>
                    
                    {user.profile?.university && (
                      <Text style={styles.userMeta}>
                        <Ionicons name="school-outline" size={14} color="#a0a0a0" />
                        {' '}{user.profile.university}
                      </Text>
                    )}
                    
                    {user.profile?.course && (
                      <Text style={styles.userMeta}>
                        <Ionicons name="book-outline" size={14} color="#a0a0a0" />
                        {' '}{user.profile.course}
                      </Text>
                    )}
                    
                    {user.profile?.destination_country && (
                      <Text style={styles.userMeta}>
                        <Ionicons name="location-outline" size={14} color="#a0a0a0" />
                        {' '}{user.profile.destination_city}, {user.profile.destination_country}
                      </Text>
                    )}
                  </View>
                </View>

                <TouchableOpacity
                  style={styles.connectButton}
                  onPress={() => sendConnectionRequest(user.id)}
                  activeOpacity={0.8}
                >
                  <Ionicons name="person-add-outline" size={20} color="#6c5ce7" />
                </TouchableOpacity>
              </View>
            ))}
          </View>
        )}

        {/* Empty State */}
        {searchResults.length === 0 && !loading && (
          <View style={styles.emptyState}>
            <Ionicons name="search-outline" size={64} color="#666666" />
            <Text style={styles.emptyStateTitle}>Discover Students</Text>
            <Text style={styles.emptyStateText}>
              Search for students by university, course, location, or name to start connecting
            </Text>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  headerButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  searchSection: {
    padding: 20,
  },
  searchInput: {
    marginBottom: 16,
  },
  filtersContainer: {
    marginBottom: 20,
  },
  filterChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 12,
    borderWidth: 1,
    borderColor: '#404040',
  },
  filterChipActive: {
    backgroundColor: '#6c5ce7',
    borderColor: '#6c5ce7',
  },
  filterChipText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginLeft: 6,
    fontWeight: '500',
  },
  filterChipTextActive: {
    color: '#ffffff',
  },
  searchButton: {
    marginTop: 8,
  },
  resultsSection: {
    paddingHorizontal: 20,
    paddingBottom: 20,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  userCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    backgroundColor: '#2a2a2a',
    padding: 16,
    borderRadius: 16,
    marginBottom: 12,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#6c5ce7',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  avatarText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  userDetails: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  userMeta: {
    fontSize: 12,
    color: '#a0a0a0',
    marginBottom: 2,
  },
  connectButton: {
    padding: 12,
    backgroundColor: '#252545',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#6c5ce7',
  },
  emptyState: {
    alignItems: 'center',
    paddingHorizontal: 40,
    paddingVertical: 60,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#ffffff',
    marginTop: 16,
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 14,
    color: '#a0a0a0',
    textAlign: 'center',
    lineHeight: 20,
  },
});
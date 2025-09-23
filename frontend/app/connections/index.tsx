import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  ScrollView,
  Alert,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';
import { LoadingButton } from '../components/LoadingButton';

interface ConnectionRequest {
  id: string;
  from_user_id: string;
  to_user_id: string;
  status: string;
  created_at: string;
}

interface ConnectionRequestWithUser extends ConnectionRequest {
  user: {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
    profile?: {
      university?: string;
      course?: string;
      origin_country?: string;
      destination_country?: string;
    };
  };
}

export default function ConnectionsScreen() {
  const [incomingRequests, setIncomingRequests] = useState<ConnectionRequestWithUser[]>([]);
  const [outgoingRequests, setOutgoingRequests] = useState<ConnectionRequestWithUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [processingRequestId, setProcessingRequestId] = useState<string | null>(null);
  const router = useRouter();

  useFocusEffect(
    useCallback(() => {
      loadConnectionRequests();
    }, [])
  );

  const loadConnectionRequests = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/connections/requests`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        
        // Fetch user details for each request
        const incomingWithUsers = await Promise.all(
          (data.incoming || []).map(async (request: ConnectionRequest) => {
            const userDetails = await fetchUserDetails(request.from_user_id, token);
            return {
              ...request,
              user: userDetails,
            };
          })
        );

        const outgoingWithUsers = await Promise.all(
          (data.outgoing || []).map(async (request: ConnectionRequest) => {
            const userDetails = await fetchUserDetails(request.to_user_id, token);
            return {
              ...request,
              user: userDetails,
            };
          })
        );

        setIncomingRequests(incomingWithUsers.filter(req => req.user));
        setOutgoingRequests(outgoingWithUsers.filter(req => req.user));
      } else {
        Alert.alert('Error', 'Failed to load connection requests');
      }
    } catch (error) {
      console.error('Error loading connection requests:', error);
      Alert.alert('Error', 'Failed to load connection requests');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchUserDetails = async (userId: string, token: string) => {
    try {
      // Search for user since we don't have a direct user endpoint
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/users/search?limit=50`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const searchResults = await response.json();
        const user = searchResults.users?.find((u: any) => u.id === userId);
        return user || null;
      }
    } catch (error) {
      console.error('Error fetching user details:', error);
    }
    return null;
  };

  const handleConnectionResponse = async (requestId: string, action: 'accept' | 'reject') => {
    setProcessingRequestId(requestId);

    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/connections/respond?request_id=${requestId}&action=${action}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        Alert.alert(
          'Success', 
          `Connection request ${action}ed successfully!`,
          [
            {
              text: 'OK',
              onPress: () => loadConnectionRequests(),
            },
          ]
        );
      } else {
        const result = await response.json();
        Alert.alert('Error', result.detail || `Failed to ${action} connection request`);
      }
    } catch (error) {
      console.error(`Error ${action}ing connection request:`, error);
      Alert.alert('Error', `Failed to ${action} connection request`);
    } finally {
      setProcessingRequestId(null);
    }
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadConnectionRequests();
  };

  const renderConnectionRequest = (request: ConnectionRequestWithUser, isIncoming: boolean) => (
    <View key={request.id} style={styles.requestCard}>
      <TouchableOpacity
        style={styles.userInfo}
        onPress={() => router.push(`/users/profile/${request.user.id}`)}
        activeOpacity={0.8}
      >
        <View style={styles.avatar}>
          <Text style={styles.avatarText}>
            {request.user.first_name[0]}{request.user.last_name[0]}
          </Text>
        </View>
        
        <View style={styles.userDetails}>
          <Text style={styles.userName}>
            {request.user.first_name} {request.user.last_name}
          </Text>
          
          {request.user.profile?.university && (
            <Text style={styles.userMeta}>
              <Ionicons name="school-outline" size={12} color="#a0a0a0" />
              {' '}{request.user.profile.university}
            </Text>
          )}
          
          {request.user.profile?.course && (
            <Text style={styles.userMeta}>
              <Ionicons name="book-outline" size={12} color="#a0a0a0" />
              {' '}{request.user.profile.course}
            </Text>
          )}
          
          <Text style={styles.requestDate}>
            {new Date(request.created_at).toLocaleDateString()}
          </Text>
        </View>
      </TouchableOpacity>

      {isIncoming ? (
        <View style={styles.actionButtons}>
          <LoadingButton
            title="Accept"
            onPress={() => handleConnectionResponse(request.id, 'accept')}
            loading={processingRequestId === request.id}
            style={styles.acceptButton}
            textStyle={styles.acceptButtonText}
          />
          <LoadingButton
            title="Reject"
            onPress={() => handleConnectionResponse(request.id, 'reject')}
            loading={processingRequestId === request.id}
            style={styles.rejectButton}
            textStyle={styles.rejectButtonText}
          />
        </View>
      ) : (
        <View style={styles.pendingBadge}>
          <Text style={styles.pendingText}>Pending</Text>
        </View>
      )}
    </View>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading connections...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      {/* Header */}
      <View style={styles.header}>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => router.back()}
          activeOpacity={0.8}
        >
          <Ionicons name="arrow-back" size={24} color="#ffffff" />
        </TouchableOpacity>
        
        <Text style={styles.headerTitle}>Connections</Text>
        
        <View style={styles.headerRight} />
      </View>

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            colors={['#6c5ce7']}
            tintColor="#6c5ce7"
          />
        }
      >
        {/* Incoming Requests */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Incoming Requests ({incomingRequests.length})
          </Text>
          
          {incomingRequests.length > 0 ? (
            incomingRequests.map(request => renderConnectionRequest(request, true))
          ) : (
            <View style={styles.emptyState}>
              <Ionicons name="person-add-outline" size={48} color="#666666" />
              <Text style={styles.emptyStateText}>No incoming requests</Text>
            </View>
          )}
        </View>

        {/* Outgoing Requests */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>
            Sent Requests ({outgoingRequests.length})
          </Text>
          
          {outgoingRequests.length > 0 ? (
            outgoingRequests.map(request => renderConnectionRequest(request, false))
          ) : (
            <View style={styles.emptyState}>
              <Ionicons name="paper-plane-outline" size={48} color="#666666" />
              <Text style={styles.emptyStateText}>No sent requests</Text>
            </View>
          )}
        </View>

        {/* Tips Section */}
        <View style={styles.tipsSection}>
          <Text style={styles.sectionTitle}>Tips</Text>
          <View style={styles.tip}>
            <Ionicons name="bulb-outline" size={16} color="#6c5ce7" />
            <Text style={styles.tipText}>
              Connect with students from your university or destination country
            </Text>
          </View>
          <View style={styles.tip}>
            <Ionicons name="people-outline" size={16} color="#6c5ce7" />
            <Text style={styles.tipText}>
              Use the search feature to find students with similar interests
            </Text>
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#a0a0a0',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
  },
  headerRight: {
    width: 40,
  },
  content: {
    flex: 1,
  },
  section: {
    paddingHorizontal: 20,
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
    marginTop: 20,
  },
  requestCard: {
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
  requestDate: {
    fontSize: 11,
    color: '#666666',
    marginTop: 4,
  },
  actionButtons: {
    flexDirection: 'column',
    gap: 8,
    minWidth: 80,
  },
  acceptButton: {
    backgroundColor: '#00b894',
    paddingHorizontal: 16,
    paddingVertical: 8,
    minHeight: 32,
  },
  acceptButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  rejectButton: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#e74c3c',
    paddingHorizontal: 16,
    paddingVertical: 8,
    minHeight: 32,
  },
  rejectButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#e74c3c',
  },
  pendingBadge: {
    backgroundColor: '#2a2a2a',
    borderWidth: 1,
    borderColor: '#6c5ce7',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  pendingText: {
    fontSize: 12,
    color: '#6c5ce7',
    fontWeight: '600',
  },
  emptyState: {
    alignItems: 'center',
    paddingVertical: 40,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#666666',
    marginTop: 12,
  },
  tipsSection: {
    paddingHorizontal: 20,
    paddingBottom: 32,
  },
  tip: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#2a2a2a',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  tipText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginLeft: 12,
    flex: 1,
    lineHeight: 20,
  },
});
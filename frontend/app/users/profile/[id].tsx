import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  ScrollView,
  Alert,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LoadingButton } from '../../components/LoadingButton';

interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  phone?: string;
  is_verified: boolean;
  is_student_verified: boolean;
  profile?: {
    age?: number;
    gender?: string;
    bio?: string;
    profile_picture?: string;
    origin_country?: string;
    origin_city?: string;
    destination_country?: string;
    destination_city?: string;
    university?: string;
    course?: string;
    study_level?: string;
  };
}

export default function UserProfileScreen() {
  const { id: userId } = useLocalSearchParams<{ id: string }>();
  const [user, setUser] = useState<User | null>(null);
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [connectionLoading, setConnectionLoading] = useState(false);
  const [connectionStatus, setConnectionStatus] = useState<'none' | 'pending' | 'connected'>('none');
  const router = useRouter();

  useEffect(() => {
    if (userId) {
      loadUserProfile();
      loadCurrentUser();
      checkConnectionStatus();
    }
  }, [userId]);

  const loadCurrentUser = async () => {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      if (userData) {
        setCurrentUser(JSON.parse(userData));
      }
    } catch (error) {
      console.error('Error loading current user:', error);
    }
  };

  const loadUserProfile = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      // For now, we'll search for the user since we don't have a direct user profile endpoint
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
        const foundUser = searchResults.users?.find((u: User) => u.id === userId);
        
        if (foundUser) {
          setUser(foundUser);
        } else {
          Alert.alert('Error', 'User not found');
          router.back();
        }
      } else {
        Alert.alert('Error', 'Failed to load user profile');
        router.back();
      }
    } catch (error) {
      console.error('Error loading user profile:', error);
      Alert.alert('Error', 'Failed to load user profile');
      router.back();
    } finally {
      setLoading(false);
    }
  };

  const checkConnectionStatus = async () => {
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
        const requests = await response.json();
        
        // Check if there's an outgoing request to this user
        const outgoingRequest = requests.outgoing?.find((req: any) => req.to_user_id === userId);
        if (outgoingRequest) {
          setConnectionStatus('pending');
          return;
        }

        // Check if there's an incoming request from this user
        const incomingRequest = requests.incoming?.find((req: any) => req.from_user_id === userId);
        if (incomingRequest) {
          setConnectionStatus('pending');
          return;
        }

        // TODO: Check if already connected (would need a connections endpoint)
        setConnectionStatus('none');
      }
    } catch (error) {
      console.error('Error checking connection status:', error);
    }
  };

  const handleSendConnectionRequest = async () => {
    if (!userId) return;

    setConnectionLoading(true);

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
          body: JSON.stringify({
            to_user_id: userId,
          }),
        }
      );

      if (response.ok) {
        setConnectionStatus('pending');
        Alert.alert('Success', 'Connection request sent successfully!');
      } else {
        const result = await response.json();
        Alert.alert('Error', result.detail || 'Failed to send connection request');
      }
    } catch (error) {
      console.error('Error sending connection request:', error);
      Alert.alert('Error', 'Failed to send connection request');
    } finally {
      setConnectionLoading(false);
    }
  };

  const handleStartChat = async () => {
    if (!userId) return;

    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      // Create a conversation with this user
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/chat/conversations`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            participants: [userId],
            is_group_chat: false,
          }),
        }
      );

      if (response.ok) {
        const conversation = await response.json();
        router.push(`/chat/conversation/${conversation.id}`);
      } else {
        Alert.alert('Error', 'Failed to start conversation');
      }
    } catch (error) {
      console.error('Error starting chat:', error);
      Alert.alert('Error', 'Failed to start conversation');
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading profile...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
        <View style={styles.errorContainer}>
          <Text style={styles.errorText}>User not found</Text>
        </View>
      </SafeAreaView>
    );
  }

  const isOwnProfile = currentUser?.id === user.id;

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
        
        <Text style={styles.headerTitle}>Profile</Text>
        
        <View style={styles.headerRight} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatarContainer}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {user.first_name[0]}{user.last_name[0]}
              </Text>
            </View>
          </View>

          <Text style={styles.userName}>
            {user.first_name} {user.last_name}
          </Text>
          
          <Text style={styles.userEmail}>{user.email}</Text>

          {/* Verification Status */}
          <View style={styles.verificationContainer}>
            <View style={[
              styles.verificationBadge,
              user.is_verified ? styles.verifiedBadge : styles.unverifiedBadge
            ]}>
              <Ionicons 
                name={user.is_verified ? "checkmark-circle" : "alert-circle"} 
                size={16} 
                color={user.is_verified ? "#00b894" : "#e74c3c"} 
              />
              <Text style={[
                styles.verificationText,
                user.is_verified ? styles.verifiedText : styles.unverifiedText
              ]}>
                {user.is_verified ? "Email Verified" : "Email Not Verified"}
              </Text>
            </View>

            <View style={[
              styles.verificationBadge,
              user.is_student_verified ? styles.verifiedBadge : styles.unverifiedBadge
            ]}>
              <Ionicons 
                name={user.is_student_verified ? "school" : "school-outline"} 
                size={16} 
                color={user.is_student_verified ? "#6c5ce7" : "#a0a0a0"} 
              />
              <Text style={[
                styles.verificationText,
                user.is_student_verified ? styles.verifiedText : styles.unverifiedText
              ]}>
                {user.is_student_verified ? "Student Verified" : "Not Student Verified"}
              </Text>
            </View>
          </View>

          {/* Action Buttons */}
          {!isOwnProfile && (
            <View style={styles.actionButtons}>
              {connectionStatus === 'none' ? (
                <LoadingButton
                  title="Connect"
                  onPress={handleSendConnectionRequest}
                  loading={connectionLoading}
                  style={styles.connectButton}
                />
              ) : connectionStatus === 'pending' ? (
                <View style={styles.pendingButton}>
                  <Text style={styles.pendingButtonText}>Request Sent</Text>
                </View>
              ) : (
                <TouchableOpacity style={styles.connectedButton}>
                  <Text style={styles.connectedButtonText}>Connected</Text>
                </TouchableOpacity>
              )}

              <TouchableOpacity 
                style={styles.messageButton}
                onPress={handleStartChat}
              >
                <Ionicons name="chatbubble-outline" size={20} color="#6c5ce7" />
                <Text style={styles.messageButtonText}>Message</Text>
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Profile Bio */}
        {user.profile?.bio && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>About</Text>
            <View style={styles.bioCard}>
              <Text style={styles.bioText}>{user.profile.bio}</Text>
            </View>
          </View>
        )}

        {/* Academic Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Academic Information</Text>
          
          <View style={styles.infoCard}>
            <View style={styles.infoItem}>
              <Ionicons name="school-outline" size={20} color="#a0a0a0" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>University</Text>
                <Text style={styles.infoValue}>
                  {user.profile?.university || 'Not specified'}
                </Text>
              </View>
            </View>

            <View style={styles.infoItem}>
              <Ionicons name="book-outline" size={20} color="#a0a0a0" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Course</Text>
                <Text style={styles.infoValue}>
                  {user.profile?.course || 'Not specified'}
                </Text>
              </View>
            </View>

            <View style={styles.infoItem}>
              <Ionicons name="trophy-outline" size={20} color="#a0a0a0" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Study Level</Text>
                <Text style={styles.infoValue}>
                  {user.profile?.study_level || 'Not specified'}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Location Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Location</Text>
          
          <View style={styles.infoCard}>
            <View style={styles.infoItem}>
              <Ionicons name="home-outline" size={20} color="#a0a0a0" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Origin</Text>
                <Text style={styles.infoValue}>
                  {user.profile?.origin_city && user.profile?.origin_country
                    ? `${user.profile.origin_city}, ${user.profile.origin_country}`
                    : 'Not specified'
                  }
                </Text>
              </View>
            </View>

            <View style={styles.infoItem}>
              <Ionicons name="location-outline" size={20} color="#a0a0a0" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Destination</Text>
                <Text style={styles.infoValue}>
                  {user.profile?.destination_city && user.profile?.destination_country
                    ? `${user.profile.destination_city}, ${user.profile.destination_country}`
                    : 'Not specified'
                  }
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Personal Information */}
        {(user.profile?.age || user.profile?.gender || user.phone) && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Personal Information</Text>
            
            <View style={styles.infoCard}>
              {user.profile?.age && (
                <View style={styles.infoItem}>
                  <Ionicons name="person-outline" size={20} color="#a0a0a0" />
                  <View style={styles.infoContent}>
                    <Text style={styles.infoLabel}>Age</Text>
                    <Text style={styles.infoValue}>{user.profile.age}</Text>
                  </View>
                </View>
              )}

              {user.profile?.gender && (
                <View style={styles.infoItem}>
                  <Ionicons name="transgender-outline" size={20} color="#a0a0a0" />
                  <View style={styles.infoContent}>
                    <Text style={styles.infoLabel}>Gender</Text>
                    <Text style={styles.infoValue}>{user.profile.gender}</Text>
                  </View>
                </View>
              )}

              {user.phone && (
                <View style={styles.infoItem}>
                  <Ionicons name="call-outline" size={20} color="#a0a0a0" />
                  <View style={styles.infoContent}>
                    <Text style={styles.infoLabel}>Phone</Text>
                    <Text style={styles.infoValue}>{user.phone}</Text>
                  </View>
                </View>
              )}
            </View>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#a0a0a0',
  },
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  errorText: {
    fontSize: 16,
    color: '#e74c3c',
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
  profileHeader: {
    alignItems: 'center',
    paddingVertical: 32,
    paddingHorizontal: 20,
    backgroundColor: '#252545',
    marginHorizontal: 16,
    marginTop: 16,
    borderRadius: 20,
  },
  avatarContainer: {
    marginBottom: 16,
  },
  avatar: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#6c5ce7',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  userName: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 4,
  },
  userEmail: {
    fontSize: 14,
    color: '#a0a0a0',
    marginBottom: 16,
  },
  verificationContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 24,
  },
  verificationBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 16,
  },
  verifiedBadge: {
    backgroundColor: '#0b3d2e',
  },
  unverifiedBadge: {
    backgroundColor: '#3d1a1a',
  },
  verificationText: {
    fontSize: 12,
    marginLeft: 6,
    fontWeight: '500',
  },
  verifiedText: {
    color: '#00b894',
  },
  unverifiedText: {
    color: '#e74c3c',
  },
  actionButtons: {
    flexDirection: 'row',
    gap: 12,
  },
  connectButton: {
    paddingHorizontal: 24,
    paddingVertical: 10,
  },
  pendingButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#6c5ce7',
  },
  pendingButtonText: {
    color: '#6c5ce7',
    fontSize: 16,
    fontWeight: '600',
  },
  connectedButton: {
    paddingHorizontal: 24,
    paddingVertical: 12,
    backgroundColor: '#00b894',
    borderRadius: 12,
  },
  connectedButtonText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '600',
  },
  messageButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#6c5ce7',
    borderRadius: 12,
  },
  messageButtonText: {
    color: '#6c5ce7',
    fontSize: 16,
    fontWeight: '600',
    marginLeft: 8,
  },
  section: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 12,
  },
  bioCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 16,
  },
  bioText: {
    fontSize: 16,
    color: '#ffffff',
    lineHeight: 22,
  },
  infoCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 4,
  },
  infoItem: {
    flexDirection: 'row',
    alignItems: 'center',
    padding: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  infoContent: {
    marginLeft: 16,
    flex: 1,
  },
  infoLabel: {
    fontSize: 12,
    color: '#a0a0a0',
    marginBottom: 2,
  },
  infoValue: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: '500',
  },
});
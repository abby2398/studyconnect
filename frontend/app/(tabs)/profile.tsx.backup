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
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
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

export default function ProfileScreen() {
  const [user, setUser] = useState<User | null>(null);
  const router = useRouter();

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      if (userData) {
        setUser(JSON.parse(userData));
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const handleLogout = async () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            try {
              await AsyncStorage.multiRemove(['auth_token', 'user_data']);
              router.replace('/auth/welcome');
            } catch (error) {
              console.error('Logout error:', error);
            }
          },
        },
      ]
    );
  };

  const profileCompleteness = () => {
    if (!user?.profile) return 0;
    
    const fields = [
      'age', 'gender', 'bio', 'origin_country', 'origin_city',
      'destination_country', 'destination_city', 'university', 'course', 'study_level'
    ];
    
    const completedFields = fields.filter(field => 
      user.profile![field as keyof typeof user.profile]
    ).length;
    
    return Math.round((completedFields / fields.length) * 100);
  };

  if (!user) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Profile</Text>
        <TouchableOpacity style={styles.headerButton}>
          <Ionicons name="settings-outline" size={24} color="#ffffff" />
        </TouchableOpacity>
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
            
            <TouchableOpacity style={styles.editAvatarButton}>
              <Ionicons name="camera" size={16} color="#ffffff" />
            </TouchableOpacity>
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
                {user.is_student_verified ? "Student Verified" : "Verify Student Status"}
              </Text>
            </View>
          </View>

          <TouchableOpacity 
            style={styles.editProfileButton} 
            activeOpacity={0.8}
            onPress={() => router.push('/profile/edit')}
          >
            <Text style={styles.editProfileText}>Edit Profile</Text>
            <Ionicons name="chevron-forward" size={16} color="#6c5ce7" />
          </TouchableOpacity>
        </View>

        {/* Profile Completeness */}
        <View style={styles.completenessCard}>
          <View style={styles.completenessHeader}>
            <Text style={styles.completenessTitle}>Profile Completeness</Text>
            <Text style={styles.completenessPercentage}>
              {profileCompleteness()}%
            </Text>
          </View>
          
          <View style={styles.progressBar}>
            <View 
              style={[
                styles.progressFill,
                { width: `${profileCompleteness()}%` }
              ]} 
            />
          </View>
          
          <Text style={styles.completenessDescription}>
            Complete your profile to get better matches and connect with more students
          </Text>
        </View>

        {/* Profile Information */}
        <View style={styles.profileSection}>
          <Text style={styles.sectionTitle}>Personal Information</Text>
          
          <View style={styles.infoCard}>
            <View style={styles.infoItem}>
              <Ionicons name="person-outline" size={20} color="#a0a0a0" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Age</Text>
                <Text style={styles.infoValue}>
                  {user.profile?.age || 'Not specified'}
                </Text>
              </View>
            </View>

            <View style={styles.infoItem}>
              <Ionicons name="transgender-outline" size={20} color="#a0a0a0" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Gender</Text>
                <Text style={styles.infoValue}>
                  {user.profile?.gender || 'Not specified'}
                </Text>
              </View>
            </View>

            <View style={styles.infoItem}>
              <Ionicons name="call-outline" size={20} color="#a0a0a0" />
              <View style={styles.infoContent}>
                <Text style={styles.infoLabel}>Phone</Text>
                <Text style={styles.infoValue}>
                  {user.phone || 'Not specified'}
                </Text>
              </View>
            </View>
          </View>
        </View>

        {/* Academic Information */}
        <View style={styles.profileSection}>
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
        <View style={styles.profileSection}>
          <Text style={styles.sectionTitle}>Location Information</Text>
          
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

        {/* Account Actions */}
        <View style={styles.actionsSection}>
          <TouchableOpacity 
            style={styles.actionItem} 
            activeOpacity={0.8}
            onPress={() => router.push('/connections')}
          >
            <Ionicons name="people-outline" size={24} color="#6c5ce7" />
            <Text style={styles.actionTitle}>My Connections</Text>
            <Ionicons name="chevron-forward" size={20} color="#a0a0a0" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionItem} activeOpacity={0.8}>
            <Ionicons name="shield-checkmark-outline" size={24} color="#00b894" />
            <Text style={styles.actionTitle}>Privacy Settings</Text>
            <Ionicons name="chevron-forward" size={20} color="#a0a0a0" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionItem} activeOpacity={0.8}>
            <Ionicons name="help-circle-outline" size={24} color="#74b9ff" />
            <Text style={styles.actionTitle}>Help & Support</Text>
            <Ionicons name="chevron-forward" size={20} color="#a0a0a0" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionItem} activeOpacity={0.8}>
            <Ionicons name="document-text-outline" size={24} color="#fdcb6e" />
            <Text style={styles.actionTitle}>Terms & Privacy Policy</Text>
            <Ionicons name="chevron-forward" size={20} color="#a0a0a0" />
          </TouchableOpacity>

          <TouchableOpacity 
            style={[styles.actionItem, styles.logoutItem]} 
            onPress={handleLogout}
            activeOpacity={0.8}
          >
            <Ionicons name="log-out-outline" size={24} color="#e74c3c" />
            <Text style={[styles.actionTitle, styles.logoutText]}>Logout</Text>
          </TouchableOpacity>
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
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    fontSize: 16,
    color: '#a0a0a0',
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
    position: 'relative',
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
  editAvatarButton: {
    position: 'absolute',
    bottom: -4,
    right: -4,
    width: 32,
    height: 32,
    borderRadius: 16,
    backgroundColor: '#2a2a2a',
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 3,
    borderColor: '#252545',
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
  editProfileButton: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 12,
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#6c5ce7',
    borderRadius: 12,
  },
  editProfileText: {
    fontSize: 16,
    color: '#6c5ce7',
    fontWeight: '600',
    marginRight: 8,
  },
  completenessCard: {
    backgroundColor: '#2a2a2a',
    marginHorizontal: 16,
    marginVertical: 16,
    padding: 20,
    borderRadius: 16,
  },
  completenessHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  completenessTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  completenessPercentage: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#6c5ce7',
  },
  progressBar: {
    height: 8,
    backgroundColor: '#404040',
    borderRadius: 4,
    marginBottom: 12,
  },
  progressFill: {
    height: '100%',
    backgroundColor: '#6c5ce7',
    borderRadius: 4,
  },
  completenessDescription: {
    fontSize: 12,
    color: '#a0a0a0',
    lineHeight: 18,
  },
  profileSection: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 12,
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
  actionsSection: {
    paddingHorizontal: 16,
    paddingBottom: 32,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    padding: 16,
    borderRadius: 16,
    marginBottom: 12,
  },
  actionTitle: {
    fontSize: 16,
    color: '#ffffff',
    fontWeight: '500',
    flex: 1,
    marginLeft: 16,
  },
  logoutItem: {
    marginTop: 16,
  },
  logoutText: {
    color: '#e74c3c',
  },
});
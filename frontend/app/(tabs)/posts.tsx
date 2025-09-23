import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';

export default function PostsScreen() {
  const [user, setUser] = useState(null);
  const [refreshing, setRefreshing] = useState(false);
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

  const onRefresh = async () => {
    setRefreshing(true);
    await loadUserData();
    setRefreshing(false);
  };

  const handleCreatePost = () => {
    // Navigate to create post screen
    router.push('/posts/create');
  };

  const handleAskAI = () => {
    // Navigate to AI assistant screen
    router.push('/ai/assistant');
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>StudyConnect</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={handleAskAI}
            activeOpacity={0.8}
          >
            <Ionicons name="bulb-outline" size={24} color="#6c5ce7" />
          </TouchableOpacity>
          <TouchableOpacity 
            style={styles.headerButton}
            activeOpacity={0.8}
          >
            <Ionicons name="notifications-outline" size={24} color="#ffffff" />
          </TouchableOpacity>
        </View>
      </View>

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#6c5ce7"
          />
        }
      >
        {/* Welcome Section */}
        {user && (
          <View style={styles.welcomeSection}>
            <Text style={styles.welcomeText}>
              Welcome back, {user.first_name}! 👋
            </Text>
            {!user.is_verified && (
              <View style={styles.verificationBanner}>
                <Ionicons name="warning-outline" size={20} color="#f39c12" />
                <Text style={styles.verificationText}>
                  Please verify your email to start posting
                </Text>
                <TouchableOpacity style={styles.verifyButton}>
                  <Text style={styles.verifyButtonText}>Verify</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}

        {/* Create Post Section */}
        <View style={styles.createPostSection}>
          <TouchableOpacity 
            style={styles.createPostButton}
            onPress={handleCreatePost}
            activeOpacity={0.8}
          >
            <Ionicons name="add-circle-outline" size={24} color="#6c5ce7" />
            <Text style={styles.createPostText}>Share your journey...</Text>
          </TouchableOpacity>
        </View>

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          <View style={styles.actionGrid}>
            <TouchableOpacity 
              style={styles.actionCard}
              onPress={() => router.push('/(tabs)/search')}
              activeOpacity={0.8}
            >
              <Ionicons name="people-outline" size={32} color="#74b9ff" />
              <Text style={styles.actionTitle}>Find Students</Text>
              <Text style={styles.actionSubtitle}>Connect with peers</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.actionCard}
              onPress={() => router.push('/(tabs)/events')}
              activeOpacity={0.8}
            >
              <Ionicons name="calendar-outline" size={32} color="#fd79a8" />
              <Text style={styles.actionTitle}>Campus Events</Text>
              <Text style={styles.actionSubtitle}>Discover activities</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.actionCard}
              onPress={handleAskAI}
              activeOpacity={0.8}
            >
              <Ionicons name="bulb-outline" size={32} color="#fdcb6e" />
              <Text style={styles.actionTitle}>Ask AI</Text>
              <Text style={styles.actionSubtitle}>Get instant help</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.actionCard}
              onPress={() => router.push('/(tabs)/chat')}
              activeOpacity={0.8}
            >
              <Ionicons name="chatbubble-outline" size={32} color="#55a3ff" />
              <Text style={styles.actionTitle}>Messages</Text>
              <Text style={styles.actionSubtitle}>Chat with friends</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Posts Feed Placeholder */}
        <View style={styles.postsSection}>
          <Text style={styles.sectionTitle}>Recent Posts</Text>
          <View style={styles.emptyState}>
            <Ionicons name="document-text-outline" size={64} color="#666666" />
            <Text style={styles.emptyStateTitle}>No posts yet</Text>
            <Text style={styles.emptyStateText}>
              Be the first to share something with the community!
            </Text>
            <TouchableOpacity 
              style={styles.emptyStateButton}
              onPress={handleCreatePost}
              activeOpacity={0.8}
            >
              <Text style={styles.emptyStateButtonText}>Create Post</Text>
            </TouchableOpacity>
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
  headerActions: {
    flexDirection: 'row',
    gap: 16,
  },
  headerButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  welcomeSection: {
    padding: 20,
    backgroundColor: '#252545',
    margin: 16,
    borderRadius: 16,
  },
  welcomeText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  verificationBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2c2416',
    padding: 12,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#f39c12',
  },
  verificationText: {
    flex: 1,
    fontSize: 14,
    color: '#f39c12',
    marginLeft: 8,
  },
  verifyButton: {
    backgroundColor: '#f39c12',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  verifyButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  createPostSection: {
    marginHorizontal: 16,
    marginBottom: 16,
  },
  createPostButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#404040',
  },
  createPostText: {
    fontSize: 16,
    color: '#a0a0a0',
    marginLeft: 12,
  },
  quickActions: {
    marginHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  actionGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  actionCard: {
    flex: 1,
    minWidth: '47%',
    backgroundColor: '#2a2a2a',
    padding: 20,
    borderRadius: 16,
    alignItems: 'center',
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginTop: 12,
    marginBottom: 4,
    textAlign: 'center',
  },
  actionSubtitle: {
    fontSize: 12,
    color: '#a0a0a0',
    textAlign: 'center',
  },
  postsSection: {
    marginHorizontal: 16,
    marginBottom: 24,
  },
  emptyState: {
    backgroundColor: '#2a2a2a',
    padding: 40,
    borderRadius: 16,
    alignItems: 'center',
  },
  emptyStateTitle: {
    fontSize: 18,
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
    marginBottom: 24,
  },
  emptyStateButton: {
    backgroundColor: '#6c5ce7',
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 12,
  },
  emptyStateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
});
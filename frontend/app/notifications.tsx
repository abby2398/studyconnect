import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';

interface Notification {
  id: string;
  type: string;
  title: string;
  message: string;
  data?: any;
  created_at: string;
  read_at?: string;
  sender_id?: string;
}

interface NotificationWithUser extends Notification {
  sender?: {
    id: string;
    first_name: string;
    last_name: string;
  };
}

export default function NotificationsScreen() {
  const [notifications, setNotifications] = useState<NotificationWithUser[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const router = useRouter();

  useFocusEffect(
    useCallback(() => {
      loadNotifications();
    }, [])
  );

  const loadNotifications = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/notifications/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const notificationsData = await response.json();
        
        // Enhance notifications with sender info
        const enhancedNotifications = await Promise.all(
          notificationsData.map(async (notification: Notification) => {
            if (notification.sender_id) {
              const senderInfo = await fetchUserInfo(notification.sender_id, token);
              return {
                ...notification,
                sender: senderInfo,
              };
            }
            return notification;
          })
        );
        
        setNotifications(enhancedNotifications);
      } else {
        Alert.alert('Error', 'Failed to load notifications');
      }
    } catch (error) {
      console.error('Error loading notifications:', error);
      Alert.alert('Error', 'Failed to load notifications');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const fetchUserInfo = async (userId: string, token: string) => {
    try {
      // Use search endpoint since we don't have direct user fetch
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/users/search?limit=50`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const searchData = await response.json();
        const user = searchData.users?.find((u: any) => u.id === userId);
        return user ? {
          id: user.id,
          first_name: user.first_name,
          last_name: user.last_name,
        } : null;
      }
    } catch (error) {
      console.error('Error fetching user info:', error);
    }
    return null;
  };

  const markAsRead = async (notificationId: string) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/notifications/${notificationId}/read`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        // Update local state
        setNotifications(prev => 
          prev.map(notif => 
            notif.id === notificationId 
              ? { ...notif, read_at: new Date().toISOString() }
              : notif
          )
        );
      }
    } catch (error) {
      console.error('Error marking notification as read:', error);
    }
  };

  const markAllAsRead = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/notifications/read-all`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        // Update local state
        const now = new Date().toISOString();
        setNotifications(prev => 
          prev.map(notif => ({ ...notif, read_at: notif.read_at || now }))
        );
        Alert.alert('Success', 'All notifications marked as read');
      }
    } catch (error) {
      console.error('Error marking all notifications as read:', error);
      Alert.alert('Error', 'Failed to mark all as read');
    }
  };

  const deleteNotification = async (notificationId: string) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/notifications/${notificationId}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        setNotifications(prev => prev.filter(notif => notif.id !== notificationId));
      }
    } catch (error) {
      console.error('Error deleting notification:', error);
    }
  };

  const handleNotificationPress = (notification: NotificationWithUser) => {
    // Mark as read if unread
    if (!notification.read_at) {
      markAsRead(notification.id);
    }

    // Navigate based on notification type
    const { type, data } = notification;
    
    switch (type) {
      case 'connection_request':
        router.push('/connections');
        break;
      case 'connection_accepted':
        router.push('/connections');
        break;
      case 'message_received':
        if (data?.sender_id) {
          router.push(`/chat/conversation/${data.sender_id}`);
        } else {
          router.push('/(tabs)/chat');
        }
        break;
      case 'event_invitation':
      case 'event_reminder':
      case 'event_update':
        if (data?.event_id) {
          router.push(`/events/${data.event_id}`);
        } else {
          router.push('/(tabs)/events');
        }
        break;
      case 'post_liked':
      case 'post_commented':
      case 'post_shared':
        if (data?.post_id) {
          router.push(`/posts/${data.post_id}`);
        } else {
          router.push('/(tabs)/posts');
        }
        break;
      default:
        // Default navigation for other types
        break;
    }
  };

  const getNotificationIcon = (type: string) => {
    const iconMap: { [key: string]: string } = {
      connection_request: 'person-add-outline',
      connection_accepted: 'checkmark-circle-outline',
      message_received: 'chatbubble-outline',
      event_invitation: 'calendar-outline',
      event_reminder: 'alarm-outline',
      event_update: 'refresh-outline',
      event_joined: 'people-outline',
      post_liked: 'heart-outline',
      post_commented: 'chatbubble-ellipses-outline',
      post_shared: 'share-outline',
      system_announcement: 'megaphone-outline',
      welcome: 'hand-left-outline',
    };
    
    return iconMap[type] || 'notifications-outline';
  };

  const getNotificationColor = (type: string) => {
    const colorMap: { [key: string]: string } = {
      connection_request: '#6c5ce7',
      connection_accepted: '#00b894',
      message_received: '#fd79a8',
      event_invitation: '#74b9ff',
      event_reminder: '#fdcb6e',
      event_update: '#e17055',
      post_liked: '#e84393',
      post_commented: '#00cec9',
      post_shared: '#a29bfe',
      system_announcement: '#fd79a8',
      welcome: '#00b894',
    };
    
    return colorMap[type] || '#a0a0a0';
  };

  const renderNotification = (notification: NotificationWithUser) => {
    const isUnread = !notification.read_at;
    const timeAgo = getTimeAgo(notification.created_at);
    
    return (
      <TouchableOpacity
        key={notification.id}
        style={[
          styles.notificationCard,
          isUnread && styles.unreadNotification
        ]}
        onPress={() => handleNotificationPress(notification)}
        activeOpacity={0.8}
      >
        <View style={styles.notificationContent}>
          <View style={styles.notificationHeader}>
            <View style={[
              styles.notificationIcon,
              { backgroundColor: getNotificationColor(notification.type) }
            ]}>
              <Ionicons 
                name={getNotificationIcon(notification.type) as any} 
                size={20} 
                color="#ffffff" 
              />
            </View>
            
            <View style={styles.notificationInfo}>
              <Text style={[
                styles.notificationTitle,
                isUnread && styles.unreadTitle
              ]}>
                {notification.title}
              </Text>
              <Text style={styles.notificationTime}>{timeAgo}</Text>
            </View>
            
            <TouchableOpacity
              style={styles.deleteButton}
              onPress={() => deleteNotification(notification.id)}
              activeOpacity={0.8}
            >
              <Ionicons name="close-outline" size={20} color="#a0a0a0" />
            </TouchableOpacity>
          </View>
          
          <Text style={[
            styles.notificationMessage,
            isUnread && styles.unreadMessage
          ]}>
            {notification.message}
          </Text>
          
          {notification.sender && (
            <Text style={styles.senderInfo}>
              From {notification.sender.first_name} {notification.sender.last_name}
            </Text>
          )}
        </View>
        
        {isUnread && <View style={styles.unreadDot} />}
      </TouchableOpacity>
    );
  };

  const getTimeAgo = (timestamp: string) => {
    const now = new Date();
    const time = new Date(timestamp);
    const diff = Math.floor((now.getTime() - time.getTime()) / 1000);
    
    if (diff < 60) return 'Just now';
    if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
    if (diff < 604800) return `${Math.floor(diff / 86400)}d ago`;
    return time.toLocaleDateString();
  };

  const onRefresh = () => {
    setRefreshing(true);
    loadNotifications();
  };

  const unreadCount = notifications.filter(n => !n.read_at).length;

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
        
        <View style={styles.headerInfo}>
          <Text style={styles.headerTitle}>Notifications</Text>
          {unreadCount > 0 && (
            <View style={styles.unreadBadge}>
              <Text style={styles.unreadBadgeText}>{unreadCount}</Text>
            </View>
          )}
        </View>
        
        <TouchableOpacity
          style={styles.markAllButton}
          onPress={markAllAsRead}
          activeOpacity={0.8}
        >
          <Text style={styles.markAllText}>Mark All Read</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#6c5ce7"
            colors={['#6c5ce7']}
          />
        }
      >
        {loading ? (
          <View style={styles.loadingContainer}>
            <Text style={styles.loadingText}>Loading notifications...</Text>
          </View>
        ) : notifications.length > 0 ? (
          <View style={styles.notificationsContainer}>
            {notifications.map(renderNotification)}
          </View>
        ) : (
          <View style={styles.emptyState}>
            <Ionicons name="notifications-outline" size={64} color="#666666" />
            <Text style={styles.emptyStateTitle}>No Notifications</Text>
            <Text style={styles.emptyStateText}>
              You're all caught up! Notifications will appear here when you receive them.
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
  headerInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    justifyContent: 'center',
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
  },
  unreadBadge: {
    backgroundColor: '#e74c3c',
    borderRadius: 10,
    paddingHorizontal: 6,
    paddingVertical: 2,
    marginLeft: 8,
  },
  unreadBadgeText: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  markAllButton: {
    paddingHorizontal: 12,
    paddingVertical: 8,
  },
  markAllText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#6c5ce7',
  },
  content: {
    flex: 1,
  },
  loadingContainer: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: 60,
  },
  loadingText: {
    fontSize: 16,
    color: '#a0a0a0',
  },
  notificationsContainer: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  notificationCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    position: 'relative',
  },
  unreadNotification: {
    backgroundColor: '#2d2a3e',
    borderLeftWidth: 4,
    borderLeftColor: '#6c5ce7',
  },
  notificationContent: {
    flex: 1,
  },
  notificationHeader: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  notificationIcon: {
    width: 40,
    height: 40,
    borderRadius: 20,
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  notificationInfo: {
    flex: 1,
  },
  notificationTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  unreadTitle: {
    fontWeight: 'bold',
  },
  notificationTime: {
    fontSize: 12,
    color: '#a0a0a0',
  },
  deleteButton: {
    padding: 4,
  },
  notificationMessage: {
    fontSize: 14,
    color: '#d0d0d0',
    lineHeight: 20,
    marginBottom: 8,
  },
  unreadMessage: {
    color: '#ffffff',
  },
  senderInfo: {
    fontSize: 12,
    color: '#6c5ce7',
    fontStyle: 'italic',
  },
  unreadDot: {
    position: 'absolute',
    top: 12,
    right: 12,
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#6c5ce7',
  },
  emptyState: {
    alignItems: 'center',
    paddingHorizontal: 40,
    paddingVertical: 80,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#ffffff',
    marginTop: 20,
    marginBottom: 12,
  },
  emptyStateText: {
    fontSize: 16,
    color: '#a0a0a0',
    textAlign: 'center',
    lineHeight: 24,
  },
});
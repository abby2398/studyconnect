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

interface ChatItem {
  id: string;
  user_name: string;
  last_message: string;
  timestamp: string;
  unread_count: number;
  is_online: boolean;
}

export default function ChatScreen() {
  const [chats, setChats] = useState<ChatItem[]>([]);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadChats();
  }, []);

  const loadChats = async () => {
    // TODO: Implement actual chat loading
    // For now, show empty state
    setChats([]);
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadChats();
    setRefreshing(false);
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const days = Math.floor(diff / (1000 * 60 * 60 * 24));
    
    if (days === 0) {
      return date.toLocaleTimeString('en-US', { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } else if (days === 1) {
      return 'Yesterday';
    } else if (days < 7) {
      return date.toLocaleDateString('en-US', { weekday: 'short' });
    } else {
      return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric' 
      });
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Messages</Text>
        <TouchableOpacity style={styles.headerButton}>
          <Ionicons name="create-outline" size={24} color="#ffffff" />
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
          />
        }
      >
        {chats.length > 0 ? (
          // Chat List
          <View style={styles.chatList}>
            {chats.map((chat) => (
              <TouchableOpacity
                key={chat.id}
                style={styles.chatItem}
                activeOpacity={0.8}
              >
                <View style={styles.chatAvatar}>
                  <Text style={styles.avatarText}>
                    {chat.user_name.charAt(0).toUpperCase()}
                  </Text>
                  {chat.is_online && <View style={styles.onlineIndicator} />}
                </View>

                <View style={styles.chatInfo}>
                  <View style={styles.chatHeader}>
                    <Text style={styles.chatName}>{chat.user_name}</Text>
                    <Text style={styles.chatTime}>
                      {formatTime(chat.timestamp)}
                    </Text>
                  </View>
                  
                  <View style={styles.chatPreview}>
                    <Text style={styles.lastMessage} numberOfLines={1}>
                      {chat.last_message}
                    </Text>
                    {chat.unread_count > 0 && (
                      <View style={styles.unreadBadge}>
                        <Text style={styles.unreadCount}>
                          {chat.unread_count > 99 ? '99+' : chat.unread_count}
                        </Text>
                      </View>
                    )}
                  </View>
                </View>
              </TouchableOpacity>
            ))}
          </View>
        ) : (
          // Empty State
          <View style={styles.emptyState}>
            <Ionicons name="chatbubble-outline" size={80} color="#666666" />
            <Text style={styles.emptyStateTitle}>No messages yet</Text>
            <Text style={styles.emptyStateText}>
              Start connecting with fellow students to begin conversations
            </Text>
            
            <TouchableOpacity 
              style={styles.emptyStateButton}
              activeOpacity={0.8}
            >
              <Text style={styles.emptyStateButtonText}>Find Students</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Quick Actions */}
        <View style={styles.quickActions}>
          <Text style={styles.sectionTitle}>Quick Actions</Text>
          
          <TouchableOpacity style={styles.actionItem} activeOpacity={0.8}>
            <View style={styles.actionIcon}>
              <Ionicons name="people-outline" size={24} color="#74b9ff" />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Group Chats</Text>
              <Text style={styles.actionSubtitle}>Join university-specific groups</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#a0a0a0" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionItem} activeOpacity={0.8}>
            <View style={styles.actionIcon}>
              <Ionicons name="help-circle-outline" size={24} color="#fd79a8" />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Ask Community</Text>
              <Text style={styles.actionSubtitle}>Get help from experienced students</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#a0a0a0" />
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionItem} activeOpacity={0.8}>
            <View style={styles.actionIcon}>
              <Ionicons name="globe-outline" size={24} color="#fdcb6e" />
            </View>
            <View style={styles.actionContent}>
              <Text style={styles.actionTitle}>Language Exchange</Text>
              <Text style={styles.actionSubtitle}>Practice languages with native speakers</Text>
            </View>
            <Ionicons name="chevron-forward" size={20} color="#a0a0a0" />
          </TouchableOpacity>
        </View>

        {/* Chat Features Info */}
        <View style={styles.featuresInfo}>
          <Text style={styles.sectionTitle}>Chat Features</Text>
          
          <View style={styles.featureGrid}>
            <View style={styles.featureItem}>
              <Ionicons name="checkmark-done-outline" size={20} color="#55a3ff" />
              <Text style={styles.featureText}>Read receipts</Text>
            </View>
            
            <View style={styles.featureItem}>
              <Ionicons name="ellipsis-horizontal" size={20} color="#55a3ff" />
              <Text style={styles.featureText}>Typing indicators</Text>
            </View>
            
            <View style={styles.featureItem}>
              <Ionicons name="mic-outline" size={20} color="#55a3ff" />
              <Text style={styles.featureText}>Voice messages</Text>
            </View>
            
            <View style={styles.featureItem}>
              <Ionicons name="attach-outline" size={20} color="#55a3ff" />
              <Text style={styles.featureText}>File sharing</Text>
            </View>
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
  headerButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  chatList: {
    paddingVertical: 8,
  },
  chatItem: {
    flexDirection: 'row',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#2a2a2a',
  },
  chatAvatar: {
    width: 50,
    height: 50,
    borderRadius: 25,
    backgroundColor: '#6c5ce7',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
    position: 'relative',
  },
  avatarText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  onlineIndicator: {
    position: 'absolute',
    bottom: 2,
    right: 2,
    width: 14,
    height: 14,
    borderRadius: 7,
    backgroundColor: '#00b894',
    borderWidth: 2,
    borderColor: '#1a1a2e',
  },
  chatInfo: {
    flex: 1,
  },
  chatHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 4,
  },
  chatName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  chatTime: {
    fontSize: 12,
    color: '#a0a0a0',
  },
  chatPreview: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  lastMessage: {
    fontSize: 14,
    color: '#a0a0a0',
    flex: 1,
    marginRight: 8,
  },
  unreadBadge: {
    backgroundColor: '#6c5ce7',
    borderRadius: 12,
    paddingHorizontal: 8,
    paddingVertical: 2,
    minWidth: 20,
    alignItems: 'center',
  },
  unreadCount: {
    fontSize: 12,
    fontWeight: 'bold',
    color: '#ffffff',
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
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 14,
    color: '#a0a0a0',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 32,
  },
  emptyStateButton: {
    backgroundColor: '#6c5ce7',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
  },
  emptyStateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  quickActions: {
    paddingHorizontal: 20,
    paddingVertical: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  actionItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    padding: 16,
    borderRadius: 16,
    marginBottom: 12,
  },
  actionIcon: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#1a1a2e',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 16,
  },
  actionContent: {
    flex: 1,
  },
  actionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 2,
  },
  actionSubtitle: {
    fontSize: 12,
    color: '#a0a0a0',
  },
  featuresInfo: {
    paddingHorizontal: 20,
    paddingBottom: 32,
  },
  featureGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 16,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 12,
    minWidth: '47%',
  },
  featureText: {
    fontSize: 14,
    color: '#ffffff',
    marginLeft: 8,
    fontWeight: '500',
  },
});
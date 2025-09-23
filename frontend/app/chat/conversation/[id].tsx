import React, { useState, useEffect, useRef, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  ScrollView,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Alert,
  Animated,
  Dimensions,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { io, Socket } from 'socket.io-client';

const { width: screenWidth } = Dimensions.get('window');

interface Message {
  id: string;
  conversation_id: string;
  sender_id: string;
  message_type: 'text' | 'image' | 'voice' | 'file' | 'system';
  content?: string;
  timestamp: string;
  status: 'sent' | 'delivered' | 'read';
  read_by: string[];
}

interface User {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
}

interface TypingUser {
  user_id: string;
  timestamp: string;
}

export default function ConversationScreen() {
  const { id: conversationId } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  
  const [messages, setMessages] = useState<Message[]>([]);
  const [newMessage, setNewMessage] = useState('');
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [otherUser, setOtherUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [sending, setSending] = useState(false);
  const [socket, setSocket] = useState<Socket | null>(null);
  const [typingUsers, setTypingUsers] = useState<TypingUser[]>([]);
  const [isTyping, setIsTyping] = useState(false);
  const [onlineUsers, setOnlineUsers] = useState<string[]>([]);
  
  const scrollViewRef = useRef<ScrollView>(null);
  const typingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const messageInputRef = useRef<TextInput>(null);
  
  // Animated values for typing indicator
  const typingOpacity = useRef(new Animated.Value(0)).current;
  const typingScale = useRef(new Animated.Value(0.8)).current;

  useEffect(() => {
    loadUserData();
    loadConversation();
    setupSocketConnection();
    
    return () => {
      if (socket) {
        socket.disconnect();
      }
    };
  }, [conversationId]);

  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      if (userData) {
        setCurrentUser(JSON.parse(userData));
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const loadConversation = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token || !conversationId) return;

      // Load conversation details
      const conversationResponse = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/chat/conversations`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      if (conversationResponse.ok) {
        const conversations = await conversationResponse.json();
        const currentConversation = conversations.find(
          (conv: any) => conv.conversation.id === conversationId
        );
        
        if (currentConversation?.other_participant) {
          setOtherUser(currentConversation.other_participant);
        }
      }

      // Load messages
      const messagesResponse = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/chat/messages/${conversationId}`,
        {
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      if (messagesResponse.ok) {
        const messagesData = await messagesResponse.json();
        setMessages(messagesData);
        
        // Mark messages as read
        for (const message of messagesData) {
          if (message.sender_id !== currentUser?.id && !message.read_by.includes(currentUser?.id)) {
            markMessageAsRead(message.id);
          }
        }
      }
    } catch (error) {
      console.error('Error loading conversation:', error);
    } finally {
      setLoading(false);
    }
  };

  const setupSocketConnection = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      const userData = await AsyncStorage.getItem('user_data');
      
      if (!token || !userData) return;

      const user = JSON.parse(userData);
      const backendUrl = process.env.EXPO_PUBLIC_BACKEND_URL?.replace('/api', '') || 'http://localhost:8001';
      
      const socketInstance = io(backendUrl, {
        transports: ['websocket', 'polling'],
      });

      socketInstance.on('connect', () => {
        console.log('Socket connected');
        
        // Authenticate
        socketInstance.emit('authenticate', {
          user_id: user.id,
          token: token,
        });
        
        // Join conversation
        if (conversationId) {
          socketInstance.emit('join_conversation', {
            conversation_id: conversationId,
          });
        }
      });

      socketInstance.on('authenticated', (data) => {
        console.log('Socket authenticated:', data);
      });

      socketInstance.on('new_message', (data) => {
        console.log('New message received:', data);
        
        if (data.conversation_id === conversationId) {
          const newMsg: Message = {
            id: data.message.id,
            conversation_id: data.conversation_id,
            sender_id: data.sender_id,
            message_type: data.message.message_type || 'text',
            content: data.message.content,
            timestamp: data.timestamp,
            status: 'delivered',
            read_by: data.message.read_by || [],
          };
          
          setMessages(prev => [...prev, newMsg]);
          
          // Auto-scroll to bottom
          setTimeout(() => {
            scrollViewRef.current?.scrollToEnd({ animated: true });
          }, 100);
          
          // Mark as read if not from current user
          if (data.sender_id !== currentUser?.id) {
            markMessageAsRead(newMsg.id);
          }
        }
      });

      socketInstance.on('typing_start', (data) => {
        if (data.conversation_id === conversationId && data.user_id !== currentUser?.id) {
          setTypingUsers(prev => {
            const filtered = prev.filter(u => u.user_id !== data.user_id);
            return [...filtered, { user_id: data.user_id, timestamp: data.timestamp }];
          });
        }
      });

      socketInstance.on('typing_stop', (data) => {
        if (data.conversation_id === conversationId) {
          setTypingUsers(prev => prev.filter(u => u.user_id !== data.user_id));
        }
      });

      socketInstance.on('message_read', (data) => {
        if (data.conversation_id === conversationId) {
          setMessages(prev => prev.map(msg => {
            if (msg.id === data.message_id) {
              return {
                ...msg,
                read_by: [...(msg.read_by || []), data.user_id],
                status: 'read',
              };
            }
            return msg;
          }));
        }
      });

      socketInstance.on('user_status_change', (data) => {
        if (data.is_online) {
          setOnlineUsers(prev => [...new Set([...prev, data.user_id])]);
        } else {
          setOnlineUsers(prev => prev.filter(id => id !== data.user_id));
        }
      });

      setSocket(socketInstance);
    } catch (error) {
      console.error('Error setting up socket:', error);
    }
  };

  const markMessageAsRead = async (messageId: string) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/chat/messages/${messageId}/read`,
        {
          method: 'POST',
          headers: { 'Authorization': `Bearer ${token}` },
        }
      );

      // Emit read receipt via socket
      if (socket && conversationId) {
        socket.emit('message_read', {
          message_id: messageId,
          conversation_id: conversationId,
        });
      }
    } catch (error) {
      console.error('Error marking message as read:', error);
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || sending || !currentUser || !conversationId) return;

    setSending(true);
    const messageText = newMessage.trim();
    setNewMessage('');

    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/chat/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            conversation_id: conversationId,
            message_type: 'text',
            content: messageText,
          }),
        }
      );

      if (!response.ok) {
        throw new Error('Failed to send message');
      }

      const messageData = await response.json();

      // Emit message via socket for real-time delivery
      if (socket) {
        socket.emit('send_message', {
          conversation_id: conversationId,
          message: messageData,
        });
      }

      // Add message to local state
      setMessages(prev => [...prev, messageData]);
      
      // Stop typing indicator
      handleStopTyping();
      
      // Auto-scroll to bottom
      setTimeout(() => {
        scrollViewRef.current?.scrollToEnd({ animated: true });
      }, 100);

    } catch (error) {
      console.error('Error sending message:', error);
      Alert.alert('Error', 'Failed to send message. Please try again.');
      setNewMessage(messageText); // Restore message
    } finally {
      setSending(false);
    }
  };

  const handleTyping = useCallback((text: string) => {
    setNewMessage(text);

    if (!socket || !conversationId || !currentUser) return;

    // Start typing indicator
    if (text.length > 0 && !isTyping) {
      setIsTyping(true);
      socket.emit('typing_start', {
        conversation_id: conversationId,
      });
    }

    // Clear existing timeout
    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
    }

    // Set new timeout to stop typing
    typingTimeoutRef.current = setTimeout(() => {
      handleStopTyping();
    }, 2000);
  }, [socket, conversationId, currentUser, isTyping]);

  const handleStopTyping = useCallback(() => {
    if (isTyping && socket && conversationId) {
      setIsTyping(false);
      socket.emit('typing_stop', {
        conversation_id: conversationId,
      });
    }

    if (typingTimeoutRef.current) {
      clearTimeout(typingTimeoutRef.current);
      typingTimeoutRef.current = null;
    }
  }, [isTyping, socket, conversationId]);

  // Animate typing indicator
  useEffect(() => {
    if (typingUsers.length > 0) {
      Animated.parallel([
        Animated.timing(typingOpacity, {
          toValue: 1,
          duration: 300,
          useNativeDriver: true,
        }),
        Animated.spring(typingScale, {
          toValue: 1,
          useNativeDriver: true,
        }),
      ]).start();
    } else {
      Animated.parallel([
        Animated.timing(typingOpacity, {
          toValue: 0,
          duration: 200,
          useNativeDriver: true,
        }),
        Animated.spring(typingScale, {
          toValue: 0.8,
          useNativeDriver: true,
        }),
      ]).start();
    }
  }, [typingUsers.length]);

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit',
      hour12: true,
    });
  };

  const isOtherUserOnline = otherUser && onlineUsers.includes(otherUser.id);

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading conversation...</Text>
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

        <View style={styles.headerInfo}>
          <View style={styles.avatarContainer}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {otherUser ? `${otherUser.first_name[0]}${otherUser.last_name[0]}` : 'U'}
              </Text>
            </View>
            {isOtherUserOnline && <View style={styles.onlineIndicator} />}
          </View>
          
          <View style={styles.userInfo}>
            <Text style={styles.userName}>
              {otherUser ? `${otherUser.first_name} ${otherUser.last_name}` : 'User'}
            </Text>
            <Text style={styles.userStatus}>
              {isOtherUserOnline ? 'Online' : 'Last seen recently'}
            </Text>
          </View>
        </View>

        <TouchableOpacity style={styles.headerButton}>
          <Ionicons name="call-outline" size={24} color="#ffffff" />
        </TouchableOpacity>
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.chatContainer}
      >
        {/* Messages */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
          onContentSizeChange={() => scrollViewRef.current?.scrollToEnd({ animated: true })}
        >
          {messages.map((message) => {
            const isOwnMessage = message.sender_id === currentUser?.id;
            
            return (
              <View
                key={message.id}
                style={[
                  styles.messageContainer,
                  isOwnMessage ? styles.ownMessage : styles.otherMessage,
                ]}
              >
                <View
                  style={[
                    styles.messageBubble,
                    isOwnMessage ? styles.ownMessageBubble : styles.otherMessageBubble,
                  ]}
                >
                  <Text
                    style={[
                      styles.messageText,
                      isOwnMessage ? styles.ownMessageText : styles.otherMessageText,
                    ]}
                  >
                    {message.content}
                  </Text>
                  
                  <View style={styles.messageFooter}>
                    <Text
                      style={[
                        styles.messageTime,
                        isOwnMessage ? styles.ownMessageTime : styles.otherMessageTime,
                      ]}
                    >
                      {formatTime(message.timestamp)}
                    </Text>
                    
                    {isOwnMessage && (
                      <Ionicons
                        name={
                          message.status === 'read' 
                            ? 'checkmark-done' 
                            : message.status === 'delivered'
                            ? 'checkmark'
                            : 'time-outline'
                        }
                        size={14}
                        color={message.status === 'read' ? '#00b894' : '#a0a0a0'}
                        style={styles.messageStatus}
                      />
                    )}
                  </View>
                </View>
              </View>
            );
          })}

          {/* Typing Indicator */}
          {typingUsers.length > 0 && (
            <Animated.View
              style={[
                styles.typingContainer,
                {
                  opacity: typingOpacity,
                  transform: [{ scale: typingScale }],
                },
              ]}
            >
              <View style={styles.typingBubble}>
                <View style={styles.typingDots}>
                  <View style={[styles.typingDot, { animationDelay: '0ms' }]} />
                  <View style={[styles.typingDot, { animationDelay: '160ms' }]} />
                  <View style={[styles.typingDot, { animationDelay: '320ms' }]} />
                </View>
              </View>
            </Animated.View>
          )}
        </ScrollView>

        {/* Message Input */}
        <View style={styles.inputContainer}>
          <View style={styles.inputWrapper}>
            <TouchableOpacity style={styles.attachButton}>
              <Ionicons name="add" size={24} color="#6c5ce7" />
            </TouchableOpacity>

            <TextInput
              ref={messageInputRef}
              style={styles.textInput}
              placeholder="Type a message..."
              placeholderTextColor="#666666"
              value={newMessage}
              onChangeText={handleTyping}
              multiline
              maxLength={1000}
              editable={!sending}
            />

            <TouchableOpacity style={styles.voiceButton}>
              <Ionicons name="mic-outline" size={24} color="#6c5ce7" />
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[
              styles.sendButton,
              (!newMessage.trim() || sending) && styles.sendButtonDisabled,
            ]}
            onPress={sendMessage}
            disabled={!newMessage.trim() || sending}
            activeOpacity={0.8}
          >
            <Ionicons
              name={sending ? "hourglass-outline" : "send"}
              size={20}
              color="#ffffff"
            />
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
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
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
    backgroundColor: '#1a1a2e',
  },
  backButton: {
    padding: 8,
    marginRight: 8,
  },
  headerInfo: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
  },
  avatarContainer: {
    position: 'relative',
    marginRight: 12,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#6c5ce7',
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  onlineIndicator: {
    position: 'absolute',
    bottom: 0,
    right: 0,
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: '#00b894',
    borderWidth: 2,
    borderColor: '#1a1a2e',
  },
  userInfo: {
    flex: 1,
  },
  userName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 2,
  },
  userStatus: {
    fontSize: 12,
    color: '#a0a0a0',
  },
  headerButton: {
    padding: 8,
    marginLeft: 8,
  },
  chatContainer: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
    backgroundColor: '#0f0f1e',
  },
  messagesContent: {
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  messageContainer: {
    marginVertical: 4,
    maxWidth: screenWidth * 0.75,
  },
  ownMessage: {
    alignSelf: 'flex-end',
  },
  otherMessage: {
    alignSelf: 'flex-start',
  },
  messageBubble: {
    padding: 12,
    borderRadius: 18,
    minWidth: 60,
  },
  ownMessageBubble: {
    backgroundColor: '#6c5ce7',
    borderBottomRightRadius: 4,
  },
  otherMessageBubble: {
    backgroundColor: '#2a2a2a',
    borderBottomLeftRadius: 4,
  },
  messageText: {
    fontSize: 16,
    lineHeight: 20,
  },
  ownMessageText: {
    color: '#ffffff',
  },
  otherMessageText: {
    color: '#ffffff',
  },
  messageFooter: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'flex-end',
    marginTop: 4,
  },
  messageTime: {
    fontSize: 11,
    marginRight: 4,
  },
  ownMessageTime: {
    color: 'rgba(255, 255, 255, 0.7)',
  },
  otherMessageTime: {
    color: '#a0a0a0',
  },
  messageStatus: {
    marginLeft: 2,
  },
  typingContainer: {
    alignSelf: 'flex-start',
    maxWidth: screenWidth * 0.75,
    marginVertical: 4,
  },
  typingBubble: {
    backgroundColor: '#2a2a2a',
    padding: 12,
    borderRadius: 18,
    borderBottomLeftRadius: 4,
  },
  typingDots: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typingDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: '#a0a0a0',
    marginHorizontal: 2,
  },
  inputContainer: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    paddingHorizontal: 16,
    paddingVertical: 12,
    backgroundColor: '#1a1a2e',
    borderTopWidth: 1,
    borderTopColor: '#404040',
  },
  inputWrapper: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'flex-end',
    backgroundColor: '#2a2a2a',
    borderRadius: 24,
    paddingHorizontal: 4,
    marginRight: 8,
    minHeight: 48,
  },
  attachButton: {
    padding: 12,
  },
  textInput: {
    flex: 1,
    fontSize: 16,
    color: '#ffffff',
    paddingVertical: 12,
    paddingHorizontal: 8,
    maxHeight: 120,
  },
  voiceButton: {
    padding: 12,
  },
  sendButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: '#6c5ce7',
    justifyContent: 'center',
    alignItems: 'center',
  },
  sendButtonDisabled: {
    opacity: 0.5,
  },
});
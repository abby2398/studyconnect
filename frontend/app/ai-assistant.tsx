import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  ScrollView,
  Alert,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter } from 'expo-router';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TextInput } from './components/TextInput';
import { LoadingButton } from './components/LoadingButton';

interface AIMessage {
  id: string;
  role: 'user' | 'assistant';
  message: string;
  timestamp: string;
}

interface AISuggestion {
  suggestions: string[];
}

export default function AIAssistantScreen() {
  const [messages, setMessages] = useState<AIMessage[]>([]);
  const [currentMessage, setCurrentMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const scrollViewRef = useRef<ScrollView>(null);
  const router = useRouter();

  useEffect(() => {
    loadChatHistory();
    loadSuggestions();
  }, []);

  const loadChatHistory = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/ai/chat/history`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const history = await response.json();
        setMessages(history);
        setTimeout(() => scrollToBottom(), 100);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  const loadSuggestions = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/ai/suggestions`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data: AISuggestion = await response.json();
        setSuggestions(data.suggestions);
      }
    } catch (error) {
      console.error('Error loading suggestions:', error);
    }
  };

  const sendMessage = async (messageText?: string) => {
    const textToSend = messageText || currentMessage.trim();
    if (!textToSend || loading) return;

    setLoading(true);
    const userMessage: AIMessage = {
      id: `temp_${Date.now()}`,
      role: 'user',
      message: textToSend,
      timestamp: new Date().toISOString(),
    };

    // Add user message immediately
    setMessages(prev => [...prev, userMessage]);
    setCurrentMessage('');
    
    setTimeout(() => scrollToBottom(), 100);

    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        Alert.alert('Error', 'Authentication required');
        return;
      }

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/ai/chat/send`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            message: textToSend,
            context: { source: 'mobile_app' },
          }),
        }
      );

      if (response.ok) {
        const aiMessage = await response.json();
        
        // Remove temp user message and add both messages from server
        setMessages(prev => {
          const filtered = prev.filter(msg => msg.id !== userMessage.id);
          return [...filtered, 
            { ...userMessage, id: aiMessage.id.replace('ai_', 'user_') },
            aiMessage
          ];
        });
        
        setTimeout(() => scrollToBottom(), 100);
      } else {
        const error = await response.json();
        Alert.alert('Error', error.detail || 'Failed to send message');
        // Remove temp message on error
        setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
      }
    } catch (error) {
      console.error('Error sending message:', error);
      Alert.alert('Error', 'Failed to send message');
      // Remove temp message on error
      setMessages(prev => prev.filter(msg => msg.id !== userMessage.id));
    } finally {
      setLoading(false);
    }
  };

  const scrollToBottom = () => {
    scrollViewRef.current?.scrollToEnd({ animated: true });
  };

  const renderMessage = (message: AIMessage) => {
    const isUser = message.role === 'user';
    
    return (
      <View
        key={message.id}
        style={[
          styles.messageContainer,
          isUser ? styles.userMessageContainer : styles.aiMessageContainer
        ]}
      >
        <View style={[
          styles.messageBubble,
          isUser ? styles.userBubble : styles.aiBubble
        ]}>
          <Text style={[
            styles.messageText,
            isUser ? styles.userText : styles.aiText
          ]}>
            {message.message}
          </Text>
        </View>
        <Text style={styles.messageTime}>
          {new Date(message.timestamp).toLocaleTimeString('en-US', {
            hour: 'numeric',
            minute: '2-digit',
            hour12: true,
          })}
        </Text>
      </View>
    );
  };

  const renderSuggestionChip = (suggestion: string) => (
    <TouchableOpacity
      key={suggestion}
      style={styles.suggestionChip}
      onPress={() => sendMessage(suggestion)}
      activeOpacity={0.8}
    >
      <Text style={styles.suggestionText}>{suggestion}</Text>
    </TouchableOpacity>
  );

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
          <Text style={styles.headerTitle}>AI Assistant</Text>
          <Text style={styles.headerSubtitle}>StudyConnect Helper</Text>
        </View>
        
        <View style={styles.aiIndicator}>
          <View style={styles.aiDot} />
        </View>
      </View>

      <KeyboardAvoidingView 
        style={styles.keyboardContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        {/* Chat Messages */}
        <ScrollView
          ref={scrollViewRef}
          style={styles.messagesContainer}
          contentContainerStyle={styles.messagesContent}
          showsVerticalScrollIndicator={false}
        >
          {messages.length === 0 ? (
            <View style={styles.welcomeContainer}>
              <View style={styles.welcomeIcon}>
                <Ionicons name="chatbubble-ellipses" size={48} color="#6c5ce7" />
              </View>
              <Text style={styles.welcomeTitle}>Hi there! 👋</Text>
              <Text style={styles.welcomeText}>
                I'm your StudyConnect AI assistant. I'm here to help you with:
              </Text>
              
              <View style={styles.featuresContainer}>
                <View style={styles.featureItem}>
                  <Ionicons name="school-outline" size={20} color="#6c5ce7" />
                  <Text style={styles.featureText}>Academic questions & study tips</Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="people-outline" size={20} color="#6c5ce7" />
                  <Text style={styles.featureText}>Making friends & connections</Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="globe-outline" size={20} color="#6c5ce7" />
                  <Text style={styles.featureText}>Living abroad & cultural tips</Text>
                </View>
                <View style={styles.featureItem}>
                  <Ionicons name="phone-portrait-outline" size={20} color="#6c5ce7" />
                  <Text style={styles.featureText}>Using StudyConnect features</Text>
                </View>
              </View>

              {suggestions.length > 0 && (
                <View style={styles.suggestionsContainer}>
                  <Text style={styles.suggestionsTitle}>Try asking:</Text>
                  {suggestions.map(renderSuggestionChip)}
                </View>
              )}
            </View>
          ) : (
            <>
              {messages.map(renderMessage)}
              {loading && (
                <View style={styles.typingContainer}>
                  <View style={styles.typingBubble}>
                    <View style={styles.typingDots}>
                      <View style={[styles.typingDot, styles.dot1]} />
                      <View style={[styles.typingDot, styles.dot2]} />
                      <View style={[styles.typingDot, styles.dot3]} />
                    </View>
                  </View>
                </View>
              )}
            </>
          )}
        </ScrollView>

        {/* Input Area */}
        <View style={styles.inputContainer}>
          <View style={styles.inputRow}>
            <View style={styles.textInputContainer}>
              <TextInput
                value={currentMessage}
                onChangeText={setCurrentMessage}
                placeholder="Ask me anything about studying abroad..."
                multiline
                maxLength={2000}
                style={styles.messageInput}
              />
            </View>
            
            <LoadingButton
              title=""
              onPress={() => sendMessage()}
              loading={loading}
              disabled={!currentMessage.trim() || loading}
              style={[
                styles.sendButton,
                (!currentMessage.trim() || loading) && styles.sendButtonDisabled
              ]}
              textStyle={styles.sendButtonText}
            >
              <Ionicons 
                name="send" 
                size={20} 
                color={(!currentMessage.trim() || loading) ? "#666666" : "#ffffff"} 
              />
            </LoadingButton>
          </View>
          
          <Text style={styles.inputHint}>
            AI can make mistakes. Verify important information.
          </Text>
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
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  backButton: {
    padding: 8,
  },
  headerInfo: {
    flex: 1,
    marginLeft: 16,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
  },
  headerSubtitle: {
    fontSize: 14,
    color: '#a0a0a0',
  },
  aiIndicator: {
    padding: 8,
  },
  aiDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#00b894',
  },
  keyboardContainer: {
    flex: 1,
  },
  messagesContainer: {
    flex: 1,
  },
  messagesContent: {
    paddingVertical: 16,
    flexGrow: 1,
  },
  welcomeContainer: {
    alignItems: 'center',
    paddingHorizontal: 32,
    paddingVertical: 40,
    flex: 1,
    justifyContent: 'center',
  },
  welcomeIcon: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: '#2a2a2a',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 24,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    marginBottom: 12,
  },
  welcomeText: {
    fontSize: 16,
    color: '#a0a0a0',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  featuresContainer: {
    alignSelf: 'stretch',
    marginBottom: 32,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 12,
    paddingHorizontal: 16,
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    marginBottom: 12,
  },
  featureText: {
    fontSize: 14,
    color: '#ffffff',
    marginLeft: 16,
    flex: 1,
  },
  suggestionsContainer: {
    alignSelf: 'stretch',
  },
  suggestionsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
    textAlign: 'center',
  },
  suggestionChip: {
    backgroundColor: '#6c5ce7',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
    marginBottom: 12,
  },
  suggestionText: {
    fontSize: 14,
    color: '#ffffff',
    textAlign: 'center',
  },
  messageContainer: {
    marginBottom: 16,
    paddingHorizontal: 16,
  },
  userMessageContainer: {
    alignItems: 'flex-end',
  },
  aiMessageContainer: {
    alignItems: 'flex-start',
  },
  messageBubble: {
    maxWidth: '80%',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
  },
  userBubble: {
    backgroundColor: '#6c5ce7',
  },
  aiBubble: {
    backgroundColor: '#2a2a2a',
  },
  messageText: {
    fontSize: 16,
    lineHeight: 22,
  },
  userText: {
    color: '#ffffff',
  },
  aiText: {
    color: '#ffffff',
  },
  messageTime: {
    fontSize: 12,
    color: '#666666',
    marginTop: 4,
  },
  typingContainer: {
    paddingHorizontal: 16,
    alignItems: 'flex-start',
  },
  typingBubble: {
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderRadius: 20,
  },
  typingDots: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  typingDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#666666',
    marginHorizontal: 2,
  },
  dot1: {
    // Animation would be added here
  },
  dot2: {
    // Animation would be added here
  },
  dot3: {
    // Animation would be added here
  },
  inputContainer: {
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#404040',
    backgroundColor: '#1a1a2e',
  },
  inputRow: {
    flexDirection: 'row',
    alignItems: 'flex-end',
    marginBottom: 8,
  },
  textInputContainer: {
    flex: 1,
    marginRight: 12,
  },
  messageInput: {
    maxHeight: 100,
    backgroundColor: '#2a2a2a',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 12,
    fontSize: 16,
    color: '#ffffff',
    textAlignVertical: 'center',
  },
  sendButton: {
    width: 44,
    height: 44,
    borderRadius: 22,
    backgroundColor: '#6c5ce7',
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 44,
  },
  sendButtonDisabled: {
    backgroundColor: '#404040',
  },
  sendButtonText: {
    fontSize: 16,
  },
  inputHint: {
    fontSize: 12,
    color: '#666666',
    textAlign: 'center',
    fontStyle: 'italic',
  },
});
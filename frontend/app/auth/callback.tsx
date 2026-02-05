import React, { useEffect, useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  ActivityIndicator,
} from 'react-native';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';

export default function AuthCallbackScreen() {
  const router = useRouter();
  const params = useLocalSearchParams();
  const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
  const [message, setMessage] = useState('Processing authentication...');

  useEffect(() => {
    handleCallback();
  }, []);

  const handleCallback = async () => {
    try {
      // Get the full URL to extract session_id from fragment
      const url = window?.location?.href || '';
      console.log('Callback URL:', url);
      
      // Try to get session_id from URL fragment or query params
      let sessionId = params.session_id as string;
      
      // If not in params, try to extract from URL fragment
      if (!sessionId && url.includes('#session_id=')) {
        const match = url.match(/#session_id=([^&]+)/);
        if (match) {
          sessionId = match[1];
        }
      }
      
      // Also check query string
      if (!sessionId && url.includes('session_id=')) {
        const match = url.match(/[?&]session_id=([^&#]+)/);
        if (match) {
          sessionId = match[1];
        }
      }

      console.log('Session ID:', sessionId);

      if (!sessionId) {
        throw new Error('No session ID found in callback');
      }

      setMessage('Verifying your account...');

      // Get session data from Emergent auth service
      const response = await fetch('https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data', {
        method: 'GET',
        headers: {
          'X-Session-ID': sessionId,
        },
      });

      if (!response.ok) {
        throw new Error('Failed to get session data from auth service');
      }

      const sessionData = await response.json();
      console.log('Session data received:', sessionData);

      setMessage('Signing you in...');

      // Process the Google OAuth data through our backend
      const backendResponse = await fetch(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/auth/google-oauth`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          google_data: sessionData,
          session_token: sessionData.session_token,
        }),
      });

      if (backendResponse.ok) {
        const result = await backendResponse.json();
        
        // Store auth data
        await AsyncStorage.setItem('auth_token', result.access_token);
        await AsyncStorage.setItem('user_data', JSON.stringify(result.user));
        
        setStatus('success');
        setMessage('Successfully signed in!');
        
        // Redirect to main app after a brief delay
        setTimeout(() => {
          router.replace('/(tabs)/posts');
        }, 1000);
      } else {
        const errorResult = await backendResponse.json();
        throw new Error(errorResult.detail || 'Failed to process Google authentication');
      }
    } catch (error) {
      console.error('Error processing callback:', error);
      setStatus('error');
      setMessage(error instanceof Error ? error.message : 'Authentication failed');
      
      // Redirect back to login after a delay
      setTimeout(() => {
        router.replace('/auth/login');
      }, 3000);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      <View style={styles.content}>
        {status === 'processing' && (
          <>
            <ActivityIndicator size="large" color="#6c5ce7" />
            <Text style={styles.title}>Signing In</Text>
            <Text style={styles.message}>{message}</Text>
          </>
        )}
        
        {status === 'success' && (
          <>
            <View style={styles.iconContainer}>
              <Ionicons name="checkmark-circle" size={80} color="#00b894" />
            </View>
            <Text style={styles.title}>Success!</Text>
            <Text style={styles.message}>{message}</Text>
            <Text style={styles.redirectText}>Redirecting to app...</Text>
          </>
        )}
        
        {status === 'error' && (
          <>
            <View style={styles.iconContainer}>
              <Ionicons name="close-circle" size={80} color="#e74c3c" />
            </View>
            <Text style={styles.title}>Authentication Failed</Text>
            <Text style={styles.message}>{message}</Text>
            <Text style={styles.redirectText}>Redirecting to login...</Text>
          </>
        )}
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  content: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  iconContainer: {
    marginBottom: 24,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    marginTop: 24,
    marginBottom: 12,
    textAlign: 'center',
  },
  message: {
    fontSize: 16,
    color: '#a0a0a0',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 16,
  },
  redirectText: {
    fontSize: 14,
    color: '#6c5ce7',
    marginTop: 16,
  },
});

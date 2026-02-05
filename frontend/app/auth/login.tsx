import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  StatusBar,
  Linking,
} from 'react-native';
import { useRouter } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as WebBrowser from 'expo-web-browser';
import { TextInput } from '../components/TextInput';
import { LoadingButton } from '../components/LoadingButton';

const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(1, 'Password is required'),
});

type LoginFormData = z.infer<typeof loginSchema>;

export default function LoginScreen() {
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);
  const router = useRouter();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormData>({
    resolver: zodResolver(loginSchema),
    defaultValues: {
      email: '',
      password: '',
    },
  });

  // Check for existing session or process Google OAuth callback
  useEffect(() => {
    checkExistingSession();
  }, []);

  const checkExistingSession = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      const userData = await AsyncStorage.getItem('user_data');
      
      if (token && userData) {
        // User is already logged in, redirect to main app
        router.replace('/(tabs)/posts');
        return;
      }
    } catch (error) {
      console.error('Error checking existing session:', error);
    }
  };

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    
    try {
      // Get the base URL for the app
      const baseUrl = process.env.EXPO_PUBLIC_BACKEND_URL?.replace('/api', '') || '';
      // Redirect URL should be the frontend callback page
      const redirectUrl = `${baseUrl}/auth/callback`;
      const authUrl = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
      
      console.log('Opening Google OAuth URL:', authUrl);
      console.log('Redirect URL:', redirectUrl);
      
      // Open the OAuth URL in browser
      const result = await WebBrowser.openAuthSessionAsync(authUrl, redirectUrl);
      
      if (result.type === 'success') {
        const url = result.url;
        console.log('OAuth callback URL:', url);
        
        // Extract session_id from URL fragment
        const sessionIdMatch = url.match(/#session_id=([^&]+)/);
        if (sessionIdMatch) {
          const sessionId = sessionIdMatch[1];
          await processGoogleSession(sessionId);
        } else {
          throw new Error('No session ID found in callback URL');
        }
      } else {
        console.log('OAuth cancelled or failed:', result);
      }
    } catch (error) {
      console.error('Google OAuth error:', error);
      Alert.alert(
        'Authentication Error', 
        'Failed to authenticate with Google. Please try again.'
      );
    } finally {
      setGoogleLoading(false);
    }
  };

  const handleAppleLogin = async () => {
    Alert.alert(
      'Coming Soon',
      'Apple Sign-In will be available soon! For now, please use Google OAuth or create an account with email.',
      [{ text: 'OK' }]
    );
  };

  const processGoogleSession = async (sessionId: string) => {
    try {
      console.log('Processing Google session:', sessionId);
      
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
        
        Alert.alert('Success', 'Logged in with Google successfully!', [
          {
            text: 'OK',
            onPress: () => router.replace('/(tabs)/posts'),
          },
        ]);
      } else {
        const errorResult = await backendResponse.json();
        throw new Error(errorResult.detail || 'Failed to process Google authentication');
      }
    } catch (error) {
      console.error('Error processing Google session:', error);
      Alert.alert(
        'Authentication Error',
        error instanceof Error ? error.message : 'Failed to process Google authentication'
      );
    }
  };

  // const onSubmit = async (data: LoginFormData) => {
  //   setLoading(true);
  //   try {
  //     const response = await fetch(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/auth/login`, {
  //       method: 'POST',
  //       headers: {
  //         'Content-Type': 'application/json',
  //       },
  //       body: JSON.stringify(data),
  //     });

  //     const result = await response.json();

  //     if (!response.ok) {
  //       throw new Error(result.detail || 'Login failed');
  //     }

  //     // Store token and user data
  //     await AsyncStorage.multiSet([
  //       ['auth_token', result.access_token],
  //       ['user_data', JSON.stringify(result.user)],
  //     ]);

  //     // Navigate to main app
  //     router.replace('/(tabs)/posts');
  //   } catch (error) {
  //     console.error('Login error:', error);
  //     Alert.alert(
  //       'Login Error',
  //       error instanceof Error ? error.message : 'Something went wrong. Please try again.'
  //     );
  //   } finally {
  //     setLoading(false);
  //   }
  // };

  const onSubmit = async (data: LoginFormData) => {
  setLoading(true);
  try {
    const response = await fetch(`${process.env.EXPO_PUBLIC_BACKEND_URL}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    let result;
    const text = await response.text(); // Always read as text first
    try {
      result = JSON.parse(text); // Try to parse JSON
    } catch {
      result = { detail: text }; // Fallback if not JSON
    }

    if (!response.ok) {
      throw new Error(result.detail || 'Login failed');
    }

    // Store token and user data
    await AsyncStorage.multiSet([
      ['auth_token', result.access_token],
      ['user_data', JSON.stringify(result.user)],
    ]);

    router.replace('/(tabs)/posts');
  } catch (error) {
    console.error('Login error:', error);
    Alert.alert(
      'Login Error',
      error instanceof Error ? error.message : 'Something went wrong. Please try again.'
    );
  } finally {
    setLoading(false);
  }
};


  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          style={styles.scrollView}
          contentContainerStyle={styles.scrollContent}
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => router.back()}
              activeOpacity={0.8}
            >
              <Ionicons name="arrow-back" size={24} color="#ffffff" />
            </TouchableOpacity>
            
            <View style={styles.titleContainer}>
              <Ionicons name="school-outline" size={60} color="#6c5ce7" />
              <Text style={styles.title}>Welcome Back</Text>
              <Text style={styles.subtitle}>Sign in to continue your journey</Text>
            </View>
          </View>

          {/* Form */}
          <View style={styles.form}>
            <Controller
              control={control}
              name="email"
              render={({ field: { onChange, onBlur, value } }) => (
                <TextInput
                  placeholder="Email address"
                  value={value}
                  onChangeText={onChange}
                  onBlur={onBlur}
                  error={errors.email?.message}
                  keyboardType="email-address"
                  autoCapitalize="none"
                  leftIcon="mail-outline"
                />
              )}
            />

            <Controller
              control={control}
              name="password"
              render={({ field: { onChange, onBlur, value } }) => (
                <TextInput
                  placeholder="Password"
                  value={value}
                  onChangeText={onChange}
                  onBlur={onBlur}
                  error={errors.password?.message}
                  secureTextEntry={!showPassword}
                  leftIcon="lock-closed-outline"
                  rightIcon={showPassword ? "eye-off-outline" : "eye-outline"}
                  onRightIconPress={() => setShowPassword(!showPassword)}
                />
              )}
            />

            <TouchableOpacity
              style={styles.forgotPassword}
              onPress={() => router.push('/auth/forgot-password')}
              activeOpacity={0.8}
            >
              <Text style={styles.forgotPasswordText}>Forgot Password?</Text>
            </TouchableOpacity>

            <LoadingButton
              title="Sign In"
              onPress={handleSubmit(onSubmit)}
              loading={loading}
              style={styles.submitButton}
            />

            {/* Divider */}
            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>or</Text>
              <View style={styles.dividerLine} />
            </View>

            {/* Social Login Buttons */}
            <TouchableOpacity
              style={styles.socialButton}
              activeOpacity={0.8}
              onPress={handleGoogleLogin}
              disabled={googleLoading || loading}
            >
              {googleLoading ? (
                <Ionicons name="refresh" size={20} color="#ffffff" />
              ) : (
                <Ionicons name="logo-google" size={20} color="#ffffff" />
              )}
              <Text style={styles.socialButtonText}>
                {googleLoading ? 'Connecting...' : 'Continue with Google'}
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.socialButton, styles.appleSocialButton]}
              activeOpacity={0.8}
              onPress={handleAppleLogin}
              disabled={loading}
            >
              <Ionicons name="logo-apple" size={20} color="#000000" />
              <Text style={[styles.socialButtonText, styles.appleSocialText]}>
                Continue with Apple
              </Text>
            </TouchableOpacity>

            {/* Forgot Password Link */}
            <TouchableOpacity
              style={styles.forgotPasswordContainer}
              onPress={() => router.push('/auth/forgot-password')}
              activeOpacity={0.8}
            >
              <Text style={styles.forgotPasswordText}>Forgot your password?</Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={styles.registerLink}
              onPress={() => router.push('/auth/register')}
              activeOpacity={0.8}
            >
              <Text style={styles.registerText}>
                Don't have an account? <Text style={styles.registerLinkText}>Sign Up</Text>
              </Text>
            </TouchableOpacity>
          </View>

          {/* Footer */}
          <View style={styles.footer}>
            <Text style={styles.footerText}>
              By signing in, you agree to our Terms of Service and Privacy Policy
            </Text>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1a1a2e',
  },
  keyboardView: {
    flex: 1,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  header: {
    paddingTop: 20,
    paddingBottom: 40,
  },
  backButton: {
    alignSelf: 'flex-start',
    padding: 8,
    marginBottom: 30,
  },
  titleContainer: {
    alignItems: 'center',
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
    marginTop: 16,
    marginBottom: 8,
  },
  subtitle: {
    fontSize: 16,
    color: '#a0a0a0',
    lineHeight: 24,
  },
  form: {
    flex: 1,
  },
  forgotPassword: {
    alignSelf: 'flex-end',
    marginBottom: 24,
  },
  forgotPasswordText: {
    fontSize: 14,
    color: '#6c5ce7',
    fontWeight: '500',
  },
  submitButton: {
    marginBottom: 24,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 24,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#404040',
  },
  dividerText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginHorizontal: 16,
  },
  socialButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    paddingVertical: 16,
    paddingHorizontal: 24,
    marginBottom: 24,
  },
  socialButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginLeft: 12,
  },
  appleSocialButton: {
    backgroundColor: '#ffffff',
    borderWidth: 1,
    borderColor: '#e0e0e0',
  },
  appleSocialText: {
    color: '#000000',
  },
  registerLink: {
    alignItems: 'center',
    paddingVertical: 16,
  },
  registerText: {
    fontSize: 16,
    color: '#a0a0a0',
  },
  registerLinkText: {
    color: '#6c5ce7',
    fontWeight: '600',
  },
  footer: {
    alignItems: 'center',
    marginTop: 40,
    paddingHorizontal: 40,
  },
  footerText: {
    fontSize: 12,
    color: '#666666',
    textAlign: 'center',
    lineHeight: 18,
  },
});
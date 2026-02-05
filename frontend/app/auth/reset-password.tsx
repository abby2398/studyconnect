import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  Alert,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { useRouter, useLocalSearchParams } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TextInput } from '../components/TextInput';
import { LoadingButton } from '../components/LoadingButton';

// Validation schema
const resetPasswordSchema = z.object({
  password: z
    .string()
    .min(8, 'Password must be at least 8 characters')
    .regex(/[A-Z]/, 'Password must contain at least one uppercase letter')
    .regex(/[a-z]/, 'Password must contain at least one lowercase letter')
    .regex(/[0-9]/, 'Password must contain at least one number'),
  confirmPassword: z.string(),
}).refine((data) => data.password === data.confirmPassword, {
  message: "Passwords don't match",
  path: ["confirmPassword"],
});

type ResetPasswordFormData = z.infer<typeof resetPasswordSchema>;

export default function ResetPasswordScreen() {
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [userEmail, setUserEmail] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const router = useRouter();
  const { token } = useLocalSearchParams<{ token: string }>();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<ResetPasswordFormData>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: {
      password: '',
      confirmPassword: '',
    },
  });

  useEffect(() => {
    if (token) {
      verifyToken();
    } else {
      setVerifying(false);
      Alert.alert('Error', 'Invalid reset link');
    }
  }, [token]);

  const verifyToken = async () => {
    try {
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/auth/verify-reset-token/${token}`,
        {
          method: 'GET',
        }
      );

      const result = await response.json();

      if (response.ok) {
        setTokenValid(true);
        setUserEmail(result.email);
      } else {
        setTokenValid(false);
        Alert.alert('Invalid Link', result.detail || 'This reset link is invalid or has expired.');
      }
    } catch (error) {
      console.error('Token verification error:', error);
      setTokenValid(false);
      Alert.alert('Error', 'Failed to verify reset link. Please try again.');
    } finally {
      setVerifying(false);
    }
  };

  const handleResetPassword = async (data: ResetPasswordFormData) => {
    setLoading(true);

    try {
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/auth/reset-password`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            token: token,
            new_password: data.password,
          }),
        }
      );

      const result = await response.json();

      if (response.ok) {
        Alert.alert(
          'Success',
          'Your password has been reset successfully!',
          [
            {
              text: 'OK',
              onPress: () => router.push('/auth/login'),
            },
          ]
        );
      } else {
        Alert.alert('Error', result.detail || 'Failed to reset password');
      }
    } catch (error) {
      console.error('Reset password error:', error);
      Alert.alert('Error', 'Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  if (verifying) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
        <View style={styles.loadingContainer}>
          <Ionicons name="shield-checkmark-outline" size={64} color="#6c5ce7" />
          <Text style={styles.loadingTitle}>Verifying Reset Link...</Text>
          <Text style={styles.loadingText}>Please wait while we verify your password reset link.</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!tokenValid) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
        <View style={styles.errorContainer}>
          <Ionicons name="close-circle-outline" size={64} color="#e74c3c" />
          <Text style={styles.errorTitle}>Invalid or Expired Link</Text>
          <Text style={styles.errorText}>
            This password reset link is invalid or has expired. Please request a new password reset.
          </Text>
          
          <View style={styles.errorActions}>
            <TouchableOpacity
              style={styles.requestNewButton}
              onPress={() => router.push('/auth/forgot-password')}
              activeOpacity={0.8}
            >
              <Text style={styles.requestNewButtonText}>Request New Reset Link</Text>
            </TouchableOpacity>
            
            <TouchableOpacity
              style={styles.backToLoginButton}
              onPress={() => router.push('/auth/login')}
              activeOpacity={0.8}
            >
              <Text style={styles.backToLoginText}>Back to Login</Text>
            </TouchableOpacity>
          </View>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      <KeyboardAvoidingView 
        style={styles.keyboardContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          style={styles.scrollContainer}
          contentContainerStyle={styles.scrollContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {/* Header */}
          <View style={styles.header}>
            <TouchableOpacity
              style={styles.backButton}
              onPress={() => router.push('/auth/login')}
              activeOpacity={0.8}
            >
              <Ionicons name="arrow-back" size={24} color="#ffffff" />
            </TouchableOpacity>
          </View>

          {/* Content */}
          <View style={styles.content}>
            <View style={styles.iconContainer}>
              <Ionicons name="key-outline" size={48} color="#6c5ce7" />
            </View>
            
            <Text style={styles.title}>Reset Password</Text>
            <Text style={styles.subtitle}>
              Create a new password for your account: {userEmail}
            </Text>

            {/* Form */}
            <View style={styles.form}>
              <Controller
                control={control}
                name="password"
                render={({ field: { onChange, onBlur, value } }) => (
                  <View style={styles.passwordContainer}>
                    <TextInput
                      label="New Password"
                      placeholder="Enter your new password"
                      value={value}
                      onChangeText={onChange}
                      onBlur={onBlur}
                      error={errors.password?.message}
                      secureTextEntry={!showPassword}
                      autoCapitalize="none"
                      textContentType="newPassword"
                    />
                    <TouchableOpacity
                      style={styles.eyeButton}
                      onPress={() => setShowPassword(!showPassword)}
                      activeOpacity={0.8}
                    >
                      <Ionicons
                        name={showPassword ? 'eye-off-outline' : 'eye-outline'}
                        size={20}
                        color="#a0a0a0"
                      />
                    </TouchableOpacity>
                  </View>
                )}
              />

              <Controller
                control={control}
                name="confirmPassword"
                render={({ field: { onChange, onBlur, value } }) => (
                  <View style={styles.passwordContainer}>
                    <TextInput
                      label="Confirm New Password"
                      placeholder="Confirm your new password"
                      value={value}
                      onChangeText={onChange}
                      onBlur={onBlur}
                      error={errors.confirmPassword?.message}
                      secureTextEntry={!showConfirmPassword}
                      autoCapitalize="none"
                      textContentType="newPassword"
                    />
                    <TouchableOpacity
                      style={styles.eyeButton}
                      onPress={() => setShowConfirmPassword(!showConfirmPassword)}
                      activeOpacity={0.8}
                    >
                      <Ionicons
                        name={showConfirmPassword ? 'eye-off-outline' : 'eye-outline'}
                        size={20}
                        color="#a0a0a0"
                      />
                    </TouchableOpacity>
                  </View>
                )}
              />

              <LoadingButton
                title="Reset Password"
                onPress={handleSubmit(handleResetPassword)}
                loading={loading}
                style={styles.submitButton}
                textStyle={styles.submitButtonText}
              />
            </View>

            {/* Password Requirements */}
            <View style={styles.requirementsContainer}>
              <Text style={styles.requirementsTitle}>Password Requirements:</Text>
              <View style={styles.requirementsList}>
                <View style={styles.requirementItem}>
                  <Ionicons name="checkmark-circle-outline" size={16} color="#00b894" />
                  <Text style={styles.requirementText}>At least 8 characters</Text>
                </View>
                <View style={styles.requirementItem}>
                  <Ionicons name="checkmark-circle-outline" size={16} color="#00b894" />
                  <Text style={styles.requirementText}>One uppercase letter</Text>
                </View>
                <View style={styles.requirementItem}>
                  <Ionicons name="checkmark-circle-outline" size={16} color="#00b894" />
                  <Text style={styles.requirementText}>One lowercase letter</Text>
                </View>
                <View style={styles.requirementItem}>
                  <Ionicons name="checkmark-circle-outline" size={16} color="#00b894" />
                  <Text style={styles.requirementText}>One number</Text>
                </View>
              </View>
            </View>
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
  keyboardContainer: {
    flex: 1,
  },
  scrollContainer: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
  },
  header: {
    paddingHorizontal: 20,
    paddingTop: 20,
  },
  backButton: {
    padding: 8,
    alignSelf: 'flex-start',
  },
  content: {
    flex: 1,
    paddingHorizontal: 30,
    paddingVertical: 40,
    justifyContent: 'center',
  },
  iconContainer: {
    alignItems: 'center',
    marginBottom: 30,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 16,
  },
  subtitle: {
    fontSize: 16,
    color: '#a0a0a0',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 40,
  },
  form: {
    marginBottom: 40,
  },
  passwordContainer: {
    position: 'relative',
    marginBottom: 16,
  },
  eyeButton: {
    position: 'absolute',
    right: 16,
    top: 48,
    padding: 8,
  },
  submitButton: {
    backgroundColor: '#6c5ce7',
    marginTop: 24,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  requirementsContainer: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 20,
  },
  requirementsTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  requirementsList: {
    gap: 8,
  },
  requirementItem: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  requirementText: {
    fontSize: 14,
    color: '#d0d0d0',
    marginLeft: 12,
  },
  // Loading screen styles
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  loadingTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 12,
  },
  loadingText: {
    fontSize: 16,
    color: '#a0a0a0',
    textAlign: 'center',
    lineHeight: 24,
  },
  // Error screen styles
  errorContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 40,
  },
  errorTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 12,
  },
  errorText: {
    fontSize: 16,
    color: '#a0a0a0',
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 40,
  },
  errorActions: {
    alignSelf: 'stretch',
  },
  requestNewButton: {
    backgroundColor: '#6c5ce7',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  requestNewButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  backToLoginButton: {
    backgroundColor: 'transparent',
    borderWidth: 2,
    borderColor: '#404040',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  backToLoginText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#a0a0a0',
  },
});
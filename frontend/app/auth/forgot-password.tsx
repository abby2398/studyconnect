import React, { useState } from 'react';
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
import { useRouter } from 'expo-router';
import { useForm, Controller } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { TextInput } from '../components/TextInput';
import { LoadingButton } from '../components/LoadingButton';

// Validation schema
const forgotPasswordSchema = z.object({
  email: z
    .string()
    .min(1, 'Email is required')
    .email('Please enter a valid email address')
    .refine(
      (email) => email.endsWith('.edu'),
      'Please use your university (.edu) email address'
    ),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export default function ForgotPasswordScreen() {
  const [loading, setLoading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const [sentEmail, setSentEmail] = useState('');
  const router = useRouter();

  const {
    control,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const handleForgotPassword = async (data: ForgotPasswordFormData) => {
    setLoading(true);

    try {
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/auth/forgot-password`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email: data.email }),
        }
      );

      const result = await response.json();

      if (response.ok) {
        setEmailSent(true);
        setSentEmail(data.email);
      } else {
        Alert.alert('Error', result.detail || 'Failed to send reset email');
      }
    } catch (error) {
      console.error('Forgot password error:', error);
      Alert.alert('Error', 'Network error. Please check your connection and try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResendEmail = async () => {
    if (!sentEmail) return;
    
    setLoading(true);
    try {
      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/auth/forgot-password`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ email: sentEmail }),
        }
      );

      const result = await response.json();

      if (response.ok) {
        Alert.alert('Success', 'Password reset email sent again!');
      } else {
        Alert.alert('Error', result.detail || 'Failed to resend email');
      }
    } catch (error) {
      Alert.alert('Error', 'Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  if (emailSent) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
        
        <View style={styles.successContainer}>
          <TouchableOpacity
            style={styles.backButton}
            onPress={() => router.back()}
            activeOpacity={0.8}
          >
            <Ionicons name="arrow-back" size={24} color="#ffffff" />
          </TouchableOpacity>

          <View style={styles.successContent}>
            <View style={styles.successIcon}>
              <Ionicons name="mail-outline" size={64} color="#6c5ce7" />
            </View>
            
            <Text style={styles.successTitle}>Check Your Email</Text>
            
            <Text style={styles.successMessage}>
              We've sent a password reset link to:
            </Text>
            
            <Text style={styles.emailAddress}>{sentEmail}</Text>
            
            <View style={styles.instructionsContainer}>
              <Text style={styles.instructionsTitle}>What's next?</Text>
              <View style={styles.instructionItem}>
                <Ionicons name="checkmark-circle-outline" size={20} color="#00b894" />
                <Text style={styles.instructionText}>
                  Check your email inbox (and spam folder)
                </Text>
              </View>
              <View style={styles.instructionItem}>
                <Ionicons name="checkmark-circle-outline" size={20} color="#00b894" />
                <Text style={styles.instructionText}>
                  Click the "Reset Password" button in the email
                </Text>
              </View>
              <View style={styles.instructionItem}>
                <Ionicons name="checkmark-circle-outline" size={20} color="#00b894" />
                <Text style={styles.instructionText}>
                  Create your new password
                </Text>
              </View>
            </View>

            <View style={styles.actionButtons}>
              <TouchableOpacity
                style={styles.resendButton}
                onPress={handleResendEmail}
                disabled={loading}
                activeOpacity={0.8}
              >
                <Text style={styles.resendButtonText}>
                  {loading ? 'Sending...' : 'Resend Email'}
                </Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.backToLoginButton}
                onPress={() => router.push('/auth/login')}
                activeOpacity={0.8}
              >
                <Text style={styles.backToLoginText}>Back to Login</Text>
              </TouchableOpacity>
            </View>

            <View style={styles.helpContainer}>
              <Text style={styles.helpText}>
                Didn't receive the email? Check your spam folder or contact support.
              </Text>
            </View>
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
              onPress={() => router.back()}
              activeOpacity={0.8}
            >
              <Ionicons name="arrow-back" size={24} color="#ffffff" />
            </TouchableOpacity>
          </View>

          {/* Content */}
          <View style={styles.content}>
            <View style={styles.iconContainer}>
              <Ionicons name="lock-closed-outline" size={48} color="#6c5ce7" />
            </View>
            
            <Text style={styles.title}>Forgot Password?</Text>
            <Text style={styles.subtitle}>
              No worries! Enter your university email address and we'll send you a link to reset your password.
            </Text>

            {/* Form */}
            <View style={styles.form}>
              <Controller
                control={control}
                name="email"
                render={({ field: { onChange, onBlur, value } }) => (
                  <TextInput
                    label="University Email"
                    placeholder="your.name@university.edu"
                    value={value}
                    onChangeText={onChange}
                    onBlur={onBlur}
                    error={errors.email?.message}
                    keyboardType="email-address"
                    autoCapitalize="none"
                    autoComplete="email"
                    textContentType="emailAddress"
                  />
                )}
              />

              <LoadingButton
                title="Send Reset Link"
                onPress={handleSubmit(handleForgotPassword)}
                loading={loading}
                style={styles.submitButton}
                textStyle={styles.submitButtonText}
              />
            </View>

            {/* Security Info */}
            <View style={styles.securityInfo}>
              <View style={styles.securityItem}>
                <Ionicons name="shield-checkmark-outline" size={20} color="#00b894" />
                <Text style={styles.securityText}>
                  Reset links expire in 1 hour for your security
                </Text>
              </View>
              <View style={styles.securityItem}>
                <Ionicons name="time-outline" size={20} color="#74b9ff" />
                <Text style={styles.securityText}>
                  Limited to 3 attempts per 24 hours
                </Text>
              </View>
            </View>

            {/* Back to Login */}
            <View style={styles.footerContainer}>
              <Text style={styles.footerText}>Remember your password? </Text>
              <TouchableOpacity
                onPress={() => router.push('/auth/login')}
                activeOpacity={0.8}
              >
                <Text style={styles.footerLink}>Sign in here</Text>
              </TouchableOpacity>
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
  submitButton: {
    backgroundColor: '#6c5ce7',
    marginTop: 24,
  },
  submitButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  securityInfo: {
    backgroundColor: '#2a2a2a',
    borderRadius: 12,
    padding: 20,
    marginBottom: 40,
  },
  securityItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  securityText: {
    fontSize: 14,
    color: '#d0d0d0',
    marginLeft: 12,
    flex: 1,
  },
  footerContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: '#a0a0a0',
  },
  footerLink: {
    fontSize: 14,
    color: '#6c5ce7',
    fontWeight: '600',
  },
  // Success screen styles
  successContainer: {
    flex: 1,
    padding: 20,
  },
  successContent: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  successIcon: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: '#2a2a2a',
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 30,
  },
  successTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: '#ffffff',
    textAlign: 'center',
    marginBottom: 16,
  },
  successMessage: {
    fontSize: 16,
    color: '#a0a0a0',
    textAlign: 'center',
    marginBottom: 8,
  },
  emailAddress: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6c5ce7',
    textAlign: 'center',
    marginBottom: 40,
  },
  instructionsContainer: {
    alignSelf: 'stretch',
    marginBottom: 40,
  },
  instructionsTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 20,
    textAlign: 'center',
  },
  instructionItem: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 16,
    paddingHorizontal: 20,
  },
  instructionText: {
    fontSize: 14,
    color: '#d0d0d0',
    marginLeft: 12,
    flex: 1,
    lineHeight: 20,
  },
  actionButtons: {
    alignSelf: 'stretch',
    marginBottom: 30,
  },
  resendButton: {
    backgroundColor: '#6c5ce7',
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
    marginBottom: 16,
  },
  resendButtonText: {
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
  helpContainer: {
    backgroundColor: '#2a2a2a',
    borderRadius: 8,
    padding: 16,
  },
  helpText: {
    fontSize: 12,
    color: '#a0a0a0',
    textAlign: 'center',
    lineHeight: 18,
  },
});
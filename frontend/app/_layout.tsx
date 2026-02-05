import React, { useEffect } from 'react';
import { Stack } from 'expo-router';
import { StatusBar } from 'expo-status-bar';
import { pushNotificationService } from './services/PushNotificationService';

export default function RootLayout() {
  useEffect(() => {
    // Initialize push notifications when app starts
    pushNotificationService.initialize();

    // Cleanup on app unmount
    return () => {
      pushNotificationService.cleanup();
    };
  }, []);

  return (
    <>
      <StatusBar style="light" backgroundColor="#1a1a2e" />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: '#1a1a2e' },
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen name="index" />
        <Stack.Screen name="(tabs)" />
        <Stack.Screen name="auth/welcome" />
        <Stack.Screen name="auth/login" />
        <Stack.Screen name="auth/register" />
        <Stack.Screen name="profile/edit" />
        <Stack.Screen name="connections/index" />
        <Stack.Screen name="ai-assistant" />
        <Stack.Screen name="notifications" />
        <Stack.Screen name="events/create" />
        <Stack.Screen name="events/[id]" />
        <Stack.Screen name="posts/create" />
        <Stack.Screen name="posts/[id]/comments" />
        <Stack.Screen name="users/profile/[id]" />
        <Stack.Screen name="chat/conversation/[id]" />
      </Stack>
    </>
  );
}
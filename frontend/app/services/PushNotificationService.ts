import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Configure notification handler
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

class PushNotificationService {
  private expoPushToken: string | null = null;

  async initialize() {
    try {
      // Register for push notifications
      const token = await this.registerForPushNotifications();
      if (token) {
        this.expoPushToken = token;
        await this.registerTokenWithBackend(token);
      }

      // Handle notification received while app is foregrounded
      Notifications.addNotificationReceivedListener(this.handleNotificationReceived);

      // Handle notification response (when user taps notification)
      Notifications.addNotificationResponseReceivedListener(this.handleNotificationResponse);

      console.log('Push notification service initialized successfully');
    } catch (error) {
      console.error('Error initializing push notifications:', error);
    }
  }

  async registerForPushNotifications(): Promise<string | null> {
    try {
      if (!Device.isDevice) {
        console.log('Must use physical device for Push Notifications');
        return null;
      }

      const { status: existingStatus } = await Notifications.getPermissionsAsync();
      let finalStatus = existingStatus;

      if (existingStatus !== 'granted') {
        const { status } = await Notifications.requestPermissionsAsync();
        finalStatus = status;
      }

      if (finalStatus !== 'granted') {
        console.log('Failed to get push token for push notification!');
        return null;
      }

      const token = (await Notifications.getExpoPushTokenAsync()).data;
      console.log('Expo Push Token:', token);

      if (Platform.OS === 'android') {
        Notifications.setNotificationChannelAsync('default', {
          name: 'StudyConnect',
          importance: Notifications.AndroidImportance.MAX,
          vibrationPattern: [0, 250, 250, 250],
          lightColor: '#6c5ce7',
          sound: 'default',
        });
      }

      return token;
    } catch (error) {
      console.error('Error getting push token:', error);
      return null;
    }
  }

  async registerTokenWithBackend(token: string) {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');
      if (!authToken) {
        console.log('No auth token available, skipping token registration');
        return;
      }

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/notifications/push-tokens`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
          body: JSON.stringify({
            token: token,
            device_type: Platform.OS,
            device_id: Device.modelName || 'unknown',
            app_version: '1.0.0', // You can get this from app config
          }),
        }
      );

      if (response.ok) {
        console.log('Push token registered successfully with backend');
      } else {
        const error = await response.json();
        console.error('Failed to register push token:', error);
      }
    } catch (error) {
      console.error('Error registering push token with backend:', error);
    }
  }

  handleNotificationReceived = (notification: Notifications.Notification) => {
    console.log('Notification received while app is open:', notification);
    
    // You can customize this behavior
    // For example, update a global state or show an in-app notification
    
    // The notification will still be shown by the system
    // but you can add custom handling here
  };

  handleNotificationResponse = (response: Notifications.NotificationResponse) => {
    console.log('User tapped notification:', response);
    
    const data = response.notification.request.content.data;
    
    // Handle navigation based on notification type
    this.handleNotificationNavigation(data);
  };

  handleNotificationNavigation = (data: any) => {
    // This would typically use your navigation system
    // For now, we'll just log the data
    console.log('Navigation data from notification:', data);
    
    // Example of how you might handle different notification types:
    /*
    switch (data.type) {
      case 'connection_request':
        // Navigate to connections screen
        break;
      case 'message_received':
        // Navigate to chat with specific user
        break;
      case 'event_invitation':
        // Navigate to specific event
        break;
      default:
        // Navigate to main app
        break;
    }
    */
  };

  async deregisterToken() {
    try {
      if (!this.expoPushToken) return;

      const authToken = await AsyncStorage.getItem('auth_token');
      if (!authToken) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/notifications/push-tokens/${encodeURIComponent(this.expoPushToken)}`,
        {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        }
      );

      if (response.ok) {
        console.log('Push token deregistered successfully');
        this.expoPushToken = null;
      }
    } catch (error) {
      console.error('Error deregistering push token:', error);
    }
  }

  async updateNotificationPreferences(preferences: any) {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');
      if (!authToken) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/notifications/preferences`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${authToken}`,
          },
          body: JSON.stringify(preferences),
        }
      );

      if (response.ok) {
        console.log('Notification preferences updated successfully');
        return await response.json();
      } else {
        console.error('Failed to update notification preferences');
      }
    } catch (error) {
      console.error('Error updating notification preferences:', error);
    }
  }

  async sendTestNotification() {
    try {
      const authToken = await AsyncStorage.getItem('auth_token');
      if (!authToken) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/notifications/test`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${authToken}`,
          },
        }
      );

      if (response.ok) {
        console.log('Test notification sent successfully');
      } else {
        console.error('Failed to send test notification');
      }
    } catch (error) {
      console.error('Error sending test notification:', error);
    }
  }

  getExpoPushToken(): string | null {
    return this.expoPushToken;
  }

  // Clean up listeners (call this when user logs out or app unmounts)
  cleanup() {
    Notifications.removeAllNotificationListeners();
  }
}

// Export singleton instance
export const pushNotificationService = new PushNotificationService();

// Export types for use in components
export interface NotificationData {
  type: string;
  title: string;
  body: string;
  data?: any;
}

// Helper function to schedule local notifications (for development/testing)
export async function scheduleLocalNotification(
  title: string,
  body: string,
  data: any = {},
  seconds: number = 1
) {
  await Notifications.scheduleNotificationAsync({
    content: {
      title,
      body,
      data,
      sound: 'default',
    },
    trigger: { seconds },
  });
}
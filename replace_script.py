#!/usr/bin/env python3

import re

# Read the file
with open('/app/frontend/app/(tabs)/search.tsx', 'r') as f:
    content = f.read()

# Define the old and new strings
old_str = '''  const sendConnectionRequest = async (userId: string) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/connections/request`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({ to_user_id: userId }),
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to send connection request');
      }

      Alert.alert('Success', 'Connection request sent!');
    } catch (error) {
      console.error('Connection request error:', error);
      Alert.alert(
        'Error',
        error instanceof Error ? error.message : 'Failed to send connection request'
      );
    }
  };'''

new_str = '''  const sendConnectionRequest = async (userId: string) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/connections/request?to_user_id=${userId}`,
        {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to send connection request');
      }

      Alert.alert('Success', 'Connection request sent!');
    } catch (error) {
      console.error('Connection request error:', error);
      Alert.alert(
        'Error',
        error instanceof Error ? error.message : 'Failed to send connection request'
      );
    }
  };'''

# Perform the replacement
if old_str in content:
    new_content = content.replace(old_str, new_str)
    
    # Write the updated content back to the file
    with open('/app/frontend/app/(tabs)/search.tsx', 'w') as f:
        f.write(new_content)
    
    print("Replacement successful!")
else:
    print("Old string not found in file")
    print("Searching for partial matches...")
    
    # Let's check what's actually in the file around the sendConnectionRequest function
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if 'sendConnectionRequest' in line:
            print(f"Found at line {i+1}: {line}")
            # Print surrounding lines for context
            start = max(0, i-5)
            end = min(len(lines), i+30)
            print("Context:")
            for j in range(start, end):
                print(f"{j+1:3d}: {lines[j]}")
            break
import React, { useState, useEffect } from 'react';
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
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { TextInput } from '../components/TextInput';
import { LoadingButton } from '../components/LoadingButton';

interface UserProfile {
  age?: number;
  gender?: string;
  bio?: string;
  profile_picture?: string;
  origin_country?: string;
  origin_city?: string;
  destination_country?: string;
  destination_city?: string;
  university?: string;
  course?: string;
  study_level?: string;
}

interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  phone?: string;
  profile?: UserProfile;
}

export default function EditProfileScreen() {
  const [user, setUser] = useState<User | null>(null);
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [phone, setPhone] = useState('');
  const [age, setAge] = useState('');
  const [gender, setGender] = useState('');
  const [bio, setBio] = useState('');
  const [originCountry, setOriginCountry] = useState('');
  const [originCity, setOriginCity] = useState('');
  const [destinationCountry, setDestinationCountry] = useState('');
  const [destinationCity, setDestinationCity] = useState('');
  const [university, setUniversity] = useState('');
  const [course, setCourse] = useState('');
  const [studyLevel, setStudyLevel] = useState('');
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState(false);
  const router = useRouter();

  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      if (userData) {
        const user = JSON.parse(userData);
        setUser(user);
        
        // Populate form fields
        setFirstName(user.first_name || '');
        setLastName(user.last_name || '');
        setPhone(user.phone || '');
        setAge(user.profile?.age?.toString() || '');
        setGender(user.profile?.gender || '');
        setBio(user.profile?.bio || '');
        setOriginCountry(user.profile?.origin_country || '');
        setOriginCity(user.profile?.origin_city || '');
        setDestinationCountry(user.profile?.destination_country || '');
        setDestinationCity(user.profile?.destination_city || '');
        setUniversity(user.profile?.university || '');
        setCourse(user.profile?.course || '');
        setStudyLevel(user.profile?.study_level || '');
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateProfile = async () => {
    if (!firstName.trim() || !lastName.trim()) {
      Alert.alert('Error', 'First name and last name are required');
      return;
    }

    setUpdating(true);

    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const updateData = {
        first_name: firstName.trim(),
        last_name: lastName.trim(),
        phone: phone.trim() || null,
        profile: {
          age: age ? parseInt(age) : null,
          gender: gender.trim() || null,
          bio: bio.trim() || null,
          origin_country: originCountry.trim() || null,
          origin_city: originCity.trim() || null,
          destination_country: destinationCountry.trim() || null,
          destination_city: destinationCity.trim() || null,
          university: university.trim() || null,
          course: course.trim() || null,
          study_level: studyLevel.trim() || null,
        },
      };

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/users/me`,
        {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(updateData),
        }
      );

      if (response.ok) {
        const result = await response.json();
        
        // Update stored user data
        await AsyncStorage.setItem('user_data', JSON.stringify(result.user));
        
        Alert.alert(
          'Success',
          'Your profile has been updated successfully!',
          [
            {
              text: 'OK',
              onPress: () => router.back(),
            },
          ]
        );
      } else {
        const result = await response.json();
        Alert.alert('Error', result.detail || 'Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      Alert.alert('Error', 'Failed to update profile');
    } finally {
      setUpdating(false);
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading profile...</Text>
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
          style={styles.headerButton}
          onPress={() => router.back()}
          activeOpacity={0.8}
        >
          <Ionicons name="close" size={24} color="#ffffff" />
        </TouchableOpacity>
        
        <Text style={styles.headerTitle}>Edit Profile</Text>
        
        <LoadingButton
          title="Save"
          onPress={handleUpdateProfile}
          loading={updating}
          style={styles.saveButton}
          textStyle={styles.saveButtonText}
        />
      </View>

      <KeyboardAvoidingView
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
        style={styles.keyboardView}
      >
        <ScrollView
          style={styles.content}
          showsVerticalScrollIndicator={false}
          keyboardShouldPersistTaps="handled"
        >
          {/* Personal Information */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Personal Information</Text>
            
            <View style={styles.nameRow}>
              <View style={styles.nameField}>
                <TextInput
                  label="First Name"
                  placeholder="First Name"
                  value={firstName}
                  onChangeText={setFirstName}
                  maxLength={50}
                />
              </View>
              
              <View style={styles.nameField}>
                <TextInput
                  label="Last Name"
                  placeholder="Last Name"
                  value={lastName}
                  onChangeText={setLastName}
                  maxLength={50}
                />
              </View>
            </View>

            <TextInput
              label="Phone Number (Optional)"
              placeholder="Phone Number"
              value={phone}
              onChangeText={setPhone}
              keyboardType="phone-pad"
              leftIcon="call-outline"
              maxLength={20}
            />

            <View style={styles.nameRow}>
              <View style={styles.nameField}>
                <TextInput
                  label="Age (Optional)"
                  placeholder="Age"
                  value={age}
                  onChangeText={setAge}
                  keyboardType="numeric"
                  maxLength={3}
                />
              </View>
              
              <View style={styles.nameField}>
                <TextInput
                  label="Gender (Optional)"
                  placeholder="Gender"
                  value={gender}
                  onChangeText={setGender}
                  maxLength={20}
                />
              </View>
            </View>

            <TextInput
              label="Bio (Optional)"
              placeholder="Tell us about yourself..."
              value={bio}
              onChangeText={setBio}
              multiline
              maxLength={500}
              style={styles.bioInput}
            />
          </View>

          {/* Academic Information */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Academic Information</Text>
            
            <TextInput
              label="University"
              placeholder="University Name"
              value={university}
              onChangeText={setUniversity}
              leftIcon="school-outline"
              maxLength={100}
            />

            <TextInput
              label="Course/Major"
              placeholder="Your Course or Major"
              value={course}
              onChangeText={setCourse}
              leftIcon="book-outline"
              maxLength={100}
            />

            <TextInput
              label="Study Level"
              placeholder="e.g., Masters, Bachelors, PhD"
              value={studyLevel}
              onChangeText={setStudyLevel}
              leftIcon="trophy-outline"
              maxLength={50}
            />
          </View>

          {/* Location Information */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Location Information</Text>
            
            <View style={styles.locationSubsection}>
              <Text style={styles.subsectionTitle}>Origin</Text>
              <View style={styles.nameRow}>
                <View style={styles.nameField}>
                  <TextInput
                    label="Country"
                    placeholder="Origin Country"
                    value={originCountry}
                    onChangeText={setOriginCountry}
                    maxLength={50}
                  />
                </View>
                
                <View style={styles.nameField}>
                  <TextInput
                    label="City"
                    placeholder="Origin City"
                    value={originCity}
                    onChangeText={setOriginCity}
                    maxLength={50}
                  />
                </View>
              </View>
            </View>

            <View style={styles.locationSubsection}>
              <Text style={styles.subsectionTitle}>Study Destination</Text>
              <View style={styles.nameRow}>
                <View style={styles.nameField}>
                  <TextInput
                    label="Country"
                    placeholder="Destination Country"
                    value={destinationCountry}
                    onChangeText={setDestinationCountry}
                    maxLength={50}
                  />
                </View>
                
                <View style={styles.nameField}>
                  <TextInput
                    label="City"
                    placeholder="Destination City"
                    value={destinationCity}
                    onChangeText={setDestinationCity}
                    maxLength={50}
                  />
                </View>
              </View>
            </View>
          </View>

          {/* Profile Tips */}
          <View style={styles.tipsSection}>
            <Text style={styles.sectionTitle}>Profile Tips</Text>
            <View style={styles.tip}>
              <Ionicons name="bulb-outline" size={16} color="#6c5ce7" />
              <Text style={styles.tipText}>
                Complete your profile to get better matches and connect with more students
              </Text>
            </View>
            <View style={styles.tip}>
              <Ionicons name="people-outline" size={16} color="#6c5ce7" />
              <Text style={styles.tipText}>
                Add your university and course to find students in similar programs
              </Text>
            </View>
            <View style={styles.tip}>
              <Ionicons name="location-outline" size={16} color="#6c5ce7" />
              <Text style={styles.tipText}>
                Include your destination to connect with students in the same area
              </Text>
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
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  headerButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
  },
  saveButton: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    minHeight: 36,
  },
  saveButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  subsectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#a0a0a0',
    marginBottom: 12,
  },
  nameRow: {
    flexDirection: 'row',
    gap: 12,
  },
  nameField: {
    flex: 1,
  },
  bioInput: {
    minHeight: 80,
    textAlignVertical: 'top',
  },
  locationSubsection: {
    marginBottom: 20,
  },
  tipsSection: {
    marginBottom: 32,
  },
  tip: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    backgroundColor: '#2a2a2a',
    padding: 16,
    borderRadius: 12,
    marginBottom: 12,
  },
  tipText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginLeft: 12,
    flex: 1,
    lineHeight: 20,
  },
});
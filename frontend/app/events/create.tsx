import React, { useState } from 'react';
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
import { TextInput } from '../components/TextInput';
import { LoadingButton } from '../components/LoadingButton';

interface EventFormData {
  title: string;
  description: string;
  category: string;
  start_datetime: string;
  end_datetime: string;
  location: {
    address: string;
    city: string;
    country: string;
    venue_name: string;
    is_online: boolean;
    online_link: string;
  };
  max_attendees: string;
  tags: string;
  is_private: boolean;
  registration_required: boolean;
}

export default function CreateEventScreen() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [formData, setFormData] = useState<EventFormData>({
    title: '',
    description: '',
    category: 'study_group',
    start_datetime: '',
    end_datetime: '',
    location: {
      address: '',
      city: '',
      country: '',
      venue_name: '',
      is_online: false,
      online_link: '',
    },
    max_attendees: '',
    tags: '',
    is_private: false,
    registration_required: false,
  });

  const categories = [
    { id: 'study_group', label: 'Study Group', icon: 'school-outline' },
    { id: 'social', label: 'Social', icon: 'people-outline' },
    { id: 'networking', label: 'Networking', icon: 'business-outline' },
    { id: 'workshop', label: 'Workshop', icon: 'construct-outline' },
    { id: 'sports', label: 'Sports', icon: 'fitness-outline' },
    { id: 'cultural', label: 'Cultural', icon: 'globe-outline' },
    { id: 'career', label: 'Career', icon: 'briefcase-outline' },
    { id: 'other', label: 'Other', icon: 'ellipsis-horizontal-outline' },
  ];

  const validateForm = () => {
    if (!formData.title.trim()) {
      Alert.alert('Error', 'Event title is required');
      return false;
    }
    if (!formData.description.trim()) {
      Alert.alert('Error', 'Event description is required');
      return false;
    }
    if (!formData.start_datetime) {
      Alert.alert('Error', 'Start date and time is required');
      return false;
    }
    if (!formData.end_datetime) {
      Alert.alert('Error', 'End date and time is required');
      return false;
    }
    if (!formData.location.is_online && !formData.location.city) {
      Alert.alert('Error', 'City is required for offline events');
      return false;
    }
    if (formData.location.is_online && !formData.location.online_link) {
      Alert.alert('Error', 'Online link is required for online events');
      return false;
    }
    
    const startDate = new Date(formData.start_datetime);
    const endDate = new Date(formData.end_datetime);
    const now = new Date();
    
    if (startDate <= now) {
      Alert.alert('Error', 'Start time must be in the future');
      return false;
    }
    
    if (endDate <= startDate) {
      Alert.alert('Error', 'End time must be after start time');
      return false;
    }
    
    return true;
  };

  const handleCreateEvent = async () => {
    if (!validateForm()) return;

    setLoading(true);

    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        Alert.alert('Error', 'Authentication required');
        return;
      }

      // Prepare event data
      const eventData = {
        title: formData.title.trim(),
        description: formData.description.trim(),
        category: formData.category,
        start_datetime: new Date(formData.start_datetime).toISOString(),
        end_datetime: new Date(formData.end_datetime).toISOString(),
        location: {
          address: formData.location.address || undefined,
          city: formData.location.city || 'Online',
          country: formData.location.country || 'Global',
          venue_name: formData.location.venue_name || undefined,
          is_online: formData.location.is_online,
          online_link: formData.location.online_link || undefined,
        },
        max_attendees: formData.max_attendees ? parseInt(formData.max_attendees) : undefined,
        tags: formData.tags ? formData.tags.split(',').map(tag => tag.trim()).filter(tag => tag) : [],
        is_private: formData.is_private,
        registration_required: formData.registration_required,
      };

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/events/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(eventData),
        }
      );

      if (response.ok) {
        const createdEvent = await response.json();
        Alert.alert('Success', 'Event created successfully!', [
          {
            text: 'OK',
            onPress: () => router.back(),
          },
        ]);
      } else {
        const result = await response.json();
        Alert.alert('Error', result.detail || 'Failed to create event');
      }
    } catch (error) {
      console.error('Error creating event:', error);
      Alert.alert('Error', 'Failed to create event');
    } finally {
      setLoading(false);
    }
  };

  const formatDateTimeForInput = (date: Date) => {
    const year = date.getFullYear();
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const day = String(date.getDate()).padStart(2, '0');
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    return `${year}-${month}-${day}T${hours}:${minutes}`;
  };

  const setDefaultTimes = () => {
    const now = new Date();
    const startTime = new Date(now.getTime() + 2 * 60 * 60 * 1000); // 2 hours from now
    const endTime = new Date(startTime.getTime() + 2 * 60 * 60 * 1000); // 2 hours duration
    
    setFormData(prev => ({
      ...prev,
      start_datetime: formatDateTimeForInput(startTime),
      end_datetime: formatDateTimeForInput(endTime),
    }));
  };

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
        
        <Text style={styles.headerTitle}>Create Event</Text>
        
        <View style={styles.headerRight} />
      </View>

      <KeyboardAvoidingView 
        style={styles.keyboardContainer}
        behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      >
        <ScrollView
          style={styles.content}
          showsVerticalScrollIndicator={false}
          contentContainerStyle={styles.contentContainer}
        >
          {/* Event Details */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Event Details</Text>
            
            <TextInput
              label="Event Title"
              value={formData.title}
              onChangeText={(text) => setFormData(prev => ({ ...prev, title: text }))}
              placeholder="Enter event title..."
              maxLength={200}
            />

            <TextInput
              label="Description"
              value={formData.description}
              onChangeText={(text) => setFormData(prev => ({ ...prev, description: text }))}
              placeholder="Describe your event..."
              multiline
              numberOfLines={4}
              maxLength={2000}
            />

            <Text style={styles.inputLabel}>Category</Text>
            <ScrollView 
              horizontal 
              showsHorizontalScrollIndicator={false}
              style={styles.categoriesContainer}
            >
              {categories.map((category) => (
                <TouchableOpacity
                  key={category.id}
                  style={[
                    styles.categoryChip,
                    formData.category === category.id && styles.categoryChipActive
                  ]}
                  onPress={() => setFormData(prev => ({ ...prev, category: category.id }))}
                  activeOpacity={0.8}
                >
                  <Ionicons 
                    name={category.icon as keyof typeof Ionicons.glyphMap} 
                    size={16} 
                    color={formData.category === category.id ? '#ffffff' : '#a0a0a0'} 
                  />
                  <Text 
                    style={[
                      styles.categoryChipText,
                      formData.category === category.id && styles.categoryChipTextActive
                    ]}
                  >
                    {category.label}
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>

          {/* Date & Time */}
          <View style={styles.section}>
            <View style={styles.sectionHeader}>
              <Text style={styles.sectionTitle}>Date & Time</Text>
              <TouchableOpacity
                style={styles.quickFillButton}
                onPress={setDefaultTimes}
                activeOpacity={0.8}
              >
                <Text style={styles.quickFillText}>Quick Fill</Text>
              </TouchableOpacity>
            </View>
            
            <View style={styles.dateTimeRow}>
              <View style={styles.dateTimeField}>
                <Text style={styles.inputLabel}>Start Date & Time</Text>
                <TouchableOpacity style={styles.dateTimeInput}>
                  <TextInput
                    value={formData.start_datetime}
                    onChangeText={(text) => setFormData(prev => ({ 
                      ...prev, 
                      start_datetime: text 
                    }))}
                    placeholder="YYYY-MM-DDTHH:MM"
                    placeholderTextColor="#a0a0a0"
                  />
                </TouchableOpacity>
              </View>
            </View>

            <View style={styles.dateTimeRow}>
              <View style={styles.dateTimeField}>
                <Text style={styles.inputLabel}>End Date & Time</Text>
                <TouchableOpacity style={styles.dateTimeInput}>
                  <TextInput
                    value={formData.end_datetime}
                    onChangeText={(text) => setFormData(prev => ({ 
                      ...prev, 
                      end_datetime: text 
                    }))}
                    placeholder="YYYY-MM-DDTHH:MM"
                    placeholderTextColor="#a0a0a0"
                  />
                </TouchableOpacity>
              </View>
            </View>

            <Text style={styles.helpText}>
              Format: 2024-01-20T14:00 (Year-Month-Day T Hour:Minute)
            </Text>
          </View>

          {/* Location */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Location</Text>
            
            <View style={styles.toggleRow}>
              <Text style={styles.toggleLabel}>Online Event</Text>
              <TouchableOpacity
                style={[
                  styles.toggle,
                  formData.location.is_online && styles.toggleActive
                ]}
                onPress={() => setFormData(prev => ({ 
                  ...prev, 
                  location: { ...prev.location, is_online: !prev.location.is_online }
                }))}
                activeOpacity={0.8}
              >
                <View style={[
                  styles.toggleIndicator,
                  formData.location.is_online && styles.toggleIndicatorActive
                ]} />
              </TouchableOpacity>
            </View>

            {formData.location.is_online ? (
              <TextInput
                label="Online Meeting Link"
                value={formData.location.online_link}
                onChangeText={(text) => setFormData(prev => ({ 
                  ...prev, 
                  location: { ...prev.location, online_link: text }
                }))}
                placeholder="https://zoom.us/j/... or meet.google.com/..."
              />
            ) : (
              <>
                <TextInput
                  label="Venue Name"
                  value={formData.location.venue_name}
                  onChangeText={(text) => setFormData(prev => ({ 
                    ...prev, 
                    location: { ...prev.location, venue_name: text }
                  }))}
                  placeholder="University Library, Student Center..."
                />

                <TextInput
                  label="Address"
                  value={formData.location.address}
                  onChangeText={(text) => setFormData(prev => ({ 
                    ...prev, 
                    location: { ...prev.location, address: text }
                  }))}
                  placeholder="Street address..."
                />

                <View style={styles.locationRow}>
                  <View style={styles.locationField}>
                    <TextInput
                      label="City"
                      value={formData.location.city}
                      onChangeText={(text) => setFormData(prev => ({ 
                        ...prev, 
                        location: { ...prev.location, city: text }
                      }))}
                      placeholder="City name..."
                    />
                  </View>
                  <View style={styles.locationField}>
                    <TextInput
                      label="Country"
                      value={formData.location.country}
                      onChangeText={(text) => setFormData(prev => ({ 
                        ...prev, 
                        location: { ...prev.location, country: text }
                      }))}
                      placeholder="Country name..."
                    />
                  </View>
                </View>
              </>
            )}
          </View>

          {/* Additional Options */}
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>Additional Options</Text>
            
            <TextInput
              label="Maximum Attendees (Optional)"
              value={formData.max_attendees}
              onChangeText={(text) => setFormData(prev => ({ ...prev, max_attendees: text }))}
              placeholder="Leave empty for unlimited"
              keyboardType="numeric"
            />

            <TextInput
              label="Tags (Optional)"
              value={formData.tags}
              onChangeText={(text) => setFormData(prev => ({ ...prev, tags: text }))}
              placeholder="machine-learning, study, algorithms (comma separated)"
            />

            <View style={styles.optionsContainer}>
              <TouchableOpacity
                style={styles.optionRow}
                onPress={() => setFormData(prev => ({ ...prev, is_private: !prev.is_private }))}
                activeOpacity={0.8}
              >
                <View style={styles.optionInfo}>
                  <Text style={styles.optionTitle}>Private Event</Text>
                  <Text style={styles.optionDescription}>
                    Only invited members can see and join
                  </Text>
                </View>
                <View style={[
                  styles.checkbox,
                  formData.is_private && styles.checkboxActive
                ]}>
                  {formData.is_private && (
                    <Ionicons name="checkmark" size={16} color="#ffffff" />
                  )}
                </View>
              </TouchableOpacity>

              <TouchableOpacity
                style={styles.optionRow}
                onPress={() => setFormData(prev => ({ 
                  ...prev, 
                  registration_required: !prev.registration_required 
                }))}
                activeOpacity={0.8}
              >
                <View style={styles.optionInfo}>
                  <Text style={styles.optionTitle}>Registration Required</Text>
                  <Text style={styles.optionDescription}>
                    Members must register to join the event
                  </Text>
                </View>
                <View style={[
                  styles.checkbox,
                  formData.registration_required && styles.checkboxActive
                ]}>
                  {formData.registration_required && (
                    <Ionicons name="checkmark" size={16} color="#ffffff" />
                  )}
                </View>
              </TouchableOpacity>
            </View>
          </View>
        </ScrollView>

        {/* Create Button */}
        <View style={styles.footer}>
          <LoadingButton
            title="Create Event"
            onPress={handleCreateEvent}
            loading={loading}
            style={styles.createButton}
            textStyle={styles.createButtonText}
          />
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
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  backButton: {
    padding: 8,
  },
  headerTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
  },
  headerRight: {
    width: 40,
  },
  keyboardContainer: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  contentContainer: {
    paddingBottom: 20,
  },
  section: {
    paddingHorizontal: 20,
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  quickFillButton: {
    backgroundColor: '#6c5ce7',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  quickFillText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
  },
  inputLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 8,
    marginTop: 16,
  },
  categoriesContainer: {
    marginTop: 8,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    marginRight: 12,
  },
  categoryChipActive: {
    backgroundColor: '#6c5ce7',
  },
  categoryChipText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginLeft: 8,
  },
  categoryChipTextActive: {
    color: '#ffffff',
  },
  dateTimeRow: {
    marginBottom: 16,
  },
  dateTimeField: {
    flex: 1,
  },
  dateTimeInput: {
    borderWidth: 1,
    borderColor: '#404040',
    borderRadius: 12,
    backgroundColor: '#2a2a2a',
  },
  helpText: {
    fontSize: 12,
    color: '#a0a0a0',
    marginTop: 8,
    fontStyle: 'italic',
  },
  toggleRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 16,
  },
  toggleLabel: {
    fontSize: 16,
    color: '#ffffff',
  },
  toggle: {
    width: 50,
    height: 30,
    borderRadius: 15,
    backgroundColor: '#404040',
    justifyContent: 'center',
    paddingHorizontal: 3,
  },
  toggleActive: {
    backgroundColor: '#6c5ce7',
  },
  toggleIndicator: {
    width: 24,
    height: 24,
    borderRadius: 12,
    backgroundColor: '#ffffff',
    alignSelf: 'flex-start',
  },
  toggleIndicatorActive: {
    alignSelf: 'flex-end',
  },
  locationRow: {
    flexDirection: 'row',
    gap: 16,
  },
  locationField: {
    flex: 1,
  },
  optionsContainer: {
    marginTop: 8,
  },
  optionRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  optionInfo: {
    flex: 1,
  },
  optionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  optionDescription: {
    fontSize: 14,
    color: '#a0a0a0',
    lineHeight: 20,
  },
  checkbox: {
    width: 24,
    height: 24,
    borderRadius: 4,
    borderWidth: 2,
    borderColor: '#404040',
    backgroundColor: 'transparent',
    alignItems: 'center',
    justifyContent: 'center',
  },
  checkboxActive: {
    backgroundColor: '#6c5ce7',
    borderColor: '#6c5ce7',
  },
  footer: {
    padding: 20,
    borderTopWidth: 1,
    borderTopColor: '#404040',
  },
  createButton: {
    backgroundColor: '#6c5ce7',
  },
  createButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
});
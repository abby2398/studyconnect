import React, { useState, useEffect, useCallback } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';

interface EventLocation {
  address?: string;
  city: string;
  country: string;
  venue_name?: string;
  is_online: boolean;
  online_link?: string;
}

interface Event {
  id: string;
  title: string;
  description: string;
  category: string;
  creator_id: string;
  start_datetime: string;
  end_datetime: string;
  location: EventLocation;
  max_attendees?: number;
  current_attendees: number;
  tags: string[];
  status: string;
  created_at: string;
}

interface EventWithDetails {
  event: Event;
  creator: {
    id: string;
    first_name: string;
    last_name: string;
    profile?: any;
  };
  attendee_count: number;
  user_attendance_status?: string;
  is_creator: boolean;
  can_join: boolean;
}

export default function EventsScreen() {
  const [events, setEvents] = useState<EventWithDetails[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState('all');
  const router = useRouter();

  const categories = [
    { id: 'all', label: 'All Events', icon: 'grid-outline' },
    { id: 'study_group', label: 'Study Groups', icon: 'school-outline' },
    { id: 'social', label: 'Social', icon: 'people-outline' },
    { id: 'networking', label: 'Networking', icon: 'business-outline' },
    { id: 'workshop', label: 'Workshops', icon: 'construct-outline' },
    { id: 'sports', label: 'Sports', icon: 'fitness-outline' },
    { id: 'cultural', label: 'Cultural', icon: 'globe-outline' },
    { id: 'career', label: 'Career', icon: 'briefcase-outline' },
  ];

  useFocusEffect(
    useCallback(() => {
      loadEvents();
    }, [selectedCategory])
  );

  const loadEvents = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const params = new URLSearchParams();
      if (selectedCategory !== 'all') {
        params.append('category', selectedCategory);
      }

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/events/?${params}`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const data = await response.json();
        setEvents(data);
      } else {
        Alert.alert('Error', 'Failed to load events');
      }
    } catch (error) {
      console.error('Error loading events:', error);
      Alert.alert('Error', 'Failed to load events');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    loadEvents();
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  const formatTime = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleTimeString('en-US', {
      hour: 'numeric',
      minute: '2-digit',
      hour12: true,
    });
  };

  const getEventStatusColor = (event: Event) => {
    const now = new Date();
    const startDate = new Date(event.start_datetime);
    const endDate = new Date(event.end_datetime);

    if (now < startDate) return '#6c5ce7'; // Upcoming (purple)
    if (now >= startDate && now <= endDate) return '#00b894'; // Ongoing (green)
    return '#a0a0a0'; // Completed (gray)
  };

  const getEventStatusText = (event: Event) => {
    const now = new Date();
    const startDate = new Date(event.start_datetime);
    const endDate = new Date(event.end_datetime);

    if (now < startDate) return 'Upcoming';
    if (now >= startDate && now <= endDate) return 'Live';
    return 'Ended';
  };

  const handleJoinEvent = async (eventId: string) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/events/${eventId}/join`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify({
            status: 'joined',
          }),
        }
      );

      if (response.ok) {
        Alert.alert('Success', 'Joined event successfully!');
        loadEvents(); // Refresh the list
      } else {
        const result = await response.json();
        Alert.alert('Error', result.detail || 'Failed to join event');
      }
    } catch (error) {
      console.error('Error joining event:', error);
      Alert.alert('Error', 'Failed to join event');
    }
  };

  const renderEventCard = (eventWithDetails: EventWithDetails) => {
    const { event, creator, user_attendance_status, can_join, is_creator } = eventWithDetails;
    
    return (
      <TouchableOpacity
        key={event.id}
        style={styles.eventCard}
        onPress={() => router.push(`/events/${event.id}`)}
        activeOpacity={0.8}
      >
        {/* Event Header */}
        <View style={styles.eventHeader}>
          <View style={styles.eventTitleContainer}>
            <Text style={styles.eventTitle} numberOfLines={2}>
              {event.title}
            </Text>
            <View style={styles.eventMeta}>
              <View style={[
                styles.statusBadge,
                { backgroundColor: getEventStatusColor(event) }
              ]}>
                <Text style={styles.statusText}>
                  {getEventStatusText(event)}
                </Text>
              </View>
              <Text style={styles.categoryText}>
                {event.category.replace('_', ' ').toUpperCase()}
              </Text>
            </View>
          </View>
          
          <TouchableOpacity style={styles.eventOptions}>
            <Ionicons name="ellipsis-horizontal" size={20} color="#a0a0a0" />
          </TouchableOpacity>
        </View>

        {/* Event Details */}
        <View style={styles.eventDetails}>
          <View style={styles.eventDetailRow}>
            <Ionicons name="calendar-outline" size={16} color="#a0a0a0" />
            <Text style={styles.eventDetailText}>
              {formatDate(event.start_datetime)} at {formatTime(event.start_datetime)}
            </Text>
          </View>
          
          <View style={styles.eventDetailRow}>
            <Ionicons 
              name={event.location.is_online ? "videocam-outline" : "location-outline"} 
              size={16} 
              color="#a0a0a0" 
            />
            <Text style={styles.eventDetailText}>
              {event.location.is_online ? 'Online Event' : `${event.location.city}, ${event.location.country}`}
            </Text>
          </View>
          
          <View style={styles.eventDetailRow}>
            <Ionicons name="person-outline" size={16} color="#a0a0a0" />
            <Text style={styles.eventDetailText}>
              By {creator.first_name} {creator.last_name}
            </Text>
          </View>
        </View>

        {/* Event Description */}
        <Text style={styles.eventDescription} numberOfLines={2}>
          {event.description}
        </Text>

        {/* Event Stats and Actions */}
        <View style={styles.eventFooter}>
          <View style={styles.eventStats}>
            <View style={styles.statItem}>
              <Ionicons name="people-outline" size={16} color="#a0a0a0" />
              <Text style={styles.statText}>
                {event.current_attendees}
                {event.max_attendees ? `/${event.max_attendees}` : ''}
              </Text>
            </View>
            
            {event.tags.length > 0 && (
              <View style={styles.tagsContainer}>
                {event.tags.slice(0, 2).map((tag, index) => (
                  <View key={index} style={styles.tag}>
                    <Text style={styles.tagText}>#{tag}</Text>
                  </View>
                ))}
                {event.tags.length > 2 && (
                  <Text style={styles.moreTagsText}>+{event.tags.length - 2}</Text>
                )}
              </View>
            )}
          </View>

          <View style={styles.eventActions}>
            {user_attendance_status === 'joined' ? (
              <View style={styles.joinedBadge}>
                <Text style={styles.joinedText}>Joined</Text>
              </View>
            ) : is_creator ? (
              <View style={styles.creatorBadge}>
                <Text style={styles.creatorText}>Creator</Text>
              </View>
            ) : can_join ? (
              <TouchableOpacity
                style={styles.joinButton}
                onPress={() => handleJoinEvent(event.id)}
                activeOpacity={0.8}
              >
                <Text style={styles.joinButtonText}>Join</Text>
              </TouchableOpacity>
            ) : (
              <View style={styles.fullBadge}>
                <Text style={styles.fullText}>Full</Text>
              </View>
            )}
          </View>
        </View>
      </TouchableOpacity>
    );
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Campus Events</Text>
        <TouchableOpacity 
          style={styles.headerButton}
          onPress={() => router.push('/events/create')}
        >
          <Ionicons name="add-outline" size={24} color="#ffffff" />
        </TouchableOpacity>
      </View>

      <ScrollView
        style={styles.content}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={onRefresh}
            tintColor="#6c5ce7"
          />
        }
      >
        {/* Category Filters */}
        <ScrollView 
          horizontal 
          showsHorizontalScrollIndicator={false}
          style={styles.categoriesContainer}
          contentContainerStyle={styles.categoriesContent}
        >
          {categories.map((category) => (
            <TouchableOpacity
              key={category.id}
              style={[
                styles.categoryChip,
                selectedCategory === category.id && styles.categoryChipActive
              ]}
              onPress={() => setSelectedCategory(category.id)}
              activeOpacity={0.8}
            >
              <Ionicons 
                name={category.icon as keyof typeof Ionicons.glyphMap} 
                size={16} 
                color={selectedCategory === category.id ? '#ffffff' : '#a0a0a0'} 
              />
              <Text 
                style={[
                  styles.categoryChipText,
                  selectedCategory === category.id && styles.categoryChipTextActive
                ]}
              >
                {category.label}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {events.length > 0 ? (
          // Events List
          <View style={styles.eventsSection}>
            {events.map((eventWithDetails) => renderEventCard(eventWithDetails))}
          </View>
        ) : (
          // Empty State
          <View style={styles.emptyState}>
            <Ionicons name="calendar-outline" size={80} color="#666666" />
            <Text style={styles.emptyStateTitle}>No events yet</Text>
            <Text style={styles.emptyStateText}>
              Be the first to create an event for your university community!
            </Text>
            
            <TouchableOpacity 
              style={styles.emptyStateButton}
              onPress={() => router.push('/events/create')}
              activeOpacity={0.8}
            >
              <Text style={styles.emptyStateButtonText}>Create Event</Text>
            </TouchableOpacity>
          </View>
        )}

        {/* Popular Event Types */}
        <View style={styles.popularSection}>
          <Text style={styles.sectionTitle}>Popular Event Types</Text>
          
          <View style={styles.eventTypeGrid}>
            <TouchableOpacity 
              style={styles.eventTypeCard} 
              activeOpacity={0.8}
              onPress={() => setSelectedCategory('study_group')}
            >
              <Ionicons name="school-outline" size={32} color="#74b9ff" />
              <Text style={styles.eventTypeTitle}>Study Groups</Text>
              <Text style={styles.eventTypeSubtitle}>Collaborative learning</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.eventTypeCard} 
              activeOpacity={0.8}
              onPress={() => setSelectedCategory('social')}
            >
              <Ionicons name="people-outline" size={32} color="#fd79a8" />
              <Text style={styles.eventTypeTitle}>Meetups</Text>
              <Text style={styles.eventTypeSubtitle}>Social gatherings</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.eventTypeCard} 
              activeOpacity={0.8}
              onPress={() => setSelectedCategory('cultural')}
            >
              <Ionicons name="globe-outline" size={32} color="#fdcb6e" />
              <Text style={styles.eventTypeTitle}>Cultural</Text>
              <Text style={styles.eventTypeSubtitle}>Celebrate diversity</Text>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.eventTypeCard} 
              activeOpacity={0.8}
              onPress={() => setSelectedCategory('career')}
            >
              <Ionicons name="briefcase-outline" size={32} color="#55a3ff" />
              <Text style={styles.eventTypeTitle}>Career</Text>
              <Text style={styles.eventTypeSubtitle}>Professional growth</Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Event Guidelines */}
        <View style={styles.guidelinesSection}>
          <Text style={styles.sectionTitle}>Event Guidelines</Text>
          
          <View style={styles.guideline}>
            <Ionicons name="checkmark-circle" size={20} color="#00b894" />
            <Text style={styles.guidelineText}>
              Keep events relevant to student community
            </Text>
          </View>
          
          <View style={styles.guideline}>
            <Ionicons name="checkmark-circle" size={20} color="#00b894" />
            <Text style={styles.guidelineText}>
              Provide clear location and timing details
            </Text>
          </View>
          
          <View style={styles.guideline}>
            <Ionicons name="checkmark-circle" size={20} color="#00b894" />
            <Text style={styles.guidelineText}>
              Be respectful and inclusive in all events
            </Text>
          </View>
        </View>
      </ScrollView>
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
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingVertical: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  headerButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  categoriesContainer: {
    paddingVertical: 16,
  },
  categoriesContent: {
    paddingHorizontal: 20,
    gap: 12,
  },
  categoryChip: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
    borderWidth: 1,
    borderColor: '#404040',
  },
  categoryChipActive: {
    backgroundColor: '#6c5ce7',
    borderColor: '#6c5ce7',
  },
  categoryChipText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginLeft: 6,
    fontWeight: '500',
  },
  categoryChipTextActive: {
    color: '#ffffff',
  },
  eventsSection: {
    paddingHorizontal: 20,
  },
  eventCard: {
    backgroundColor: '#2a2a2a',
    borderRadius: 16,
    padding: 20,
    marginBottom: 16,
  },
  eventHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 12,
  },
  eventTitleContainer: {
    flex: 1,
    marginRight: 12,
  },
  eventTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 8,
  },
  eventMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  statusBadge: {
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
  },
  categoryText: {
    fontSize: 12,
    color: '#a0a0a0',
    fontWeight: '500',
  },
  eventOptions: {
    padding: 4,
  },
  eventDetails: {
    marginBottom: 12,
    gap: 6,
  },
  eventDetailRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  eventDetailText: {
    fontSize: 14,
    color: '#a0a0a0',
    flex: 1,
  },
  eventDescription: {
    fontSize: 14,
    color: '#a0a0a0',
    lineHeight: 20,
    marginBottom: 16,
  },
  eventFooter: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  eventStats: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
    gap: 12,
  },
  statItem: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
  },
  statText: {
    fontSize: 12,
    color: '#a0a0a0',
    fontWeight: '500',
  },
  tagsContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
  },
  tag: {
    backgroundColor: '#404040',
    paddingHorizontal: 8,
    paddingVertical: 2,
    borderRadius: 8,
  },
  tagText: {
    fontSize: 10,
    color: '#6c5ce7',
    fontWeight: '500',
  },
  moreTagsText: {
    fontSize: 10,
    color: '#a0a0a0',
  },
  eventActions: {
    marginLeft: 12,
  },
  joinButton: {
    backgroundColor: '#6c5ce7',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 12,
  },
  joinButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  joinedBadge: {
    backgroundColor: '#00b894',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  joinedText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
  },
  creatorBadge: {
    backgroundColor: '#fdcb6e',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  creatorText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#2d3436',
  },
  fullBadge: {
    backgroundColor: '#636e72',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  fullText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#ffffff',
  },
  emptyState: {
    alignItems: 'center',
    paddingHorizontal: 40,
    paddingVertical: 60,
  },
  emptyStateTitle: {
    fontSize: 20,
    fontWeight: '600',
    color: '#ffffff',
    marginTop: 20,
    marginBottom: 8,
  },
  emptyStateText: {
    fontSize: 14,
    color: '#a0a0a0',
    textAlign: 'center',
    lineHeight: 20,
    marginBottom: 32,
  },
  emptyStateButton: {
    backgroundColor: '#6c5ce7',
    paddingHorizontal: 32,
    paddingVertical: 16,
    borderRadius: 12,
  },
  emptyStateButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
  },
  popularSection: {
    paddingHorizontal: 20,
    paddingVertical: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  eventTypeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  eventTypeCard: {
    flex: 1,
    minWidth: '47%',
    backgroundColor: '#2a2a2a',
    padding: 20,
    borderRadius: 16,
    alignItems: 'center',
  },
  eventTypeTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginTop: 12,
    marginBottom: 4,
    textAlign: 'center',
  },
  eventTypeSubtitle: {
    fontSize: 12,
    color: '#a0a0a0',
    textAlign: 'center',
  },
  guidelinesSection: {
    paddingHorizontal: 20,
    paddingBottom: 32,
  },
  guideline: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  guidelineText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginLeft: 12,
    flex: 1,
    lineHeight: 20,
  },
});
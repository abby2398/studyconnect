import React, { useState } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  ScrollView,
  RefreshControl,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface Event {
  id: string;
  title: string;
  description: string;
  date: string;
  time: string;
  location: string;
  organizer: string;
  attendees_count: number;
  category: string;
  is_attending: boolean;
}

export default function EventsScreen() {
  const [events, setEvents] = useState<Event[]>([]);
  const [refreshing, setRefreshing] = useState(false);
  const [selectedCategory, setSelectedCategory] = useState('all');

  const categories = [
    { id: 'all', label: 'All Events', icon: 'grid-outline' },
    { id: 'academic', label: 'Academic', icon: 'school-outline' },
    { id: 'social', label: 'Social', icon: 'people-outline' },
    { id: 'cultural', label: 'Cultural', icon: 'globe-outline' },
    { id: 'sports', label: 'Sports', icon: 'fitness-outline' },
    { id: 'career', label: 'Career', icon: 'briefcase-outline' },
  ];

  const onRefresh = async () => {
    setRefreshing(true);
    // TODO: Load events from API
    setRefreshing(false);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    });
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Campus Events</Text>
        <TouchableOpacity style={styles.headerButton}>
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
            {events.map((event) => (
              <View key={event.id} style={styles.eventCard}>
                <View style={styles.eventHeader}>
                  <View style={styles.eventDate}>
                    <Text style={styles.eventDay}>
                      {formatDate(event.date).split(' ')[2]}
                    </Text>
                    <Text style={styles.eventMonth}>
                      {formatDate(event.date).split(' ')[1]}
                    </Text>
                  </View>
                  
                  <View style={styles.eventInfo}>
                    <Text style={styles.eventTitle}>{event.title}</Text>
                    <Text style={styles.eventTime}>{event.time}</Text>
                    <Text style={styles.eventLocation}>
                      <Ionicons name="location-outline" size={14} color="#a0a0a0" />
                      {' '}{event.location}
                    </Text>
                  </View>

                  <TouchableOpacity
                    style={[
                      styles.attendButton,
                      event.is_attending && styles.attendButtonActive
                    ]}
                    activeOpacity={0.8}
                  >
                    <Ionicons 
                      name={event.is_attending ? "checkmark" : "add"} 
                      size={20} 
                      color={event.is_attending ? "#ffffff" : "#6c5ce7"} 
                    />
                  </TouchableOpacity>
                </View>

                <Text style={styles.eventDescription} numberOfLines={2}>
                  {event.description}
                </Text>

                <View style={styles.eventFooter}>
                  <Text style={styles.eventOrganizer}>
                    By {event.organizer}
                  </Text>
                  <Text style={styles.attendeesCount}>
                    {event.attendees_count} attending
                  </Text>
                </View>
              </View>
            ))}
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
            <TouchableOpacity style={styles.eventTypeCard} activeOpacity={0.8}>
              <Ionicons name="school-outline" size={32} color="#74b9ff" />
              <Text style={styles.eventTypeTitle}>Study Groups</Text>
              <Text style={styles.eventTypeSubtitle}>Collaborative learning</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.eventTypeCard} activeOpacity={0.8}>
              <Ionicons name="people-outline" size={32} color="#fd79a8" />
              <Text style={styles.eventTypeTitle}>Meetups</Text>
              <Text style={styles.eventTypeSubtitle}>Social gatherings</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.eventTypeCard} activeOpacity={0.8}>
              <Ionicons name="globe-outline" size={32} color="#fdcb6e" />
              <Text style={styles.eventTypeTitle}>Cultural</Text>
              <Text style={styles.eventTypeSubtitle}>Celebrate diversity</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.eventTypeCard} activeOpacity={0.8}>
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
    marginBottom: 12,
  },
  eventDate: {
    backgroundColor: '#6c5ce7',
    borderRadius: 12,
    padding: 12,
    alignItems: 'center',
    marginRight: 16,
    minWidth: 60,
  },
  eventDay: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  eventMonth: {
    fontSize: 12,
    color: '#ffffff',
    marginTop: 2,
  },
  eventInfo: {
    flex: 1,
  },
  eventTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 4,
  },
  eventTime: {
    fontSize: 14,
    color: '#a0a0a0',
    marginBottom: 2,
  },
  eventLocation: {
    fontSize: 14,
    color: '#a0a0a0',
  },
  attendButton: {
    padding: 12,
    backgroundColor: 'transparent',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#6c5ce7',
  },
  attendButtonActive: {
    backgroundColor: '#6c5ce7',
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
  eventOrganizer: {
    fontSize: 12,
    color: '#a0a0a0',
  },
  attendeesCount: {
    fontSize: 12,
    color: '#6c5ce7',
    fontWeight: '500',
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
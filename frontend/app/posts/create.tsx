import React, { useState, useRef } from 'react';
import {
  View,
  Text,
  StyleSheet,
  SafeAreaView,
  StatusBar,
  TouchableOpacity,
  TextInput,
  ScrollView,
  Alert,
  Image,
  Dimensions,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { useRouter } from 'expo-router';
import { Ionicons } from '@expo/vector-icons';
import * as ImagePicker from 'expo-image-picker';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { LoadingButton } from '../components/LoadingButton';

const { width: screenWidth } = Dimensions.get('window');

interface MediaAttachment {
  id: string;
  file_type: string;
  mime_type: string;
  file_size: number;
  width?: number;
  height?: number;
  data: string;
}

export default function CreatePostScreen() {
  const [content, setContent] = useState('');
  const [location, setLocation] = useState('');
  const [mediaAttachments, setMediaAttachments] = useState<MediaAttachment[]>([]);
  const [posting, setPosting] = useState(false);
  const router = useRouter();
  const textInputRef = useRef<TextInput>(null);

  const pickImage = async () => {
    try {
      // Request permission
      const permissionResult = await ImagePicker.requestMediaLibraryPermissionsAsync();
      
      if (permissionResult.granted === false) {
        Alert.alert('Permission Required', 'Permission to access camera roll is required!');
        return;
      }

      // Launch image picker
      const result = await ImagePicker.launchImageLibraryAsync({
        mediaTypes: ImagePicker.MediaTypeOptions.Images,
        allowsEditing: true,
        aspect: [4, 3],
        quality: 0.8,
        base64: true,
      });

      if (!result.canceled && result.assets[0]) {
        const asset = result.assets[0];
        
        if (!asset.base64) {
          Alert.alert('Error', 'Failed to process image');
          return;
        }

        // Create media attachment
        const mediaAttachment: MediaAttachment = {
          id: Date.now().toString(),
          file_type: 'image',
          mime_type: asset.mimeType || 'image/jpeg',
          file_size: Math.round((asset.base64.length * 3) / 4), // Approximate file size
          width: asset.width,
          height: asset.height,
          data: asset.base64,
        };

        setMediaAttachments(prev => [...prev, mediaAttachment]);
      }
    } catch (error) {
      console.error('Error picking image:', error);
      Alert.alert('Error', 'Failed to pick image');
    }
  };

  const removeMedia = (mediaId: string) => {
    setMediaAttachments(prev => prev.filter(media => media.id !== mediaId));
  };

  const handlePost = async () => {
    if (!content.trim() && mediaAttachments.length === 0) {
      Alert.alert('Error', 'Please add some content or media to your post');
      return;
    }

    setPosting(true);
    
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        Alert.alert('Error', 'Please login again');
        return;
      }

      const postData = {
        content: content.trim() || null,
        post_type: mediaAttachments.length > 0 ? 
          (mediaAttachments.length === 1 ? mediaAttachments[0].file_type : 'mixed') : 
          'text',
        media_attachments: mediaAttachments,
        visibility: 'public',
        location: location.trim() || null,
      };

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/posts/`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`,
          },
          body: JSON.stringify(postData),
        }
      );

      const result = await response.json();

      if (!response.ok) {
        throw new Error(result.detail || 'Failed to create post');
      }

      Alert.alert(
        'Success',
        'Your post has been created successfully!',
        [
          {
            text: 'OK',
            onPress: () => router.back(),
          },
        ]
      );
    } catch (error) {
      console.error('Error creating post:', error);
      Alert.alert(
        'Error',
        error instanceof Error ? error.message : 'Failed to create post'
      );
    } finally {
      setPosting(false);
    }
  };

  const renderMediaAttachment = (media: MediaAttachment) => {
    const imageData = `data:${media.mime_type};base64,${media.data}`;
    const aspectRatio = media.width && media.height ? media.width / media.height : 1;
    const imageHeight = Math.min(200, (screenWidth - 64) / aspectRatio);
    
    return (
      <View key={media.id} style={styles.mediaItem}>
        <Image
          source={{ uri: imageData }}
          style={[
            styles.mediaImage,
            { 
              height: imageHeight,
              aspectRatio: aspectRatio
            }
          ]}
          resizeMode="cover"
        />
        <TouchableOpacity
          style={styles.removeMediaButton}
          onPress={() => removeMedia(media.id)}
          activeOpacity={0.8}
        >
          <Ionicons name="close-circle" size={24} color="#e74c3c" />
        </TouchableOpacity>
      </View>
    );
  };

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
        
        <Text style={styles.headerTitle}>Create Post</Text>
        
        <LoadingButton
          title="Post"
          onPress={handlePost}
          loading={posting}
          disabled={!content.trim() && mediaAttachments.length === 0}
          style={styles.postButton}
          textStyle={styles.postButtonText}
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
          {/* Main Content Input */}
          <View style={styles.inputSection}>
            <TextInput
              ref={textInputRef}
              style={styles.contentInput}
              placeholder="What's on your mind?"
              placeholderTextColor="#666666"
              value={content}
              onChangeText={setContent}
              multiline
              maxLength={2000}
              textAlignVertical="top"
              autoFocus
            />
          </View>

          {/* Character Count */}
          <View style={styles.characterCount}>
            <Text style={[
              styles.characterCountText,
              content.length > 1800 && styles.characterCountWarning
            ]}>
              {content.length}/2000
            </Text>
          </View>

          {/* Media Attachments */}
          {mediaAttachments.length > 0 && (
            <View style={styles.mediaSection}>
              <Text style={styles.sectionTitle}>Media</Text>
              <ScrollView
                horizontal
                showsHorizontalScrollIndicator={false}
                style={styles.mediaScrollView}
              >
                {mediaAttachments.map(renderMediaAttachment)}
              </ScrollView>
            </View>
          )}

          {/* Location Input */}
          <View style={styles.locationSection}>
            <View style={styles.locationHeader}>
              <Ionicons name="location-outline" size={20} color="#a0a0a0" />
              <Text style={styles.sectionTitle}>Add Location</Text>
            </View>
            <TextInput
              style={styles.locationInput}
              placeholder="Where are you?"
              placeholderTextColor="#666666"
              value={location}
              onChangeText={setLocation}
              maxLength={100}
            />
          </View>

          {/* Post Options */}
          <View style={styles.optionsSection}>
            <Text style={styles.sectionTitle}>Add to Your Post</Text>
            
            <View style={styles.optionsGrid}>
              <TouchableOpacity
                style={styles.optionButton}
                onPress={pickImage}
                activeOpacity={0.8}
              >
                <Ionicons name="image-outline" size={24} color="#74b9ff" />
                <Text style={styles.optionText}>Photo</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.optionButton, styles.optionButtonDisabled]}
                activeOpacity={0.8}
              >
                <Ionicons name="videocam-outline" size={24} color="#666666" />
                <Text style={[styles.optionText, styles.optionTextDisabled]}>Video</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.optionButton, styles.optionButtonDisabled]}
                activeOpacity={0.8}
              >
                <Ionicons name="happy-outline" size={24} color="#666666" />
                <Text style={[styles.optionText, styles.optionTextDisabled]}>GIF</Text>
              </TouchableOpacity>

              <TouchableOpacity
                style={[styles.optionButton, styles.optionButtonDisabled]}
                activeOpacity={0.8}
              >
                <Ionicons name="pricetag-outline" size={24} color="#666666" />
                <Text style={[styles.optionText, styles.optionTextDisabled]}>Tag</Text>
              </TouchableOpacity>
            </View>
          </View>

          {/* Post Guidelines */}
          <View style={styles.guidelinesSection}>
            <Text style={styles.sectionTitle}>Posting Guidelines</Text>
            <View style={styles.guideline}>
              <Ionicons name="checkmark-circle" size={16} color="#00b894" />
              <Text style={styles.guidelineText}>
                Be respectful and inclusive
              </Text>
            </View>
            <View style={styles.guideline}>
              <Ionicons name="checkmark-circle" size={16} color="#00b894" />
              <Text style={styles.guidelineText}>
                Share relevant student experiences
              </Text>
            </View>
            <View style={styles.guideline}>
              <Ionicons name="checkmark-circle" size={16} color="#00b894" />
              <Text style={styles.guidelineText}>
                Use hashtags to reach more students
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
  postButton: {
    paddingHorizontal: 20,
    paddingVertical: 8,
    minHeight: 36,
  },
  postButtonText: {
    fontSize: 16,
    fontWeight: '600',
  },
  keyboardView: {
    flex: 1,
  },
  content: {
    flex: 1,
  },
  inputSection: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  contentInput: {
    fontSize: 18,
    color: '#ffffff',
    lineHeight: 24,
    minHeight: 120,
    textAlignVertical: 'top',
  },
  characterCount: {
    alignItems: 'flex-end',
    paddingHorizontal: 20,
    paddingVertical: 8,
  },
  characterCountText: {
    fontSize: 12,
    color: '#a0a0a0',
  },
  characterCountWarning: {
    color: '#f39c12',
  },
  mediaSection: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  mediaScrollView: {
    marginTop: 12,
  },
  mediaItem: {
    position: 'relative',
    marginRight: 12,
  },
  mediaImage: {
    borderRadius: 12,
    backgroundColor: '#404040',
  },
  removeMediaButton: {
    position: 'absolute',
    top: 8,
    right: 8,
    backgroundColor: 'rgba(0, 0, 0, 0.6)',
    borderRadius: 12,
  },
  locationSection: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  locationHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 12,
  },
  locationInput: {
    fontSize: 16,
    color: '#ffffff',
    backgroundColor: '#2a2a2a',
    padding: 12,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#404040',
  },
  optionsSection: {
    padding: 20,
    borderBottomWidth: 1,
    borderBottomColor: '#404040',
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginLeft: 8,
  },
  optionsGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    marginTop: 16,
    gap: 16,
  },
  optionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#404040',
    minWidth: '47%',
  },
  optionButtonDisabled: {
    opacity: 0.5,
  },
  optionText: {
    fontSize: 14,
    color: '#ffffff',
    marginLeft: 8,
    fontWeight: '500',
  },
  optionTextDisabled: {
    color: '#666666',
  },
  guidelinesSection: {
    padding: 20,
  },
  guideline: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: 8,
  },
  guidelineText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginLeft: 8,
    flex: 1,
  },
});
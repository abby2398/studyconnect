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
  Image,
  Dimensions,
  Alert,
} from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { useRouter } from 'expo-router';
import { useFocusEffect } from '@react-navigation/native';

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

interface Post {
  id: string;
  author_id: string;
  content?: string;
  post_type: string;
  media_attachments: MediaAttachment[];
  likes_count: number;
  comments_count: number;
  shares_count: number;
  visibility: string;
  hashtags: string[];
  location?: string;
  created_at: string;
}

interface PostWithDetails {
  post: Post;
  author: {
    id: string;
    first_name: string;
    last_name: string;
    profile?: any;
  };
  is_liked: boolean;
  is_shared: boolean;
  user_can_interact: boolean;
}

interface User {
  id: string;
  first_name: string;
  last_name: string;
  is_verified: boolean;
}

export default function PostsScreen() {
  const [posts, setPosts] = useState<PostWithDetails[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  useFocusEffect(
    useCallback(() => {
      loadUserData();
      loadPosts();
    }, [])
  );

  const loadUserData = async () => {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      if (userData) {
        setUser(JSON.parse(userData));
      }
    } catch (error) {
      console.error('Error loading user data:', error);
    }
  };

  const loadPosts = async () => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const response = await fetch(
        `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/posts/`,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        }
      );

      if (response.ok) {
        const postsData = await response.json();
        setPosts(postsData);
      }
    } catch (error) {
      console.error('Error loading posts:', error);
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadPosts();
    setRefreshing(false);
  };

  const handleCreatePost = () => {
    if (!user?.is_verified) {
      Alert.alert(
        'Verification Required',
        'Only verified students can create posts. Please verify your email first.',
        [{ text: 'OK' }]
      );
      return;
    }
    router.push('/posts/create');
  };

  const handleLikePost = async (postId: string, isLiked: boolean) => {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) return;

      const url = `${process.env.EXPO_PUBLIC_BACKEND_URL}/api/posts/${postId}/like`;
      const method = isLiked ? 'DELETE' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      if (response.ok) {
        // Update local state
        setPosts(prevPosts => 
          prevPosts.map(postItem => {
            if (postItem.post.id === postId) {
              return {
                ...postItem,
                is_liked: !isLiked,
                post: {
                  ...postItem.post,
                  likes_count: isLiked 
                    ? postItem.post.likes_count - 1 
                    : postItem.post.likes_count + 1
                }
              };
            }
            return postItem;
          })
        );
      }
    } catch (error) {
      console.error('Error liking post:', error);
    }
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m`;
    if (hours < 24) return `${hours}h`;
    if (days < 7) return `${days}d`;
    
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric',
      year: date.getFullYear() !== now.getFullYear() ? 'numeric' : undefined
    });
  };

  const renderMediaAttachment = (media: MediaAttachment) => {
    if (media.file_type === 'image') {
      const imageData = `data:${media.mime_type};base64,${media.data}`;
      const aspectRatio = media.width && media.height ? media.width / media.height : 1;
      const imageHeight = Math.min(300, screenWidth * 0.85 / aspectRatio);
      
      return (
        <Image
          key={media.id}
          source={{ uri: imageData }}
          style={[
            styles.postImage,
            { 
              height: imageHeight,
              aspectRatio: aspectRatio
            }
          ]}
          resizeMode="cover"
        />
      );
    }
    
    return (
      <View key={media.id} style={styles.mediaPlaceholder}>
        <Ionicons 
          name={media.file_type === 'video' ? 'play-circle' : 'document'}
          size={48} 
          color="#a0a0a0" 
        />
        <Text style={styles.mediaPlaceholderText}>
          {media.file_type === 'video' ? 'Video' : 'Media'} ({Math.round(media.file_size / 1024)} KB)
        </Text>
      </View>
    );
  };

  const renderPost = (item: PostWithDetails) => {
    const { post, author, is_liked } = item;
    
    return (
      <View key={post.id} style={styles.postContainer}>
        {/* Post Header */}
        <View style={styles.postHeader}>
          <View style={styles.authorInfo}>
            <View style={styles.avatar}>
              <Text style={styles.avatarText}>
                {author.first_name[0]}{author.last_name[0]}
              </Text>
            </View>
            
            <View style={styles.authorDetails}>
              <Text style={styles.authorName}>
                {author.first_name} {author.last_name}
              </Text>
              <Text style={styles.postTime}>
                {formatTime(post.created_at)}
                {post.location && (
                  <Text style={styles.location}>
                    {' • '}{post.location}
                  </Text>
                )}
              </Text>
            </View>
          </View>
          
          <TouchableOpacity style={styles.moreButton}>
            <Ionicons name="ellipsis-horizontal" size={20} color="#a0a0a0" />
          </TouchableOpacity>
        </View>

        {/* Post Content */}
        {post.content && (
          <Text style={styles.postContent}>{post.content}</Text>
        )}

        {/* Media Attachments */}
        {post.media_attachments.length > 0 && (
          <View style={styles.mediaContainer}>
            {post.media_attachments.map(renderMediaAttachment)}
          </View>
        )}

        {/* Hashtags */}
        {post.hashtags.length > 0 && (
          <View style={styles.hashtagsContainer}>
            {post.hashtags.map(hashtag => (
              <TouchableOpacity key={hashtag} style={styles.hashtag}>
                <Text style={styles.hashtagText}>#{hashtag}</Text>
              </TouchableOpacity>
            ))}
          </View>
        )}

        {/* Post Actions */}
        <View style={styles.postActions}>
          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => handleLikePost(post.id, is_liked)}
          >
            <Ionicons 
              name={is_liked ? "heart" : "heart-outline"} 
              size={24} 
              color={is_liked ? "#e74c3c" : "#a0a0a0"} 
            />
            <Text style={[
              styles.actionText,
              is_liked && styles.likedText
            ]}>
              {post.likes_count}
            </Text>
          </TouchableOpacity>

          <TouchableOpacity 
            style={styles.actionButton}
            onPress={() => router.push(`/posts/${post.id}/comments`)}
          >
            <Ionicons name="chatbubble-outline" size={24} color="#a0a0a0" />
            <Text style={styles.actionText}>{post.comments_count}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="arrow-redo-outline" size={24} color="#a0a0a0" />
            <Text style={styles.actionText}>{post.shares_count}</Text>
          </TouchableOpacity>

          <TouchableOpacity style={styles.actionButton}>
            <Ionicons name="bookmark-outline" size={24} color="#a0a0a0" />
          </TouchableOpacity>
        </View>
      </View>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
        <View style={styles.loadingContainer}>
          <Text style={styles.loadingText}>Loading posts...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a2e" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>StudyConnect</Text>
        <View style={styles.headerActions}>
          <TouchableOpacity 
            style={styles.headerButton}
            onPress={() => router.push('/ai/assistant')}
          >
            <Ionicons name="bulb-outline" size={24} color="#6c5ce7" />
          </TouchableOpacity>
          <TouchableOpacity style={styles.headerButton}>
            <Ionicons name="notifications-outline" size={24} color="#ffffff" />
          </TouchableOpacity>
        </View>
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
        {/* Welcome Section */}
        {user && (
          <View style={styles.welcomeSection}>
            <Text style={styles.welcomeText}>
              Welcome back, {user.first_name}! 👋
            </Text>
            {!user.is_verified && (
              <View style={styles.verificationBanner}>
                <Ionicons name="warning-outline" size={20} color="#f39c12" />
                <Text style={styles.verificationText}>
                  Please verify your email to start posting
                </Text>
                <TouchableOpacity style={styles.verifyButton}>
                  <Text style={styles.verifyButtonText}>Verify</Text>
                </TouchableOpacity>
              </View>
            )}
          </View>
        )}

        {/* Create Post Section */}
        <View style={styles.createPostSection}>
          <TouchableOpacity 
            style={styles.createPostButton}
            onPress={handleCreatePost}
            activeOpacity={0.8}
          >
            <View style={styles.createPostAvatar}>
              <Text style={styles.createPostAvatarText}>
                {user ? `${user.first_name[0]}${user.last_name[0]}` : 'U'}
              </Text>
            </View>
            <Text style={styles.createPostText}>Share your journey...</Text>
            <Ionicons name="add-circle-outline" size={24} color="#6c5ce7" />
          </TouchableOpacity>
        </View>

        {/* Posts Feed */}
        {posts.length > 0 ? (
          posts.map(renderPost)
        ) : (
          <View style={styles.emptyState}>
            <Ionicons name="document-text-outline" size={64} color="#666666" />
            <Text style={styles.emptyStateTitle}>No posts yet</Text>
            <Text style={styles.emptyStateText}>
              Be the first to share something with the community!
            </Text>
            {user?.is_verified && (
              <TouchableOpacity 
                style={styles.emptyStateButton}
                onPress={handleCreatePost}
                activeOpacity={0.8}
              >
                <Text style={styles.emptyStateButtonText}>Create Post</Text>
              </TouchableOpacity>
            )}
          </View>
        )}
      </ScrollView>
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
  headerActions: {
    flexDirection: 'row',
    gap: 16,
  },
  headerButton: {
    padding: 8,
  },
  content: {
    flex: 1,
  },
  welcomeSection: {
    padding: 20,
    backgroundColor: '#252545',
    margin: 16,
    borderRadius: 16,
  },
  welcomeText: {
    fontSize: 18,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 16,
  },
  verificationBanner: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2c2416',
    padding: 12,
    borderRadius: 12,
    borderLeftWidth: 4,
    borderLeftColor: '#f39c12',
  },
  verificationText: {
    flex: 1,
    fontSize: 14,
    color: '#f39c12',
    marginLeft: 8,
  },
  verifyButton: {
    backgroundColor: '#f39c12',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
  },
  verifyButtonText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#ffffff',
  },
  createPostSection: {
    marginHorizontal: 16,
    marginBottom: 16,
  },
  createPostButton: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#2a2a2a',
    padding: 16,
    borderRadius: 16,
    borderWidth: 1,
    borderColor: '#404040',
  },
  createPostAvatar: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#6c5ce7',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  createPostAvatarText: {
    fontSize: 14,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  createPostText: {
    fontSize: 16,
    color: '#a0a0a0',
    flex: 1,
  },
  postContainer: {
    backgroundColor: '#2a2a2a',
    marginHorizontal: 16,
    marginBottom: 16,
    borderRadius: 16,
    overflow: 'hidden',
  },
  postHeader: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 16,
    paddingBottom: 12,
  },
  authorInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    flex: 1,
  },
  avatar: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#6c5ce7',
    justifyContent: 'center',
    alignItems: 'center',
    marginRight: 12,
  },
  avatarText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: '#ffffff',
  },
  authorDetails: {
    flex: 1,
  },
  authorName: {
    fontSize: 16,
    fontWeight: '600',
    color: '#ffffff',
    marginBottom: 2,
  },
  postTime: {
    fontSize: 12,
    color: '#a0a0a0',
  },
  location: {
    color: '#6c5ce7',
  },
  moreButton: {
    padding: 8,
  },
  postContent: {
    fontSize: 16,
    color: '#ffffff',
    lineHeight: 22,
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  mediaContainer: {
    marginBottom: 12,
  },
  postImage: {
    width: '100%',
    backgroundColor: '#404040',
  },
  mediaPlaceholder: {
    backgroundColor: '#404040',
    padding: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  mediaPlaceholderText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginTop: 8,
  },
  hashtagsContainer: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    paddingHorizontal: 16,
    marginBottom: 12,
  },
  hashtag: {
    marginRight: 8,
    marginBottom: 4,
  },
  hashtagText: {
    fontSize: 14,
    color: '#6c5ce7',
    fontWeight: '500',
  },
  postActions: {
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
    borderTopWidth: 1,
    borderTopColor: '#404040',
  },
  actionButton: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: 24,
  },
  actionText: {
    fontSize: 14,
    color: '#a0a0a0',
    marginLeft: 6,
    fontWeight: '500',
  },
  likedText: {
    color: '#e74c3c',
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
    marginTop: 16,
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
});
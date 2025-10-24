import React, { useState, useEffect } from 'react';
import { StyleSheet, SafeAreaView, StatusBar, View, Text, Pressable, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { Image } from 'expo-image';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

interface Topic {
  topic: string;
  concept_count: number;
}

interface TopicCardProps {
  title: string;
  count: number;
  icon: string;
  onPress: () => void;
}

/**
 * Topic card component - matches HomeScreen style
 */
const TopicCard: React.FC<TopicCardProps> = ({ title, count, icon, onPress }) => {
  return (
    <Pressable onPress={onPress} style={styles.topicCard}>
      <Text style={styles.topicIcon}>{icon}</Text>
      <Text style={styles.topicTitle}>{title}</Text>
      <Text style={styles.topicCount}>{count} כרטיסיות</Text>
    </Pressable>
  );
};

/**
 * Topic Selection Screen - Grid of topics
 */
export const TopicSelectionScreen: React.FC = () => {
  const navigation = useNavigation();
  const { getToken } = useAuth();
  const [topics, setTopics] = useState<Topic[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('[TopicSelection] 🟢 Screen mounted');
    console.log('[TopicSelection] API_URL:', API_URL);
    loadTopics();
  }, []);

  const loadTopics = async () => {
    try {
      console.log('[TopicSelection] 📡 Fetching topics...');
      setLoading(true);
      setError(null);

      const token = await getToken();
      console.log('[TopicSelection] 🔑 Got auth token:', token ? `${token.substring(0, 20)}...` : 'null');

      if (!token) {
        throw new Error('No auth token available');
      }

      const url = `${API_URL}/api/concepts/topics`;
      console.log('[TopicSelection] 🌐 Fetching from:', url);

      const response = await fetch(url, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      console.log('[TopicSelection] 📥 Response status:', response.status);

      if (!response.ok) {
        const errorText = await response.text();
        console.error('[TopicSelection] ❌ API Error:', response.status, errorText);
        throw new Error(`API returned ${response.status}: ${errorText}`);
      }

      const data = await response.json();
      console.log('[TopicSelection] ✅ Topics loaded:', data.length, 'topics');
      console.log('[TopicSelection] 📊 Topics data:', JSON.stringify(data, null, 2));
      setTopics(data);
    } catch (error: any) {
      const errorMessage = error.message || 'Unknown error';
      console.error('[TopicSelection] 💥 ERROR loading topics:', errorMessage);
      console.error('[TopicSelection] 💥 ERROR stack:', error.stack);
      setError(errorMessage);
      Alert.alert('שגיאה', `לא ניתן לטעון נושאים: ${errorMessage}`);
    } finally {
      setLoading(false);
      console.log('[TopicSelection] ⏹️ Loading finished');
    }
  };

  const handleTopicPress = (topic: string) => {
    navigation.navigate('TopicDetail', { topic });
  };

  // Map topic names to icons (you can customize these)
  const getTopicIcon = (index: number) => {
    const icons = ['📚', '⚖️', '📝', '🏛️', '📋', '🔍', '📄', '✍️', '📊', '🎯',
                   '📌', '🔑', '📖', '💼', '🏢', '📑', '🔖', '📎'];
    return icons[index % icons.length];
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>טוען נושאים...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            {/* Back Button */}
            <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
              <Text style={styles.backIcon}>→</Text>
            </Pressable>

            {/* Title */}
            <Text style={styles.headerTitle}>מושגים וחוקים</Text>

            {/* Empty space for alignment */}
            <View style={{ width: 40 }} />
          </View>
        </View>

        {/* Topic Grid */}
        <View style={styles.topicGrid}>
          {topics.map((topic, index) => {
            // Create rows of 2 cards
            if (index % 2 === 0) {
              const nextTopic = topics[index + 1];
              return (
                <View key={index} style={styles.topicRow}>
                  <TopicCard
                    title={topic.topic}
                    count={topic.concept_count}
                    icon={getTopicIcon(index)}
                    onPress={() => handleTopicPress(topic.topic)}
                  />
                  {nextTopic && (
                    <TopicCard
                      title={nextTopic.topic}
                      count={nextTopic.concept_count}
                      icon={getTopicIcon(index + 1)}
                      onPress={() => handleTopicPress(nextTopic.topic)}
                    />
                  )}
                </View>
              );
            }
            return null;
          })}
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 24,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 24,
    backgroundColor: Colors.background,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backIcon: {
    fontSize: 28,
    color: Colors.textPrimary,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.textPrimary,
  },
  logo: {
    width: 80,
    height: 50,
  },
  topicGrid: {
    paddingHorizontal: 24,
    gap: 16,
  },
  topicRow: {
    flexDirection: 'row',
    gap: 16,
  },
  topicCard: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 140,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  topicIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  topicTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textPrimary,
    textAlign: 'center',
    marginBottom: 4,
  },
  topicCount: {
    fontSize: 12,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
});

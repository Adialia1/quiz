import React, { useState, useEffect } from 'react';
import { StyleSheet, SafeAreaView, StatusBar, View, Text, Pressable, ActivityIndicator, Alert, FlatList } from 'react-native';
import { Image } from 'expo-image';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
// Temporarily using FlatList instead of FlashList to debug AutoLayoutView error
// import { FlashList } from '@shopify/flash-list';
import { Colors } from '../config/colors';
import { practiceApi } from '../utils/practiceApi';
import { usePracticeStore } from '../stores/practiceStore';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

interface Concept {
  id: string;
  topic: string;
  title: string;
  explanation: string;
  example?: string;
  key_points: string[];
}

/**
 * Starred Concepts Screen - Shows user's favorite concepts
 */
export const StarredConceptsScreen: React.FC = () => {
  const navigation = useNavigation();
  const { userId, getToken } = useAuth();

  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [loading, setLoading] = useState(true);
  const [creatingSession, setCreatingSession] = useState(false);

  useEffect(() => {
    loadFavorites();
  }, []);

  // Reload favorites when screen comes into focus (after unfavoriting in flashcard view)
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      loadFavorites();
    });

    return unsubscribe;
  }, [navigation]);

  const loadFavorites = async () => {
    if (!userId) {
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(`${API_URL}/api/concepts/favorites/${userId}`);
      const data = await response.json();
      setConcepts(data);
    } catch (error) {
      console.error('Error loading favorites:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConceptPress = (concept: Concept) => {
    navigation.navigate('FlashcardStudy', {
      topic: concept.topic,
      mode: 'single',
      conceptId: concept.id
    });
  };

  const handleStartGame = async () => {
    if (concepts.length === 0) return;

    try {
      setCreatingSession(true);

      // Get all unique topic names from starred concepts
      const topics = [...new Set(concepts.map(c => c.topic))];

      // We need to create a custom request since practiceApi.createPracticeSession
      // doesn't support multiple topics. Let's call the API directly.
      const token = await getToken();

      const response = await fetch(`${API_URL}/api/exams`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          exam_type: 'practice',
          question_count: Math.min(25, concepts.length * 3), // Request questions based on favorites
          topics: topics, // Pass array of topics from starred concepts
          // Don't specify difficulty to get questions from all difficulties
        }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to create practice session');
      }

      const session = await response.json();

      // Start session in store
      usePracticeStore.getState().startSession(session);

      // Navigate to practice question screen
      navigation.navigate('PracticeQuestion' as never);
    } catch (error: any) {
      console.error('Error starting favorites practice:', error);

      // Check if error is about insufficient questions
      if (error.message && error.message.includes('Not enough questions')) {
        Alert.alert(
          'אין שאלות זמינות',
          'מצטערים, אך אין שאלות תרגול זמינות עבור הנושאים שסימנת כמועדפים.\n\n' +
          'נסה:\n' +
          '• לסמן מושגים מנושאים נוספים\n' +
          '• לבחור תרגול רגיל מהעמוד הראשי'
        );
      } else {
        Alert.alert(
          'שגיאה',
          error.message || 'לא ניתן ליצור תרגול כרגע. אנא נסה שוב מאוחר יותר.'
        );
      }
    } finally {
      setCreatingSession(false);
    }
  };

  const renderConceptItem = ({ item }: { item: Concept }) => (
    <Pressable
      onPress={() => handleConceptPress(item)}
      style={styles.conceptItem}
    >
      <View style={styles.conceptContent}>
        <View style={styles.topicBadge}>
          <Text style={styles.topicBadgeText}>{item.topic}</Text>
        </View>
        <Text style={styles.conceptTitle}>{item.title}</Text>
        <Text style={styles.conceptPreview} numberOfLines={2}>
          {item.explanation}
        </Text>
      </View>
      <Text style={styles.arrowIcon}>←</Text>
    </Pressable>
  );

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>טוען מועדפים...</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      {/* Loading overlay for creating session */}
      {creatingSession && (
        <View style={styles.loadingOverlay}>
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingOverlayText}>יוצר תרגול...</Text>
          </View>
        </View>
      )}

      {/* Header */}
      <View style={styles.header}>
        <View style={styles.headerContent}>
          {/* Back Button */}
          <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
            <Text style={styles.backIcon}>→</Text>
          </Pressable>

          {/* Title */}
          <Text style={styles.headerTitle}>המועדפים שלי</Text>

          {/* Logo */}
          <Image
            source={require('../../assets/logo.png')}
            style={styles.logo}
            contentFit="contain"
          />
        </View>
      </View>

      {concepts.length === 0 ? (
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyIcon}>⭐</Text>
          <Text style={styles.emptyTitle}>אין עדיין מועדפים</Text>
          <Text style={styles.emptyText}>
            לחץ על הכוכב בכרטיסיות כדי לשמור מושגים למועדפים
          </Text>
        </View>
      ) : (
        <>
          {/* Start Game Button */}
          <View style={styles.startButtonContainer}>
            <Pressable onPress={handleStartGame} style={styles.startButton}>
              <Text style={styles.startButtonIcon}>🎮</Text>
              <Text style={styles.startButtonText}>תרגל מועדפים</Text>
            </Pressable>
          </View>

          {/* Favorites List */}
          <View style={styles.listContainer}>
            <FlatList
              data={concepts}
              renderItem={renderConceptItem}
              keyExtractor={(item) => item.id}
              showsVerticalScrollIndicator={false}
              ItemSeparatorComponent={() => <View style={styles.separator} />}
            />
          </View>
        </>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 16,
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
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.textPrimary,
  },
  logo: {
    width: 60,
    height: 40,
  },
  startButtonContainer: {
    paddingHorizontal: 24,
    paddingVertical: 16,
  },
  startButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 25,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  startButtonIcon: {
    fontSize: 24,
  },
  startButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.white,
  },
  listContainer: {
    flex: 1,
    paddingHorizontal: 24,
  },
  conceptItem: {
    backgroundColor: Colors.white,
    padding: 16,
    borderRadius: 12,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  conceptContent: {
    flex: 1,
    marginRight: 12,
  },
  topicBadge: {
    backgroundColor: Colors.secondaryLight,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 8,
    alignSelf: 'flex-start',
    marginBottom: 8,
  },
  topicBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.primary,
  },
  conceptTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: 4,
    textAlign: 'right',
  },
  conceptPreview: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'right',
    lineHeight: 20,
  },
  arrowIcon: {
    fontSize: 20,
    color: Colors.textSecondary,
  },
  separator: {
    height: 12,
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
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 40,
    gap: 16,
  },
  emptyIcon: {
    fontSize: 64,
    marginBottom: 8,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  loadingBox: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    gap: 16,
  },
  loadingOverlayText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
});

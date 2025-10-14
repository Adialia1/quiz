import React, { useState, useEffect, useRef } from 'react';
import { StyleSheet, SafeAreaView, StatusBar, View, Text, Pressable, ActivityIndicator, Animated, Dimensions, Alert } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';
import { GestureDetector, Gesture, GestureHandlerRootView } from 'react-native-gesture-handler';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';
const { width: SCREEN_WIDTH } = Dimensions.get('window');

interface Concept {
  id: string;
  topic: string;
  title: string;
  explanation: string;
  example?: string;
  key_points: string[];
}

interface RouteParams {
  topic: string;
  mode?: 'all' | 'single';
  conceptId?: string;
}

/**
 * Flashcard Study Screen - Quizlet-style swipeable cards
 */
export const FlashcardStudyScreen: React.FC = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const { userId } = useAuth();
  const { topic, mode = 'all', conceptId } = route.params as RouteParams;

  const [concepts, setConcepts] = useState<Concept[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isFlipped, setIsFlipped] = useState(false);
  const [showExample, setShowExample] = useState(false);
  const [loading, setLoading] = useState(true);
  const [favorites, setFavorites] = useState<Set<string>>(new Set());

  // Animation values
  const flipAnim = useRef(new Animated.Value(0)).current;
  const fadeAnim = useRef(new Animated.Value(1)).current;

  useEffect(() => {
    loadConcepts();
    if (userId) {
      loadFavorites();
    }
  }, [topic, mode, conceptId]);

  const loadConcepts = async () => {
    try {
      if (mode === 'single' && conceptId) {
        // Load single concept
        const response = await fetch(`${API_URL}/api/concepts/${conceptId}`);
        const data = await response.json();
        setConcepts([data]);
      } else {
        // Load all concepts for topic
        const response = await fetch(`${API_URL}/api/concepts/topics/${encodeURIComponent(topic)}`);
        const data = await response.json();
        setConcepts(data);
      }
    } catch (error) {
      console.error('Error loading concepts:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadFavorites = async () => {
    if (!userId) return;
    try {
      const response = await fetch(`${API_URL}/api/concepts/favorites/${userId}`);
      const data = await response.json();
      const favoriteIds = new Set(data.map((c: Concept) => c.id));
      setFavorites(favoriteIds);
    } catch (error) {
      console.error('Error loading favorites:', error);
    }
  };

  const toggleFavorite = async () => {
    if (!userId) {
      Alert.alert('שגיאה', 'יש להתחבר כדי לשמור מועדפים');
      return;
    }

    const currentConcept = concepts[currentIndex];
    const isFavorite = favorites.has(currentConcept.id);

    try {
      if (isFavorite) {
        // Remove from favorites
        await fetch(`${API_URL}/api/concepts/favorites/${userId}/${currentConcept.id}`, {
          method: 'DELETE',
        });
        setFavorites(prev => {
          const newSet = new Set(prev);
          newSet.delete(currentConcept.id);
          return newSet;
        });
      } else {
        // Add to favorites
        await fetch(`${API_URL}/api/concepts/favorites`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId,
            concept_id: currentConcept.id,
          }),
        });
        setFavorites(prev => new Set([...prev, currentConcept.id]));
      }
    } catch (error) {
      console.error('Error toggling favorite:', error);
      Alert.alert('שגיאה', 'אירעה שגיאה בשמירת מועדף');
    }
  };

  const handleFlip = () => {
    const toValue = isFlipped ? 0 : 1;

    Animated.spring(flipAnim, {
      toValue,
      friction: 8,
      tension: 10,
      useNativeDriver: true,
    }).start();

    setIsFlipped(!isFlipped);
  };

  const handleNext = () => {
    if (currentIndex < concepts.length - 1) {
      // Fade out animation
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true,
      }).start(() => {
        setCurrentIndex(currentIndex + 1);
        setIsFlipped(false);
        setShowExample(false);
        flipAnim.setValue(0);

        // Fade in animation
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 150,
          useNativeDriver: true,
        }).start();
      });
    }
  };

  const handlePrevious = () => {
    if (currentIndex > 0) {
      // Fade out animation
      Animated.timing(fadeAnim, {
        toValue: 0,
        duration: 150,
        useNativeDriver: true,
      }).start(() => {
        setCurrentIndex(currentIndex - 1);
        setIsFlipped(false);
        setShowExample(false);
        flipAnim.setValue(0);

        // Fade in animation
        Animated.timing(fadeAnim, {
          toValue: 1,
          duration: 150,
          useNativeDriver: true,
        }).start();
      });
    }
  };

  const frontInterpolate = flipAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['0deg', '180deg'],
  });

  const backInterpolate = flipAnim.interpolate({
    inputRange: [0, 1],
    outputRange: ['180deg', '360deg'],
  });

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.white} />
          <Text style={styles.loadingText}>טוען כרטיסיות...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (concepts.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" />
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>אין כרטיסיות זמינות</Text>
          <Pressable onPress={() => navigation.goBack()} style={styles.backButtonEmpty}>
            <Text style={styles.backButtonText}>חזרה</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  const currentConcept = concepts[currentIndex];

  if (!currentConcept) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.white} />
        </View>
      </SafeAreaView>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="light-content" />

        {/* Header */}
        <View style={styles.header}>
          <Pressable onPress={() => navigation.goBack()} style={styles.closeButton}>
            <Text style={styles.closeIcon}>✕</Text>
          </Pressable>

          <View style={styles.progressContainer}>
            <Text style={styles.progressText}>
              {currentIndex + 1} / {concepts.length}
            </Text>
          </View>

          <View style={styles.placeholder} />
        </View>

        {/* Topic Title */}
        <Text style={styles.topicTitle}>{topic}</Text>

        {/* Flashcard Container */}
        <View style={styles.cardContainer}>
          <Animated.View
            style={[
              styles.cardWrapper,
              {
                opacity: fadeAnim,
              },
            ]}
          >
            <Pressable onPress={handleFlip} style={styles.card}>
              {/* Front of card */}
              <Animated.View
                style={[
                  styles.cardFace,
                  styles.cardFront,
                  {
                    transform: [{ rotateY: frontInterpolate }],
                  },
                ]}
              >
                <Pressable
                  onPress={(e) => {
                    e.stopPropagation();
                    toggleFavorite();
                  }}
                  style={styles.starButtonCard}
                >
                  <Text style={styles.starIconCard}>
                    {favorites.has(currentConcept.id) ? '⭐' : '☆'}
                  </Text>
                </Pressable>
                <View style={styles.tapHint}>
                  <Text style={styles.tapHintText}>👆 הקש להפיכה</Text>
                </View>
                <Text style={styles.cardTitle}>{currentConcept.title}</Text>
              </Animated.View>

              {/* Back of card */}
              <Animated.View
                style={[
                  styles.cardFace,
                  styles.cardBack,
                  {
                    transform: [{ rotateY: backInterpolate }],
                  },
                ]}
              >
                <Pressable
                  onPress={(e) => {
                    e.stopPropagation();
                    toggleFavorite();
                  }}
                  style={styles.starButtonCard}
                >
                  <Text style={styles.starIconCard}>
                    {favorites.has(currentConcept.id) ? '⭐' : '☆'}
                  </Text>
                </Pressable>
                {!showExample ? (
                  <>
                    <Text style={styles.cardExplanation}>{currentConcept.explanation}</Text>

                    {currentConcept.example && (
                      <Pressable
                        onPress={(e) => {
                          e.stopPropagation();
                          setShowExample(true);
                        }}
                        style={styles.exampleButton}
                      >
                        <Text style={styles.exampleButtonText}>💡 דוגמה</Text>
                      </Pressable>
                    )}
                  </>
                ) : (
                  <>
                    <View style={styles.exampleBox}>
                      <Text style={styles.exampleTitle}>💡 דוגמה</Text>
                      <Text style={styles.exampleText}>{currentConcept.example}</Text>
                    </View>

                    <Pressable
                      onPress={(e) => {
                        e.stopPropagation();
                        setShowExample(false);
                      }}
                      style={styles.backToExplanationButton}
                    >
                      <Text style={styles.backToExplanationButtonText}>← חזרה להסבר</Text>
                    </Pressable>
                  </>
                )}
              </Animated.View>
            </Pressable>
          </Animated.View>
        </View>

        {/* Navigation Buttons */}
        <View style={styles.navigationContainer}>
          <Pressable
            onPress={handlePrevious}
            style={[
              styles.navButton,
              currentIndex === 0 && styles.navButtonDisabled,
            ]}
            disabled={currentIndex === 0}
          >
            <Text style={styles.navButtonText}>←</Text>
            <Text style={styles.navButtonLabel}>הקודם</Text>
          </Pressable>

          <Pressable
            onPress={handleNext}
            style={[
              styles.navButton,
              currentIndex === concepts.length - 1 && styles.navButtonDisabled,
            ]}
            disabled={currentIndex === concepts.length - 1}
          >
            <Text style={styles.navButtonText}>→</Text>
            <Text style={styles.navButtonLabel}>הבא</Text>
          </Pressable>
        </View>

        {/* Progress Bar */}
        <View style={styles.progressBar}>
          <View
            style={[
              styles.progressFill,
              {
                width: `${((currentIndex + 1) / concepts.length) * 100}%`,
              },
            ]}
          />
        </View>
      </SafeAreaView>
    </GestureHandlerRootView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.primary,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    paddingHorizontal: 20,
    paddingTop: 10,
    paddingBottom: 10,
  },
  closeButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  closeIcon: {
    fontSize: 28,
    color: Colors.white,
    fontWeight: 'bold',
  },
  progressContainer: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  progressText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.white,
  },
  placeholder: {
    width: 40,
  },
  starButtonCard: {
    position: 'absolute',
    top: 16,
    left: 16,
    width: 44,
    height: 44,
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.9)',
    borderRadius: 22,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
    zIndex: 10,
  },
  starIconCard: {
    fontSize: 26,
  },
  topicTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.white,
    textAlign: 'center',
    marginBottom: 20,
    paddingHorizontal: 20,
  },
  cardContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    paddingHorizontal: 20,
  },
  cardWrapper: {
    width: '100%',
    height: '80%',
  },
  card: {
    width: '100%',
    height: '100%',
    position: 'relative',
  },
  cardFace: {
    position: 'absolute',
    width: '100%',
    height: '100%',
    backgroundColor: Colors.white,
    borderRadius: 20,
    padding: 30,
    backfaceVisibility: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 10,
    elevation: 8,
  },
  cardFront: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  cardBack: {
    justifyContent: 'flex-start',
  },
  tapHint: {
    position: 'absolute',
    top: 20,
    alignSelf: 'center',
    backgroundColor: Colors.secondaryLight,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 20,
  },
  tapHintText: {
    fontSize: 14,
    color: Colors.textSecondary,
  },
  cardTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    textAlign: 'center',
    lineHeight: 38,
  },
  cardExplanation: {
    fontSize: 18,
    color: Colors.textPrimary,
    textAlign: 'right',
    lineHeight: 28,
    marginBottom: 20,
  },
  exampleButton: {
    backgroundColor: Colors.accent,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 25,
    alignSelf: 'center',
    marginTop: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  exampleButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.white,
  },
  backToExplanationButton: {
    backgroundColor: Colors.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 25,
    alignSelf: 'center',
    marginTop: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
    elevation: 3,
  },
  backToExplanationButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.white,
  },
  exampleBox: {
    backgroundColor: '#FFF9E6',
    padding: 20,
    borderRadius: 16,
    borderRightWidth: 4,
    borderRightColor: Colors.accent,
  },
  exampleTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    marginBottom: 12,
    textAlign: 'right',
  },
  exampleText: {
    fontSize: 16,
    color: Colors.textPrimary,
    textAlign: 'right',
    lineHeight: 26,
  },
  navigationContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    paddingHorizontal: 40,
    paddingVertical: 20,
  },
  navButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    paddingHorizontal: 30,
    paddingVertical: 16,
    borderRadius: 30,
    alignItems: 'center',
    minWidth: 120,
  },
  navButtonDisabled: {
    opacity: 0.3,
  },
  navButtonText: {
    fontSize: 24,
    color: Colors.white,
    marginBottom: 4,
  },
  navButtonLabel: {
    fontSize: 14,
    color: Colors.white,
    fontWeight: '600',
  },
  progressBar: {
    height: 4,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    marginHorizontal: 20,
    marginBottom: 10,
    borderRadius: 2,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: Colors.accent,
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
    color: Colors.white,
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 24,
    paddingHorizontal: 40,
  },
  emptyText: {
    fontSize: 18,
    color: Colors.white,
    textAlign: 'center',
  },
  backButtonEmpty: {
    backgroundColor: Colors.white,
    paddingHorizontal: 30,
    paddingVertical: 12,
    borderRadius: 25,
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.primary,
  },
});

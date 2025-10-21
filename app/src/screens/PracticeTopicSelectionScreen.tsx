import React, { useState, useEffect } from 'react';
import { StyleSheet, SafeAreaView, StatusBar, ScrollView, ActivityIndicator, Alert, Pressable, View, Text } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';
import { practiceApi, TopicInfo } from '../utils/practiceApi';
import { usePracticeStore } from '../stores/practiceStore';

/**
 * מסך בחירת נושא ורמת קושי לתרגול
 * Practice Topic and Difficulty Selection Screen
 */
export const PracticeTopicSelectionScreen: React.FC = () => {
  const navigation = useNavigation();
  const { getToken } = useAuth();
  const { config, setConfig, resetConfig } = usePracticeStore();

  const [loading, setLoading] = useState(true);
  const [topics, setTopics] = useState<TopicInfo[]>([]);
  const [difficulties] = useState<string[]>(['קל', 'בינוני', 'קשה']);
  const [maxQuestions, setMaxQuestions] = useState<number>(50);

  // Load topics on mount
  useEffect(() => {
    loadTopics();
  }, []);

  const loadTopics = async () => {
    try {
      setLoading(true);
      const data = await practiceApi.getTopics(getToken);
      setTopics(data.topics);
    } catch (error: any) {
      console.error('Failed to load topics:', error);
      Alert.alert('שגיאה', error.message || 'שגיאה בטעינת נושאים');
    } finally {
      setLoading(false);
    }
  };

  const handleStartPractice = async () => {
    if (!config.selectedTopic) {
      Alert.alert('שים לב', 'יש לבחור נושא');
      return;
    }

    if (!config.selectedDifficulty) {
      Alert.alert('שים לב', 'יש לבחור רמת קושי');
      return;
    }

    try {
      setLoading(true);

      // Try to create session with requested count first to check availability
      const session = await practiceApi.createPracticeSession(
        config.selectedTopic === 'all' ? null : config.selectedTopic,
        config.selectedDifficulty,
        config.questionCount,
        getToken
      );

      // Success - start the session
      usePracticeStore.getState().startSession(session);
      navigation.navigate('PracticeQuestion' as never);
      setLoading(false);
    } catch (error: any) {
      // Handle insufficient questions - automatically create with available count
      if (error.message && error.message.includes('Not enough questions')) {
        const match = error.message.match(/Available: (\d+)/);
        const available = match ? parseInt(match[1]) : 10;
        const requested = config.questionCount;

        // Automatically retry with available count
        try {
          const retrySession = await practiceApi.createPracticeSession(
            config.selectedTopic === 'all' ? null : config.selectedTopic,
            config.selectedDifficulty,
            available, // Use the available count
            getToken
          );

          // Start the session
          usePracticeStore.getState().startSession(retrySession);

          // Update config for next time
          setConfig({ questionCount: available });
          setMaxQuestions(available);

          // Navigate to practice screen
          navigation.navigate('PracticeQuestion' as never);
          setLoading(false);

          // Show informational message AFTER navigation
          setTimeout(() => {
            Alert.alert(
              'הודעה',
              `לא נמצאו ${requested} שאלות עבור הנושא והרמה שנבחרו.\n\nהתרגול התחיל עם ${available} שאלות זמינות.`
            );
          }, 500);
        } catch (retryError: any) {
          setLoading(false);
          console.error('Retry failed:', retryError);
          Alert.alert('שגיאה', retryError.message || 'שגיאה ביצירת תרגול');
        }
      } else {
        setLoading(false);
        Alert.alert('שגיאה', error.message || 'שגיאה ביצירת תרגול');
      }
    }
  };

  const handleTopicSelect = (topicName: string) => {
    const updates: Partial<typeof config> = { selectedTopic: topicName };

    // Update max questions based on selected topic
    let newMax = 50;
    if (topicName === 'all') {
      const totalQuestions = topics.reduce((sum, t) => sum + t.question_count, 0);
      newMax = Math.min(50, totalQuestions);

      // Auto-select "כל הרמות" when "כל הנושאים" is selected
      updates.selectedDifficulty = 'all';
    } else {
      const selectedTopicInfo = topics.find(t => t.name === topicName);
      if (selectedTopicInfo) {
        newMax = Math.min(50, selectedTopicInfo.question_count);
      }

      // Reset difficulty to null if switching from "all topics"
      if (config.selectedTopic === 'all' && config.selectedDifficulty === 'all') {
        updates.selectedDifficulty = null;
      }
    }
    setMaxQuestions(newMax);

    // Auto-adjust question count if it exceeds the new maximum
    if (config.questionCount > newMax) {
      updates.questionCount = newMax;
    }

    setConfig(updates);
  };

  const handleDifficultySelect = (difficulty: string) => {
    setConfig({ selectedDifficulty: difficulty });
  };

  const handleQuestionCountChange = (delta: number) => {
    const newCount = Math.max(10, Math.min(maxQuestions, config.questionCount + delta));
    setConfig({ questionCount: newCount });
  };

  if (loading && topics.length === 0) {
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

      {/* Loading overlay */}
      {loading && (
        <View style={styles.loadingOverlay}>
          <View style={styles.loadingCard}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>יוצר תרגול...</Text>
          </View>
        </View>
      )}

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
            <Text style={styles.backIcon}>→</Text>
          </Pressable>
          <Text style={styles.title}>תרגול שאלות</Text>
        </View>

        {/* Topic Selection */}
        <View style={styles.section}>
          <View style={styles.sectionTitleContainer}>
            <Text style={styles.sectionTitle}>📋 בחר נושא:</Text>
          </View>
          <View style={styles.optionsContainer}>
            {/* All Topics Option */}
            <Pressable
              style={[
                styles.optionCard,
                config.selectedTopic === 'all' && styles.optionCardSelected,
              ]}
              onPress={() => handleTopicSelect('all')}
            >
              <View style={styles.radioCircle}>
                {config.selectedTopic === 'all' && <View style={styles.radioSelected} />}
              </View>
              <Text style={[
                styles.optionText,
                config.selectedTopic === 'all' && styles.optionTextSelected,
              ]}>
                כל הנושאים
              </Text>
            </Pressable>

            {/* Individual Topics */}
            {topics.map((topic) => (
              <Pressable
                key={topic.name}
                style={[
                  styles.optionCard,
                  config.selectedTopic === topic.name && styles.optionCardSelected,
                ]}
                onPress={() => handleTopicSelect(topic.name)}
              >
                <View style={styles.radioCircle}>
                  {config.selectedTopic === topic.name && <View style={styles.radioSelected} />}
                </View>
                <Text style={[
                  styles.optionText,
                  config.selectedTopic === topic.name && styles.optionTextSelected,
                ]}>
                  {topic.name}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>

        {/* Difficulty Selection */}
        <View style={styles.section}>
          <View style={styles.sectionTitleContainer}>
            <Text style={styles.sectionTitle}>🎯 בחר רמת קושי:</Text>
          </View>
          <View style={styles.optionsContainer}>
            {/* All difficulties option - only shown for "all topics" */}
            {config.selectedTopic === 'all' && (
              <Pressable
                style={[
                  styles.optionCard,
                  config.selectedDifficulty === 'all' && styles.optionCardSelected,
                ]}
                onPress={() => handleDifficultySelect('all')}
              >
                <View style={styles.radioCircle}>
                  {config.selectedDifficulty === 'all' && <View style={styles.radioSelected} />}
                </View>
                <Text style={[
                  styles.optionText,
                  config.selectedDifficulty === 'all' && styles.optionTextSelected,
                ]}>
                  כל הרמות (מומלץ)
                </Text>
              </Pressable>
            )}
            {difficulties.map((difficulty) => (
              <Pressable
                key={difficulty}
                style={[
                  styles.optionCard,
                  config.selectedDifficulty === difficulty && styles.optionCardSelected,
                ]}
                onPress={() => handleDifficultySelect(difficulty)}
              >
                <View style={styles.radioCircle}>
                  {config.selectedDifficulty === difficulty && <View style={styles.radioSelected} />}
                </View>
                <Text style={[
                  styles.optionText,
                  config.selectedDifficulty === difficulty && styles.optionTextSelected,
                ]}>
                  {difficulty}
                </Text>
              </Pressable>
            ))}
          </View>
        </View>

        {/* Question Count */}
        <View style={styles.section}>
          <View style={styles.sectionTitleContainer}>
            <Text style={styles.sectionTitle}>📊 מספר שאלות:</Text>
          </View>
          <View style={styles.counterContainer}>
            <Pressable style={styles.counterButton} onPress={() => handleQuestionCountChange(5)}>
              <Text style={styles.counterButtonText}>+</Text>
            </Pressable>
            <Text style={styles.counterValue}>{config.questionCount}</Text>
            <Pressable style={styles.counterButton} onPress={() => handleQuestionCountChange(-5)}>
              <Text style={styles.counterButtonText}>-</Text>
            </Pressable>
          </View>
          <Text style={styles.counterHint}>
            {config.selectedTopic ? `10-${maxQuestions} שאלות זמינות` : '10-50 שאלות'}
          </Text>
        </View>

        {/* Start Button */}
        <Pressable
          style={[
            styles.startButton,
            (!config.selectedTopic || !config.selectedDifficulty) && styles.startButtonDisabled,
          ]}
          onPress={handleStartPractice}
          disabled={!config.selectedTopic || !config.selectedDifficulty || loading}
        >
          <Text style={styles.startButtonText}>התחל תרגול</Text>
        </Pressable>
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
    padding: 24,
    paddingBottom: 40,
  },
  loadingContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 16,
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
  loadingCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.primary,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 32,
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  backIcon: {
    fontSize: 24,
    color: Colors.primary,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: Colors.primary,
    flex: 1,
    textAlign: 'center',
  },
  section: {
    marginBottom: 32,
  },
  sectionTitleContainer: {
    width: '100%',
    alignItems: 'flex-start', // In RTL, flex-start is the right side
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.primary,
    textAlign: 'right',
  },
  optionsContainer: {
    gap: 12,
  },
  optionCard: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: Colors.gray[200],
  },
  optionCardSelected: {
    borderColor: Colors.primary,
    backgroundColor: Colors.primaryLight,
  },
  radioCircle: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: Colors.gray[400],
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: 12,
  },
  radioSelected: {
    width: 12,
    height: 12,
    borderRadius: 6,
    backgroundColor: Colors.primary,
  },
  optionText: {
    fontSize: 16,
    color: Colors.gray[800],
    textAlign: 'right',
  },
  optionTextSelected: {
    color: Colors.primary,
    fontWeight: '600',
  },
  counterContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 24,
    marginBottom: 8,
  },
  counterButton: {
    width: 48,
    height: 48,
    borderRadius: 24,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  counterButtonText: {
    fontSize: 24,
    color: Colors.white,
    fontWeight: 'bold',
  },
  counterValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: Colors.primary,
    minWidth: 60,
    textAlign: 'center',
  },
  counterHint: {
    fontSize: 14,
    color: Colors.gray[600],
    textAlign: 'center',
  },
  startButton: {
    backgroundColor: Colors.accent,
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginTop: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  startButtonDisabled: {
    backgroundColor: Colors.gray[300],
  },
  startButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.white,
  },
});

import React, { useState, useEffect } from 'react';
import { StyleSheet, SafeAreaView, StatusBar, ScrollView, Alert, Pressable, View, Text } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';
import { usePracticeStore } from '../stores/practiceStore';
import { practiceApi } from '../utils/practiceApi';

/**
 * מסך שאלת תרגול עם משוב מיידי
 * Practice Question Screen with Immediate Feedback
 */
export const PracticeQuestionScreen: React.FC = () => {
  const navigation = useNavigation();
  const { getToken } = useAuth();

  const {
    currentSession,
    currentQuestionIndex,
    showingFeedback,
    currentFeedback,
    correctAnswers,
    wrongAnswers,
    getCurrentQuestion,
    getProgress,
    isLastQuestion,
    showFeedback,
    nextQuestion,
    resetSession,
    startQuestionTimer,
    getTimeTaken,
  } = usePracticeStore();

  const [selectedAnswer, setSelectedAnswer] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const question = getCurrentQuestion();
  const progress = getProgress();

  // Start timer when question loads
  useEffect(() => {
    startQuestionTimer();
    setSelectedAnswer(null);
  }, [currentQuestionIndex]);

  // Verify session exists on mount only
  useEffect(() => {
    if (!currentSession) {
      // Only show alert and navigate back on initial mount
      // Don't trigger on session reset during navigation
      const timer = setTimeout(() => {
        Alert.alert('שגיאה', 'לא נמצא תרגול פעיל');
        navigation.goBack();
      }, 100);
      return () => clearTimeout(timer);
    }
  }, []); // Empty dependency array - only run on mount

  const handleAnswerSelect = (answer: string) => {
    if (showingFeedback) return; // Can't change answer after feedback
    setSelectedAnswer(answer);
  };

  const handleCheckAnswer = async () => {
    if (!selectedAnswer || !question || !currentSession) return;

    try {
      setSubmitting(true);

      const timeTaken = getTimeTaken();
      const feedback = await practiceApi.submitAnswer(
        currentSession.exam_id,
        question.id,
        selectedAnswer,
        timeTaken,
        getToken
      );

      // Show feedback
      showFeedback(feedback);
    } catch (error: any) {
      console.error('Failed to submit answer:', error);
      Alert.alert('שגיאה', error.message || 'שגיאה בשליחת תשובה');
    } finally {
      setSubmitting(false);
    }
  };

  const handleNext = () => {
    if (isLastQuestion()) {
      // Show summary and navigate back
      handleComplete();
    } else {
      nextQuestion();
    }
  };

  const handleComplete = () => {
    const total = correctAnswers + wrongAnswers;
    const percentage = total > 0 ? Math.round((correctAnswers / total) * 100) : 0;

    Alert.alert(
      '🎉 סיימת תרגול!',
      `ענית נכון על ${correctAnswers} מתוך ${total}\n` +
      `דיוק: ${percentage}%`,
      [
        {
          text: 'חזור לדף הבית',
          onPress: () => {
            // Navigate first, then reset
            navigation.navigate('Home' as never);
            // Reset after a small delay to allow navigation to complete
            setTimeout(() => {
              resetSession();
            }, 100);
          },
        },
      ]
    );
  };

  const handleBack = () => {
    Alert.alert(
      'לעזוב תרגול?',
      'התקדמות שלך תישמר',
      [
        { text: 'ביטול', style: 'cancel' },
        {
          text: 'עזוב',
          style: 'destructive',
          onPress: () => {
            // Navigate first, then reset
            navigation.goBack();
            setTimeout(() => {
              resetSession();
            }, 100);
          },
        },
      ]
    );
  };

  if (!question || !currentSession) {
    return null;
  }

  const options = [
    { key: 'A', label: 'א', text: question.option_a },
    { key: 'B', label: 'ב', text: question.option_b },
    { key: 'C', label: 'ג', text: question.option_c },
    { key: 'D', label: 'ד', text: question.option_d },
    { key: 'E', label: 'ה', text: question.option_e },
  ];

  const getOptionStyle = (optionKey: string) => {
    if (!showingFeedback) {
      return selectedAnswer === optionKey ? styles.optionSelected : styles.option;
    }

    // Showing feedback
    if (currentFeedback?.correct_answer === optionKey) {
      return styles.optionCorrect; // Green for correct answer
    }
    if (selectedAnswer === optionKey && !currentFeedback?.is_correct) {
      return styles.optionWrong; // Red for wrong answer
    }
    return styles.option;
  };

  const getOptionIcon = (optionKey: string) => {
    if (!showingFeedback) return null;

    if (currentFeedback?.correct_answer === optionKey) {
      return '✅';
    }
    if (selectedAnswer === optionKey && !currentFeedback?.is_correct) {
      return '❌';
    }
    return null;
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Pressable onPress={handleBack} style={styles.backButton}>
            <Text style={styles.backIcon}>→</Text>
          </Pressable>
          <View style={styles.headerCenter}>
            <Text style={styles.questionNumber}>
              שאלה {currentQuestionIndex + 1} מתוך {currentSession.total_questions}
            </Text>
            <View style={styles.progressBar}>
              <View style={[styles.progressFill, { width: `${progress}%` }]} />
            </View>
          </View>
        </View>

        {/* Stats */}
        <View style={styles.stats}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{correctAnswers}</Text>
            <Text style={styles.statLabel}>נכונות</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{wrongAnswers}</Text>
            <Text style={styles.statLabel}>טעויות</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>
              {correctAnswers + wrongAnswers > 0
                ? Math.round((correctAnswers / (correctAnswers + wrongAnswers)) * 100)
                : 0}%
            </Text>
            <Text style={styles.statLabel}>דיוק</Text>
          </View>
        </View>

        {/* Question Info */}
        <View style={styles.questionInfo}>
          <Text style={styles.questionTopic}>📋 {question.topic}</Text>
          <View style={styles.questionMeta}>
            {currentSession.exam_type === 'review_mistakes' && (
              <View style={styles.mistakeBadge}>
                <Text style={styles.mistakeBadgeText}>🔄 טעות מהעבר</Text>
              </View>
            )}
            <Text style={styles.questionDifficulty}>
              {question.difficulty_level === 'easy' && '🟢 קל'}
              {question.difficulty_level === 'medium' && '🟡 בינוני'}
              {question.difficulty_level === 'hard' && '🔴 קשה'}
            </Text>
          </View>
        </View>

        {/* Question Text */}
        <View style={styles.questionCard}>
          <Text style={styles.questionText}>{question.question_text}</Text>
        </View>

        {/* Options */}
        <View style={styles.optionsContainer}>
          {options.map((option) => (
            <Pressable
              key={option.key}
              style={getOptionStyle(option.key)}
              onPress={() => handleAnswerSelect(option.key)}
              disabled={showingFeedback}
            >
              <View style={styles.optionContent}>
                <Text style={styles.optionKey}>{option.label})</Text>
                <Text style={styles.optionText}>{option.text}</Text>
                {getOptionIcon(option.key) && (
                  <Text style={styles.optionIcon}>{getOptionIcon(option.key)}</Text>
                )}
              </View>
            </Pressable>
          ))}
        </View>

        {/* Feedback Section */}
        {showingFeedback && currentFeedback && (
          <View style={styles.feedbackCard}>
            <View style={[
              styles.feedbackHeader,
              currentFeedback.is_correct ? styles.feedbackHeaderCorrect : styles.feedbackHeaderWrong
            ]}>
              <Text style={styles.feedbackTitle}>
                {currentFeedback.is_correct ? '✅ תשובה נכונה!' : '❌ תשובה שגויה'}
              </Text>
            </View>
            <View style={styles.feedbackContent}>
              <Text style={styles.feedbackLabel}>📖 הסבר:</Text>
              <Text style={styles.feedbackExplanation}>{currentFeedback.explanation}</Text>
            </View>
          </View>
        )}

        {/* Action Button */}
        {!showingFeedback ? (
          <Pressable
            style={[styles.actionButton, !selectedAnswer && styles.actionButtonDisabled]}
            onPress={handleCheckAnswer}
            disabled={!selectedAnswer || submitting}
          >
            <Text style={styles.actionButtonText}>
              {submitting ? 'בודק...' : 'בדוק תשובה'}
            </Text>
          </Pressable>
        ) : (
          <Pressable style={styles.actionButton} onPress={handleNext}>
            <Text style={styles.actionButtonText}>
              {isLastQuestion() ? 'סיים תרגול' : 'שאלה הבאה ←'}
            </Text>
          </Pressable>
        )}
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
    padding: 20,
    paddingBottom: 40,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 16,
    gap: 12,
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
  headerCenter: {
    flex: 1,
  },
  questionNumber: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.primary,
    textAlign: 'center',
    marginBottom: 8,
  },
  progressBar: {
    height: 8,
    backgroundColor: Colors.gray[200],
    borderRadius: 4,
    overflow: 'hidden',
  },
  progressFill: {
    height: '100%',
    backgroundColor: Colors.primary,
    borderRadius: 4,
  },
  stats: {
    flexDirection: 'row',
    backgroundColor: Colors.white,
    borderRadius: 12,
    padding: 16,
    marginBottom: 16,
    alignItems: 'center',
    justifyContent: 'space-around',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  statItem: {
    alignItems: 'center',
    flex: 1,
  },
  statValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.primary,
  },
  statLabel: {
    fontSize: 12,
    color: Colors.gray[600],
    marginTop: 4,
  },
  statDivider: {
    width: 1,
    height: 30,
    backgroundColor: Colors.gray[300],
  },
  questionInfo: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  questionTopic: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.primary,
  },
  questionMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  mistakeBadge: {
    backgroundColor: '#FFF3E0',
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: '#FFC107',
  },
  mistakeBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#F57C00',
  },
  questionDifficulty: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.gray[700],
  },
  questionCard: {
    backgroundColor: Colors.primaryLight,
    borderRadius: 12,
    padding: 20,
    marginBottom: 24,
  },
  questionText: {
    fontSize: 18,
    lineHeight: 28,
    color: Colors.gray[900],
    textAlign: 'right',
  },
  optionsContainer: {
    gap: 12,
    marginBottom: 24,
  },
  option: {
    backgroundColor: Colors.white,
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: Colors.gray[200],
  },
  optionSelected: {
    backgroundColor: Colors.primaryLight,
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: Colors.primary,
  },
  optionCorrect: {
    backgroundColor: '#E8F5E9',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: Colors.success,
  },
  optionWrong: {
    backgroundColor: '#FFEBEE',
    borderRadius: 12,
    padding: 16,
    borderWidth: 2,
    borderColor: Colors.error,
  },
  optionContent: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  optionKey: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.primary,
    minWidth: 24,
  },
  optionText: {
    fontSize: 16,
    color: Colors.gray[800],
    flex: 1,
    textAlign: 'right',
  },
  optionIcon: {
    fontSize: 20,
  },
  feedbackCard: {
    backgroundColor: Colors.white,
    borderRadius: 12,
    marginBottom: 24,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  feedbackHeader: {
    padding: 16,
  },
  feedbackHeaderCorrect: {
    backgroundColor: Colors.success,
  },
  feedbackHeaderWrong: {
    backgroundColor: Colors.error,
  },
  feedbackTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.white,
    textAlign: 'center',
  },
  feedbackContent: {
    padding: 20,
  },
  feedbackLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.primary,
    marginBottom: 8,
  },
  feedbackExplanation: {
    fontSize: 16,
    lineHeight: 24,
    color: Colors.gray[800],
    textAlign: 'right',
  },
  actionButton: {
    backgroundColor: Colors.accent,
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  actionButtonDisabled: {
    backgroundColor: Colors.gray[300],
  },
  actionButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.white,
  },
});

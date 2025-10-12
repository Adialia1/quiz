import React, { useEffect, useState } from 'react';
import { SafeAreaView, ActivityIndicator, Alert, View, Text, Pressable, ScrollView, StyleSheet } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { useExamStore, QuestionResult } from '../stores/examStore';
import { examApi } from '../utils/examApi';
import { Colors } from '../config/colors';

/**
 * ExamReviewScreen - Review exam results question by question
 * Using same Duolingo-style card layout as ExamScreen
 */
export const ExamReviewScreen: React.FC = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const { getToken } = useAuth();

  const { examId, results } = route.params as {
    examId: string;
    results: any;
  };

  const [loading, setLoading] = useState(true);
  const [detailedResults, setDetailedResults] = useState<QuestionResult[]>([]);
  const [examData, setExamData] = useState<any>(null);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);

  const { setDetailedResults: setStoreDetailedResults } = useExamStore();

  // Fetch detailed results
  useEffect(() => {
    const fetchDetailedResults = async () => {
      try {
        setLoading(true);
        const data = await examApi.getExamResults(examId, getToken);
        setDetailedResults(data.questions);
        setExamData(data.exam);
        setStoreDetailedResults(data.questions);
      } catch (error: any) {
        console.error('Fetch results error:', error);
        Alert.alert('שגיאה', error.message || 'שגיאה בטעינת תוצאות');
      } finally {
        setLoading(false);
      }
    };

    fetchDetailedResults();
  }, [examId]);

  if (loading || detailedResults.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>טוען תוצאות...</Text>
        </View>
      </SafeAreaView>
    );
  }

  const currentQuestion = detailedResults[currentQuestionIndex];
  const totalQuestions = detailedResults.length;
  const progressPercentage = ((currentQuestionIndex + 1) / totalQuestions) * 100;

  // Calculate score from questions
  const correctAnswers = detailedResults.filter(q => q.is_correct).length;
  const scorePercentage = (correctAnswers / totalQuestions) * 100;
  const passed = scorePercentage >= 85;

  // Format time
  const formatTime = (seconds: number): string => {
    const minutes = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${minutes}:${secs.toString().padStart(2, '0')}`;
  };

  // Navigate to question
  const goToQuestion = (index: number) => {
    if (index < 0 || index >= totalQuestions) return;
    setCurrentQuestionIndex(index);
  };

  // Handle back navigation - always go to Home, not back to ExamScreen
  const handleBackToHome = () => {
    // Use reset to navigate to Home and clear the navigation stack
    // This prevents going back to ExamScreen which no longer has exam data
    navigation.reset({
      index: 0,
      routes: [{ name: 'Home' }],
    });
  };

  // Prepare answer options - show ALL options
  const options = [
    { key: 'A', text: currentQuestion.option_a },
    { key: 'B', text: currentQuestion.option_b },
    { key: 'C', text: currentQuestion.option_c },
    { key: 'D', text: currentQuestion.option_d },
    { key: 'E', text: currentQuestion.option_e },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.blueBackground}>
        {/* Top Navigation Row */}
        <View style={styles.topNav}>
          {/* Exit button */}
          <Pressable onPress={handleBackToHome} style={styles.exitButton}>
            <Text style={styles.exitText}>×</Text>
          </Pressable>

          {/* Question progress */}
          <Text style={styles.progressText}>
            {currentQuestionIndex + 1} מתוך {totalQuestions}
          </Text>

          {/* Score badge */}
          <View style={[styles.scoreBadge, passed ? styles.scoreBadgeSuccess : styles.scoreBadgeError]}>
            <Text style={styles.scoreText}>{scorePercentage.toFixed(0)}%</Text>
          </View>
        </View>

        {/* Progress bar */}
        <View style={styles.progressBarContainer}>
          <View style={[styles.progressBarFill, { width: `${progressPercentage}%` }]} />
        </View>

        {/* White Card */}
        <View style={styles.card}>
          <ScrollView showsVerticalScrollIndicator={false}>
            {/* Result badge */}
            <View style={styles.resultBadgeContainer}>
              <View style={[styles.resultBadge, currentQuestion.is_correct ? styles.resultBadgeSuccess : styles.resultBadgeError]}>
                <Text style={styles.resultBadgeText}>
                  {currentQuestion.is_correct ? '✓ תשובה נכונה' : '✗ תשובה שגויה'}
                </Text>
              </View>
            </View>

            {/* Question text */}
            <Text style={styles.questionText}>
              {currentQuestion.question_text}
            </Text>

            {/* Answer options */}
            <View style={styles.optionsContainer}>
              {options.map((option) => {
                // Skip empty options
                if (!option.text) return null;

                const hasUserAnswer = currentQuestion.user_answer && currentQuestion.user_answer !== "Not answered";
                const isUserAnswer = hasUserAnswer && currentQuestion.user_answer === option.key;
                const isCorrectAnswer = currentQuestion.correct_answer === option.key;

                return (
                  <View
                    key={option.key}
                    style={[
                      styles.optionButton,
                      isCorrectAnswer && styles.optionButtonCorrect,
                      isUserAnswer && !currentQuestion.is_correct && styles.optionButtonWrong,
                    ]}
                  >
                    {/* Radio circle - first child = RIGHT side in RTL */}
                    <View style={[
                      styles.radioOuter,
                      isCorrectAnswer && styles.radioOuterCorrect,
                      isUserAnswer && !currentQuestion.is_correct && styles.radioOuterWrong,
                    ]}>
                      {(isCorrectAnswer || isUserAnswer) && (
                        <View style={[
                          styles.radioInner,
                          isCorrectAnswer && styles.radioInnerCorrect,
                          isUserAnswer && !currentQuestion.is_correct && styles.radioInnerWrong,
                        ]} />
                      )}
                    </View>

                    {/* Answer text - second child = LEFT side in RTL */}
                    <Text style={[
                      styles.optionText,
                      isCorrectAnswer && styles.optionTextCorrect,
                      isUserAnswer && !currentQuestion.is_correct && styles.optionTextWrong,
                    ]}>
                      {option.text}
                    </Text>
                  </View>
                );
              })}
            </View>

            {/* Explanation */}
            <View style={styles.explanationContainer}>
              <Text style={styles.explanationTitle}>הסבר</Text>
              <Text style={styles.explanationText}>{currentQuestion.explanation}</Text>
            </View>
          </ScrollView>

          {/* Navigation */}
          <View style={styles.navContainer}>
            {/* Back to home button on last question */}
            {currentQuestionIndex === totalQuestions - 1 && (
              <Pressable onPress={handleBackToHome} style={styles.homeButton}>
                <Text style={styles.homeButtonText}>חזרה לדף הבית</Text>
              </Pressable>
            )}

            {/* Navigation arrows - RTL: first child = right side, second child = left side */}
            <View style={styles.navArrows}>
              {/* Previous button - first child = RIGHT side in RTL */}
              <Pressable
                onPress={() => goToQuestion(currentQuestionIndex - 1)}
                disabled={currentQuestionIndex === 0}
                style={[
                  styles.navButton,
                  currentQuestionIndex === 0 && styles.navButtonDisabled
                ]}
              >
                <Text style={[
                  styles.navButtonText,
                  currentQuestionIndex === 0 && styles.navButtonTextDisabled
                ]}>
                  {'>'}
                </Text>
              </Pressable>

              {/* Next button - second child = LEFT side in RTL */}
              <Pressable
                onPress={() => goToQuestion(currentQuestionIndex + 1)}
                disabled={currentQuestionIndex === totalQuestions - 1}
                style={[
                  styles.navButton,
                  currentQuestionIndex === totalQuestions - 1 && styles.navButtonDisabled
                ]}
              >
                <Text style={[
                  styles.navButtonText,
                  currentQuestionIndex === totalQuestions - 1 && styles.navButtonTextDisabled
                ]}>
                  {'<'}
                </Text>
              </Pressable>
            </View>
          </View>
        </View>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.primary,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: Colors.white,
  },
  blueBackground: {
    flex: 1,
    backgroundColor: Colors.primary,
    padding: 16,
  },
  topNav: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  exitButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255,255,255,0.2)',
    alignItems: 'center',
    justifyContent: 'center',
  },
  exitText: {
    color: Colors.white,
    fontSize: 24,
    fontWeight: '600',
  },
  progressText: {
    color: Colors.white,
    fontSize: 16,
    fontWeight: '600',
  },
  scoreBadge: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  scoreBadgeSuccess: {
    backgroundColor: Colors.success,
  },
  scoreBadgeError: {
    backgroundColor: Colors.error,
  },
  scoreText: {
    color: Colors.white,
    fontSize: 16,
    fontWeight: '700',
  },
  progressBarContainer: {
    height: 4,
    backgroundColor: 'rgba(255,255,255,0.3)',
    borderRadius: 2,
    marginBottom: 20,
  },
  progressBarFill: {
    height: '100%',
    backgroundColor: Colors.white,
    borderRadius: 2,
  },
  card: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  resultBadgeContainer: {
    alignItems: 'center',
    marginBottom: 24,
  },
  resultBadge: {
    paddingHorizontal: 20,
    paddingVertical: 10,
    borderRadius: 20,
  },
  resultBadgeSuccess: {
    backgroundColor: Colors.success,
  },
  resultBadgeError: {
    backgroundColor: Colors.error,
  },
  resultBadgeText: {
    color: Colors.white,
    fontSize: 16,
    fontWeight: '700',
  },
  questionText: {
    fontSize: 20,
    fontWeight: '600',
    color: '#1F2937',
    textAlign: 'right',
    marginBottom: 24,
    lineHeight: 32,
  },
  optionsContainer: {
    gap: 12,
    marginTop: 8,
  },
  optionButton: {
    backgroundColor: '#F9FAFB',
    borderRadius: 16,
    padding: 18,
    paddingRight: 20,
    paddingLeft: 20,
    flexDirection: 'row',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#E5E7EB',
    marginBottom: 12,
  },
  optionButtonCorrect: {
    backgroundColor: '#F0FDF4',
    borderColor: Colors.success,
  },
  optionButtonWrong: {
    backgroundColor: '#FEF2F2',
    borderColor: Colors.error,
  },
  optionText: {
    fontSize: 16,
    textAlign: 'right',
    flex: 1,
    color: '#374151',
    lineHeight: 24,
    marginRight: 8,
  },
  optionTextCorrect: {
    color: '#15803D',
    fontWeight: '600',
  },
  optionTextWrong: {
    color: '#B91C1C',
    fontWeight: '600',
  },
  radioOuter: {
    width: 20,
    height: 20,
    borderRadius: 10,
    borderWidth: 2,
    borderColor: '#9CA3AF',
    backgroundColor: Colors.white,
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioOuterCorrect: {
    borderColor: Colors.success,
  },
  radioOuterWrong: {
    borderColor: Colors.error,
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: '#9CA3AF',
  },
  radioInnerCorrect: {
    backgroundColor: Colors.success,
  },
  radioInnerWrong: {
    backgroundColor: Colors.error,
  },
  explanationContainer: {
    marginTop: 24,
    padding: 16,
    backgroundColor: '#EFF6FF',
    borderRadius: 12,
    borderWidth: 1,
    borderColor: '#BFDBFE',
  },
  explanationTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1E40AF',
    textAlign: 'right',
    marginBottom: 8,
  },
  explanationText: {
    fontSize: 15,
    color: '#1E3A8A',
    textAlign: 'right',
    lineHeight: 24,
  },
  navContainer: {
    marginTop: 24,
    gap: 16,
  },
  homeButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
  },
  homeButtonText: {
    color: Colors.white,
    fontSize: 18,
    fontWeight: '700',
  },
  navArrows: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    gap: 16,
  },
  navButton: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.white,
    borderWidth: 2,
    borderColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  navButtonDisabled: {
    backgroundColor: '#F3F4F6',
    borderColor: '#E5E7EB',
  },
  navButtonText: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.primary,
  },
  navButtonTextDisabled: {
    color: '#D1D5DB',
  },
});

import React, { useEffect, useState, useRef } from 'react';
import { SafeAreaView, Alert, ActivityIndicator, View, Text, Pressable, ScrollView, StyleSheet } from 'react-native';
import { useNavigation, useRoute } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { useExamStore } from '../stores/examStore';
import { examApi } from '../utils/examApi';
import { Colors } from '../config/colors';

/**
 * ExamScreen - Main exam taking screen
 *
 * Features:
 * - Timer (counts up for practice, counts down for simulation)
 * - Question navigation (< >)
 * - Answer selection
 * - Progress tracking
 * - Submit exam with batch API
 */
export const ExamScreen: React.FC = () => {
  const navigation = useNavigation();
  const route = useRoute();
  const { getToken } = useAuth();
  const { examId } = (route.params as { examId?: string }) || {};

  const {
    currentExam,
    currentQuestionIndex,
    userAnswers,
    elapsedTime,
    setCurrentQuestionIndex,
    setUserAnswer,
    startQuestion,
    finishQuestion,
    updateElapsedTime,
    getCurrentQuestion,
    getUserAnswer,
    getAnsweredCount,
    resetExam,
    setCurrentExam,
  } = useExamStore();

  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const timerRef = useRef<NodeJS.Timeout | null>(null);
  const questionStartTimeRef = useRef<number>(Date.now());

  // Load exam if examId is provided (continuing from history)
  useEffect(() => {
    if (examId && !currentExam) {
      const loadExam = async () => {
        try {
          setLoading(true);
          const examData = await examApi.getExam(examId, getToken);
          setCurrentExam(examData);

          // Restore previous answers if they exist
          if (examData.previous_answers && Array.isArray(examData.previous_answers)) {
            examData.previous_answers.forEach((prevAnswer: any) => {
              if (prevAnswer.user_answer) {
                setUserAnswer(prevAnswer.question_id, prevAnswer.user_answer);
              }
            });
          }
        } catch (error: any) {
          console.error('Load exam error:', error);
          Alert.alert('שגיאה', error.message || 'שגיאה בטעינת המבחן');
          navigation.goBack();
        } finally {
          setLoading(false);
        }
      };
      loadExam();
    }
  }, [examId]);

  const currentQuestion = getCurrentQuestion();
  const currentAnswer = currentQuestion ? getUserAnswer(currentQuestion.id) : undefined;
  const answeredCount = getAnsweredCount();
  const totalQuestions = currentExam?.total_questions || 0;
  const progressPercentage = totalQuestions > 0 ? ((currentQuestionIndex + 1) / totalQuestions) * 100 : 0;

  // Timer logic
  useEffect(() => {
    if (!currentExam) return;

    // Start timer
    questionStartTimeRef.current = Date.now();

    timerRef.current = setInterval(() => {
      const elapsed = Math.floor((Date.now() - (currentExam?.started_at ? new Date(currentExam.started_at).getTime() : Date.now())) / 1000);
      updateElapsedTime(elapsed);

      // Check time limit for full_simulation
      if (currentExam.exam_type === 'full_simulation' && currentExam.time_limit_minutes) {
        const timeLimit = currentExam.time_limit_minutes * 60;
        if (elapsed >= timeLimit) {
          handleTimeUp();
        }
      }
    }, 1000);

    return () => {
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    };
  }, [currentExam]);

  // Track question time
  useEffect(() => {
    if (currentQuestion) {
      startQuestion(currentQuestion.id);
      questionStartTimeRef.current = Date.now();
    }

    return () => {
      if (currentQuestion) {
        finishQuestion(currentQuestion.id);
      }
    };
  }, [currentQuestionIndex]);

  // Handle time up
  const handleTimeUp = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
    }

    Alert.alert(
      'הזמן תם!',
      'זמן המבחן הסתיים. המבחן יוגש אוטומטית.',
      [
        {
          text: 'אישור',
          onPress: () => handleSubmitExam(),
        },
      ],
      { cancelable: false }
    );
  };

  // Format timer display
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;
    return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  };

  // Get remaining time for simulation
  const getRemainingTime = (): string => {
    if (currentExam?.exam_type !== 'full_simulation' || !currentExam.time_limit_minutes) {
      return formatTime(elapsedTime);
    }

    const timeLimit = currentExam.time_limit_minutes * 60;
    const remaining = Math.max(0, timeLimit - elapsedTime);
    return formatTime(remaining);
  };

  // Handle answer selection
  const handleSelectAnswer = (option: string) => {
    if (!currentQuestion) return;

    setUserAnswer(currentQuestion.id, option);
  };

  // Navigate to question
  const goToQuestion = (index: number) => {
    if (index < 0 || index >= totalQuestions) return;

    // Save time for current question
    if (currentQuestion) {
      finishQuestion(currentQuestion.id);
    }

    setCurrentQuestionIndex(index);
  };

  // Handle submit exam
  const handleSubmitExam = async () => {
    // Check if all questions are answered
    if (answeredCount < totalQuestions) {
      Alert.alert(
        'האם אתה בטוח?',
        `השלמת רק ${answeredCount} מתוך ${totalQuestions} שאלות.\nהאם אתה בטוח שברצונך להגיש?`,
        [
          { text: 'ביטול', style: 'cancel' },
          { text: 'הגש מבחן', onPress: () => submitExam(), style: 'destructive' },
        ]
      );
      return;
    }

    submitExam();
  };

  const submitExam = async () => {
    if (!currentExam) return;

    try {
      setSubmitting(true);

      // Prepare all answers
      const answers = Array.from(userAnswers.values())
        .filter((answer) => answer.user_answer !== null)
        .map((answer) => ({
          question_id: answer.question_id,
          user_answer: answer.user_answer!,
          time_taken_seconds: answer.time_taken_seconds,
        }));

      // Submit batch answers
      await examApi.submitAnswersBatch(currentExam.exam_id, answers, getToken);

      // Submit exam to get results
      const results = await examApi.submitExam(currentExam.exam_id, getToken);

      // Navigate to results screen
      navigation.navigate('ExamResults', {
        examId: currentExam.exam_id,
        results,
      });

      // Reset exam state
      resetExam();
    } catch (error: any) {
      console.error('Submit exam error:', error);
      Alert.alert('שגיאה', error.message || 'שגיאה בהגשת המבחן. נסה שוב.');
    } finally {
      setSubmitting(false);
    }
  };

  // Handle abandon exam
  const handleAbandonExam = () => {
    Alert.alert(
      'יציאה מהמבחן',
      'האם אתה בטוח שברצונך לצאת? התקדמותך לא תישמר.',
      [
        { text: 'ביטול', style: 'cancel' },
        {
          text: 'צא',
          style: 'destructive',
          onPress: async () => {
            if (currentExam) {
              try {
                await examApi.abandonExam(currentExam.exam_id, getToken);
              } catch (error) {
                console.error('Abandon exam error:', error);
              }
            }
            resetExam();
            navigation.goBack();
          },
        },
      ]
    );
  };

  if (!currentExam || !currentQuestion) {
    return (
      <SafeAreaView style={{ flex: 1, backgroundColor: Colors.white }}>
        <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center' }}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={{ marginTop: 16 }}>טוען מבחן...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Answer options
  const options = [
    { key: 'A', text: currentQuestion.option_a },
    { key: 'B', text: currentQuestion.option_b },
    { key: 'C', text: currentQuestion.option_c },
    { key: 'D', text: currentQuestion.option_d },
    { key: 'E', text: currentQuestion.option_e },
  ];

  return (
    <SafeAreaView style={styles.container}>
      {/* Blue Background Container */}
      <View style={styles.blueBackground}>
        {/* Top Navigation Row */}
        <View style={styles.topNav}>
          {/* Exit button (left side) */}
          <Pressable onPress={handleAbandonExam} style={styles.exitButton}>
            <Text style={styles.exitText}>×</Text>
          </Pressable>

          {/* Question progress (center) */}
          <Text style={styles.progressText}>
            {currentQuestionIndex + 1} מתוך {totalQuestions}
          </Text>

          {/* Timer and Submit button (right side) */}
          <View style={styles.timerContainer}>
            <Pressable onPress={handleSubmitExam} disabled={submitting}>
              <Text style={styles.submitEarlyText}>סיים מבחן</Text>
            </Pressable>
            <Text style={styles.timerText}>
              {getRemainingTime()}
            </Text>
          </View>
        </View>

        {/* Progress bar - Simplified */}
        <View style={{ height: 4, backgroundColor: 'rgba(255,255,255,0.3)', borderRadius: 2, marginBottom: 20 }}>
          <View style={{ height: '100%', width: `${progressPercentage}%`, backgroundColor: Colors.white, borderRadius: 2 }} />
        </View>

        {/* White Card Container */}
        <View style={styles.card}>
          <ScrollView
            showsVerticalScrollIndicator={false}
            contentContainerStyle={styles.scrollContent}
          >
            {/* Question text */}
            <Text style={styles.questionText}>
              {currentQuestion?.question_text || 'No question text'}
            </Text>

            {/* Answer options */}
            <View style={styles.optionsContainer}>
              {options.map((option) => {
                const isSelected = currentAnswer?.user_answer === option.key;

                return (
                  <Pressable
                    key={option.key}
                    onPress={() => handleSelectAnswer(option.key)}
                    style={[
                      styles.optionButton,
                      isSelected && styles.optionButtonSelected
                    ]}
                  >
                    {/* Radio circle - first child = RIGHT side in RTL */}
                    <View style={[
                      styles.radioOuter,
                      isSelected && styles.radioOuterSelected
                    ]}>
                      {isSelected && (
                        <View style={styles.radioInner} />
                      )}
                    </View>

                    {/* Answer text - second child = LEFT side in RTL */}
                    <Text style={styles.optionText}>
                      {option.text}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </ScrollView>

          {/* Navigation buttons inside card */}
          <View style={styles.navContainer}>
            {/* Submit button (only on last question) */}
            {currentQuestionIndex === totalQuestions - 1 ? (
              <Pressable
                onPress={handleSubmitExam}
                disabled={submitting}
                style={[styles.submitButton, submitting && styles.submitButtonDisabled]}
              >
                {submitting ? (
                  <ActivityIndicator color={Colors.white} />
                ) : (
                  <Text style={styles.submitButtonText}>
                    הגש מבחן
                  </Text>
                )}
              </Pressable>
            ) : null}

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

      {/* Loading Overlay */}
      {submitting && (
        <View style={styles.loadingOverlay}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>טוען תוצאות...</Text>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.primary,
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
    marginBottom: 12,
  },
  exitButton: {
    padding: 8,
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
  timerContainer: {
    alignItems: 'flex-end',
  },
  submitEarlyText: {
    color: Colors.white,
    fontSize: 12,
    fontWeight: '600',
    marginBottom: 4,
  },
  timerText: {
    color: Colors.white,
    fontSize: 14,
    fontWeight: '500',
  },
  card: {
    flex: 1,
    backgroundColor: '#FFFFFF',
    borderRadius: 20,
    padding: 24,
    marginBottom: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 5,
  },
  scrollContent: {
    flexGrow: 1,
  },
  questionText: {
    fontSize: 18,
    fontWeight: '700',
    textAlign: 'right',
    color: '#1F2937',
    marginBottom: 24,
    lineHeight: 28,
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
  optionButtonSelected: {
    backgroundColor: '#E0F2FE',
    borderColor: Colors.primary,
  },
  optionText: {
    fontSize: 16,
    textAlign: 'right',
    flex: 1,
    color: '#374151',
    lineHeight: 24,
    marginRight: 8,
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
  radioOuterSelected: {
    borderColor: Colors.primary,
  },
  radioInner: {
    width: 10,
    height: 10,
    borderRadius: 5,
    backgroundColor: Colors.primary,
  },
  navContainer: {
    marginTop: 'auto',
    paddingTop: 24,
  },
  submitButton: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    padding: 18,
    alignItems: 'center',
    marginBottom: 16,
  },
  submitButtonDisabled: {
    backgroundColor: '#9CA3AF',
  },
  submitButtonText: {
    color: Colors.white,
    fontSize: 16,
    fontWeight: '700',
  },
  navArrows: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  navButton: {
    width: 64,
    height: 64,
    borderRadius: 16,
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
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.7)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  loadingContainer: {
    backgroundColor: Colors.white,
    padding: 32,
    borderRadius: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  loadingText: {
    marginTop: 16,
    fontSize: 18,
    fontWeight: '600',
    color: Colors.primary,
    textAlign: 'center',
  },
});

import React, { useEffect } from 'react';
import {
  StyleSheet,
  SafeAreaView,
  StatusBar,
  ScrollView,
  ActivityIndicator,
  Alert,
  Pressable,
  View,
  Text,
} from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';
import { useMistakeStore } from '../stores/mistakeStore';
import { mistakeApi } from '../utils/mistakeApi';
import { usePracticeStore } from '../stores/practiceStore';

/**
 * מסך בחירת נושא לחזרה על טעויות
 * Mistake Review Selection Screen
 */
export const MistakeReviewSelectionScreen: React.FC = () => {
  const navigation = useNavigation();
  const { getToken } = useAuth();

  const {
    topics,
    analytics,
    loadingTopics,
    loadingAnalytics,
    setTopics,
    setAnalytics,
    setLoadingTopics,
    setLoadingAnalytics,
  } = useMistakeStore();

  const { startSession } = usePracticeStore();
  const [creatingSession, setCreatingSession] = React.useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoadingTopics(true);
      setLoadingAnalytics(true);

      const [topicsData, analyticsData] = await Promise.all([
        mistakeApi.getMistakeTopics(getToken),
        mistakeApi.getAnalytics(getToken),
      ]);

      setTopics(topicsData.topics);
      setAnalytics(analyticsData);
    } catch (error: any) {
      console.error('Failed to load mistake data:', error);
      Alert.alert('שגיאה', error.message || 'שגיאה בטעינת נתונים');
    } finally {
      setLoadingTopics(false);
      setLoadingAnalytics(false);
    }
  };

  const handleStartReview = async (topicName: string | null) => {
    if (creatingSession) return; // Prevent double-clicks

    try {
      setCreatingSession(true);

      // Determine question count
      const questionCount = topicName ? 10 : 25; // 10 for specific topic, 25 for all

      // Create review session via mistakeApi
      const session = await mistakeApi.createMistakeReviewSession(topicName, questionCount, getToken);

      // Start practice session with review_mistakes type
      startSession({
        exam_id: session.exam_id,
        exam_type: 'review_mistakes',
        total_questions: session.questions.length,
        questions: session.questions,
        started_at: new Date().toISOString(),
        time_limit_minutes: null,
      });

      // Navigate to practice question screen (with immediate feedback)
      navigation.navigate('PracticeQuestion' as never);
    } catch (error: any) {
      console.error('Failed to create review session:', error);
      Alert.alert('שגיאה', error.message || 'שגיאה ביצירת תרגול');
    } finally {
      setCreatingSession(false);
    }
  };

  if (loadingTopics || loadingAnalytics) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>טוען נתונים...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // No mistakes found
  if (!topics || topics.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyEmoji}>🎉</Text>
          <Text style={styles.emptyTitle}>אין טעויות!</Text>
          <Text style={styles.emptyText}>
            עדיין לא נמצאו טעויות בתרגולים שלך.{'\n'}
            המשך לתרגל כדי לזהות נקודות חולשה.
          </Text>
          <Pressable
            style={styles.backButton}
            onPress={() => navigation.goBack()}
          >
            <Text style={styles.backButtonText}>חזרה לדף הבית</Text>
          </Pressable>
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
          <Pressable onPress={() => navigation.goBack()} style={styles.headerBackButton}>
            <Text style={styles.headerBackIcon}>→</Text>
          </Pressable>
          <Text style={styles.headerTitle}>חזרה על טעויות</Text>
        </View>

        {/* Analytics Card */}
        {analytics && (
          <View style={styles.analyticsCard}>
            <Text style={styles.analyticsTitle}>📊 סטטיסטיקה</Text>

            <View style={styles.analyticsGrid}>
              <View style={styles.analyticsStat}>
                <Text style={styles.analyticsValue}>{analytics.total_mistakes}</Text>
                <Text style={styles.analyticsLabel}>סה"כ טעויות</Text>
              </View>
              <View style={styles.analyticsStat}>
                <Text style={[styles.analyticsValue, { color: Colors.error }]}>
                  {analytics.unresolved}
                </Text>
                <Text style={styles.analyticsLabel}>לא פתורות</Text>
              </View>
              <View style={styles.analyticsStat}>
                <Text style={[styles.analyticsValue, { color: Colors.success }]}>
                  {analytics.resolved}
                </Text>
                <Text style={styles.analyticsLabel}>פתורות</Text>
              </View>
              <View style={styles.analyticsStat}>
                <Text style={[styles.analyticsValue, { color: Colors.accent }]}>
                  {analytics.improvement_rate.toFixed(0)}%
                </Text>
                <Text style={styles.analyticsLabel}>שיפור</Text>
              </View>
            </View>

            {/* Weekly Progress */}
            <View style={styles.weeklyProgress}>
              <Text style={styles.weeklyTitle}>📈 השבוע</Text>
              <Text style={styles.weeklyText}>
                נסקרו {analytics.progress_this_week.questions_reviewed} שאלות
              </Text>
              <Text style={styles.weeklyText}>
                נפתרו {analytics.progress_this_week.newly_resolved} טעויות חדשות
              </Text>
            </View>
          </View>
        )}

        {/* Practice All Button */}
        <Pressable
          style={styles.practiceAllButton}
          onPress={() => handleStartReview(null)}
        >
          <Text style={styles.practiceAllText}>🔥 תרגל את כל הטעויות</Text>
        </Pressable>

        {/* Topics Section */}
        <Text style={styles.sectionTitle}>נושאים לתרגול</Text>
        <Text style={styles.sectionSubtitle}>בחר נושא ספציפי או תרגל הכל</Text>

        {/* Topic Cards */}
        <View style={styles.topicsContainer}>
          {topics.map((topic) => (
            <Pressable
              key={topic.name}
              style={[
                styles.topicCard,
                topic.priority === 'high' && styles.topicCardHigh,
                topic.priority === 'medium' && styles.topicCardMedium,
                topic.priority === 'low' && styles.topicCardLow,
              ]}
              onPress={() => handleStartReview(topic.name)}
            >
              {/* Priority Badge */}
              <View style={styles.topicBadge}>
                <Text style={styles.topicEmoji}>{topic.priority_emoji}</Text>
              </View>

              {/* Topic Name */}
              <Text style={styles.topicName}>{topic.name}</Text>

              {/* Stats */}
              <View style={styles.topicStats}>
                <View style={styles.topicStat}>
                  <Text style={styles.topicStatValue}>{topic.mistake_count}</Text>
                  <Text style={styles.topicStatLabel}>טעויות</Text>
                </View>
                <View style={styles.topicStatDivider} />
                <View style={styles.topicStat}>
                  <Text style={styles.topicStatValue}>
                    {topic.accuracy_percentage.toFixed(0)}%
                  </Text>
                  <Text style={styles.topicStatLabel}>דיוק</Text>
                </View>
              </View>

              {/* Practice Button */}
              <View style={styles.topicButton}>
                <Text style={styles.topicButtonText}>תרגל נושא זה</Text>
              </View>
            </Pressable>
          ))}
        </View>
      </ScrollView>

      {/* Loading Overlay */}
      {creatingSession && (
        <View style={styles.loadingOverlay}>
          <View style={styles.loadingBox}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingOverlayText}>מכין תרגול...</Text>
          </View>
        </View>
      )}
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: Colors.gray[600],
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 40,
  },
  emptyEmoji: {
    fontSize: 80,
    marginBottom: 24,
  },
  emptyTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: Colors.primary,
    marginBottom: 16,
    textAlign: 'center',
  },
  emptyText: {
    fontSize: 16,
    color: Colors.gray[600],
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 32,
  },
  backButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
  },
  backButtonText: {
    color: Colors.white,
    fontSize: 18,
    fontWeight: 'bold',
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
    marginBottom: 24,
    gap: 12,
  },
  headerBackButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerBackIcon: {
    fontSize: 24,
    color: Colors.primary,
  },
  headerTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.primary,
    flex: 1,
    textAlign: 'right',
  },
  analyticsCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 20,
    marginBottom: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  analyticsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.primary,
    marginBottom: 16,
    textAlign: 'right',
  },
  analyticsGrid: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    marginBottom: 20,
  },
  analyticsStat: {
    alignItems: 'center',
    flex: 1,
  },
  analyticsValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.primary,
  },
  analyticsLabel: {
    fontSize: 12,
    color: Colors.gray[600],
    marginTop: 4,
  },
  weeklyProgress: {
    backgroundColor: Colors.primaryLight,
    borderRadius: 12,
    padding: 16,
  },
  weeklyTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.primary,
    marginBottom: 8,
    textAlign: 'right',
  },
  weeklyText: {
    fontSize: 14,
    color: Colors.gray[700],
    textAlign: 'right',
    marginTop: 4,
  },
  practiceAllButton: {
    backgroundColor: Colors.accent,
    borderRadius: 16,
    padding: 20,
    alignItems: 'center',
    marginBottom: 32,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
  },
  practiceAllText: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.white,
  },
  sectionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.primary,
    marginBottom: 8,
    textAlign: 'right',
  },
  sectionSubtitle: {
    fontSize: 14,
    color: Colors.gray[600],
    marginBottom: 16,
    textAlign: 'right',
  },
  topicsContainer: {
    gap: 16,
  },
  topicCard: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 4,
    borderWidth: 2,
    borderColor: 'transparent',
  },
  topicCardHigh: {
    borderColor: Colors.error,
  },
  topicCardMedium: {
    borderColor: '#FFC107',
  },
  topicCardLow: {
    borderColor: Colors.success,
  },
  topicBadge: {
    alignSelf: 'flex-end',
    marginBottom: 12,
  },
  topicEmoji: {
    fontSize: 32,
  },
  topicName: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.primary,
    marginBottom: 16,
    textAlign: 'right',
  },
  topicStats: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    gap: 24,
  },
  topicStat: {
    alignItems: 'center',
  },
  topicStatValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.primary,
  },
  topicStatLabel: {
    fontSize: 12,
    color: Colors.gray[600],
    marginTop: 4,
  },
  topicStatDivider: {
    width: 1,
    height: 30,
    backgroundColor: Colors.gray[300],
  },
  topicButton: {
    backgroundColor: Colors.primaryLight,
    borderRadius: 12,
    padding: 14,
    alignItems: 'center',
  },
  topicButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.primary,
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingBox: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 12,
    elevation: 8,
  },
  loadingOverlayText: {
    marginTop: 16,
    fontSize: 18,
    fontWeight: '600',
    color: Colors.primary,
  },
});

import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  StatusBar,
  View,
  Text,
  Pressable,
  ScrollView,
  ActivityIndicator,
  Dimensions,
  Alert
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';
import {
  ProgressOverview,
  ExamHistoryItem,
  TopicPerformance,
  PerformanceTrends,
  MistakeInsights,
  MasteryLevel
} from '../types/progress';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * מסך מעקב התקדמות
 * Progress Tracking Screen
 */
export const ProgressScreen: React.FC = () => {
  const navigation = useNavigation();
  const { getToken } = useAuth();

  const [loading, setLoading] = useState(true);
  const [overview, setOverview] = useState<ProgressOverview | null>(null);
  const [examHistory, setExamHistory] = useState<ExamHistoryItem[]>([]);
  const [topicPerformance, setTopicPerformance] = useState<TopicPerformance[]>([]);
  const [trends, setTrends] = useState<PerformanceTrends | null>(null);
  const [mistakes, setMistakes] = useState<MistakeInsights | null>(null);
  const [mastery, setMastery] = useState<MasteryLevel | null>(null);

  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    console.log('🟢 ProgressScreen mounted');
    loadProgressData();
  }, []);

  const loadProgressData = async () => {
    console.log('🟢 Starting loadProgressData');
    try {
      setLoading(true);
      setError(null);

      console.log('🔐 Getting auth token...');
      const token = await getToken();

      if (!token) {
        console.log('❌ No auth token found');
        setError('לא נמצא טוקן אימות. נא להתחבר מחדש.');
        Alert.alert('שגיאה', 'לא נמצא טוקן אימות. נא להתחבר מחדש.');
        return;
      }

      console.log('✅ Token obtained (length:', token.length, ')');
      console.log('🔑 Token preview:', token.substring(0, 20) + '...');

      const headers = {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      };

      console.log('📡 Fetching progress data from:', API_URL);
      console.log('📡 Headers:', {
        Authorization: 'Bearer ' + token.substring(0, 10) + '...',
        'Content-Type': 'application/json'
      });

      // Fetch all progress data in parallel
      console.log('🚀 Making parallel API requests...');
      const [overviewRes, historyRes, topicsRes, trendsRes, mistakesRes, masteryRes] = await Promise.all([
        fetch(`${API_URL}/api/progress/overview`, { headers }),
        fetch(`${API_URL}/api/progress/exam-history?limit=10`, { headers }),
        fetch(`${API_URL}/api/progress/topics`, { headers }),
        fetch(`${API_URL}/api/progress/trends`, { headers }),
        fetch(`${API_URL}/api/progress/mistakes`, { headers }),
        fetch(`${API_URL}/api/progress/mastery`, { headers }),
      ]);

      console.log('📊 Response status codes:', {
        overview: overviewRes.status,
        history: historyRes.status,
        topics: topicsRes.status,
        trends: trendsRes.status,
        mistakes: mistakesRes.status,
        mastery: masteryRes.status,
      });

      if (overviewRes.ok) {
        const data = await overviewRes.json();
        console.log('✅ Overview data:', data);
        setOverview(data);
      } else {
        const errorText = await overviewRes.text();
        console.log('❌ Overview error:', overviewRes.status, errorText);
      }

      if (historyRes.ok) {
        const data = await historyRes.json();
        console.log('✅ History data (count:', data.length, ')');
        setExamHistory(data);
      } else {
        const errorText = await historyRes.text();
        console.log('❌ History error:', historyRes.status, errorText);
      }

      if (topicsRes.ok) {
        const data = await topicsRes.json();
        console.log('✅ Topics data (count:', data.length, ')');
        setTopicPerformance(data);
      } else {
        const errorText = await topicsRes.text();
        console.log('❌ Topics error:', topicsRes.status, errorText);
      }

      if (trendsRes.ok) {
        const data = await trendsRes.json();
        console.log('✅ Trends data:', data);
        setTrends(data);
      } else {
        const errorText = await trendsRes.text();
        console.log('❌ Trends error:', trendsRes.status, errorText);
      }

      if (mistakesRes.ok) {
        const data = await mistakesRes.json();
        console.log('✅ Mistakes data:', data);
        setMistakes(data);
      } else {
        const errorText = await mistakesRes.text();
        console.log('❌ Mistakes error:', mistakesRes.status, errorText);
      }

      if (masteryRes.ok) {
        const data = await masteryRes.json();
        console.log('✅ Mastery data:', data);
        setMastery(data);
      } else {
        const errorText = await masteryRes.text();
        console.log('❌ Mastery error:', masteryRes.status, errorText);
      }

      console.log('✅ Progress data loaded successfully');

    } catch (error: any) {
      console.error('❌ Error loading progress data:', error);
      console.error('❌ Error message:', error.message);
      console.error('❌ Error stack:', error.stack);

      const errorMessage = error.message || 'שגיאה בטעינת נתוני התקדמות';
      setError(errorMessage);
      Alert.alert('שגיאה', errorMessage + '\nנסה שוב מאוחר יותר');
    } finally {
      setLoading(false);
      console.log('🏁 loadProgressData completed');
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return date.toLocaleDateString('he-IL', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
      });
    } catch {
      return dateString;
    }
  };

  const formatExamType = (type: string) => {
    switch (type) {
      case 'practice':
        return 'תרגול';
      case 'full_simulation':
        return 'סימולציה מלאה';
      case 'review_mistakes':
        return 'חזרה על טעויות';
      default:
        return type;
    }
  };

  const getStrengthIcon = (level: string) => {
    switch (level) {
      case 'strong':
        return '💪';
      case 'weak':
        return '📚';
      default:
        return '📊';
    }
  };

  const getStrengthColor = (level: string) => {
    switch (level) {
      case 'strong':
        return Colors.success;
      case 'weak':
        return Colors.error;
      default:
        return Colors.warning;
    }
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <StatusBar barStyle="dark-content" />
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>טוען נתונים...</Text>
        </View>
      </SafeAreaView>
    );
  }

  // Calculate top 3 strongest and weakest topics
  const strongTopics = topicPerformance
    .filter(t => t.strength_level === 'strong')
    .slice(0, 3);

  const weakTopics = topicPerformance
    .filter(t => t.strength_level === 'weak')
    .slice(0, 3);

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
            <Text style={styles.backIcon}>→</Text>
          </Pressable>
          <Text style={styles.headerTitle}>התקדמות שלי</Text>
          <View style={styles.placeholder} />
        </View>

        {/* Exam Countdown Card */}
        {overview && overview.exam_date && (
          <View style={styles.examCountdownCard}>
            <View style={styles.examCountdownContent}>
              <Text style={styles.examCountdownIcon}>📅</Text>
              <View style={styles.examCountdownInfo}>
                <Text style={styles.examCountdownTitle}>מועד המבחן שלך</Text>
                <Text style={styles.examCountdownDate}>
                  {formatDate(overview.exam_date)}
                </Text>
              </View>
            </View>

            {overview.days_until_exam !== null && (
              <View style={styles.examCountdownDays}>
                <Text style={styles.examCountdownDaysNumber}>
                  {overview.days_until_exam}
                </Text>
                <Text style={styles.examCountdownDaysLabel}>
                  {overview.days_until_exam === 1 ? 'יום נותר' : 'ימים נותרים'}
                </Text>

                {/* Motivational message based on days remaining */}
                {overview.days_until_exam <= 7 && overview.days_until_exam > 0 && (
                  <Text style={styles.examCountdownMotivation}>
                    🔥 השבוע האחרון! זמן לסיכום
                  </Text>
                )}
                {overview.days_until_exam > 7 && overview.days_until_exam <= 30 && (
                  <Text style={styles.examCountdownMotivation}>
                    💪 חודש אחרון - תתמקד בנקודות החולשה
                  </Text>
                )}
                {overview.days_until_exam > 30 && (
                  <Text style={styles.examCountdownMotivation}>
                    📚 יש לך זמן - לימוד יציב ועקבי
                  </Text>
                )}
                {overview.days_until_exam === 0 && (
                  <Text style={styles.examCountdownMotivation}>
                    🎯 היום הגדול הגיע! בהצלחה!
                  </Text>
                )}
                {overview.days_until_exam < 0 && (
                  <Text style={styles.examCountdownMotivation}>
                    המבחן עבר - המשך תרגול!
                  </Text>
                )}
              </View>
            )}
          </View>
        )}

        {/* Overview Stats Cards */}
        {overview && (
          <View style={styles.statsGrid}>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>{overview.total_exams}</Text>
              <Text style={styles.statLabel}>מבחנים שהשלמתי</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>{overview.total_questions_answered}</Text>
              <Text style={styles.statLabel}>שאלות שעניתי</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>
                {overview.average_score ? `${overview.average_score.toFixed(1)}%` : '-'}
              </Text>
              <Text style={styles.statLabel}>ציון ממוצע</Text>
            </View>
            <View style={styles.statCard}>
              <Text style={styles.statValue}>
                {overview.days_until_exam !== null ? overview.days_until_exam : '-'}
              </Text>
              <Text style={styles.statLabel}>ימים למבחן</Text>
            </View>
          </View>
        )}

        {/* Study Streak */}
        {overview && overview.study_streak_days > 0 && (
          <View style={styles.streakCard}>
            <Text style={styles.streakIcon}>🔥</Text>
            <Text style={styles.streakText}>
              רצף לימוד: {overview.study_streak_days} ימים
            </Text>
          </View>
        )}

        {/* Exam History */}
        {examHistory.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>היסטוריית מבחנים</Text>
            {examHistory.slice(0, 5).map((exam) => (
              <View key={exam.id} style={styles.examCard}>
                <View style={styles.examHeader}>
                  <View style={styles.examInfo}>
                    <Text style={styles.examIcon}>
                      {exam.passed ? '✅' : '❌'}
                    </Text>
                    <View>
                      <Text style={styles.examDate}>{formatDate(exam.date)}</Text>
                      <Text style={styles.examType}>{formatExamType(exam.exam_type)}</Text>
                    </View>
                  </View>
                  <View style={styles.examScore}>
                    <Text style={[
                      styles.scoreText,
                      { color: exam.passed ? Colors.success : Colors.error }
                    ]}>
                      {exam.score ? `${exam.score.toFixed(1)}%` : '-'}
                    </Text>
                    <Text style={styles.examStatus}>
                      {exam.passed ? 'עבר' : 'נכשל'}
                    </Text>
                  </View>
                </View>
                <View style={styles.examDetails}>
                  <Text style={styles.examDetailText}>
                    ✓ {exam.correct_answers}/{exam.total_questions}
                  </Text>
                  <Text style={styles.examDetailText}>
                    📝 {exam.total_questions} שאלות
                  </Text>
                  <Text style={styles.examDetailText}>
                    ⏱ {exam.time_taken_minutes ? `${exam.time_taken_minutes} דקות` : '-'}
                  </Text>
                </View>
              </View>
            ))}
          </View>
        )}

        {/* Strengths & Weaknesses */}
        {(strongTopics.length > 0 || weakTopics.length > 0) && (
          <View style={styles.strengthsWeaknessesContainer}>
            {/* Strengths */}
            {strongTopics.length > 0 && (
              <View style={styles.halfSection}>
                <Text style={styles.sectionTitle}>נקודות חוזק 💪</Text>
                {strongTopics.map((topic, index) => (
                  <View key={index} style={styles.topicItem}>
                    <Text style={styles.topicName} numberOfLines={1}>
                      {topic.topic}
                    </Text>
                    <Text style={[styles.topicAccuracy, { color: Colors.success }]}>
                      {topic.accuracy ? `${topic.accuracy.toFixed(0)}%` : '-'}
                    </Text>
                  </View>
                ))}
              </View>
            )}

            {/* Weaknesses */}
            {weakTopics.length > 0 && (
              <View style={styles.halfSection}>
                <Text style={styles.sectionTitle}>נקודות תורפה 📚</Text>
                {weakTopics.map((topic, index) => (
                  <View key={index} style={styles.topicItem}>
                    <Text style={styles.topicName} numberOfLines={1}>
                      {topic.topic}
                    </Text>
                    <Text style={[styles.topicAccuracy, { color: Colors.error }]}>
                      {topic.accuracy ? `${topic.accuracy.toFixed(0)}%` : '-'}
                    </Text>
                  </View>
                ))}
              </View>
            )}
          </View>
        )}

        {/* Topic Performance */}
        {topicPerformance.length > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>ביצועים לפי נושא</Text>
            {topicPerformance.slice(0, 8).map((topic, index) => {
              const accuracy = topic.accuracy || 0;
              const barWidth = `${Math.min(accuracy, 100)}%`;

              return (
                <View key={index} style={styles.topicPerformanceItem}>
                  <View style={styles.topicPerformanceHeader}>
                    <Text style={styles.topicPerformanceName} numberOfLines={1}>
                      {topic.topic}
                    </Text>
                    <Text style={styles.topicPerformanceIcon}>
                      {getStrengthIcon(topic.strength_level)}
                    </Text>
                  </View>
                  <View style={styles.progressBarContainer}>
                    <View
                      style={[
                        styles.progressBar,
                        {
                          width: barWidth,
                          backgroundColor: getStrengthColor(topic.strength_level)
                        }
                      ]}
                    />
                  </View>
                  <View style={styles.topicPerformanceStats}>
                    <Text style={styles.topicPerformanceStatText}>
                      {accuracy.toFixed(0)}%
                    </Text>
                    <Text style={styles.topicPerformanceStatText}>
                      {topic.total_questions} שאלות
                    </Text>
                  </View>
                </View>
              );
            })}
          </View>
        )}

        {/* Mastery Level */}
        {mastery && (mastery.mastered > 0 || mastery.practicing > 0 || mastery.learning > 0) && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>הבנה ורמת שליטה</Text>
            <View style={styles.masteryCard}>
              {mastery.mastered > 0 && (
                <View style={styles.masteryItem}>
                  <View style={styles.masteryTextContainer}>
                    <Text style={styles.masteryLabel}>שאלות שהשתלטתי עליהן</Text>
                    <Text style={styles.masteryValue}>{mastery.mastered}</Text>
                  </View>
                  <Text style={styles.masteryIcon}>🏆</Text>
                </View>
              )}
              {mastery.practicing > 0 && (
                <View style={styles.masteryItem}>
                  <View style={styles.masteryTextContainer}>
                    <Text style={styles.masteryLabel}>שאלות בתרגול</Text>
                    <Text style={styles.masteryValue}>{mastery.practicing}</Text>
                  </View>
                  <Text style={styles.masteryIcon}>📝</Text>
                </View>
              )}
              {mastery.learning > 0 && (
                <View style={styles.masteryItem}>
                  <View style={styles.masteryTextContainer}>
                    <Text style={styles.masteryLabel}>שאלות ללמידה</Text>
                    <Text style={styles.masteryValue}>{mastery.learning}</Text>
                  </View>
                  <Text style={styles.masteryIcon}>📖</Text>
                </View>
              )}
            </View>
          </View>
        )}

        {/* Mistake Insights */}
        {mistakes && mistakes.total_mistakes > 0 && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>ניתוח טעויות</Text>
            <View style={styles.mistakesCard}>
              <View style={styles.mistakesSummary}>
                <View style={styles.mistakeStat}>
                  <Text style={styles.mistakeStatValue}>{mistakes.total_mistakes}</Text>
                  <Text style={styles.mistakeStatLabel}>סך כל טעויות</Text>
                </View>
                <View style={styles.mistakeStat}>
                  <Text style={[styles.mistakeStatValue, { color: Colors.success }]}>
                    {mistakes.resolved_mistakes}
                  </Text>
                  <Text style={styles.mistakeStatLabel}>תוקנו</Text>
                </View>
                <View style={styles.mistakeStat}>
                  <Text style={[styles.mistakeStatValue, { color: Colors.warning }]}>
                    {mistakes.unresolved_mistakes}
                  </Text>
                  <Text style={styles.mistakeStatLabel}>דורשות חזרה</Text>
                </View>
              </View>

              {mistakes.top_mistake_topics.length > 0 && (
                <View style={styles.topMistakes}>
                  <Text style={styles.topMistakesTitle}>נושאים עם הכי הרבה טעויות:</Text>
                  {mistakes.top_mistake_topics.slice(0, 3).map((topic, index) => (
                    <View key={index} style={styles.topMistakeItem}>
                      <Text style={styles.topMistakeCount}>{topic.count} טעויות</Text>
                      <Text style={styles.topMistakeTopic} numberOfLines={1}>
                        {topic.topic}
                      </Text>
                      <Text style={styles.topMistakeRank}>.{index + 1}</Text>
                    </View>
                  ))}
                </View>
              )}
            </View>
          </View>
        )}

        {/* Best Day of Week */}
        {trends && trends.best_day_of_week && (
          <View style={styles.section}>
            <Text style={styles.sectionTitle}>פעילות שבועית</Text>
            <View style={styles.bestDayCard}>
              <Text style={styles.bestDayLabel}>היום הכי טוב שלך:</Text>
              <Text style={styles.bestDayValue}>{trends.best_day_of_week}</Text>
              {trends.best_day_score && (
                <Text style={styles.bestDayScore}>
                  ציון ממוצע: {trends.best_day_score.toFixed(1)}%
                </Text>
              )}
            </View>
          </View>
        )}

        {/* Bottom Padding */}
        <View style={{ height: 40 }} />
      </ScrollView>
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
    color: Colors.textPrimary,
    fontWeight: '600',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 20,
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: Colors.background,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  backButton: {
    padding: 8,
  },
  backIcon: {
    fontSize: 24,
    color: Colors.primary,
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  placeholder: {
    width: 40,
  },
  examCountdownCard: {
    backgroundColor: Colors.primary,
    marginHorizontal: 16,
    marginTop: 16,
    marginBottom: 8,
    borderRadius: 16,
    padding: 20,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 6,
  },
  examCountdownContent: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    marginBottom: 16,
  },
  examCountdownIcon: {
    fontSize: 40,
    marginLeft: 16,
  },
  examCountdownInfo: {
    flex: 1,
  },
  examCountdownTitle: {
    fontSize: 16,
    color: '#FFFFFF',
    marginBottom: 4,
    textAlign: 'right',
    fontWeight: '600',
  },
  examCountdownDate: {
    fontSize: 22,
    color: '#FFFFFF',
    fontWeight: 'bold',
    textAlign: 'right',
  },
  examCountdownDays: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderRadius: 12,
    padding: 16,
    alignItems: 'center',
  },
  examCountdownDaysNumber: {
    fontSize: 48,
    color: '#FFFFFF',
    fontWeight: 'bold',
    textAlign: 'center',
  },
  examCountdownDaysLabel: {
    fontSize: 18,
    color: '#FFFFFF',
    marginTop: 4,
    textAlign: 'center',
    fontWeight: '600',
  },
  examCountdownMotivation: {
    fontSize: 14,
    color: '#FFFFFF',
    marginTop: 12,
    textAlign: 'center',
    fontWeight: '500',
    opacity: 0.95,
  },
  statsGrid: {
    flexDirection: 'row-reverse',
    flexWrap: 'wrap',
    padding: 16,
    gap: 12,
  },
  statCard: {
    width: '48%',
    backgroundColor: Colors.secondaryLight,
    borderRadius: 12,
    padding: 16,
    alignItems: 'flex-end',
  },
  statValue: {
    fontSize: 32,
    fontWeight: 'bold',
    color: Colors.primary,
    marginBottom: 8,
    textAlign: 'right',
  },
  statLabel: {
    fontSize: 14,
    color: Colors.textPrimary,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  streakCard: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.accent,
    marginHorizontal: 16,
    marginBottom: 16,
    padding: 16,
    borderRadius: 12,
  },
  streakIcon: {
    fontSize: 24,
    marginLeft: 12,
  },
  streakText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    textAlign: 'center',
    writingDirection: 'rtl',
  },
  section: {
    paddingHorizontal: 16,
    marginBottom: 24,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    marginBottom: 12,
    textAlign: 'center',
    writingDirection: 'rtl',
    width: '100%',
  },
  examCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  examHeader: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 12,
  },
  examInfo: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    gap: 12,
  },
  examIcon: {
    fontSize: 24,
  },
  examDate: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  examType: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginTop: 2,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  examScore: {
    alignItems: 'flex-end',
  },
  scoreText: {
    fontSize: 24,
    fontWeight: 'bold',
    textAlign: 'right',
  },
  examStatus: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginTop: 2,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  examDetails: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#E0E0E0',
  },
  examDetailText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  strengthsWeaknessesContainer: {
    flexDirection: 'row-reverse',
    paddingHorizontal: 16,
    marginBottom: 24,
    gap: 12,
  },
  halfSection: {
    flex: 1,
  },
  topicItem: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
    padding: 12,
    borderRadius: 8,
    marginBottom: 8,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  topicName: {
    flex: 1,
    fontSize: 14,
    color: Colors.textPrimary,
    marginLeft: 8,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  topicAccuracy: {
    fontSize: 16,
    fontWeight: 'bold',
    textAlign: 'right',
  },
  topicPerformanceItem: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  topicPerformanceHeader: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8,
  },
  topicPerformanceName: {
    flex: 1,
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginLeft: 8,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  topicPerformanceIcon: {
    fontSize: 20,
  },
  progressBarContainer: {
    height: 8,
    backgroundColor: '#E0E0E0',
    borderRadius: 4,
    overflow: 'hidden',
    marginBottom: 8,
  },
  progressBar: {
    height: '100%',
    borderRadius: 4,
  },
  topicPerformanceStats: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
  },
  topicPerformanceStatText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  masteryCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  masteryItem: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingVertical: 12,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  masteryIcon: {
    fontSize: 24,
  },
  masteryTextContainer: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    gap: 4,
    flex: 1,
  },
  masteryLabel: {
    fontSize: 16,
    color: Colors.textPrimary,
    textAlign: 'right',
    writingDirection: 'rtl',
    flex: 1,
  },
  masteryValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.primary,
    textAlign: 'right',
  },
  mistakesCard: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: '#E0E0E0',
  },
  mistakesSummary: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-around',
    paddingBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: '#E0E0E0',
  },
  mistakeStat: {
    alignItems: 'center',
  },
  mistakeStatValue: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    textAlign: 'right',
  },
  mistakeStatLabel: {
    fontSize: 12,
    color: Colors.textSecondary,
    marginTop: 4,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  topMistakes: {
    marginTop: 16,
  },
  topMistakesTitle: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textPrimary,
    marginBottom: 8,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  topMistakeItem: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    paddingVertical: 8,
  },
  topMistakeRank: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.primary,
    width: 24,
    textAlign: 'right',
  },
  topMistakeTopic: {
    flex: 1,
    fontSize: 14,
    color: Colors.textPrimary,
    marginHorizontal: 8,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  topMistakeCount: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  bestDayCard: {
    backgroundColor: Colors.secondaryLight,
    borderRadius: 12,
    padding: 20,
    alignItems: 'center',
  },
  bestDayLabel: {
    fontSize: 14,
    color: Colors.textSecondary,
    marginBottom: 8,
    textAlign: 'center',
    writingDirection: 'rtl',
  },
  bestDayValue: {
    fontSize: 28,
    fontWeight: 'bold',
    color: Colors.primary,
    marginBottom: 4,
    textAlign: 'center',
    writingDirection: 'rtl',
  },
  bestDayScore: {
    fontSize: 16,
    color: Colors.textPrimary,
    textAlign: 'center',
    writingDirection: 'rtl',
  },
});

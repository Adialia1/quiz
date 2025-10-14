import React, { useEffect, useState } from 'react';
import { SafeAreaView, ActivityIndicator, Alert, View, Text, Pressable, FlatList, StyleSheet, RefreshControl } from 'react-native';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { examApi } from '../utils/examApi';
import { Colors } from '../config/colors';
import { useHistoryStore, ExamHistoryItem, ExamHistoryData } from '../stores/historyStore';

/**
 * ExamHistoryScreen - Shows user's exam history with beautiful cards
 *
 * Features:
 * - Card-based list with FlashList
 * - Date, score, and status indicators
 * - Color-coded by pass/fail
 * - Tap to review results
 * - Pull to refresh
 */
export const ExamHistoryScreen: React.FC = () => {
  const navigation = useNavigation();
  const { getToken } = useAuth();
  const { historyData, setHistoryData, shouldRefetch } = useHistoryStore();

  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [archiving, setArchiving] = useState<string | null>(null);

  // Fetch history
  const fetchHistory = async (isRefresh = false) => {
    try {
      if (isRefresh) {
        setRefreshing(true);
      } else {
        setLoading(true);
      }

      // Reset pagination on refresh
      const data = await examApi.getExamHistory(getToken, { limit: 20, offset: 0 });
      setHistoryData(data);
      setHasMore(data.exams.length >= 20);
    } catch (error: any) {
      console.error('Fetch history error:', error);
      Alert.alert('שגיאה', error.message || 'שגיאה בטעינת היסטוריה');
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  };

  // Load more exams
  const loadMore = async () => {
    if (loadingMore || !hasMore || !historyData) return;

    try {
      setLoadingMore(true);
      const offset = historyData.exams.length;
      const data = await examApi.getExamHistory(getToken, { limit: 20, offset });

      // Append new exams
      setHistoryData({
        ...data,
        exams: [...historyData.exams, ...data.exams],
      });

      // Check if there are more
      setHasMore(data.exams.length >= 20);
    } catch (error: any) {
      console.error('Load more error:', error);
      Alert.alert('שגיאה', error.message || 'שגיאה בטעינת נתונים נוספים');
    } finally {
      setLoadingMore(false);
    }
  };

  // Initial load
  useEffect(() => {
    // Use cache if available and fresh, otherwise fetch
    if (!historyData || shouldRefetch()) {
      fetchHistory();
    }
  }, []);

  // Refresh on screen focus (when coming back from exam results)
  useEffect(() => {
    const unsubscribe = navigation.addListener('focus', () => {
      // Only refetch if cache is stale and not currently loading
      if (shouldRefetch() && !loading && !refreshing) {
        fetchHistory();
      }
    });

    return unsubscribe;
  }, [navigation, loading, refreshing]);

  // Format date
  const formatDate = (dateString: string): string => {
    const date = new Date(dateString);
    const today = new Date();
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);

    if (date.toDateString() === today.toDateString()) {
      return 'היום';
    } else if (date.toDateString() === yesterday.toDateString()) {
      return 'אתמול';
    }

    const day = date.getDate().toString().padStart(2, '0');
    const month = (date.getMonth() + 1).toString().padStart(2, '0');
    const year = date.getFullYear();
    return `${day}/${month}/${year}`;
  };

  // Format time
  const formatTime = (dateString: string): string => {
    const date = new Date(dateString);
    const hours = date.getHours().toString().padStart(2, '0');
    const minutes = date.getMinutes().toString().padStart(2, '0');
    return `${hours}:${minutes}`;
  };

  // Get exam type label
  const getExamTypeLabel = (type: string): string => {
    switch (type) {
      case 'practice':
        return 'אימון';
      case 'full_simulation':
        return 'סימולציה מלאה';
      case 'review_mistakes':
        return 'חזרה על טעויות';
      default:
        return type;
    }
  };

  // Get status badge
  const getStatusBadge = (exam: ExamHistoryItem) => {
    if (exam.status === 'abandoned') {
      return { text: 'נזנח', color: '#9CA3AF' };
    }
    if (exam.status === 'in_progress') {
      return { text: 'בתהליך', color: Colors.accent };
    }
    if (exam.passed) {
      return { text: 'עבר', color: Colors.success };
    }
    return { text: 'נכשל', color: Colors.error };
  };

  // Handle exam tap
  const handleExamTap = (exam: ExamHistoryItem) => {
    if (exam.status === 'completed') {
      // Navigate to results
      navigation.navigate('ExamResults', { examId: exam.id });
    } else if (exam.status === 'in_progress') {
      Alert.alert(
        'המשך מבחן',
        'האם ברצונך להמשיך את המבחן?',
        [
          { text: 'ביטול', style: 'cancel' },
          { text: 'המשך', onPress: () => navigation.navigate('Exam', { examId: exam.id }) },
        ]
      );
    }
  };

  // Handle archive exam
  const handleArchiveExam = (examId: string) => {
    Alert.alert(
      'העברה לארכיון',
      'האם אתה בטוח שברצונך להעביר מבחן זה לארכיון?',
      [
        { text: 'ביטול', style: 'cancel' },
        {
          text: 'העבר לארכיון',
          style: 'destructive',
          onPress: () => archiveExam(examId)
        },
      ]
    );
  };

  // Archive exam
  const archiveExam = async (examId: string) => {
    try {
      setArchiving(examId);

      const token = await getToken();
      const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

      const response = await fetch(`${API_URL}/api/exams/${examId}/archive`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to archive exam');
      }

      // Remove exam from local state
      if (historyData) {
        setHistoryData({
          ...historyData,
          exams: historyData.exams.filter(e => e.id !== examId),
          total_count: historyData.total_count - 1,
        });
      }
    } catch (error: any) {
      console.error('Archive exam error:', error);
      Alert.alert('שגיאה', error.message || 'לא ניתן להעביר לארכיון כרגע');
    } finally {
      setArchiving(null);
    }
  };

  // Render exam card
  const renderExamCard = ({ item }: { item: ExamHistoryItem }) => {
    const statusBadge = getStatusBadge(item);
    const canTap = item.status === 'completed' || item.status === 'in_progress';
    const isArchiving = archiving === item.id;

    return (
      <Pressable
        onPress={() => canTap && handleExamTap(item)}
        style={[styles.card, !canTap && styles.cardDisabled]}
        disabled={!canTap}
      >
        {/* Header */}
        <View style={styles.cardHeader}>
          <View style={styles.cardHeaderRight}>
            <Text style={styles.examType}>{getExamTypeLabel(item.exam_type)}</Text>
            <View style={[styles.statusBadge, { backgroundColor: statusBadge.color }]}>
              <Text style={styles.statusBadgeText}>{statusBadge.text}</Text>
            </View>
          </View>
          <View style={styles.dateAndArchive}>
            <View style={styles.dateContainer}>
              <Text style={styles.dateText}>{formatDate(item.started_at)}</Text>
              <Text style={styles.timeText}>{formatTime(item.started_at)}</Text>
            </View>
            {/* Archive button */}
            <Pressable
              onPress={(e) => {
                e.stopPropagation();
                handleArchiveExam(item.id);
              }}
              style={styles.archiveButton}
              disabled={isArchiving}
            >
              {isArchiving ? (
                <ActivityIndicator size="small" color="#9CA3AF" />
              ) : (
                <Text style={styles.archiveButtonText}>📦</Text>
              )}
            </Pressable>
          </View>
        </View>

        {/* Score section */}
        {item.score_percentage !== null && (
          <View style={styles.scoreSection}>
            <View style={styles.scoreCircle}>
              <Text style={[styles.scorePercentage, { color: item.passed ? Colors.success : Colors.error }]}>
                {item.score_percentage.toFixed(0)}%
              </Text>
            </View>
            <View style={styles.scoreDetails}>
              <Text style={styles.scoreLabel}>שאלות נכונות</Text>
              <Text style={styles.scoreValue}>
                {Math.round((item.score_percentage / 100) * item.total_questions)} מתוך {item.total_questions}
              </Text>
            </View>
          </View>
        )}

        {/* In progress indicator */}
        {item.status === 'in_progress' && (
          <View style={styles.inProgressContainer}>
            <Text style={styles.inProgressText}>לחץ להמשך המבחן</Text>
          </View>
        )}
      </Pressable>
    );
  };

  if (loading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={Colors.primary} />
          <Text style={styles.loadingText}>טוען היסטוריה...</Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!historyData || historyData.exams.length === 0) {
    return (
      <SafeAreaView style={styles.container}>
        {/* Header */}
        <View style={styles.header}>
          <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
            <Text style={styles.backButtonText}>←</Text>
          </Pressable>
          <Text style={styles.headerTitle}>היסטוריית מבחנים</Text>
          <View style={{ width: 40 }} />
        </View>

        {/* Empty state */}
        <View style={styles.emptyContainer}>
          <Text style={styles.emptyText}>עדיין לא ביצעת מבחנים</Text>
          <Text style={styles.emptySubtext}>התחל מבחן כדי לראות אותו כאן</Text>
          <Pressable onPress={() => navigation.goBack()} style={styles.startButton}>
            <Text style={styles.startButtonText}>התחל מבחן</Text>
          </Pressable>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
          <Text style={styles.backButtonText}>←</Text>
        </Pressable>
        <Text style={styles.headerTitle}>היסטוריית מבחנים</Text>
        <View style={{ width: 40 }} />
      </View>

      {/* Stats bar */}
      {historyData.average_score !== null && (
        <View style={styles.statsBar}>
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{historyData.average_score.toFixed(0)}%</Text>
            <Text style={styles.statLabel}>ציון ממוצע</Text>
          </View>
          <View style={styles.statDivider} />
          <View style={styles.statItem}>
            <Text style={styles.statValue}>{historyData.total_count}</Text>
            <Text style={styles.statLabel}>מבחנים</Text>
          </View>
        </View>
      )}

      {/* Exam list */}
      <FlatList
        data={historyData.exams}
        renderItem={renderExamCard}
        keyExtractor={(item) => item.id}
        contentContainerStyle={styles.listContent}
        showsVerticalScrollIndicator={false}
        refreshControl={
          <RefreshControl
            refreshing={refreshing}
            onRefresh={() => fetchHistory(true)}
            tintColor={Colors.primary}
          />
        }
        ListFooterComponent={
          hasMore ? (
            <Pressable
              onPress={loadMore}
              style={styles.loadMoreButton}
              disabled={loadingMore}
            >
              {loadingMore ? (
                <ActivityIndicator size="small" color={Colors.primary} />
              ) : (
                <Text style={styles.loadMoreText}>טען עוד</Text>
              )}
            </Pressable>
          ) : historyData.exams.length > 0 ? (
            <Text style={styles.endText}>זה הכל! 🎉</Text>
          ) : null
        }
      />
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F9FAFB',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: 16,
    fontSize: 16,
    color: '#6B7280',
  },
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 16,
    paddingVertical: 16,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  backButtonText: {
    fontSize: 24,
    color: Colors.primary,
    fontWeight: '600',
  },
  headerTitle: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
  },
  statsBar: {
    flexDirection: 'row',
    backgroundColor: Colors.white,
    paddingVertical: 20,
    paddingHorizontal: 32,
    marginBottom: 8,
    borderBottomWidth: 1,
    borderBottomColor: '#E5E7EB',
  },
  statItem: {
    flex: 1,
    alignItems: 'center',
  },
  statValue: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.primary,
    marginBottom: 4,
  },
  statLabel: {
    fontSize: 14,
    color: '#6B7280',
  },
  statDivider: {
    width: 1,
    backgroundColor: '#E5E7EB',
    marginHorizontal: 24,
  },
  listContent: {
    padding: 16,
    gap: 12,
  },
  card: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 16,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  cardDisabled: {
    opacity: 0.6,
  },
  cardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: 16,
  },
  cardHeaderRight: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
  },
  examType: {
    fontSize: 18,
    fontWeight: '700',
    color: '#111827',
  },
  statusBadge: {
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 12,
  },
  statusBadgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.white,
  },
  dateAndArchive: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
  },
  dateContainer: {
    alignItems: 'flex-end',
  },
  dateText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#374151',
  },
  timeText: {
    fontSize: 12,
    color: '#9CA3AF',
    marginTop: 2,
  },
  scoreSection: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 16,
    paddingTop: 12,
    borderTopWidth: 1,
    borderTopColor: '#F3F4F6',
  },
  scoreCircle: {
    width: 64,
    height: 64,
    borderRadius: 32,
    backgroundColor: '#F9FAFB',
    borderWidth: 3,
    borderColor: '#E5E7EB',
    alignItems: 'center',
    justifyContent: 'center',
  },
  scorePercentage: {
    fontSize: 20,
    fontWeight: '700',
  },
  scoreDetails: {
    flex: 1,
  },
  scoreLabel: {
    fontSize: 14,
    color: '#6B7280',
    marginBottom: 4,
  },
  scoreValue: {
    fontSize: 18,
    fontWeight: '600',
    color: '#111827',
  },
  inProgressContainer: {
    marginTop: 12,
    padding: 12,
    backgroundColor: '#FEF3C7',
    borderRadius: 8,
  },
  inProgressText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#92400E',
    textAlign: 'center',
  },
  emptyContainer: {
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 32,
  },
  emptyText: {
    fontSize: 20,
    fontWeight: '700',
    color: '#111827',
    marginBottom: 8,
  },
  emptySubtext: {
    fontSize: 16,
    color: '#6B7280',
    textAlign: 'center',
    marginBottom: 32,
  },
  startButton: {
    backgroundColor: Colors.primary,
    paddingVertical: 16,
    paddingHorizontal: 48,
    borderRadius: 12,
  },
  startButtonText: {
    fontSize: 18,
    fontWeight: '700',
    color: Colors.white,
  },
  loadMoreButton: {
    backgroundColor: Colors.white,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 12,
    marginBottom: 20,
    borderWidth: 2,
    borderColor: Colors.primary,
  },
  loadMoreText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.primary,
  },
  endText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#6B7280',
    textAlign: 'center',
    marginTop: 12,
    marginBottom: 20,
  },
  archiveButton: {
    width: 36,
    height: 36,
    borderRadius: 18,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    justifyContent: 'center',
  },
  archiveButtonText: {
    fontSize: 18,
  },
});

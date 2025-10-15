/**
 * Progress Tracking Type Definitions
 * הגדרות טיפוסים למעקב אחר התקדמות
 */

// ממשק סקירת התקדמות - Progress Overview Interface
export interface ProgressOverview {
  total_exams: number;
  total_questions_answered: number;
  average_score: number | null;
  exam_date: string | null;
  days_until_exam: number | null;
  study_streak_days: number;
  exams_this_week: number;
  exams_this_month: number;
  exams_passed: number;
  exams_failed: number;
}

// ממשק פריט היסטוריית מבחן - Exam History Item Interface
export interface ExamHistoryItem {
  id: string;
  date: string;
  exam_type: 'practice' | 'full_simulation' | 'review_mistakes';
  score: number | null;
  passed: boolean | null;
  time_taken_minutes: number | null;
  total_questions: number;
  correct_answers: number;
  wrong_answers: number;
  skipped_answers: number;
}

// ממשק ביצועים לפי נושא - Topic Performance Interface
export interface TopicPerformance {
  topic: string;
  accuracy: number | null;
  strength_level: 'weak' | 'average' | 'strong';
  total_questions: number;
  correct_answers: number;
  wrong_answers: number;
  last_practiced: string | null;
}

// ממשק נקודת מגמת ציונים - Score Trend Point Interface
export interface ScoreTrendPoint {
  date: string;
  score: number | null;
}

// ממשק נקודת פעילות שבועית - Weekly Activity Point Interface
export interface WeeklyActivityPoint {
  week: string;
  exams: number;
}

// ממשק מגמות ביצועים - Performance Trends Interface
export interface PerformanceTrends {
  score_trend: ScoreTrendPoint[];
  weekly_activity: WeeklyActivityPoint[];
  best_day_of_week: string | null;
  best_day_score: number | null;
}

// ממשק נושא עם הכי הרבה טעויות - Top Mistake Topic Interface
export interface TopMistakeTopic {
  topic: string;
  count: number;
}

// ממשק תובנות טעויות - Mistake Insights Interface
export interface MistakeInsights {
  total_mistakes: number;
  resolved_mistakes: number;
  unresolved_mistakes: number;
  top_mistake_topics: TopMistakeTopic[];
}

// ממשק רמת שליטה - Mastery Level Interface
export interface MasteryLevel {
  mastered: number;
  practicing: number;
  learning: number;
  not_seen: number;
}

// ממשק כללי של נתוני התקדמות - Overall Progress Data Interface
export interface ProgressData {
  overview: ProgressOverview;
  examHistory: ExamHistoryItem[];
  topicPerformance: TopicPerformance[];
  trends: PerformanceTrends;
  mistakes: MistakeInsights;
  mastery: MasteryLevel;
}

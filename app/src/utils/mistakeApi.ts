/**
 * Mistake Review API utility functions
 * API calls for reviewing and resolving mistakes
 */

import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.apiUrl || 'https://quiz-production-d042.up.railway.app';

/**
 * Get auth token - must be called from React component
 */
type GetTokenFn = () => Promise<string | null>;

/**
 * Topic with mistake information
 */
export interface TopicMistake {
  name: string;
  mistake_count: number;
  accuracy_percentage: number;
  priority: 'high' | 'medium' | 'low';
  priority_emoji: string;
  last_mistake_date: string;
}

/**
 * Response from /mistakes/topics endpoint
 */
export interface MistakeTopicsResponse {
  topics: TopicMistake[];
  total_mistakes: number;
  total_resolved: number;
}

/**
 * Mistake analytics data
 */
export interface MistakeAnalytics {
  total_mistakes: number;
  resolved: number;
  unresolved: number;
  improvement_rate: number;
  weak_concepts: string[];
  progress_this_week: {
    questions_reviewed: number;
    newly_resolved: number;
  };
}

/**
 * Mistake API functions
 */
export const mistakeApi = {
  /**
   * Get topics where user has unresolved mistakes
   */
  async getMistakeTopics(getToken: GetTokenFn): Promise<MistakeTopicsResponse> {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/mistakes/topics`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch mistake topics');
    }

    return response.json();
  },

  /**
   * Get detailed analytics about mistakes and improvement
   */
  async getAnalytics(getToken: GetTokenFn): Promise<MistakeAnalytics> {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/mistakes/analytics`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch analytics');
    }

    return response.json();
  },

  /**
   * Create a mistake review session for a specific topic
   */
  async createMistakeReviewSession(
    topic: string | null,
    questionCount: number,
    getToken: GetTokenFn
  ) {
    const token = await getToken();

    const body: any = {
      exam_type: 'review_mistakes',
      question_count: questionCount, // 10 for specific topic, 25 for all
    };

    if (topic) {
      body.topics = [topic];
    }

    const response = await fetch(`${API_URL}/api/exams`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create review session');
    }

    return response.json();
  },
};

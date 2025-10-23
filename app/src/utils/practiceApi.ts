/**
 * Practice API utility functions
 * API calls specific to practice mode
 */

import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.apiUrl || 'http://www.ethicaplus.net';

/**
 * Get auth token - must be called from React component
 * Import useAuth from @clerk/clerk-expo in your component
 */
type GetTokenFn = () => Promise<string | null>;

/**
 * Topic information
 */
export interface TopicInfo {
  name: string;
  question_count: number;
}

/**
 * Response from /practice/topics endpoint
 */
export interface PracticeTopicsResponse {
  topics: TopicInfo[];
  difficulties: string[];
}

/**
 * Answer feedback response from practice mode
 */
export interface AnswerFeedback {
  is_correct: boolean;
  correct_answer: string;
  explanation: string;
  immediate_feedback: boolean;
}

/**
 * Practice API functions
 */
export const practiceApi = {
  /**
   * Get available topics and difficulties for practice
   */
  async getTopics(getToken: GetTokenFn): Promise<PracticeTopicsResponse> {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/practice/topics`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to fetch topics');
    }

    return response.json();
  },

  /**
   * Create a practice session with specific topic and difficulty
   */
  async createPracticeSession(
    topic: string | null,
    difficulty: string | null,
    questionCount: number,
    getToken: GetTokenFn
  ) {
    const token = await getToken();

    const body: any = {
      exam_type: 'practice',
      question_count: questionCount,
    };

    if (topic && topic !== 'all') {
      body.topics = [topic];
    }

    // Apply difficulty filter if specified and not "all"
    if (difficulty && difficulty !== 'all') {
      // Map Hebrew to English
      const difficultyMap: { [key: string]: string } = {
        'קל': 'easy',
        'בינוני': 'medium',
        'קשה': 'hard',
      };
      body.difficulty = difficultyMap[difficulty] || difficulty;
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
      throw new Error(error.detail || 'Failed to create practice session');
    }

    return response.json();
  },

  /**
   * Submit answer for a question in practice mode
   * Returns immediate feedback with correct answer and explanation
   */
  async submitAnswer(
    examId: string,
    questionId: string,
    userAnswer: string,
    timeTaken: number,
    getToken: GetTokenFn
  ): Promise<AnswerFeedback> {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/${examId}/answer`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        question_id: questionId,
        user_answer: userAnswer,
        time_taken_seconds: timeTaken,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit answer');
    }

    return response.json();
  },
};

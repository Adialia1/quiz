import Constants from 'expo-constants';

const API_URL = Constants.expoConfig?.extra?.apiUrl || 'https://www.ethicaplus.net';

export interface CreateExamRequest {
  exam_type: 'practice' | 'full_simulation' | 'review_mistakes';
  question_count?: number;
  topics?: string[];
  difficulty?: string;
}

export interface SubmitAnswerRequest {
  question_id: string;
  user_answer: string;
  time_taken_seconds: number;
}

/**
 * Get auth token - must be called from React component
 * Import useAuth from @clerk/clerk-expo in your component
 */
type GetTokenFn = () => Promise<string | null>;

/**
 * Exam API utility functions
 * Note: Pass getToken function from useAuth() hook
 */
export const examApi = {
  /**
   * Create a new exam session
   */
  async createExam(data: CreateExamRequest, getToken: GetTokenFn) {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to create exam');
    }

    return response.json();
  },

  /**
   * Get exam details
   */
  async getExam(examId: string, getToken: GetTokenFn) {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/${examId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get exam');
    }

    return response.json();
  },

  /**
   * Submit multiple answers at once (batch)
   */
  async submitAnswersBatch(examId: string, answers: SubmitAnswerRequest[], getToken: GetTokenFn) {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/${examId}/answers/batch`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ answers }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit answers');
    }

    return response.json();
  },

  /**
   * Submit single answer (for practice mode)
   */
  async submitAnswer(examId: string, data: SubmitAnswerRequest, getToken: GetTokenFn) {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/${examId}/answer`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit answer');
    }

    return response.json();
  },

  /**
   * Submit final exam and get results
   */
  async submitExam(examId: string, getToken: GetTokenFn) {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/${examId}/submit`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to submit exam');
    }

    return response.json();
  },

  /**
   * Get detailed exam results
   */
  async getExamResults(examId: string, getToken: GetTokenFn) {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/${examId}/results`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get results');
    }

    return response.json();
  },

  /**
   * Get exam history
   */
  async getExamHistory(
    getToken: GetTokenFn,
    params?: {
      limit?: number;
      offset?: number;
      type?: string;
    }
  ) {
    const token = await getToken();

    const queryParams = new URLSearchParams(params as any).toString();
    const url = `${API_URL}/api/exams/history${queryParams ? `?${queryParams}` : ''}`;

    const response = await fetch(url, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get history');
    }

    return response.json();
  },

  /**
   * Abandon exam
   */
  async abandonExam(examId: string, getToken: GetTokenFn) {
    const token = await getToken();

    const response = await fetch(`${API_URL}/api/exams/${examId}`, {
      method: 'DELETE',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to abandon exam');
    }

    return response.json();
  },
};

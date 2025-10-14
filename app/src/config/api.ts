/**
 * API Configuration
 */
import Constants from 'expo-constants';

// Get API URL from environment variable
export const API_URL = Constants.expoConfig?.extra?.apiUrl || 'https://accepted-awfully-bug.ngrok-free.app';

// API endpoints
export const API_ENDPOINTS = {
  // User endpoints
  USER_PROFILE: '/api/users/me',
  USER_STATS: '/api/users/me/stats',
  USER_ONBOARDING: '/api/users/me/onboarding',

  // Exam endpoints
  EXAMS: '/api/exams',
  EXAM_HISTORY: '/api/exams/history',
  EXAM_DETAIL: (examId: string) => `/api/exams/${examId}`,
  EXAM_ANSWER: (examId: string) => `/api/exams/${examId}/answer`,
  EXAM_SUBMIT: (examId: string) => `/api/exams/${examId}/submit`,
  EXAM_RESULTS: (examId: string) => `/api/exams/${examId}/results`,
  EXAM_ARCHIVE: (examId: string) => `/api/exams/${examId}/archive`,

  // Chat endpoints
  CHAT_SESSIONS: '/api/chat/sessions',
  CHAT_MESSAGES: (sessionId: string) => `/api/chat/sessions/${sessionId}/messages`,
  CHAT_SEND: (sessionId: string) => `/api/chat/sessions/${sessionId}/send`,

  // Concepts endpoints
  CONCEPTS_TOPICS: '/api/concepts/topics',
  CONCEPTS_BY_TOPIC: (topic: string) => `/api/concepts/topics/${encodeURIComponent(topic)}`,
  CONCEPT_DETAIL: (conceptId: string) => `/api/concepts/${conceptId}`,
  CONCEPTS_SEARCH: '/api/concepts/search',
  CONCEPTS_STATS: '/api/concepts/stats',

  // Notifications
  SEND_NOTIFICATION: '/api/notifications/send',
  SEND_STUDY_REMINDERS: '/api/notifications/send-study-reminders',
};

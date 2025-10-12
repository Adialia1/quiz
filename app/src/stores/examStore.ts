import { create } from 'zustand';

/**
 * Question interface
 */
export interface Question {
  id: string;
  question_text: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  option_e: string;
  topic: string;
  sub_topic?: string;
  difficulty_level: string;
  image_url?: string;
}

/**
 * User's answer for a question
 */
export interface UserAnswer {
  question_id: string;
  user_answer: string | null; // A, B, C, D, E or null if not answered
  time_taken_seconds: number;
  start_time: number; // Timestamp when user started this question
}

/**
 * Exam session data
 */
export interface ExamSession {
  exam_id: string;
  exam_type: string;
  total_questions: number;
  questions: Question[];
  started_at: string;
  time_limit_minutes: number | null;
}

/**
 * Exam results
 */
export interface ExamResults {
  exam_id: string;
  score_percentage: number;
  passed: boolean;
  correct_answers: number;
  wrong_answers: number;
  time_taken_seconds: number;
  weak_topics: string[];
  strong_topics: string[];
}

/**
 * Detailed question result (for review)
 */
export interface QuestionResult {
  question_id: string;
  question_text: string;
  user_answer: string;
  correct_answer: string;
  is_correct: boolean;
  time_taken_seconds: number;
  topic: string;
  difficulty_level: string;
  explanation: string;
  option_a: string;
  option_b: string;
  option_c: string;
  option_d: string;
  option_e: string;
}

/**
 * Exam store interface
 */
interface ExamStore {
  // Current exam session
  currentExam: ExamSession | null;
  currentQuestionIndex: number;
  userAnswers: Map<string, UserAnswer>;

  // Timer
  startTime: number | null;
  elapsedTime: number; // in seconds

  // Results
  examResults: ExamResults | null;
  detailedResults: QuestionResult[] | null;

  // Actions
  setCurrentExam: (exam: ExamSession) => void;
  setCurrentQuestionIndex: (index: number) => void;
  setUserAnswer: (questionId: string, answer: string | null) => void;
  startQuestion: (questionId: string) => void;
  finishQuestion: (questionId: string) => void;
  startTimer: () => void;
  updateElapsedTime: (seconds: number) => void;
  setExamResults: (results: ExamResults) => void;
  setDetailedResults: (results: QuestionResult[]) => void;
  resetExam: () => void;

  // Getters
  getCurrentQuestion: () => Question | null;
  getUserAnswer: (questionId: string) => UserAnswer | undefined;
  getAnsweredCount: () => number;
  isQuestionAnswered: (questionId: string) => boolean;
}

/**
 * Exam state management store
 */
export const useExamStore = create<ExamStore>((set, get) => ({
  // Initial state
  currentExam: null,
  currentQuestionIndex: 0,
  userAnswers: new Map(),
  startTime: null,
  elapsedTime: 0,
  examResults: null,
  detailedResults: null,

  // Set current exam
  setCurrentExam: (exam) => {
    set({
      currentExam: exam,
      currentQuestionIndex: 0,
      userAnswers: new Map(),
      startTime: Date.now(),
      elapsedTime: 0,
      examResults: null,
      detailedResults: null,
    });
  },

  // Set current question index
  setCurrentQuestionIndex: (index) => {
    set({ currentQuestionIndex: index });
  },

  // Set user answer
  setUserAnswer: (questionId, answer) => {
    const { userAnswers } = get();
    const existing = userAnswers.get(questionId);

    if (existing) {
      // Update existing answer
      userAnswers.set(questionId, {
        ...existing,
        user_answer: answer,
      });
    } else {
      // Create new answer entry
      userAnswers.set(questionId, {
        question_id: questionId,
        user_answer: answer,
        time_taken_seconds: 0,
        start_time: Date.now(),
      });
    }

    set({ userAnswers: new Map(userAnswers) });
  },

  // Start tracking time for a question
  startQuestion: (questionId) => {
    const { userAnswers } = get();
    const existing = userAnswers.get(questionId);

    if (!existing) {
      userAnswers.set(questionId, {
        question_id: questionId,
        user_answer: null,
        time_taken_seconds: 0,
        start_time: Date.now(),
      });
      set({ userAnswers: new Map(userAnswers) });
    }
  },

  // Finish tracking time for a question
  finishQuestion: (questionId) => {
    const { userAnswers } = get();
    const answer = userAnswers.get(questionId);

    if (answer) {
      const timeTaken = Math.floor((Date.now() - answer.start_time) / 1000);
      answer.time_taken_seconds += timeTaken;
      answer.start_time = Date.now(); // Reset for next time
      set({ userAnswers: new Map(userAnswers) });
    }
  },

  // Start exam timer
  startTimer: () => {
    set({ startTime: Date.now(), elapsedTime: 0 });
  },

  // Update elapsed time
  updateElapsedTime: (seconds) => {
    set({ elapsedTime: seconds });
  },

  // Set exam results
  setExamResults: (results) => {
    set({ examResults: results });
  },

  // Set detailed results
  setDetailedResults: (results) => {
    set({ detailedResults: results });
  },

  // Reset exam
  resetExam: () => {
    set({
      currentExam: null,
      currentQuestionIndex: 0,
      userAnswers: new Map(),
      startTime: null,
      elapsedTime: 0,
      examResults: null,
      detailedResults: null,
    });
  },

  // Get current question
  getCurrentQuestion: () => {
    const { currentExam, currentQuestionIndex } = get();
    if (!currentExam || currentQuestionIndex >= currentExam.questions.length) {
      return null;
    }
    return currentExam.questions[currentQuestionIndex];
  },

  // Get user answer for a question
  getUserAnswer: (questionId) => {
    const { userAnswers } = get();
    return userAnswers.get(questionId);
  },

  // Get count of answered questions
  getAnsweredCount: () => {
    const { userAnswers } = get();
    let count = 0;
    userAnswers.forEach((answer) => {
      if (answer.user_answer !== null) {
        count++;
      }
    });
    return count;
  },

  // Check if question is answered
  isQuestionAnswered: (questionId) => {
    const { userAnswers } = get();
    const answer = userAnswers.get(questionId);
    return answer !== undefined && answer.user_answer !== null;
  },
}));

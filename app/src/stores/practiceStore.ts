import { create } from 'zustand';
import { Question, ExamSession } from './examStore';
import { AnswerFeedback } from '../utils/practiceApi';

/**
 * Practice session configuration
 */
export interface PracticeConfig {
  selectedTopic: string | null; // 'all' or specific topic name
  selectedDifficulty: string | null; // 'קל', 'בינוני', 'קשה'
  questionCount: number;
}

/**
 * Practice store interface
 */
interface PracticeStore {
  // Selection state
  config: PracticeConfig;

  // Session state
  currentSession: ExamSession | null;
  currentQuestionIndex: number;
  showingFeedback: boolean; // Track if showing answer explanation
  currentFeedback: AnswerFeedback | null; // Store feedback data
  questionStartTime: number | null; // When user started viewing current question

  // Stats
  correctAnswers: number;
  wrongAnswers: number;

  // Actions - Configuration
  setConfig: (config: Partial<PracticeConfig>) => void;
  resetConfig: () => void;

  // Actions - Session
  startSession: (session: ExamSession) => void;
  setCurrentQuestionIndex: (index: number) => void;
  showFeedback: (feedback: AnswerFeedback) => void;
  hideFeedback: () => void;
  nextQuestion: () => void;
  previousQuestion: () => void;
  startQuestionTimer: () => void;
  getTimeTaken: () => number;

  // Actions - Stats
  incrementCorrect: () => void;
  incrementWrong: () => void;

  // Actions - Reset
  resetSession: () => void;
  resetAll: () => void;

  // Getters
  getCurrentQuestion: () => Question | null;
  getProgress: () => number; // Returns percentage (0-100)
  isLastQuestion: () => boolean;
  hasSession: () => boolean;
}

const defaultConfig: PracticeConfig = {
  selectedTopic: null,
  selectedDifficulty: null,
  questionCount: 20,
};

/**
 * Practice state management store
 * Separate from examStore for practice-specific flow
 */
export const usePracticeStore = create<PracticeStore>((set, get) => ({
  // Initial state
  config: defaultConfig,
  currentSession: null,
  currentQuestionIndex: 0,
  showingFeedback: false,
  currentFeedback: null,
  questionStartTime: null,
  correctAnswers: 0,
  wrongAnswers: 0,

  // Configuration actions
  setConfig: (config) => {
    set((state) => ({
      config: { ...state.config, ...config },
    }));
  },

  resetConfig: () => {
    set({ config: defaultConfig });
  },

  // Session actions
  startSession: (session) => {
    set({
      currentSession: session,
      currentQuestionIndex: 0,
      showingFeedback: false,
      currentFeedback: null,
      questionStartTime: Date.now(),
      correctAnswers: 0,
      wrongAnswers: 0,
    });
  },

  setCurrentQuestionIndex: (index) => {
    const { currentSession } = get();
    if (!currentSession) return;

    const maxIndex = currentSession.questions.length - 1;
    const validIndex = Math.max(0, Math.min(index, maxIndex));

    set({
      currentQuestionIndex: validIndex,
      showingFeedback: false,
      currentFeedback: null,
      questionStartTime: Date.now(),
    });
  },

  showFeedback: (feedback) => {
    set({
      showingFeedback: true,
      currentFeedback: feedback,
    });

    // Update stats based on feedback
    if (feedback.is_correct) {
      get().incrementCorrect();
    } else {
      get().incrementWrong();
    }
  },

  hideFeedback: () => {
    set({
      showingFeedback: false,
      currentFeedback: null,
    });
  },

  nextQuestion: () => {
    const { currentQuestionIndex, currentSession } = get();
    if (!currentSession) return;

    const nextIndex = currentQuestionIndex + 1;
    if (nextIndex < currentSession.questions.length) {
      set({
        currentQuestionIndex: nextIndex,
        showingFeedback: false,
        currentFeedback: null,
        questionStartTime: Date.now(),
      });
    }
  },

  previousQuestion: () => {
    const { currentQuestionIndex } = get();
    if (currentQuestionIndex > 0) {
      set({
        currentQuestionIndex: currentQuestionIndex - 1,
        showingFeedback: false,
        currentFeedback: null,
        questionStartTime: Date.now(),
      });
    }
  },

  startQuestionTimer: () => {
    set({ questionStartTime: Date.now() });
  },

  getTimeTaken: () => {
    const { questionStartTime } = get();
    if (!questionStartTime) return 0;
    return Math.floor((Date.now() - questionStartTime) / 1000);
  },

  // Stats actions
  incrementCorrect: () => {
    set((state) => ({
      correctAnswers: state.correctAnswers + 1,
    }));
  },

  incrementWrong: () => {
    set((state) => ({
      wrongAnswers: state.wrongAnswers + 1,
    }));
  },

  // Reset actions
  resetSession: () => {
    set({
      currentSession: null,
      currentQuestionIndex: 0,
      showingFeedback: false,
      currentFeedback: null,
      questionStartTime: null,
      correctAnswers: 0,
      wrongAnswers: 0,
    });
  },

  resetAll: () => {
    set({
      config: defaultConfig,
      currentSession: null,
      currentQuestionIndex: 0,
      showingFeedback: false,
      currentFeedback: null,
      questionStartTime: null,
      correctAnswers: 0,
      wrongAnswers: 0,
    });
  },

  // Getters
  getCurrentQuestion: () => {
    const { currentSession, currentQuestionIndex } = get();
    if (!currentSession || !currentSession.questions || currentQuestionIndex >= currentSession.questions.length) {
      return null;
    }
    return currentSession.questions[currentQuestionIndex];
  },

  getProgress: () => {
    const { currentSession, currentQuestionIndex } = get();
    if (!currentSession || currentSession.total_questions === 0) {
      return 0;
    }
    return Math.round(((currentQuestionIndex + 1) / currentSession.total_questions) * 100);
  },

  isLastQuestion: () => {
    const { currentSession, currentQuestionIndex } = get();
    if (!currentSession) return false;
    return currentQuestionIndex === currentSession.questions.length - 1;
  },

  hasSession: () => {
    const { currentSession } = get();
    return currentSession !== null;
  },
}));

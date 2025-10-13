import { create } from 'zustand';
import { TopicMistake, MistakeAnalytics } from '../utils/mistakeApi';

/**
 * Mistake Review Store
 * Manages state for mistake review feature
 */
interface MistakeStore {
  // Data
  topics: TopicMistake[];
  analytics: MistakeAnalytics | null;

  // Loading states
  loadingTopics: boolean;
  loadingAnalytics: boolean;

  // Selected topic for review
  selectedTopic: string | null;

  // Actions
  setTopics: (topics: TopicMistake[]) => void;
  setAnalytics: (analytics: MistakeAnalytics) => void;
  setLoadingTopics: (loading: boolean) => void;
  setLoadingAnalytics: (loading: boolean) => void;
  setSelectedTopic: (topic: string | null) => void;
  reset: () => void;
}

const initialState = {
  topics: [],
  analytics: null,
  loadingTopics: false,
  loadingAnalytics: false,
  selectedTopic: null,
};

export const useMistakeStore = create<MistakeStore>((set) => ({
  ...initialState,

  setTopics: (topics) => set({ topics }),

  setAnalytics: (analytics) => set({ analytics }),

  setLoadingTopics: (loading) => set({ loadingTopics: loading }),

  setLoadingAnalytics: (loading) => set({ loadingAnalytics: loading }),

  setSelectedTopic: (topic) => set({ selectedTopic: topic }),

  reset: () => set(initialState),
}));

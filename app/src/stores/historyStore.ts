import { create } from 'zustand';

export interface ExamHistoryItem {
  id: string;
  exam_type: 'practice' | 'full_simulation' | 'review_mistakes';
  status: 'in_progress' | 'completed' | 'abandoned';
  score_percentage: number | null;
  passed: boolean | null;
  started_at: string;
  completed_at: string | null;
  total_questions: number;
}

export interface ExamHistoryData {
  exams: ExamHistoryItem[];
  total_count: number;
  average_score: number | null;
}

interface HistoryStore {
  historyData: ExamHistoryData | null;
  lastFetched: number | null;

  // Actions
  setHistoryData: (data: ExamHistoryData) => void;
  clearHistoryData: () => void;
  shouldRefetch: () => boolean;
}

const CACHE_DURATION = 60000; // 1 minute

export const useHistoryStore = create<HistoryStore>((set, get) => ({
  historyData: null,
  lastFetched: null,

  setHistoryData: (data) => set({
    historyData: data,
    lastFetched: Date.now()
  }),

  clearHistoryData: () => set({
    historyData: null,
    lastFetched: null
  }),

  shouldRefetch: () => {
    const { lastFetched } = get();
    if (!lastFetched) return true;
    return (Date.now() - lastFetched) > CACHE_DURATION;
  },
}));

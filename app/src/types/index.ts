/**
 * קבצי הגדרות TypeScript
 * TypeScript Type Definitions
 */

// ממשקי משתמש - User interfaces
export interface User {
  id: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  imageUrl?: string;
}

// ממשקי ניווט - Navigation interfaces
export type RootStackParamList = {
  Welcome: undefined;
  Auth: undefined;
  Home: undefined;
  Quiz: { quizId: string };
  Results: { score: number; total: number };
  Profile: undefined;
};

// ממשקי שאלות - Question interfaces
export interface Question {
  id: string;
  text: string;
  options: string[];
  correctAnswer: number;
  explanation?: string;
  category?: string;
  difficulty?: 'easy' | 'medium' | 'hard';
}

// ממשקי קוויז - Quiz interfaces
export interface Quiz {
  id: string;
  title: string;
  description: string;
  questions: Question[];
  category: string;
  difficulty: 'easy' | 'medium' | 'hard';
  timeLimit?: number; // בשניות
  passingScore: number; // אחוז
}

// ממשקי תוצאות - Results interfaces
export interface QuizResult {
  id: string;
  quizId: string;
  userId: string;
  score: number;
  totalQuestions: number;
  correctAnswers: number;
  timeTaken: number; // בשניות
  completedAt: Date;
  answers: UserAnswer[];
}

export interface UserAnswer {
  questionId: string;
  selectedAnswer: number;
  isCorrect: boolean;
  timeSpent: number; // בשניות
}

// ממשקי סטטיסטיקות - Statistics interfaces
export interface UserStats {
  totalQuizzes: number;
  completedQuizzes: number;
  averageScore: number;
  totalTimeSpent: number; // בשניות
  categoryStats: CategoryStats[];
}

export interface CategoryStats {
  category: string;
  quizzesCompleted: number;
  averageScore: number;
}

// ממשקי API - API interfaces
export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

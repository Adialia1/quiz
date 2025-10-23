import { create } from 'zustand';
import { StorageUtils, StorageKeys } from '../utils/storage';

/**
 * ממשק נתוני משתמש
 * User data interface
 */
export interface User {
  id: string;
  email?: string;
  firstName?: string;
  lastName?: string;
  first_name?: string;
  last_name?: string;
  imageUrl?: string;
  is_admin?: boolean;  // Admin flag - bypasses subscription checks and sees admin panel
}

/**
 * ממשק חנות האימות
 * Auth store interface
 */
interface AuthStore {
  // מצב
  isAuthenticated: boolean;
  user: User | null;
  isLoading: boolean;

  // פעולות
  setUser: (user: User | null) => void;
  setIsAuthenticated: (isAuthenticated: boolean) => void;
  setIsLoading: (isLoading: boolean) => void;
  login: (user: User) => Promise<void>;
  logout: () => Promise<void>;
  clearAllData: () => Promise<void>;
  hydrate: () => Promise<void>;
}

/**
 * חנות ניהול מצב האימות
 * Authentication state management store
 */
export const useAuthStore = create<AuthStore>((set) => ({
  // מצב התחלתי - Initial state
  isAuthenticated: false,
  user: null,
  isLoading: true,

  // עדכון משתמש - Update user
  setUser: (user) => {
    set({ user });
    if (user) {
      StorageUtils.setObject(StorageKeys.USER_DATA, user);
    } else {
      StorageUtils.delete(StorageKeys.USER_DATA);
    }
  },

  // עדכון מצב אימות - Update authentication status
  setIsAuthenticated: (isAuthenticated) => {
    set({ isAuthenticated });
  },

  // עדכון מצב טעינה - Update loading status
  setIsLoading: (isLoading) => {
    set({ isLoading });
  },

  // התחברות - Login
  login: async (user) => {
    set({
      user,
      isAuthenticated: true,
      isLoading: false,
    });
    await StorageUtils.setObject(StorageKeys.USER_DATA, user);
    await StorageUtils.setBoolean(StorageKeys.AUTH_TOKEN, true);
  },

  // התנתקות - Logout
  logout: async () => {
    set({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
    await StorageUtils.delete(StorageKeys.USER_DATA);
    await StorageUtils.delete(StorageKeys.AUTH_TOKEN);
  },

  // מחיקת כל הנתונים - Clear all data (for account deletion)
  clearAllData: async () => {
    set({
      user: null,
      isAuthenticated: false,
      isLoading: false,
    });
    // Clear all storage completely
    await StorageUtils.clearAll();
  },

  // טעינת מצב מהאחסון - Hydrate state from storage
  hydrate: async () => {
    try {
      const savedUser = await StorageUtils.getObject<User>(StorageKeys.USER_DATA);
      const hasToken = await StorageUtils.getBoolean(StorageKeys.AUTH_TOKEN);

      if (savedUser && hasToken) {
        set({
          user: savedUser,
          isAuthenticated: true,
          isLoading: false,
        });
      } else {
        set({
          user: null,
          isAuthenticated: false,
          isLoading: false,
        });
      }
    } catch (error) {
      console.error('שגיאה בטעינת מצב האימות:', error);
      set({
        user: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },
}));

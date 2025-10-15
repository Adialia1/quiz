import { create } from 'zustand';
import { SubscriptionInfo, SubscriptionStatus, SubscriptionPeriod } from '../types/subscription';
import { useAuthStore } from './authStore';

/**
 * Subscription Store
 * Manages user subscription state using Zustand
 */

interface SubscriptionStore {
  // State
  subscriptionInfo: SubscriptionInfo | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  setSubscriptionInfo: (info: SubscriptionInfo) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
  reset: () => void;

  // Computed
  isPremium: () => boolean;
  isInTrial: () => boolean;
}

const initialState = {
  subscriptionInfo: null,
  isLoading: false,
  error: null,
};

export const useSubscriptionStore = create<SubscriptionStore>((set, get) => ({
  ...initialState,

  // Actions
  setSubscriptionInfo: (info) => set({ subscriptionInfo: info, error: null }),

  setLoading: (loading) => set({ isLoading: loading }),

  setError: (error) => set({ error, isLoading: false }),

  clearError: () => set({ error: null }),

  reset: () => set(initialState),

  // Computed properties
  isPremium: () => {
    // Admin users have full access regardless of subscription status
    const user = useAuthStore.getState().user;
    if (user?.is_admin) {
      return true;
    }

    const { subscriptionInfo } = get();
    if (!subscriptionInfo) return false;
    return subscriptionInfo.status === 'active' || subscriptionInfo.status === 'trial';
  },

  isInTrial: () => {
    const { subscriptionInfo } = get();
    if (!subscriptionInfo) return false;
    return subscriptionInfo.isInTrial;
  },
}));

import Purchases, { LOG_LEVEL } from 'react-native-purchases';
import { Platform } from 'react-native';

/**
 * RevenueCat configuration
 * Initialize RevenueCat SDK for subscription management
 */

const REVENUECAT_API_KEY = process.env.EXPO_PUBLIC_REVENUECAT_API_KEY || '';

// Track if RevenueCat has been initialized
let isRevenueCatInitialized = false;

/**
 * Initialize RevenueCat SDK
 * Should be called at app startup (only once)
 */
export const initializeRevenueCat = async (userId?: string) => {
  try {
    // Prevent multiple initializations
    if (isRevenueCatInitialized) {
      console.log('⚠️ RevenueCat already initialized, skipping...');

      // If user ID is provided, login the user
      if (userId) {
        await Purchases.logIn(userId);
        console.log('✅ RevenueCat user logged in:', userId);
      }

      return;
    }

    if (!REVENUECAT_API_KEY) {
      console.warn('RevenueCat API key is not configured');
      return;
    }

    // Enable debug logs in development
    if (__DEV__) {
      Purchases.setLogLevel(LOG_LEVEL.DEBUG);
    }

    // Configure SDK
    Purchases.configure({
      apiKey: REVENUECAT_API_KEY,
      appUserID: userId, // Optional - pass Clerk user ID
      usesStoreKit2IfAvailable: false, // Use StoreKit 1 for better sandbox testing
    });

    console.log('💰 RevenueCat configured for:', __DEV__ ? 'SANDBOX/TEST' : 'PRODUCTION');

    isRevenueCatInitialized = true;
    console.log('✅ RevenueCat initialized successfully');
  } catch (error) {
    console.error('❌ Failed to initialize RevenueCat:', error);
  }
};

/**
 * Subscription plan identifiers
 * These should match the product IDs in RevenueCat dashboard
 */
export const SUBSCRIPTION_PLANS = {
  MONTHLY: 'quiz_monthly_1999',
  QUARTERLY: 'quiz_quarterly_4999', // 3 months - ~16.66 ILS/month (16.7% discount)
} as const;

/**
 * Entitlement identifier
 * This is the entitlement you create in RevenueCat dashboard
 */
export const ENTITLEMENT_ID = 'premium';

/**
 * Plan details for UI display
 */
export const PLAN_DETAILS = {
  [SUBSCRIPTION_PLANS.MONTHLY]: {
    id: SUBSCRIPTION_PLANS.MONTHLY,
    title: 'חודשי',
    titleEnglish: 'Monthly',
    price: 19.99,
    priceDisplay: '$19.99',
    period: 'לחודש',
    periodEnglish: 'per month',
    trialDays: 3,
    trialText: '3 ימי ניסיון חינם',
    savings: null,
    savingsPercent: 0,
    popular: false,
  },
  [SUBSCRIPTION_PLANS.QUARTERLY]: {
    id: SUBSCRIPTION_PLANS.QUARTERLY,
    title: '3 חודשים',
    titleEnglish: '3 Months',
    price: 49.99,
    priceDisplay: '$49.99',
    period: 'ל-3 חודשים',
    periodEnglish: 'per 3 months',
    pricePerMonth: 16.66,
    pricePerMonthDisplay: '$16.66',
    trialDays: 0,
    trialText: null,
    savings: 10, // 19.99*3 - 49.99 = 9.98 ≈ $10 savings
    savingsPercent: 16.7, // ~17% discount
    popular: true,
    badge: 'הכי משתלם! 🎉',
  },
} as const;

export type SubscriptionPlanId = keyof typeof PLAN_DETAILS;

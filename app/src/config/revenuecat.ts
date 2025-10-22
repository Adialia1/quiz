import Purchases, { LOG_LEVEL } from 'react-native-purchases';
import { Platform } from 'react-native';
import Constants from 'expo-constants';

/**
 * RevenueCat configuration
 * Initialize RevenueCat SDK for subscription management
 */

// Get RevenueCat API key from Expo config (works in production builds)
const REVENUECAT_API_KEY = Constants.expoConfig?.extra?.revenuecatApiKey || '';

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
      return;
    }

    if (!REVENUECAT_API_KEY) {
      console.warn('⚠️ RevenueCat API key is not configured');
      return;
    }

    // Check if running in Expo Go - RevenueCat doesn't work in Expo Go
    const isExpoGo = Constants.appOwnership === 'expo';
    if (isExpoGo) {
      console.log('🔧 Running in Expo Go - RevenueCat initialization skipped');
      console.log('💡 To test subscriptions, create a development build with: eas build --profile development');
      isRevenueCatInitialized = true; // Mark as initialized to prevent repeated attempts
      return;
    }

    console.log('[RevenueCat] Starting initialization...');
    console.log('[RevenueCat] API Key:', REVENUECAT_API_KEY.substring(0, 10) + '...');
    console.log('[RevenueCat] User ID:', userId || 'anonymous');

    // Enable debug logs in development
    if (__DEV__) {
      Purchases.setLogLevel(LOG_LEVEL.DEBUG);
    }

    // Configure SDK with user ID
    Purchases.configure({
      apiKey: REVENUECAT_API_KEY,
      appUserID: userId, // Pass Clerk user ID directly
      usesStoreKit2IfAvailable: false, // Use StoreKit 1 for better sandbox testing
    });

    isRevenueCatInitialized = true;

    // Check if we're in production mode
    const isProduction = !__DEV__;
    console.log('💰 RevenueCat configured for:', isProduction ? 'PRODUCTION' : 'SANDBOX/TEST');
    console.log('✅ RevenueCat initialized successfully');
  } catch (error) {
    console.error('❌ Failed to initialize RevenueCat:', error);
    // Reset flag so it can retry
    isRevenueCatInitialized = false;
  }
};

/**
 * Subscription plan identifiers
 * These should match the product IDs in RevenueCat dashboard
 */
export const SUBSCRIPTION_PLANS = {
  MONTHLY: 'quiz_monthly_1999', //Old name so keep it like this
  QUARTERLY: 'quiz_quarterly_4999', // 3 months - //Old name so keep it like this
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
    price: 39.99,
    priceDisplay: '$39.99',
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
    price: 99.99,
    priceDisplay: '$99.99',
    period: 'ל-3 חודשים',
    periodEnglish: 'per 3 months',
    pricePerMonth: 33,
    pricePerMonthDisplay: '$33',
    trialDays: 0,
    trialText: null,
    savings: 18,
    savingsPercent: 15.4, // ~15% discount
    popular: true,
    badge: 'הכי משתלם! 🎉',
  },
} as const;

export type SubscriptionPlanId = keyof typeof PLAN_DETAILS;

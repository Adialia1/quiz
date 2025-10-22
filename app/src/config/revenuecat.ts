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

    // Enable debug logs in development (but not verbose to reduce noise)
    if (__DEV__) {
      Purchases.setLogLevel(LOG_LEVEL.INFO); // Changed from DEBUG to INFO to reduce noise
    }

    // Suppress the "window.location.search" error in Expo Go
    // This is a known issue when using RevenueCat in development
    const originalConsoleError = console.error;
    console.error = (...args: any[]) => {
      if (
        typeof args[0] === 'string' &&
        (args[0].includes('Cannot read property \'search\' of undefined') ||
         args[0].includes('Error while tracking event sdk_initialized'))
      ) {
        // Suppress this specific error
        return;
      }
      originalConsoleError(...args);
    };

    // Configure SDK
    Purchases.configure({
      apiKey: REVENUECAT_API_KEY,
      appUserID: userId, // Optional - pass Clerk user ID
      usesStoreKit2IfAvailable: false, // Use StoreKit 1 for better sandbox testing
    });

    // Restore console.error after a brief delay
    setTimeout(() => {
      console.error = originalConsoleError;
    }, 1000);

    // Check if we're in production mode
    const isProduction = !__DEV__ && !process.env.EXPO_PUBLIC_USE_SANDBOX;

    console.log('💰 RevenueCat configured for:', isProduction ? 'PRODUCTION' : 'SANDBOX/TEST');

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
    price: 39,
    priceDisplay: '₪39',  // Changed to Shekels
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
    price: 99,
    priceDisplay: '₪99',  // Changed to Shekels
    period: 'ל-3 חודשים',
    periodEnglish: 'per 3 months',
    pricePerMonth: 33,
    pricePerMonthDisplay: '₪33',  // Changed to Shekels
    trialDays: 0,
    trialText: null,
    savings: 18,
    savingsPercent: 15.4, // ~15% discount
    popular: true,
    badge: 'הכי משתלם! 🎉',
  },
} as const;

export type SubscriptionPlanId = keyof typeof PLAN_DETAILS;

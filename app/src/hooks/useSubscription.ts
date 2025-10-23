import { useEffect, useCallback } from 'react';
import Purchases, { CustomerInfo, PurchasesOfferings } from 'react-native-purchases';
import Constants from 'expo-constants';
import { useSubscriptionStore } from '../stores/subscriptionStore';
import { SubscriptionInfo, AvailablePackage } from '../types/subscription';
import { ENTITLEMENT_ID, SUBSCRIPTION_PLANS } from '../config/revenuecat';

// Check if running in Expo Go
const isExpoGo = Constants.appOwnership === 'expo';

/**
 * Custom hook for managing subscriptions with RevenueCat
 */
export const useSubscription = () => {
  const {
    subscriptionInfo,
    isLoading,
    error,
    setSubscriptionInfo,
    setLoading,
    setError,
    clearError,
    isPremium,
    isInTrial,
  } = useSubscriptionStore();

  /**
   * Parse CustomerInfo to SubscriptionInfo
   */
  const parseCustomerInfo = useCallback((customerInfo: CustomerInfo): SubscriptionInfo => {
    console.log('[SUBSCRIPTION] 🔍 Parsing CustomerInfo...');
    console.log('[SUBSCRIPTION] Available entitlements:', Object.keys(customerInfo.entitlements.all));
    console.log('[SUBSCRIPTION] Active entitlements:', Object.keys(customerInfo.entitlements.active));
    console.log('[SUBSCRIPTION] Looking for entitlement ID:', ENTITLEMENT_ID);

    const entitlement = customerInfo.entitlements.active[ENTITLEMENT_ID];

    if (!entitlement) {
      console.log('[SUBSCRIPTION] ❌ No active entitlement found for:', ENTITLEMENT_ID);

      // Debug: Show ALL active entitlements
      const allActiveKeys = Object.keys(customerInfo.entitlements.active);
      if (allActiveKeys.length > 0) {
        console.log('[SUBSCRIPTION] 🔍 BUT found these active entitlements:', allActiveKeys);
        console.log('[SUBSCRIPTION] ⚠️ Your ENTITLEMENT_ID might be wrong!');
        console.log('[SUBSCRIPTION] 💡 Check RevenueCat dashboard → Entitlements');
      }

      // Check if entitlement exists but is expired
      const expiredEntitlement = customerInfo.entitlements.all[ENTITLEMENT_ID];
      if (expiredEntitlement) {
        console.log('[SUBSCRIPTION] ⏰ Found EXPIRED entitlement:');
        console.log('[SUBSCRIPTION] - Expiration date:', expiredEntitlement.expirationDate);
        console.log('[SUBSCRIPTION] - Is sandbox:', expiredEntitlement.isSandbox);
        console.log('[SUBSCRIPTION] - Is active:', expiredEntitlement.isActive);
        console.log('[SUBSCRIPTION] 💡 TIP: Sandbox subscriptions expire quickly (5-7 min for monthly). Make a new test purchase to continue testing.');
      } else {
        console.log('[SUBSCRIPTION] ❌ Entitlement', ENTITLEMENT_ID, 'does NOT exist in RevenueCat!');
        console.log('[SUBSCRIPTION] 💡 Create entitlement in RevenueCat dashboard:');
        console.log('[SUBSCRIPTION]    1. Go to RevenueCat → Entitlements');
        console.log('[SUBSCRIPTION]    2. Create entitlement with ID:', ENTITLEMENT_ID);
        console.log('[SUBSCRIPTION]    3. Attach products to this entitlement');
      }

      return {
        status: 'expired',
        period: expiredEntitlement?.productIdentifier.includes('monthly') ? 'monthly' :
                expiredEntitlement?.productIdentifier.includes('quarterly') ? 'quarterly' : null,
        expirationDate: expiredEntitlement ? new Date(expiredEntitlement.expirationDate) : null,
        willRenew: false,
        isInTrial: false,
        trialEndDate: null,
      };
    }

    console.log('[SUBSCRIPTION] ✅ Found active entitlement!');
    console.log('[SUBSCRIPTION] Product ID:', entitlement.productIdentifier);
    console.log('[SUBSCRIPTION] Is active:', entitlement.isActive);
    console.log('[SUBSCRIPTION] Period type:', entitlement.periodType);
    console.log('[SUBSCRIPTION] Will renew:', entitlement.willRenew);

    const expirationDate = new Date(entitlement.expirationDate || '');
    const isActive = entitlement.isActive;
    const willRenew = entitlement.willRenew;
    const isInTrialPeriod = entitlement.periodType === 'trial';

    // Determine period from product identifier
    let period: 'monthly' | 'quarterly' | null = null;
    if (entitlement.productIdentifier.includes('monthly')) {
      period = 'monthly';
    } else if (entitlement.productIdentifier.includes('quarterly')) {
      period = 'quarterly';
    }

    let status: 'active' | 'trial' | 'expired' | 'none' = 'none';
    if (isActive) {
      status = isInTrialPeriod ? 'trial' : 'active';
    } else {
      status = 'expired';
    }

    return {
      status,
      period,
      expirationDate,
      willRenew,
      isInTrial: isInTrialPeriod,
      trialEndDate: isInTrialPeriod ? expirationDate : null,
    };
  }, []);

  /**
   * Fetch current subscription status
   */
  const fetchSubscriptionStatus = useCallback(async () => {
    // Skip if running in Expo Go
    if (isExpoGo) {
      console.log('[SUBSCRIPTION] Skipping fetch in Expo Go');
      setLoading(false);
      return;
    }

    try {
      setLoading(true);
      const customerInfo = await Purchases.getCustomerInfo();
      const info = parseCustomerInfo(customerInfo);
      setSubscriptionInfo(info);
    } catch (err) {
      console.error('Failed to fetch subscription status:', err);
      setError('שגיאה בטעינת מצב המנוי');
    } finally {
      setLoading(false);
    }
  }, [parseCustomerInfo, setLoading, setSubscriptionInfo, setError]);

  /**
   * Get available offerings/packages
   */
  const getOfferings = useCallback(async (): Promise<AvailablePackage[]> => {
    // Skip if running in Expo Go
    if (isExpoGo) {
      console.log('[SUBSCRIPTION] Skipping offerings in Expo Go');
      return [];
    }

    try {
      console.log('[SUBSCRIPTION] Fetching offerings from RevenueCat...');
      const offerings = await Purchases.getOfferings();

      console.log('[SUBSCRIPTION] Offerings received:', {
        current: offerings.current?.identifier || 'none',
        all: Object.keys(offerings.all).length,
      });

      // Try to get current offering, or fallback to "all" offering
      let offering = offerings.current;

      if (!offering) {
        console.warn('⚠️ [SUBSCRIPTION] No current offering found, trying "all" offering...');
        offering = offerings.all['all'];
      }

      if (!offering) {
        console.warn('⚠️ [SUBSCRIPTION] No offerings found at all!');
        console.warn('📝 You need to:');
        console.warn('   1. Create products in RevenueCat dashboard');
        console.warn('   2. Create an offering and set it as "current"');
        console.warn('   3. Attach products to the offering');
        console.warn('🔗 See REVENUECAT_SETUP_GUIDE.md for detailed instructions');
        return [];
      }

      console.log('[SUBSCRIPTION] Using offering:', offering.identifier);
      console.log('[SUBSCRIPTION] Offering has', offering.availablePackages.length, 'packages');

      const packages = offering.availablePackages.map((pkg) => ({
        identifier: pkg.identifier,
        packageType: pkg.packageType,
        product: {
          identifier: pkg.product.identifier,
          description: pkg.product.description,
          title: pkg.product.title,
          price: pkg.product.price,
          priceString: pkg.product.priceString,
          currencyCode: pkg.product.currencyCode,
          introPrice: pkg.product.introPrice ? {
            price: pkg.product.introPrice.price,
            priceString: pkg.product.introPrice.priceString,
            period: pkg.product.introPrice.period || '',
            cycles: pkg.product.introPrice.cycles,
          } : undefined,
        },
        rcPackage: pkg,
      }));

      return packages;
    } catch (err) {
      console.error('Failed to get offerings:', err);
      throw new Error('שגיאה בטעינת תוכניות המנוי');
    }
  }, []);

  /**
   * Purchase a subscription
   */
  const purchaseSubscription = useCallback(
    async (packageToPurchase: AvailablePackage): Promise<boolean> => {
      try {
        setLoading(true);
        clearError();

        const { customerInfo } = await Purchases.purchasePackage(packageToPurchase.rcPackage);
        const info = parseCustomerInfo(customerInfo);
        setSubscriptionInfo(info);

        return true;
      } catch (err: any) {
        console.error('Purchase failed:', err);

        // Handle user cancellation
        if (err.userCancelled) {
          setError('הרכישה בוטלה');
          return false;
        }

        // Handle specific error codes
        let errorMessage = 'שגיאה בביצוע הרכישה';

        if (err.code) {
          switch (err.code) {
            case '1': // PURCHASE_CANCELLED
              errorMessage = 'הרכישה בוטלה';
              break;
            case '2': // STORE_PROBLEM
              errorMessage = 'בעיה בחנות האפליקציות. נסה שוב מאוחר יותר';
              break;
            case '3': // PURCHASE_NOT_ALLOWED
              errorMessage = 'הרכישה אינה מורשת. ודא שהתשלומים מופעלים במכשיר';
              break;
            case '4': // PURCHASE_INVALID
              errorMessage = 'פרטי הרכישה אינם תקינים';
              break;
            case '5': // PRODUCT_NOT_AVAILABLE / Test failure
              // This is a sandbox test error - show friendly message
              if (err.message && err.message.includes('Test purchase failure')) {
                errorMessage = 'בדיקת תשלום נכשל (מצב sandbox)';
              } else {
                errorMessage = 'המוצר אינו זמין כרגע. נסה שוב מאוחר יותר';
              }
              break;
            case '6': // PRODUCT_ALREADY_PURCHASED
              errorMessage = 'כבר יש לך מנוי פעיל';
              break;
            case '7': // NETWORK_ERROR
              errorMessage = 'בעיית רשת. בדוק את החיבור לאינטרנט';
              break;
            default:
              errorMessage = `שגיאה בביצוע הרכישה (קוד: ${err.code})`;
          }
        }

        setError(errorMessage);
        return false;
      } finally {
        setLoading(false);
      }
    },
    [parseCustomerInfo, setLoading, setSubscriptionInfo, setError, clearError]
  );

  /**
   * Restore purchases
   */
  const restorePurchases = useCallback(async (): Promise<boolean> => {
    try {
      setLoading(true);
      clearError();

      const customerInfo = await Purchases.restorePurchases();
      const info = parseCustomerInfo(customerInfo);
      setSubscriptionInfo(info);

      if (info.status === 'active' || info.status === 'trial') {
        return true;
      } else {
        setError('לא נמצאו רכישות קודמות');
        return false;
      }
    } catch (err) {
      console.error('Restore failed:', err);
      setError('שגיאה בשחזור רכישות');
      return false;
    } finally {
      setLoading(false);
    }
  }, [parseCustomerInfo, setLoading, setSubscriptionInfo, setError, clearError]);

  /**
   * Initialize - fetch subscription status on mount
   */
  useEffect(() => {
    fetchSubscriptionStatus();
  }, [fetchSubscriptionStatus]);

  return {
    // State
    subscriptionInfo,
    isLoading,
    error,
    isPremium: isPremium(),
    isInTrial: isInTrial(),

    // Actions
    fetchSubscriptionStatus,
    getOfferings,
    purchaseSubscription,
    restorePurchases,
    clearError,
  };
};

import { useEffect, useCallback } from 'react';
import Purchases, { CustomerInfo, PurchasesOfferings } from 'react-native-purchases';
import { useSubscriptionStore } from '../stores/subscriptionStore';
import { SubscriptionInfo, AvailablePackage } from '../types/subscription';
import { ENTITLEMENT_ID, SUBSCRIPTION_PLANS } from '../config/revenuecat';

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
    const entitlement = customerInfo.entitlements.active[ENTITLEMENT_ID];

    if (!entitlement) {
      return {
        status: 'none',
        period: null,
        expirationDate: null,
        willRenew: false,
        isInTrial: false,
        trialEndDate: null,
      };
    }

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
    try {
      const offerings = await Purchases.getOfferings();

      if (!offerings.current) {
        return [];
      }

      const packages = offerings.current.availablePackages.map((pkg) => ({
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

        setError('שגיאה בביצוע הרכישה');
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

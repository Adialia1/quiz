import { PurchasesPackage, CustomerInfo } from 'react-native-purchases';

/**
 * Subscription status
 */
export type SubscriptionStatus = 'active' | 'trial' | 'expired' | 'none';

/**
 * Subscription period
 */
export type SubscriptionPeriod = 'monthly' | 'quarterly';

/**
 * User subscription info
 */
export interface SubscriptionInfo {
  status: SubscriptionStatus;
  period: SubscriptionPeriod | null;
  expirationDate: Date | null;
  willRenew: boolean;
  isInTrial: boolean;
  trialEndDate: Date | null;
}

/**
 * Available package for purchase
 */
export interface AvailablePackage {
  identifier: string;
  packageType: string;
  product: {
    identifier: string;
    description: string;
    title: string;
    price: number;
    priceString: string;
    currencyCode: string;
    introPrice?: {
      price: number;
      priceString: string;
      period: string;
      cycles: number;
    };
  };
  rcPackage: PurchasesPackage; // Original RevenueCat package
}

import React, { useState, useEffect } from 'react';
import {
  StyleSheet,
  Text,
  View,
  ScrollView,
  TouchableOpacity,
  SafeAreaView,
  Dimensions,
  Alert,
  ActivityIndicator,
  Image,
} from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useSubscription } from '../hooks/useSubscription';
import { SUBSCRIPTION_PLANS } from '../config/revenuecat';

const { width } = Dimensions.get('window');

interface CustomPaywallScreenProps {
  onComplete?: () => void;
}

/**
 * Custom Paywall Screen
 * Beautiful subscription screen with improved UI design
 */
export const CustomPaywallScreen: React.FC<CustomPaywallScreenProps> = ({
  onComplete,
}) => {
  const [selectedPlan, setSelectedPlan] = useState<'monthly' | 'quarterly'>('quarterly');
  const [isLoading, setIsLoading] = useState(false);
  const [packages, setPackages] = useState<any[]>([]);

  const { getOfferings, purchaseSubscription, restorePurchases, error, clearError } =
    useSubscription();

  // Load available packages
  useEffect(() => {
    loadPackages();
  }, []);

  const loadPackages = async () => {
    try {
      console.log('[CUSTOM PAYWALL] Loading packages...');
      const offerings = await getOfferings();
      console.log('[CUSTOM PAYWALL] Received offerings:', offerings.length);
      setPackages(offerings);
    } catch (err) {
      console.error('[CUSTOM PAYWALL] Failed to load packages:', err);
    }
  };

  // Handle purchase
  const handlePurchase = async () => {
    setIsLoading(true);
    clearError();

    try {
      const packageToPurchase = packages.find((pkg) => {
        if (selectedPlan === 'monthly') {
          return pkg.identifier === '$rc_monthly' || pkg.product?.identifier === SUBSCRIPTION_PLANS.MONTHLY;
        } else {
          return pkg.identifier === '$rc_three_month' || pkg.product?.identifier === SUBSCRIPTION_PLANS.QUARTERLY;
        }
      });

      if (!packageToPurchase) {
        Alert.alert('שגיאה', 'לא נמצא מנוי זמין. אנא נסה שוב מאוחר יותר.');
        setIsLoading(false);
        return;
      }

      console.log('[CUSTOM PAYWALL] Purchasing package:', packageToPurchase.identifier);
      const success = await purchaseSubscription(packageToPurchase);

      if (success) {
        Alert.alert(
          'הצלחה! 🎉',
          'המנוי שלך הופעל בהצלחה',
          [{ text: 'המשך', onPress: () => onComplete?.() }]
        );
      }
    } catch (err: any) {
      console.error('[CUSTOM PAYWALL] Purchase error:', err);
      Alert.alert('שגיאה', err?.message || 'שגיאה בביצוע הרכישה. אנא נסה שוב.');
    } finally {
      setIsLoading(false);
    }
  };

  // Handle restore purchases
  const handleRestore = async () => {
    setIsLoading(true);
    try {
      const hasActiveSubscription = await restorePurchases();

      if (hasActiveSubscription) {
        Alert.alert('הצלחה!', 'המנוי שוחזר בהצלחה', [
          { text: 'המשך', onPress: () => onComplete?.() }
        ]);
      } else {
        Alert.alert('אין מנויים', 'לא נמצאו רכישות קודמות לשחזור');
      }
    } catch (err) {
      console.error('[CUSTOM PAYWALL] Restore error:', err);
      Alert.alert('שגיאה', 'שגיאה בשחזור רכישות. אנא נסה שוב.');
    } finally {
      setIsLoading(false);
    }
  };

  const features = [
    {
      icon: '📚',
      title: 'גישה לכל בנק השאלות של אתיקה פלוס',
      description: 'מאגר שאלות שנכתב על ידי מומחי אתיקה',
    },
    {
      icon: '⏱️',
      title: 'מבחנים מלאים ללא הגבלה',
      description: 'מבחני סימולציה כמו בבחינה',
    },
    {
      icon: '🤖',
      title: 'צ\'אט עם מנטור אתיקה מקצועי',
      description: 'צ\'אט עם בינה מלאכותית שאומנה עם מידע של הרשות',
    },
    {
      icon: '🎮',
      title: 'כרטיסיות משחק',
      description: 'כרטיסיות משחק אשר יעזרו לך ללמוד את החומר בתהליך',
    },
  ];

  const pricingPlans = [
    {
      id: 'quarterly',
      name: 'מנוי רבעוני',
      monthlyPrice: '$33.33',
      totalPrice: '$99.99/3mo',
      discount: '18% OFF',
      subtitle: 'מחיר חודשי',
    },
    {
      id: 'monthly',
      name: 'מנוי חודשי',
      monthlyPrice: '$39.99ב',
      totalPrice: '$39.99/mo',
      subtitle: 'חודש אחד',
    },
  ];

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {/* Logo Section */}
        <View style={styles.logoSection}>
          <View style={styles.logoContainer}>
            <Image
              source={require('../../assets/icon.png')}
              style={styles.logoImage}
              resizeMode="contain"
            />
          </View>
          <Text style={styles.logoText}>אתיקה פלוס</Text>
        </View>

        {/* Title */}
        <Text style={styles.title}>קבלו גישה לאתיקה פלוס</Text>

        {/* Features */}
        <View style={styles.features}>
          {features.map((feature, index) => (
            <View key={index} style={styles.featureItem}>
              <View style={styles.featureIcon}>
                <Text style={styles.featureIconText}>{feature.icon}</Text>
              </View>
              <View style={styles.featureContent}>
                <Text style={styles.featureTitle}>{feature.title}</Text>
                <Text style={styles.featureDescription}>
                  {feature.description}
                </Text>
              </View>
            </View>
          ))}
        </View>

        {/* Pricing Options */}
        <View style={styles.pricingOptions}>
          {pricingPlans.map((plan) => (
            <TouchableOpacity
              key={plan.id}
              style={[
                styles.pricingCard,
                selectedPlan === plan.id && styles.pricingCardSelected,
              ]}
              onPress={() => setSelectedPlan(plan.id as 'monthly' | 'quarterly')}
              activeOpacity={0.7}
            >
              {plan.discount && (
                <View style={styles.discountBadge}>
                  <Text style={styles.discountText}>{plan.discount}</Text>
                </View>
              )}

              <View style={styles.pricingHeader}>
                <View
                  style={[
                    styles.radioButton,
                    selectedPlan === plan.id && styles.radioButtonSelected,
                  ]}
                >
                  {selectedPlan === plan.id && (
                    <Text style={styles.radioCheckmark}>✓</Text>
                  )}
                </View>
                <Text style={styles.planName}>{plan.name}</Text>
              </View>

              <View style={styles.pricingDetails}>
                <View style={styles.priceBreakdown}>
                  <Text style={styles.monthlyPrice}>
                    {plan.monthlyPrice} · {plan.subtitle}
                  </Text>
                </View>
                <Text style={styles.totalPrice}>{plan.totalPrice}</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        {/* CTA Button */}
        <TouchableOpacity
          activeOpacity={0.8}
          onPress={handlePurchase}
          disabled={isLoading}
        >
          <LinearGradient
            colors={['#5b6eff', '#7b8aff']}
            start={{ x: 0, y: 0 }}
            end={{ x: 1, y: 1 }}
            style={styles.ctaButton}
          >
            {isLoading ? (
              <ActivityIndicator size="small" color="white" />
            ) : (
              <Text style={styles.ctaButtonText}>המשך</Text>
            )}
          </LinearGradient>
        </TouchableOpacity>

        {/* Restore Link */}
        <TouchableOpacity
          style={styles.restoreLinkContainer}
          onPress={handleRestore}
          disabled={isLoading}
        >
          <Text style={styles.restoreLink}>שחזור רכישות</Text>
        </TouchableOpacity>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f5f5f5',
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 20,
    alignItems: 'center',
  },
  logoSection: {
    alignItems: 'center',
    marginBottom: 30,
    marginTop: 20,
  },
  logoContainer: {
    width: 80,
    height: 80,
    borderRadius: 20,
    alignItems: 'center',
    justifyContent: 'center',
    marginBottom: 10,
    overflow: 'hidden',
  },
  logoImage: {
    width: 80,
    height: 80,
  },
  logoText: {
    color: '#1e6bb8',
    fontSize: 16,
    fontWeight: '600',
    marginTop: 8,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    textAlign: 'center',
    marginVertical: 30,
    color: '#1a1a1a',
    writingDirection: 'rtl',
  },
  features: {
    width: '100%',
    marginVertical: 30,
  },
  featureItem: {
    flexDirection: 'row-reverse',
    alignItems: 'flex-start',
    marginBottom: 25,
    gap: 15,
  },
  featureIcon: {
    width: 32,
    height: 32,
    backgroundColor: '#f0f0f0',
    borderRadius: 8,
    alignItems: 'center',
    justifyContent: 'center',
  },
  featureIconText: {
    fontSize: 18,
  },
  featureContent: {
    flex: 1,
    alignItems: 'flex-end',
  },
  featureTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1a1a1a',
    marginBottom: 5,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  featureDescription: {
    fontSize: 14,
    color: '#666',
    lineHeight: 21,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  pricingOptions: {
    width: '100%',
    marginVertical: 30,
  },
  pricingCard: {
    borderWidth: 2,
    borderColor: '#e0e0e0',
    borderRadius: 16,
    padding: 20,
    marginBottom: 15,
    position: 'relative',
    backgroundColor: 'white',
  },
  pricingCardSelected: {
    borderColor: '#5b6eff',
    backgroundColor: '#f8f9ff',
  },
  discountBadge: {
    position: 'absolute',
    top: 15,
    left: 15,
    backgroundColor: '#5b6eff',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
  },
  discountText: {
    color: 'white',
    fontSize: 12,
    fontWeight: '700',
  },
  pricingHeader: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    gap: 12,
    marginBottom: 12,
  },
  radioButton: {
    width: 24,
    height: 24,
    borderRadius: 12,
    borderWidth: 2,
    borderColor: '#d0d0d0',
    alignItems: 'center',
    justifyContent: 'center',
  },
  radioButtonSelected: {
    borderColor: '#5b6eff',
    backgroundColor: '#5b6eff',
  },
  radioCheckmark: {
    color: 'white',
    fontSize: 14,
    fontWeight: 'bold',
  },
  planName: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1a1a1a',
    writingDirection: 'rtl',
  },
  pricingDetails: {
    flexDirection: 'row-reverse',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginRight: 36,
  },
  priceBreakdown: {
    alignItems: 'flex-end',
  },
  monthlyPrice: {
    fontSize: 14,
    color: '#666',
    writingDirection: 'rtl',
  },
  totalPrice: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1a1a1a',
  },
  ctaButton: {
    width: width - 40,
    borderRadius: 16,
    paddingVertical: 18,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 20,
  },
  ctaButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '700',
  },
  restoreLinkContainer: {
    marginTop: 20,
    marginBottom: 30,
  },
  restoreLink: {
    color: '#666',
    fontSize: 14,
    textDecorationLine: 'underline',
    textAlign: 'center',
  },
});

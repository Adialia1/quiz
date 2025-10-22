import React, { useState, useEffect, useRef } from 'react';
import { ScrollView, Alert, StyleSheet, View, Dimensions } from 'react-native';
import Constants from 'expo-constants';
import { useClerk } from '@clerk/clerk-expo';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  ButtonText,
  Pressable,
  Spinner,
  Heading,
} from '@gluestack-ui/themed';
import { Check, X } from 'lucide-react-native';
import ConfettiCannon from 'react-native-confetti-cannon';
import { useSubscription } from '../hooks/useSubscription';
import { useAuthStore } from '../stores/authStore';
import { PLAN_DETAILS, SUBSCRIPTION_PLANS } from '../config/revenuecat';
import type { SubscriptionPlanId } from '../config/revenuecat';
import { Colors } from '../config/colors';

const { width, height } = Dimensions.get('window');
const isExpoGo = Constants.appOwnership === 'expo';

interface SubscriptionPlansScreenProps {
  onComplete?: () => void;
  onSkip?: () => void;
  showSkip?: boolean;
}

/**
 * Subscription Plans Screen
 * Beautiful plan selection with monthly (3-day trial) and quarterly options
 */
export const SubscriptionPlansScreen: React.FC<SubscriptionPlansScreenProps> = ({
  onComplete,
  onSkip,
  showSkip = false,
}) => {
  const [selectedPlan, setSelectedPlan] = useState<SubscriptionPlanId>(
    SUBSCRIPTION_PLANS.QUARTERLY // Pre-select the best value
  );
  const [isLoading, setIsLoading] = useState(false);
  const [packages, setPackages] = useState<any[]>([]);
  const [showSuccess, setShowSuccess] = useState(false);
  const confettiRef = useRef<ConfettiCannon>(null);

  const { getOfferings, purchaseSubscription, restorePurchases, error, clearError } =
    useSubscription();

  const { signOut } = useClerk();
  const { logout } = useAuthStore();

  // Load available packages
  useEffect(() => {
    loadPackages();
  }, []);

  const loadPackages = async () => {
    try {
      const offerings = await getOfferings();
      setPackages(offerings);
    } catch (err) {
      console.error('Failed to load packages:', err);
    }
  };

  // Handle purchase
  const handlePurchase = async () => {
    // In Expo Go, skip directly to the app (for UI testing)
    if (isExpoGo) {
      Alert.alert(
        'מצב פיתוח',
        'התשלומים זמינים רק באפליקציה הסופית. נכנס לאפליקציה בינתיים...',
        [
          {
            text: 'אישור',
            onPress: () => onComplete?.()
          }
        ]
      );
      return;
    }

    setIsLoading(true);
    clearError();

    try {
      // Find the package for the selected plan
      const packageToPurchase = packages.find(
        (pkg) => pkg.product.identifier === selectedPlan
      );

      if (!packageToPurchase) {
        Alert.alert('שגיאה', 'לא נמצאה התוכנית שנבחרה. אנא נסה שוב.');
        setIsLoading(false);
        return;
      }

      const success = await purchaseSubscription(packageToPurchase);

      if (success) {
        // Show success state and trigger confetti
        setIsLoading(false);
        setShowSuccess(true);
        confettiRef.current?.start();

        // Wait for confetti animation to complete before navigating
        setTimeout(() => {
          setShowSuccess(false);
          onComplete?.();
        }, 3000);
      } else {
        setIsLoading(false);
      }
    } catch (err) {
      console.error('Purchase error:', err);
      setIsLoading(false);
    }
  };

  // Handle restore
  const handleRestore = async () => {
    setIsLoading(true);
    clearError();

    try {
      const success = await restorePurchases();
      if (success) {
        Alert.alert('הצלחה!', 'המנוי שוחזר בהצלחה');
        onComplete?.();
      }
    } catch (err) {
      console.error('Restore error:', err);
    } finally {
      setIsLoading(false);
    }
  };

  // Handle logout
  const handleLogout = async () => {
    Alert.alert(
      'התנתקות',
      'האם אתה בטוח שברצונך להתנתק?',
      [
        {
          text: 'ביטול',
          style: 'cancel'
        },
        {
          text: 'התנתק',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsLoading(true);
              await logout(); // Clear local storage
              await signOut(); // Clear Clerk session
              console.log('[LOGOUT] User logged out from subscription screen');
            } catch (error) {
              console.error('[LOGOUT] Error:', error);
              Alert.alert('שגיאה', 'אירעה שגיאה בהתנתקות');
            } finally {
              setIsLoading(false);
            }
          }
        }
      ]
    );
  };

  // Show development message in Expo Go - commented out for UI development
  // if (isExpoGo) {
  //   return (
  //     <Box flex={1} bg="$white" p="$6" justifyContent="center">
  //       <VStack space="lg" alignItems="center">
  //         <Text fontSize="$2xl" fontWeight="$bold" textAlign="center" color="$primary600">
  //           🔧 מצב פיתוח
  //         </Text>
  //         <Text fontSize="$lg" textAlign="center" color="$textLight700">
  //           המנויים זמינים רק באפליקציה הסופית.{'\n'}
  //           לבינתיים, תוכל לדלג על שלב זה.
  //         </Text>
  //         <Text fontSize="$sm" textAlign="center" color="$textLight500" mt="$4">
  //           כדי לבדוק מנויים, בנה את האפליקציה עם:{'\n'}
  //           eas build --profile development
  //         </Text>
  //         <Button
  //           size="xl"
  //           bg="$primary600"
  //           onPress={() => onComplete?.()}
  //           mt="$8"
  //           w="100%"
  //         >
  //           <ButtonText color="$white" fontSize="$lg" fontWeight="$bold">
  //             המשך לאפליקציה
  //           </ButtonText>
  //         </Button>
  //       </VStack>
  //     </Box>
  //   );
  // }

  return (
    <Box flex={1} bg="$white">
      <ScrollView showsVerticalScrollIndicator={false}>
        {/* Hero Section with Gradient Background */}
        <Box style={styles.heroSection}>
          <VStack space="md" alignItems="center" pt="$16" pb="$8" px="$6">
            <Heading style={styles.heroTitle}>
              קבל גישה מלאה{'\n'}לכל התכנים
            </Heading>
            <Text style={styles.heroSubtitle}>
              בחר תוכנית והתחל ללמוד היום
            </Text>
          </VStack>
        </Box>

        <VStack px="$5" pb="$10" mt="$6">
          {/* Plan Cards */}
          <VStack space="md" mb="$6">
            {/* Monthly Plan */}
            <PlanCard
              planId={SUBSCRIPTION_PLANS.MONTHLY}
              selected={selectedPlan === SUBSCRIPTION_PLANS.MONTHLY}
              onSelect={() => setSelectedPlan(SUBSCRIPTION_PLANS.MONTHLY)}
            />

            {/* Quarterly Plan - Best Value */}
            <PlanCard
              planId={SUBSCRIPTION_PLANS.QUARTERLY}
              selected={selectedPlan === SUBSCRIPTION_PLANS.QUARTERLY}
              onSelect={() => setSelectedPlan(SUBSCRIPTION_PLANS.QUARTERLY)}
              isBestValue
            />
          </VStack>

          {/* Features List - More Compact */}
          <VStack space="xs" mb="$8" px="$2">
            <FeatureItem text="גישה לכל בנק השאלות" />
            <FeatureItem text="מבחנים מלאים ללא הגבלה" />
            <FeatureItem text="מנטור חכם לעזרה מותאמת אישית" />
            <FeatureItem text="משחקי קלפים ומעקב אחר התקדמות" />
          </VStack>

          {/* Subscribe Button */}
          <Button
            size="xl"
            style={[
              styles.subscribeButton,
              showSuccess && styles.subscribeButtonSuccess
            ]}
            onPress={handlePurchase}
            isDisabled={isLoading || showSuccess}
          >
            {isLoading ? (
              <Spinner color="$white" />
            ) : showSuccess ? (
              <ButtonText style={styles.subscribeButtonText}>
                🎉 ברוך הבא!
              </ButtonText>
            ) : (
              <ButtonText style={styles.subscribeButtonText}>
                {selectedPlan === SUBSCRIPTION_PLANS.MONTHLY
                  ? 'התחל ניסיון חינם'
                  : 'התחל עכשיו'}
              </ButtonText>
            )}
          </Button>

          {/* Reassurance Text */}
          <Text style={styles.reassuranceText}>
            ניתן לבטל בכל עת
          </Text>

          {/* Restore Purchases */}
          <Pressable onPress={handleRestore} disabled={isLoading} style={styles.restoreButton}>
            <Text style={styles.restoreText}>
              שחזר רכישות קודמות
            </Text>
          </Pressable>

          {/* Logout Button */}
          <Pressable onPress={handleLogout} disabled={isLoading} style={styles.logoutButton}>
            <Text style={styles.logoutText}>
              התנתק מהחשבון
            </Text>
          </Pressable>

          {/* Error Message */}
          {error && (
            <Box bg="$error100" p="$3" borderRadius="$lg" mt="$4">
              <Text color="$error600" textAlign="center" size="sm">
                {error}
              </Text>
            </Box>
          )}

          {/* Terms */}
          <Text style={styles.termsText}>
            בלחיצה על "התחל" אתה מסכים לתנאי השימוש ומדיניות הפרטיות.
          </Text>
        </VStack>
      </ScrollView>

      {/* Confetti Animation */}
      <ConfettiCannon
        ref={confettiRef}
        count={200}
        origin={{ x: width / 2, y: -10 }}
        autoStart={false}
        fadeOut={true}
        fallSpeed={3000}
        explosionSpeed={350}
        colors={[Colors.primary, Colors.success, Colors.accent, '#FF9800', '#E91E63']}
      />
    </Box>
  );
};

/**
 * Plan Card Component
 */
interface PlanCardProps {
  planId: SubscriptionPlanId;
  selected: boolean;
  onSelect: () => void;
  isBestValue?: boolean;
}

const PlanCard: React.FC<PlanCardProps> = ({
  planId,
  selected,
  onSelect,
  isBestValue = false,
}) => {
  const plan = PLAN_DETAILS[planId];

  return (
    <Pressable onPress={onSelect}>
      <Box
        style={[
          styles.planCard,
          selected ? styles.planCardSelected : styles.planCardUnselected,
        ]}
      >
        {/* Best Value Badge */}
        {isBestValue && (
          <Box style={styles.bestValueBadge}>
            <Text style={styles.bestValueText}>הכי משתלם!</Text>
          </Box>
        )}

        <HStack alignItems="center" justifyContent="space-between">
          {/* Right Side: Plan Info */}
          <VStack flex={1} space="xs">
            {/* Plan Title */}
            <Text style={styles.planTitle}>{plan.title}</Text>

            {/* Trial Price (if applicable) or Regular Price */}
            {plan.trialDays > 0 ? (
              <VStack space="2xs">
                {/* Big Trial Price */}
                <HStack alignItems="baseline" space="xs">
                  <Text style={styles.planPrice}>$0</Text>
                  <Text style={styles.planPeriod}>ל-{plan.trialDays} ימים</Text>
                </HStack>
                {/* Then Regular Price */}
                <Text style={styles.thenPriceText}>
                  אז {plan.priceDisplay} {plan.period}
                </Text>
              </VStack>
            ) : (
              <VStack space="2xs">
                {/* Big Regular Price */}
                <HStack alignItems="baseline" space="xs">
                  <Text style={styles.planPrice}>{plan.priceDisplay}</Text>
                  <Text style={styles.planPeriod}>{plan.period}</Text>
                </HStack>
                {/* Per Month Price if applicable */}
                {plan.pricePerMonthDisplay && (
                  <Text style={styles.savingsText}>
                    {plan.pricePerMonthDisplay} לחודש • חיסכון {Math.round(plan.savingsPercent)}%
                  </Text>
                )}
              </VStack>
            )}
          </VStack>

          {/* Left Side: Radio Button */}
          <View style={[
            styles.radioButton,
            selected && styles.radioButtonSelected
          ]}>
            {selected && <Check size={18} color={Colors.white} strokeWidth={3} />}
          </View>
        </HStack>
      </Box>
    </Pressable>
  );
};

/**
 * Feature Item Component
 */
interface FeatureItemProps {
  text: string;
}

const FeatureItem: React.FC<FeatureItemProps> = ({ text }) => {
  return (
    <HStack space="sm" alignItems="center" style={styles.featureItem}>
      <Check size={16} color={Colors.success} strokeWidth={2.5} />
      <Text style={styles.featureText}>{text}</Text>
    </HStack>
  );
};

/**
 * Styles
 */
const styles = StyleSheet.create({
  // Hero Section
  heroSection: {
    backgroundColor: Colors.primary,
    borderBottomLeftRadius: 32,
    borderBottomRightRadius: 32,
  },
  heroTitle: {
    fontSize: 32,
    fontWeight: '800',
    color: Colors.white,
    textAlign: 'center',
    lineHeight: 40,
  },
  heroSubtitle: {
    fontSize: 16,
    color: Colors.white,
    opacity: 0.9,
    textAlign: 'center',
  },

  // Plan Cards
  planCard: {
    borderRadius: 20,
    padding: 20,
    position: 'relative',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.08,
    shadowRadius: 8,
    elevation: 3,
  },
  planCardSelected: {
    backgroundColor: Colors.secondaryLight,
    borderWidth: 2.5,
    borderColor: Colors.primary,
  },
  planCardUnselected: {
    backgroundColor: Colors.white,
    borderWidth: 1.5,
    borderColor: Colors.gray[300],
  },
  bestValueBadge: {
    position: 'absolute',
    top: -14,
    right: 16,
    backgroundColor: Colors.success,
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 20,
    zIndex: 10,
    shadowColor: Colors.success,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.3,
    shadowRadius: 4,
    elevation: 4,
  },
  bestValueText: {
    color: Colors.white,
    fontSize: 12,
    fontWeight: '800',
    letterSpacing: 0.3,
  },
  planTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: Colors.primary,
    textAlign: 'right',
    marginBottom: 6,
  },
  planPrice: {
    fontSize: 32,
    fontWeight: '900',
    color: Colors.textPrimary,
    textAlign: 'right',
    letterSpacing: -1,
  },
  planPeriod: {
    fontSize: 14,
    color: Colors.gray[600],
    textAlign: 'right',
    marginBottom: 4,
  },
  trialText: {
    fontSize: 13,
    color: Colors.textPrimary,
    textAlign: 'right',
    marginTop: 4,
  },
  thenPriceText: {
    fontSize: 14,
    color: Colors.gray[600],
    textAlign: 'right',
    marginTop: 4,
  },
  savingsText: {
    fontSize: 13,
    color: Colors.success,
    fontWeight: '700',
    textAlign: 'right',
    marginTop: 4,
  },

  // Radio Button
  radioButton: {
    width: 28,
    height: 28,
    borderRadius: 14,
    borderWidth: 2,
    borderColor: Colors.gray[400],
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: Colors.white,
  },
  radioButtonSelected: {
    backgroundColor: Colors.primary,
    borderColor: Colors.primary,
  },

  // Features
  featureItem: {
    paddingVertical: 6,
  },
  featureText: {
    fontSize: 14,
    color: Colors.textPrimary,
    textAlign: 'right',
    flex: 1,
    lineHeight: 20,
  },

  // Subscribe Button
  subscribeButton: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    height: 56,
    shadowColor: Colors.primary,
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 5,
    justifyContent: 'center',
    alignItems: 'center',
  },
  subscribeButtonText: {
    fontSize: 18,
    fontWeight: '800',
    color: Colors.white,
    letterSpacing: 0.3,
    textAlign: 'center',
  },
  subscribeButtonSuccess: {
    backgroundColor: Colors.success,
    shadowColor: Colors.success,
  },

  // Reassurance and Restore
  reassuranceText: {
    fontSize: 13,
    color: Colors.gray[600],
    textAlign: 'center',
    marginTop: 12,
    fontWeight: '500',
  },
  restoreButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  restoreText: {
    fontSize: 14,
    color: Colors.primary,
    fontWeight: '600',
  },
  logoutButton: {
    paddingVertical: 12,
    alignItems: 'center',
    marginTop: 8,
  },
  logoutText: {
    fontSize: 14,
    color: Colors.error,
    fontWeight: '600',
  },

  // Terms
  termsText: {
    fontSize: 11,
    color: Colors.gray[500],
    textAlign: 'center',
    marginTop: 16,
    lineHeight: 16,
    paddingHorizontal: 8,
  },
});

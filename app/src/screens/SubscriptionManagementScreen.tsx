import React, { useState, useEffect } from 'react';
import { ScrollView, Alert, Linking, Platform, Dimensions, Pressable, StyleSheet, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Image } from 'expo-image';
import { useNavigation } from '@react-navigation/native';
import {
  Box,
  VStack,
  HStack,
  Text,
  Button,
  ButtonText,
  Icon,
  Spinner,
  Heading,
  Divider,
  Badge,
  BadgeText,
} from '@gluestack-ui/themed';
import {
  Crown,
  Calendar,
  CreditCard,
  RefreshCw,
  ExternalLink,
  CheckCircle,
  XCircle,
  Clock,
  ArrowRight,
  Sparkles,
  ArrowLeft,
  X,
} from 'lucide-react-native';
import { useSubscription } from '../hooks/useSubscription';
import { PLAN_DETAILS } from '../config/revenuecat';
import { Colors } from '../config/colors';

const { width } = Dimensions.get('window');

/**
 * Subscription Management Screen
 * Shows current subscription status and allows changing plans
 */
export const SubscriptionManagementScreen: React.FC = () => {
  const navigation = useNavigation();
  const {
    subscriptionInfo,
    isLoading,
    error,
    isPremium,
    isInTrial,
    fetchSubscriptionStatus,
    getOfferings,
    purchaseSubscription,
    restorePurchases,
    clearError,
  } = useSubscription();

  const [refreshing, setRefreshing] = useState(false);
  const [changingPlan, setChangingPlan] = useState(false);

  // Refresh subscription status
  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchSubscriptionStatus();
    setRefreshing(false);
  };

  // Calculate days remaining
  const getDaysRemaining = (): number | null => {
    if (!subscriptionInfo?.expirationDate) return null;
    const now = new Date();
    const expiration = new Date(subscriptionInfo.expirationDate);
    const diff = expiration.getTime() - now.getTime();
    const days = Math.ceil(diff / (1000 * 60 * 60 * 24));
    return days > 0 ? days : 0;
  };

  const daysRemaining = getDaysRemaining();

  // Format date
  const formatDate = (date: Date | null): string => {
    if (!date) return '-';
    return new Date(date).toLocaleDateString('he-IL', {
      day: 'numeric',
      month: 'long',
      year: 'numeric',
    });
  };

  // Get status badge
  const getStatusBadge = () => {
    if (!subscriptionInfo) return null;

    const { status } = subscriptionInfo;

    if (status === 'trial') {
      return (
        <Badge action="success" variant="solid">
          <BadgeText>תקופת ניסיון</BadgeText>
        </Badge>
      );
    } else if (status === 'active') {
      return (
        <Badge action="success" variant="solid">
          <BadgeText>פעיל</BadgeText>
        </Badge>
      );
    } else if (status === 'expired') {
      return (
        <Badge action="error" variant="solid">
          <BadgeText>פג תוקף</BadgeText>
        </Badge>
      );
    } else {
      return (
        <Badge action="muted" variant="solid">
          <BadgeText>אין מנוי</BadgeText>
        </Badge>
      );
    }
  };

  // Get plan display name
  const getPlanName = (): string => {
    if (!subscriptionInfo?.period) return 'אין מנוי פעיל';

    if (subscriptionInfo.period === 'monthly') {
      return 'תוכנית חודשית';
    } else if (subscriptionInfo.period === 'quarterly') {
      return 'תוכנית 3 חודשים';
    }
    return 'תוכנית לא ידועה';
  };

  // Open subscription management
  const openSubscriptionManagement = async () => {
    if (Platform.OS === 'ios') {
      await Linking.openURL('https://apps.apple.com/account/subscriptions');
    } else if (Platform.OS === 'android') {
      await Linking.openURL(
        'https://play.google.com/store/account/subscriptions'
      );
    }
  };

  // Handle plan change
  const handleChangePlan = async () => {
    setChangingPlan(true);
    clearError();

    try {
      const offerings = await getOfferings();

      if (offerings.length === 0) {
        Alert.alert('שגיאה', 'לא נמצאו תוכניות זמינות');
        setChangingPlan(false);
        return;
      }

      // Determine which plan to offer
      const currentPeriod = subscriptionInfo?.period;
      let targetPlan = offerings[0]; // Default

      if (currentPeriod === 'monthly') {
        // User is on monthly, offer quarterly
        targetPlan = offerings.find(p => p.product.identifier.includes('quarterly')) || offerings[0];
      } else {
        // User is on quarterly or no plan, offer monthly
        targetPlan = offerings.find(p => p.product.identifier.includes('monthly')) || offerings[0];
      }

      Alert.alert(
        'שינוי תוכנית',
        `האם ברצונך לעבור ל${targetPlan.product.title}?`,
        [
          {
            text: 'ביטול',
            style: 'cancel',
          },
          {
            text: 'אישור',
            onPress: async () => {
              const success = await purchaseSubscription(targetPlan);
              if (success) {
                Alert.alert('הצלחה!', 'התוכנית שונתה בהצלחה');
                await fetchSubscriptionStatus();
              }
            },
          },
        ]
      );
    } catch (err) {
      console.error('Failed to change plan:', err);
    } finally {
      setChangingPlan(false);
    }
  };

  // Handle restore
  const handleRestore = async () => {
    const success = await restorePurchases();
    if (success) {
      Alert.alert('הצלחה!', 'המנוי שוחזר בהצלחה');
    }
  };

  return (
    <Box flex={1} bg="$white">
      <LinearGradient
        colors={[Colors.primary, '#0966D6', '#0856B9']}
        style={styles.gradient}
      >
        <ScrollView>
          <VStack p="$6" pb="$10">
            {/* Close Button - RTL so on the right */}
            <View style={styles.headerRow}>
              <View style={styles.spacer} />
              <Pressable
                style={({ pressed }) => [
                  styles.backButton,
                  pressed && styles.buttonPressed,
                ]}
                onPress={() => navigation.goBack()}
              >
                <Text style={styles.backIcon}>→</Text>
              </Pressable>
            </View>

            {/* Header */}
            <VStack space="md" alignItems="center">
              <Box style={styles.logoWrapper}>
                <Image
                  source={require('../../assets/logo2.png')}
                  style={styles.logo}
                  contentFit="contain"
                />
              </Box>
              <Text style={styles.title}>ניהול המנוי שלך</Text>
              <Text style={styles.subtitle}>
                {isPremium ? 'המנוי שלך פעיל ומאפשר לך גישה מלאה' :
                 subscriptionInfo?.status === 'expired' ? 'המנוי שלך פג - חדש את המנוי כדי להמשיך' :
                 'אין לך מנוי פעיל כרגע'}
              </Text>
            </VStack>

            {/* Current Plan Card */}
            {(isPremium || subscriptionInfo?.status === 'expired') && subscriptionInfo ? (
              <Box style={styles.planCard}>
                <VStack space="lg">
                  {/* Status Badge */}
                  <HStack justifyContent="space-between" alignItems="center">
                    <Text style={styles.planTitle}>{getPlanName()}</Text>
                    <Box style={
                      subscriptionInfo.status === 'expired' ? styles.expiredBadge :
                      isInTrial ? styles.trialBadge : styles.activeBadge
                    }>
                      <HStack space="xs" alignItems="center">
                        <Icon
                          as={subscriptionInfo.status === 'expired' ? XCircle :
                             isInTrial ? Sparkles : CheckCircle}
                          size="xs"
                          color={Colors.white}
                        />
                        <Text style={styles.badgeText}>
                          {subscriptionInfo.status === 'expired' ? 'פג תוקף' :
                           isInTrial ? 'תקופת ניסיון' : 'פעיל'}
                        </Text>
                      </HStack>
                    </Box>
                  </HStack>

                  <Divider bg="$borderLight200" />

                  {/* Subscription Details */}
                  <VStack space="md">
                    {/* Expiration Date */}
                    <HStack justifyContent="space-between" alignItems="center">
                      <HStack space="sm" alignItems="center">
                        <Icon as={Calendar} size="sm" color={Colors.primary} />
                        <Text style={styles.infoLabel}>תאריך תפוגה</Text>
                      </HStack>
                      <Text style={styles.infoValue}>
                        {formatDate(subscriptionInfo.expirationDate)}
                      </Text>
                    </HStack>

                    {/* Days Remaining */}
                    {daysRemaining !== null && (
                      <HStack justifyContent="space-between" alignItems="center">
                        <HStack space="sm" alignItems="center">
                          <Icon as={Clock} size="sm" color={Colors.primary} />
                          <Text style={styles.infoLabel}>זמן נותר</Text>
                        </HStack>
                        <Text style={[
                          styles.infoValue,
                          { color: daysRemaining < 7 ? Colors.error : Colors.success }
                        ]}>
                          {daysRemaining} ימים
                        </Text>
                      </HStack>
                    )}

                    {/* Auto Renewal */}
                    <HStack justifyContent="space-between" alignItems="center">
                      <HStack space="sm" alignItems="center">
                        <Icon
                          as={subscriptionInfo.willRenew ? CheckCircle : XCircle}
                          size="sm"
                          color={Colors.primary}
                        />
                        <Text style={styles.infoLabel}>חידוש אוטומטי</Text>
                      </HStack>
                      <Text style={[
                        styles.infoValue,
                        { color: subscriptionInfo.willRenew ? Colors.success : Colors.error }
                      ]}>
                        {subscriptionInfo.willRenew ? 'פעיל' : 'כבוי'}
                      </Text>
                    </HStack>
                  </VStack>

                  {/* Trial Info */}
                  {isInTrial && (
                    <Box style={styles.trialInfo}>
                      <HStack space="sm" alignItems="center">
                        <Icon as={Sparkles} size="sm" color={Colors.accent} />
                        <Text style={styles.trialInfoText}>
                          אתה בתקופת ניסיון של 3 ימים בחינם!
                        </Text>
                      </HStack>
                    </Box>
                  )}

                  {/* Expired Sandbox Info */}
                  {subscriptionInfo.status === 'expired' && subscriptionInfo.expirationDate && (
                    <Box style={styles.expiredInfo}>
                      <HStack space="sm" alignItems="center">
                        <Icon as={Clock} size="sm" color={Colors.error} />
                        <Text style={styles.expiredInfoText}>
                          המנוי פג תוקף. רכוש מנוי חדש כדי להמשיך.
                        </Text>
                      </HStack>
                    </Box>
                  )}
                </VStack>
              </Box>
            ) : (
              <Box style={styles.noPlanCard}>
                <VStack space="md" alignItems="center">
                  <Icon as={Crown} size="xl" color={Colors.lightGray} />
                  <Text style={styles.noPlanTitle}>אין מנוי פעיל</Text>
                  <Text style={styles.noPlanSubtitle}>
                    רכוש מנוי כדי לגשת לכל התכונות המדהימות
                  </Text>
                </VStack>
              </Box>
            )}

            {/* Action Buttons */}
            <VStack space="md" mt="$4">
              {/* Purchase New Subscription (for expired or no subscription) */}
              {!isPremium && (
                <Pressable
                  style={({ pressed }) => [
                    styles.purchaseButton,
                    pressed && styles.buttonPressed,
                  ]}
                  onPress={handleChangePlan}
                  disabled={changingPlan || isLoading}
                >
                  {changingPlan ? (
                    <Spinner color={Colors.white} />
                  ) : (
                    <HStack space="sm" alignItems="center">
                      <Icon as={Crown} size="sm" color={Colors.white} />
                      <Text style={styles.purchaseButtonText}>
                        {subscriptionInfo?.status === 'expired' ? 'חדש מנוי' : 'רכוש מנוי'}
                      </Text>
                    </HStack>
                  )}
                </Pressable>
              )}

              {/* Refresh Button */}
              <Pressable
                style={({ pressed }) => [
                  styles.outlineButton,
                  pressed && styles.buttonPressed,
                ]}
                onPress={handleRefresh}
                disabled={refreshing || isLoading}
              >
                {refreshing ? (
                  <Spinner color={Colors.white} />
                ) : (
                  <HStack space="sm" alignItems="center">
                    <Icon as={RefreshCw} size="sm" color={Colors.white} />
                    <Text style={styles.outlineButtonText}>רענן סטטוס</Text>
                  </HStack>
                )}
              </Pressable>

              {/* Manage in Store */}
              {isPremium && (
                <Pressable
                  style={({ pressed }) => [
                    styles.outlineButton,
                    pressed && styles.buttonPressed,
                  ]}
                  onPress={openSubscriptionManagement}
                >
                  <HStack space="sm" alignItems="center">
                    <Icon as={ExternalLink} size="sm" color={Colors.white} />
                    <Text style={styles.outlineButtonText}>
                      נהל ב-{Platform.OS === 'ios' ? 'App Store' : 'Play Store'}
                    </Text>
                  </HStack>
                </Pressable>
              )}

              {/* Restore Purchases */}
              <Box mt="$2">
                <Pressable
                  style={({ pressed }) => [
                    styles.linkButton,
                    pressed && styles.buttonPressed,
                  ]}
                  onPress={handleRestore}
                  disabled={isLoading}
                >
                  <Text style={styles.linkButtonText}>שחזר רכישות קודמות</Text>
                </Pressable>
              </Box>
            </VStack>

            {/* Error Message */}
            {error && (
              <Box style={styles.errorBox}>
                <Text style={styles.errorText}>{error}</Text>
              </Box>
            )}

            {/* Info Note */}
            <Box style={styles.infoNote}>
              <Text style={styles.infoNoteText}>
                לביטול או שינוי מנוי, עבור להגדרות {Platform.OS === 'ios' ? 'App Store' : 'Play Store'} במכשיר שלך.
              </Text>
            </Box>
          </VStack>
        </ScrollView>
      </LinearGradient>
    </Box>
  );
};

/**
 * Styles
 */
const styles = StyleSheet.create({
  gradient: {
    flex: 1,
    paddingTop: 20,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 16,
  },
  spacer: {
    width: 40,
  },
  backButton: {
    padding: 8,
  },
  backIcon: {
    fontSize: 32,
    color: Colors.white,
    fontWeight: 'bold',
  },
  logoWrapper: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    padding: 15,
  },
  logo: {
    width: '100%',
    height: '100%',
  },
  iconWrapper: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: Colors.white,
    textAlign: 'center',
    marginBottom: 8,
    writingDirection: 'rtl',
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    writingDirection: 'rtl',
  },
  planCard: {
    backgroundColor: Colors.white,
    borderRadius: 20,
    padding: 24,
    marginTop: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  noPlanCard: {
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    borderRadius: 20,
    padding: 32,
    marginTop: 24,
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.3)',
  },
  planTitle: {
    fontSize: 22,
    fontWeight: 'bold',
    color: Colors.textDark,
    writingDirection: 'rtl',
  },
  activeBadge: {
    backgroundColor: Colors.success,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  trialBadge: {
    backgroundColor: Colors.accent,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  expiredBadge: {
    backgroundColor: Colors.error,
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 12,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: Colors.white,
    writingDirection: 'rtl',
  },
  infoLabel: {
    fontSize: 15,
    color: Colors.textLight,
    writingDirection: 'rtl',
  },
  infoValue: {
    fontSize: 15,
    fontWeight: '600',
    color: Colors.textDark,
    writingDirection: 'rtl',
  },
  trialInfo: {
    backgroundColor: Colors.secondaryLight,
    padding: 16,
    borderRadius: 12,
    marginTop: 8,
  },
  trialInfoText: {
    fontSize: 14,
    color: Colors.primary,
    fontWeight: '500',
    writingDirection: 'rtl',
  },
  expiredInfo: {
    backgroundColor: 'rgba(244, 67, 54, 0.1)',
    padding: 16,
    borderRadius: 12,
    marginTop: 8,
    borderWidth: 1,
    borderColor: 'rgba(244, 67, 54, 0.3)',
  },
  expiredInfoText: {
    fontSize: 14,
    color: Colors.error,
    fontWeight: '500',
    writingDirection: 'rtl',
  },
  noPlanTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.white,
    textAlign: 'center',
    writingDirection: 'rtl',
  },
  noPlanSubtitle: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    writingDirection: 'rtl',
  },
  purchaseButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  purchaseButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.white,
    writingDirection: 'rtl',
  },
  outlineButton: {
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    borderWidth: 2,
    borderColor: 'rgba(255, 255, 255, 0.4)',
    paddingVertical: 14,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  outlineButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.white,
    writingDirection: 'rtl',
  },
  linkButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  linkButtonText: {
    fontSize: 15,
    color: 'rgba(255, 255, 255, 0.9)',
    textDecorationLine: 'underline',
    writingDirection: 'rtl',
  },
  buttonPressed: {
    opacity: 0.7,
  },
  errorBox: {
    backgroundColor: 'rgba(244, 67, 54, 0.15)',
    borderWidth: 1,
    borderColor: 'rgba(244, 67, 54, 0.3)',
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
  },
  errorText: {
    fontSize: 14,
    color: Colors.white,
    textAlign: 'center',
    writingDirection: 'rtl',
  },
  infoNote: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    padding: 16,
    borderRadius: 12,
    marginTop: 24,
  },
  infoNoteText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 20,
    writingDirection: 'rtl',
  },
});

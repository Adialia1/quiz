import React, { useState, useEffect } from 'react';
import { ScrollView, Alert, Linking, Platform } from 'react-native';
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
} from 'lucide-react-native';
import { useSubscription } from '../hooks/useSubscription';
import { PLAN_DETAILS } from '../config/revenuecat';

/**
 * Subscription Management Screen
 * Shows current subscription status and allows changing plans
 */
export const SubscriptionManagementScreen: React.FC = () => {
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
      <ScrollView>
        <VStack space="xl" p="$6" pb="$10">
          {/* Header */}
          <VStack space="md" alignItems="center" mt="$4">
            <Icon as={Crown} size="xl" color="$amber500" />
            <Heading size="2xl" textAlign="center" color="$textDark950">
              ניהול מנוי
            </Heading>
          </VStack>

          {/* Current Plan Card */}
          <Box
            bg={isPremium ? '$primary50' : '$backgroundLight100'}
            borderRadius="$2xl"
            p="$6"
            borderWidth={2}
            borderColor={isPremium ? '$primary500' : '$borderLight300'}
          >
            <VStack space="md">
              <HStack justifyContent="space-between" alignItems="center">
                <Text size="xl" fontWeight="$bold" color="$textDark950">
                  {getPlanName()}
                </Text>
                {getStatusBadge()}
              </HStack>

              <Divider />

              {/* Subscription Details */}
              {isPremium && subscriptionInfo && (
                <VStack space="sm">
                  {/* Expiration Date */}
                  <InfoRow
                    icon={Calendar}
                    label="תאריך תפוגה"
                    value={formatDate(subscriptionInfo.expirationDate)}
                  />

                  {/* Days Remaining */}
                  {daysRemaining !== null && (
                    <InfoRow
                      icon={Clock}
                      label="זמן נותר"
                      value={`${daysRemaining} ימים`}
                      valueColor={daysRemaining < 7 ? '$error600' : '$success600'}
                    />
                  )}

                  {/* Auto Renewal */}
                  <InfoRow
                    icon={subscriptionInfo.willRenew ? CheckCircle : XCircle}
                    label="חידוש אוטומטי"
                    value={subscriptionInfo.willRenew ? 'פעיל' : 'כבוי'}
                    valueColor={
                      subscriptionInfo.willRenew ? '$success600' : '$error600'
                    }
                  />

                  {/* Trial Status */}
                  {isInTrial && (
                    <Box bg="$amber100" p="$3" borderRadius="$lg" mt="$2">
                      <HStack space="sm" alignItems="center">
                        <Icon as={Clock} size="sm" color="$amber600" />
                        <Text color="$amber700" fontWeight="$medium">
                          אתה בתקופת ניסיון
                        </Text>
                      </HStack>
                    </Box>
                  )}
                </VStack>
              )}

              {/* No Subscription */}
              {!isPremium && (
                <VStack space="sm">
                  <Text color="$textLight600" textAlign="center">
                    אין לך מנוי פעיל כרגע
                  </Text>
                  <Text color="$textLight500" size="sm" textAlign="center">
                    רכוש מנוי כדי לגשת לכל התכונות
                  </Text>
                </VStack>
              )}
            </VStack>
          </Box>

          {/* Action Buttons */}
          <VStack space="md" mt="$4">
            {/* Refresh Button */}
            <Button
              variant="outline"
              borderColor="$borderLight300"
              onPress={handleRefresh}
              isDisabled={refreshing || isLoading}
            >
              {refreshing ? (
                <Spinner size="small" />
              ) : (
                <HStack space="sm" alignItems="center">
                  <Icon as={RefreshCw} size="sm" color="$primary500" />
                  <ButtonText color="$primary500">רענן סטטוס</ButtonText>
                </HStack>
              )}
            </Button>

            {/* Change Plan Button */}
            {isPremium && (
              <Button
                bg="$primary500"
                onPress={handleChangePlan}
                isDisabled={changingPlan || isLoading}
              >
                {changingPlan ? (
                  <Spinner color="$white" />
                ) : (
                  <ButtonText>שנה תוכנית</ButtonText>
                )}
              </Button>
            )}

            {/* Manage Subscription (App Store/Play Store) */}
            {isPremium && (
              <Button
                variant="outline"
                borderColor="$borderLight300"
                onPress={openSubscriptionManagement}
              >
                <HStack space="sm" alignItems="center">
                  <Icon as={ExternalLink} size="sm" color="$primary500" />
                  <ButtonText color="$primary500">
                    נהל ב-{Platform.OS === 'ios' ? 'App Store' : 'Play Store'}
                  </ButtonText>
                </HStack>
              </Button>
            )}

            {/* Restore Purchases */}
            <Button
              variant="link"
              onPress={handleRestore}
              isDisabled={isLoading}
            >
              <ButtonText color="$primary500" size="sm">
                שחזר רכישות קודמות
              </ButtonText>
            </Button>
          </VStack>

          {/* Error Message */}
          {error && (
            <Box bg="$error100" p="$3" borderRadius="$lg">
              <Text color="$error600" textAlign="center">
                {error}
              </Text>
            </Box>
          )}

          {/* Info */}
          <Box bg="$backgroundLight50" p="$4" borderRadius="$lg" mt="$4">
            <Text size="sm" color="$textLight600" textAlign="center">
              לביטול או שינוי מנוי, עבור להגדרות {Platform.OS === 'ios' ? 'App Store' : 'Play Store'}{' '}
              במכשיר שלך. שינויים יכנסו לתוקף בתום תקופת החיוב הנוכחית.
            </Text>
          </Box>
        </VStack>
      </ScrollView>
    </Box>
  );
};

/**
 * Info Row Component
 */
interface InfoRowProps {
  icon: any;
  label: string;
  value: string;
  valueColor?: string;
}

const InfoRow: React.FC<InfoRowProps> = ({
  icon,
  label,
  value,
  valueColor = '$textDark950',
}) => {
  return (
    <HStack justifyContent="space-between" alignItems="center">
      <HStack space="sm" alignItems="center">
        <Icon as={icon} size="sm" color="$textLight500" />
        <Text color="$textLight600">{label}</Text>
      </HStack>
      <Text fontWeight="$medium" color={valueColor}>
        {value}
      </Text>
    </HStack>
  );
};

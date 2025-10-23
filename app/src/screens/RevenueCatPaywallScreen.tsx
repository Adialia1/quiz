import React, { useEffect } from 'react';
import { View, StyleSheet, Alert, ActivityIndicator, Platform } from 'react-native';
import { Box, Text, VStack, Pressable } from '@gluestack-ui/themed';
import RevenueCatUI, { PAYWALL_RESULT } from 'react-native-purchases-ui';
import type { CustomerInfo } from 'react-native-purchases';
import Constants from 'expo-constants';
import { useClerk } from '@clerk/clerk-expo';
import { useAuthStore } from '../stores/authStore';
import { Colors } from '../config/colors';
import * as Device from 'expo-device';

const isExpoGo = Constants.appOwnership === 'expo';
const isSimulator = !Device.isDevice; // true if simulator/emulator

interface RevenueCatPaywallScreenProps {
  onComplete?: () => void;
  onSkip?: () => void;
  showSkip?: boolean;
}

/**
 * RevenueCat Paywall Screen
 * Uses RevenueCat's pre-built paywall UI configured from the dashboard
 */
export const RevenueCatPaywallScreen: React.FC<RevenueCatPaywallScreenProps> = ({
  onComplete,
  onSkip,
  showSkip = false,
}) => {
  const { signOut } = useClerk();
  const { logout } = useAuthStore();
  const [isLoading, setIsLoading] = React.useState(false);
  const [paywallError, setPaywallError] = React.useState(false);

  // Show development message in Expo Go OR Simulator with errors
  if (isExpoGo || (isSimulator && paywallError)) {
    return (
      <Box flex={1} bg="$white" p="$6" justifyContent="center">
        <VStack space="lg" alignItems="center">
          <Text fontSize="$2xl" fontWeight="$bold" textAlign="center" color={Colors.primary}>
            🔧 מצב פיתוח
          </Text>
          <Text fontSize="$lg" textAlign="center" color={Colors.textSecondary}>
            המנויים זמינים רק באפליקציה הסופית.{'\n'}
            לבינתיים, תוכל לדלג על שלב זה.
          </Text>
          <Text fontSize="$sm" textAlign="center" color={Colors.textSecondary} mt="$4">
            כדי לבדוק מנויים, בנה את האפליקציה עם:{'\n'}
            eas build --profile development
          </Text>

          <VStack space="md" w="100%" mt="$8">
            <Pressable
              style={styles.continueButton}
              onPress={() => onComplete?.()}
            >
              <Text style={styles.continueButtonText}>
                המשך לאפליקציה
              </Text>
            </Pressable>

            <Pressable
              onPress={async () => {
                try {
                  setIsLoading(true);
                  await logout();
                  await signOut();
                } catch (error) {
                  console.error('[LOGOUT] Error:', error);
                } finally {
                  setIsLoading(false);
                }
              }}
              disabled={isLoading}
              style={styles.logoutButton}
            >
              {isLoading ? (
                <ActivityIndicator size="small" color={Colors.error} />
              ) : (
                <Text style={styles.logoutText}>
                  התנתק מהחשבון
                </Text>
              )}
            </Pressable>
          </VStack>
        </VStack>
      </Box>
    );
  }

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
              console.log('[LOGOUT] User logged out from paywall screen');
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

  // Add error boundary to catch paywall loading errors
  useEffect(() => {
    const timer = setTimeout(() => {
      // If paywall hasn't loaded after 10 seconds, show error
      console.log('[PAYWALL] Checking paywall status after 10s...');
    }, 10000);

    return () => clearTimeout(timer);
  }, []);

  return (
    <View style={styles.container}>
      {/* RevenueCat Paywall - Managed from Dashboard */}
      <RevenueCatUI.Paywall
        onPurchaseStarted={() => {
          console.log('[PAYWALL] Purchase started');
        }}
        onPurchaseCompleted={({ customerInfo }: { customerInfo: CustomerInfo }) => {
          console.log('[PAYWALL] Purchase completed:', customerInfo);
          onComplete?.();
        }}
        onPurchaseError={({ error }: { error: any }) => {
          console.error('[PAYWALL] Purchase error:', error);
          console.error('[PAYWALL] Error code:', error?.code);
          console.error('[PAYWALL] Error message:', error?.message);
          console.error('[PAYWALL] Error details:', JSON.stringify(error, null, 2));
          console.error('[PAYWALL] User cancelled?', error?.userCancelled);

          // Don't show error for user cancellation
          if (error?.userCancelled) {
            return;
          }

          Alert.alert(
            'שגיאה',
            `שגיאה בביצוע הרכישה.\n\nפרטי שגיאה: ${error?.message || error?.code || 'לא ידוע'}\n\nקוד שגיאה: ${error?.code || 'N/A'}\n\nאנא נסה שוב.`
          );
        }}
        onRestoreStarted={() => {
          console.log('[PAYWALL] Restore started');
        }}
        onRestoreCompleted={({ customerInfo }: { customerInfo: CustomerInfo }) => {
          console.log('[PAYWALL] Restore completed:', customerInfo);

          // Check if user has active entitlement
          const hasActiveEntitlement = Object.keys(customerInfo.entitlements.active).length > 0;

          if (hasActiveEntitlement) {
            Alert.alert('הצלחה!', 'המנוי שוחזר בהצלחה');
            onComplete?.();
          } else {
            Alert.alert('אין מנויים', 'לא נמצאו רכישות קודמות לשחזור');
          }
        }}
        onRestoreError={({ error }: { error: any }) => {
          console.error('[PAYWALL] Restore error:', error);
          Alert.alert('שגיאה', 'שגיאה בשחזור רכישות. אנא נסה שוב.');
        }}
        onDismiss={() => {
          console.log('[PAYWALL] Dismissed - Logging out user');
          // When user clicks X, log them out
          handleLogout();
        }}
      />
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  continueButton: {
    backgroundColor: Colors.primary,
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
  },
  continueButtonText: {
    color: Colors.white,
    fontSize: 18,
    fontWeight: '600',
  },
  logoutButton: {
    paddingVertical: 12,
    alignItems: 'center',
  },
  logoutText: {
    fontSize: 14,
    color: Colors.error,
    fontWeight: '600',
  },
});

import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View, ActivityIndicator, StyleSheet, I18nManager, Platform, Text } from 'react-native';
import { Image } from 'expo-image';
import { SafeAreaProvider } from 'react-native-safe-area-context';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ClerkProvider, useAuth, useClerk } from '@clerk/clerk-expo';
import { GluestackUIProvider } from '@gluestack-ui/themed';
import { config } from './src/config/gluestack';
import { CLERK_PUBLISHABLE_KEY } from './src/config/clerk';
import { ForceRTL } from './src/config/rtlForce';
import { initializeRevenueCat } from './src/config/revenuecat';
import { useAuthStore } from './src/stores/authStore';
import { WelcomeScreen } from './src/screens/WelcomeScreen';
import { AuthScreen } from './src/screens/AuthScreen';
import { HomeScreen } from './src/screens/HomeScreen';
import { GuestHomeScreen } from './src/screens/GuestHomeScreen';
import { ExamScreen } from './src/screens/ExamScreen';
import { ExamReviewScreen } from './src/screens/ExamReviewScreen';
import { ExamHistoryScreen } from './src/screens/ExamHistoryScreen';
import { PracticeTopicSelectionScreen } from './src/screens/PracticeTopicSelectionScreen';
import { PracticeQuestionScreen } from './src/screens/PracticeQuestionScreen';
import { MistakeReviewSelectionScreen } from './src/screens/MistakeReviewSelectionScreen';
import { ChatHistoryScreen } from './src/screens/ChatHistoryScreen';
import { AIMentorChatScreen } from './src/screens/AIMentorChatScreen';
import { TopicSelectionScreen } from './src/screens/TopicSelectionScreen';
import { TopicDetailScreen } from './src/screens/TopicDetailScreen';
import { FlashcardStudyScreen } from './src/screens/FlashcardStudyScreen';
import { StarredConceptsScreen } from './src/screens/StarredConceptsScreen';
import { OnboardingScreen } from './src/screens/OnboardingScreen';
import { SubscriptionPlansScreen } from './src/screens/SubscriptionPlansScreen';
import { CustomPaywallScreen } from './src/screens/CustomPaywallScreen';
import { SubscriptionManagementScreen } from './src/screens/SubscriptionManagementScreen';
import { ChangePasswordScreen } from './src/screens/ChangePasswordScreen';
import { TermsAndConditionsScreen } from './src/screens/TermsAndConditionsScreen';
import { ProgressScreen } from './src/screens/ProgressScreen';
import { AdminScreen } from './src/screens/AdminScreen';
import { SettingsScreen } from './src/screens/SettingsScreen';
import { tokenCache } from './src/utils/tokenCache';
import { API_URL } from './src/config/api';
import { useAuth as useClerkAuth } from '@clerk/clerk-expo';
import { ErrorBoundary } from './src/components/ErrorBoundary';

// Disable console logs in production to prevent confusion during App Review
if (!__DEV__) {
  console.log = () => {};
  console.warn = () => {};
  console.debug = () => {};
  // Keep console.error for critical issues
}

// RTL is FORCED - app is Hebrew-only and always RTL
if (__DEV__) {
  console.log('[App.tsx] ===== RTL Configuration =====');
  console.log('[App.tsx] isRTL:', I18nManager.isRTL);
  console.log('[App.tsx] Layout direction:', I18nManager.isRTL ? 'RTL (Right-to-Left) ✅' : 'LTR (Left-to-Right) ⚠️');
  console.log('[App.tsx] RTL is FORCED for Hebrew-only app');
  console.log('[App.tsx] ====================================');
}

// Create stack navigator
const Stack = createNativeStackNavigator();

/**
 * Guest Stack - Limited screens for guest users
 * Only allows browsing topics and concepts (read-only learning content)
 */
function GuestStack({ onSignUp }: { onSignUp: () => void }) {
  return (
    <>
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen name="GuestHome">
          {(props) => <GuestHomeScreen {...props} onSignUp={onSignUp} />}
        </Stack.Screen>
        <Stack.Screen name="TopicSelection" component={TopicSelectionScreen} />
        <Stack.Screen name="TopicDetail" component={TopicDetailScreen} />
        <Stack.Screen name="FlashcardStudy" component={FlashcardStudyScreen} />
        <Stack.Screen name="StarredConcepts" component={StarredConceptsScreen} />
      </Stack.Navigator>
      <StatusBar style="dark" />
    </>
  );
}

/**
 * Auth Stack - Screens for unauthenticated users
 */
function AuthStack() {
  const [showWelcome, setShowWelcome] = useState(true);
  const [isGuest, setIsGuest] = useState(false);

  if (showWelcome) {
    return (
      <>
        <WelcomeScreen
          onGetStarted={() => setShowWelcome(false)}
          onContinueAsGuest={() => {
            setShowWelcome(false);
            setIsGuest(true);
          }}
        />
        <StatusBar style="light" />
      </>
    );
  }

  if (isGuest) {
    return (
      <GuestStack
        onSignUp={() => {
          setIsGuest(false);
          setShowWelcome(false);
        }}
      />
    );
  }

  return (
    <>
      <AuthScreen
        onAuthSuccess={() => {}}
        onBack={() => {
          setIsGuest(true);
          setShowWelcome(false);
        }}
      />
      <StatusBar style="dark" />
    </>
  );
}

/**
 * Main Stack - Screens for authenticated users
 */
function MainStack() {
  return (
    <>
      <Stack.Navigator
        screenOptions={{
          headerShown: false,
          animation: 'slide_from_right',
        }}
      >
        <Stack.Screen name="Home" component={HomeScreen} />
        <Stack.Screen name="Exam" component={ExamScreen} />
        <Stack.Screen name="ExamResults" component={ExamReviewScreen} />
        <Stack.Screen name="ExamHistory" component={ExamHistoryScreen} />
        <Stack.Screen name="PracticeTopicSelection" component={PracticeTopicSelectionScreen} />
        <Stack.Screen name="PracticeQuestion" component={PracticeQuestionScreen} />
        <Stack.Screen name="MistakeReviewSelection" component={MistakeReviewSelectionScreen} />
        <Stack.Screen name="ChatHistory" component={ChatHistoryScreen} />
        <Stack.Screen name="AIMentorChat" component={AIMentorChatScreen} />
        <Stack.Screen name="TopicSelection" component={TopicSelectionScreen} />
        <Stack.Screen name="TopicDetail" component={TopicDetailScreen} />
        <Stack.Screen name="FlashcardStudy" component={FlashcardStudyScreen} />
        <Stack.Screen name="StarredConcepts" component={StarredConceptsScreen} />
        <Stack.Screen name="SubscriptionPlans" component={SubscriptionPlansScreen} />
        <Stack.Screen name="SubscriptionManagement" component={SubscriptionManagementScreen} />
        <Stack.Screen name="ChangePassword" component={ChangePasswordScreen} />
        <Stack.Screen name="TermsAndConditions" component={TermsAndConditionsScreen} />
        <Stack.Screen name="Progress" component={ProgressScreen} />
        <Stack.Screen name="Admin" component={AdminScreen} />
        <Stack.Screen name="Settings" component={SettingsScreen} />
      </Stack.Navigator>
      <StatusBar style="dark" />
    </>
  );
}

/**
 * רכיב ניתוב ראשי
 * Main Navigation Component
 */
function AppContent() {
  const clerkAuth = useAuth();
  const { signOut } = useClerk();
  const { isAuthenticated, isLoading, hydrate, logout } = useAuthStore();
  const [showOnboarding, setShowOnboarding] = useState<boolean | null>(null); // null = checking
  const [showSubscriptionPaywall, setShowSubscriptionPaywall] = useState(false);
  const [isCheckingStatus, setIsCheckingStatus] = useState(true);

  // Safely get Clerk values with fallbacks
  const isSignedIn = clerkAuth?.isSignedIn ?? false;
  const clerkLoaded = clerkAuth?.isLoaded ?? false;
  const getToken = clerkAuth?.getToken ?? (async () => null);

  // טעינת מצב האימות מהאחסון
  useEffect(() => {
    const loadAuthState = async () => {
      try {
        await hydrate();
      } catch (error) {
        console.error('[App] Error hydrating auth state:', error);
        // Continue anyway - don't block app startup
      }
    };

    loadAuthState();
  }, []);

  // Initialize RevenueCat when user is authenticated
  useEffect(() => {
    const initRC = async () => {
      if (isSignedIn || isAuthenticated) {
        try {
          // Get Clerk user ID
          const token = await getToken();
          if (token) {
            // Decode JWT to get user ID (clerk_user_id is in the token)
            const base64Url = token.split('.')[1];
            const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/');
            const jsonPayload = decodeURIComponent(
              atob(base64)
                .split('')
                .map(c => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
                .join('')
            );
            const payload = JSON.parse(jsonPayload);
            const clerkUserId = payload.sub; // Clerk user ID is in 'sub' field

            console.log('[RevenueCat] Initializing with Clerk user ID:', clerkUserId);

            // Initialize RevenueCat with Clerk user ID
            await initializeRevenueCat(clerkUserId);
          } else {
            // Fallback: initialize without user ID
            console.log('[RevenueCat] No token available, initializing without user ID');
            await initializeRevenueCat();
          }
        } catch (error) {
          console.error('[RevenueCat] Error initializing:', error);
          // Fallback: initialize without user ID - don't block app
          try {
            await initializeRevenueCat();
          } catch (fallbackError) {
            console.error('[RevenueCat] Fallback initialization also failed:', fallbackError);
            // Continue without RevenueCat - don't crash the app
          }
        }
      }
    };

    initRC();
  }, [isSignedIn, isAuthenticated, getToken]);

  // Check if onboarding is completed and subscription status from API
  useEffect(() => {
    const checkUserStatus = async () => {
      console.log('[STATUS CHECK] Starting check...', { isSignedIn, isAuthenticated });

      // If user is NOT authenticated, clear all flags and show auth screen
      if (!isSignedIn && !isAuthenticated) {
        console.log('[STATUS CHECK] User not authenticated, clearing flags');
        setShowOnboarding(false);
        setShowSubscriptionPaywall(false);
        setIsCheckingStatus(false);
        return;
      }

      // User IS authenticated, check their status from database
      try {
        setIsCheckingStatus(true);

        // Get auth token from Clerk
        const token = await getToken();
        console.log('[STATUS CHECK] Token received:', token ? `${token.substring(0, 20)}...` : 'null/undefined');

        if (!token || token.trim() === '') {
          console.log('[STATUS CHECK] No valid token available');
          setIsCheckingStatus(false);
          return;
        }

        // Fetch user profile from API
        console.log('[STATUS CHECK] Fetching user profile from database...');
        const response = await fetch(`${API_URL}/api/users/me`, {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        });

        if (response.ok) {
          const userData = await response.json();
          console.log('[STATUS CHECK] ✅ Database response:', {
            onboarding_completed: userData.onboarding_completed,
            subscription_status: userData.subscription_status,
            is_admin: userData.is_admin,
          });

          // Admins bypass all subscription checks
          const isAdmin = userData.is_admin === true;

          // Check subscription status - user has active subscription or in trial
          const hasActiveSubscription =
            userData.subscription_status === 'active' ||
            userData.subscription_status === 'premium' ||
            userData.subscription_status === 'trial';

          // LOGIC:
          // 0. If user is admin → allow full access (bypass everything)
          // 1. If onboarding NOT completed → show onboarding
          // 2. If onboarding completed BUT no subscription → show paywall
          // 3. If onboarding completed AND has subscription → allow access to app

          if (isAdmin) {
            console.log('[STATUS CHECK] → 👑 Admin user - full access granted');
            setShowOnboarding(false);
            setShowSubscriptionPaywall(false);
          } else if (!userData.onboarding_completed) {
            console.log('[STATUS CHECK] → 🔵 Show onboarding (not completed in DB)');
            setShowOnboarding(true);
            setShowSubscriptionPaywall(false);
          } else if (!hasActiveSubscription) {
            console.log('[STATUS CHECK] → 💳 Show subscription paywall (no active subscription)');
            setShowOnboarding(false);
            setShowSubscriptionPaywall(true);
          } else {
            console.log('[STATUS CHECK] → ✅ Allow app access (onboarding done + subscription active)');
            setShowOnboarding(false);
            setShowSubscriptionPaywall(false);
          }
        } else {
          console.log('[STATUS CHECK] ❌ Failed to fetch user profile:', response.status);
          const errorText = await response.text();
          console.log('[STATUS CHECK] Error details:', errorText);

          // Session is invalid - log out the user and clear cache
          console.log('[STATUS CHECK] 🔄 Disconnected session detected - logging out...');
          await logout(); // Clear local storage
          await signOut(); // Clear Clerk session

          // Reset state to show auth screen
          setShowOnboarding(false);
          setShowSubscriptionPaywall(false);
        }
      } catch (error) {
        console.error('[STATUS CHECK] ❌ Error:', error);

        // Network error or other exception - DON'T log out, just skip this check
        // The user might be offline or the API might be temporarily down
        console.log('[STATUS CHECK] ⚠️  Network error - will retry on next mount');

        // Keep current auth state - don't force logout on network errors
      } finally {
        setIsCheckingStatus(false);
      }
    };

    checkUserStatus();
  }, [isSignedIn, isAuthenticated]);

  // אם Clerk או האפליקציה עדיין טוענים
  if (!clerkLoaded || isLoading || isCheckingStatus) {
    return (
      <View style={styles.loadingContainer}>
        <Image
          source={require('./assets/icon.png')}
          style={styles.loadingLogo}
          contentFit="contain"
          transition={200}
        />
        <ActivityIndicator size="large" color="#2196F3" style={styles.loadingSpinner} />
      </View>
    );
  }

  // Show onboarding if user just registered and onboarding not completed
  if ((isSignedIn || isAuthenticated) && showOnboarding === true) {
    return (
      <>
        <OnboardingScreen
          onComplete={async () => {
            console.log('[ONBOARDING] Complete callback triggered');
            setShowOnboarding(false);

            // Wait a bit for the database to update
            await new Promise(resolve => setTimeout(resolve, 500));

            // After onboarding, check subscription status
            const token = await getToken();
            if (token) {
              console.log('[ONBOARDING] Fetching updated user data...');
              const response = await fetch(`${API_URL}/api/users/me`, {
                headers: { 'Authorization': `Bearer ${token}` },
              });
              if (response.ok) {
                const userData = await response.json();
                console.log('[ONBOARDING] Updated user data:', {
                  onboarding_completed: userData.onboarding_completed,
                  subscription_status: userData.subscription_status,
                  is_admin: userData.is_admin,
                });

                // Admins bypass subscription check
                const isAdmin = userData.is_admin === true;

                const hasActiveSubscription =
                  userData.subscription_status === 'active' ||
                  userData.subscription_status === 'premium' ||
                  userData.subscription_status === 'trial';

                if (isAdmin) {
                  console.log('[ONBOARDING] Admin user - going to home');
                  setShowSubscriptionPaywall(false);
                } else if (!hasActiveSubscription) {
                  console.log('[ONBOARDING] Showing subscription paywall');
                  setShowSubscriptionPaywall(true);
                } else {
                  console.log('[ONBOARDING] User has subscription, going to home');
                }
              }
            }
          }}
        />
        <StatusBar style="dark" />
      </>
    );
  }

  // Show subscription paywall if no active subscription
  // ALWAYS show in Expo Go for testing (even without backend check)
  if ((isSignedIn || isAuthenticated) && (showSubscriptionPaywall || __DEV__)) {
    return (
      <>
        <CustomPaywallScreen
          onComplete={() => setShowSubscriptionPaywall(false)}
        />
        <StatusBar style="dark" />
      </>
    );
  }

  return (
    <NavigationContainer>
      {isSignedIn || isAuthenticated ? <MainStack /> : <AuthStack />}
    </NavigationContainer>
  );
}

/**
 * רכיב אפליקציה ראשי
 * Main App Component
 */
export default function App() {
  // Validate required configuration
  if (!CLERK_PUBLISHABLE_KEY) {
    console.error('[App] CRITICAL: CLERK_PUBLISHABLE_KEY is not set!');
    return (
      <View style={styles.loadingContainer}>
        <Text style={{ fontSize: 16, color: '#F44336', textAlign: 'center', padding: 20 }}>
          שגיאת תצורה:{'\n'}
          CLERK_PUBLISHABLE_KEY חסר
        </Text>
      </View>
    );
  }

  return (
    <SafeAreaProvider>
      <ErrorBoundary>
        <ClerkProvider
          publishableKey={CLERK_PUBLISHABLE_KEY}
          tokenCache={tokenCache}
        >
          <GluestackUIProvider config={config}>
            <AppContent />
          </GluestackUIProvider>
        </ClerkProvider>
      </ErrorBoundary>
    </SafeAreaProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#FFFFFF',
  },
  loadingLogo: {
    width: 180,
    height: 180,
    marginBottom: 32,
  },
  loadingSpinner: {
    marginTop: 16,
  },
});

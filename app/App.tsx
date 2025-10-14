import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View, ActivityIndicator, StyleSheet, I18nManager } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { ClerkProvider, useAuth } from '@clerk/clerk-expo';
import { GluestackUIProvider } from '@gluestack-ui/themed';
import { config } from './src/config/gluestack';
import { CLERK_PUBLISHABLE_KEY } from './src/config/clerk';
import { setupRTL } from './src/config/rtl';
import { useAuthStore } from './src/stores/authStore';
import { WelcomeScreen } from './src/screens/WelcomeScreen';
import { AuthScreen } from './src/screens/AuthScreen';
import { HomeScreen } from './src/screens/HomeScreen';
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
import { tokenCache } from './src/utils/tokenCache';
import { API_URL } from './src/config/api';
import { useAuth as useClerkAuth } from '@clerk/clerk-expo';

// הגדרת RTL בעת טעינת האפליקציה
setupRTL();

// Create stack navigator
const Stack = createNativeStackNavigator();

/**
 * Auth Stack - Screens for unauthenticated users
 */
function AuthStack() {
  const [showWelcome, setShowWelcome] = useState(true);

  if (showWelcome) {
    return (
      <>
        <WelcomeScreen onGetStarted={() => setShowWelcome(false)} />
        <StatusBar style="light" />
      </>
    );
  }

  return (
    <>
      <AuthScreen onAuthSuccess={() => {}} />
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
  const { isSignedIn, isLoaded: clerkLoaded } = useAuth();
  const { isAuthenticated, isLoading, hydrate } = useAuthStore();
  const [showOnboarding, setShowOnboarding] = useState(false);

  // טעינת מצב האימות מהאחסון
  useEffect(() => {
    hydrate();
  }, []);

  // Check if onboarding is completed from API
  useEffect(() => {
    const checkOnboarding = async () => {
      if (isSignedIn || isAuthenticated) {
        try {
          // Get auth token
          const token = await tokenCache.getToken('__clerk_client_jwt');
          if (!token) {
            console.log('No token available for onboarding check');
            setShowOnboarding(false);
            return;
          }

          // Fetch user profile from API
          const response = await fetch(`${API_URL}/api/users/me`, {
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          });

          if (response.ok) {
            const userData = await response.json();
            setShowOnboarding(!userData.onboarding_completed);
          } else {
            console.log('Failed to fetch user profile:', response.status);
            setShowOnboarding(false);
          }
        } catch (error) {
          console.error('Error checking onboarding status:', error);
          setShowOnboarding(false);
        }
      }
    };
    checkOnboarding();
  }, [isSignedIn, isAuthenticated]);

  // אם Clerk או האפליקציה עדיין טוענים
  if (!clerkLoaded || isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  // Show onboarding if user just registered
  if ((isSignedIn || isAuthenticated) && showOnboarding) {
    return (
      <>
        <OnboardingScreen onComplete={() => setShowOnboarding(false)} />
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
  return (
    <ClerkProvider
      publishableKey={CLERK_PUBLISHABLE_KEY}
      tokenCache={tokenCache}
    >
      <GluestackUIProvider config={config}>
        <AppContent />
      </GluestackUIProvider>
    </ClerkProvider>
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
});

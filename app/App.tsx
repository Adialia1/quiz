import React, { useEffect, useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { View, ActivityIndicator, StyleSheet, I18nManager } from 'react-native';
import { ClerkProvider, useAuth } from '@clerk/clerk-expo';
import { GluestackUIProvider } from '@gluestack-ui/themed';
import { config } from './src/config/gluestack';
import { CLERK_PUBLISHABLE_KEY } from './src/config/clerk';
import { setupRTL } from './src/config/rtl';
import { useAuthStore } from './src/stores/authStore';
import { WelcomeScreen } from './src/screens/WelcomeScreen';
import { AuthScreen } from './src/screens/AuthScreen';
import { HomeScreen } from './src/screens/HomeScreen';
import { tokenCache } from './src/utils/tokenCache';

// הגדרת RTL בעת טעינת האפליקציה
setupRTL();

/**
 * רכיב ניתוב ראשי
 * Main Navigation Component
 */
function AppContent() {
  const { isSignedIn, isLoaded: clerkLoaded } = useAuth();
  const { isAuthenticated, isLoading, hydrate } = useAuthStore();
  const [showWelcome, setShowWelcome] = useState(true);

  // טעינת מצב האימות מהאחסון
  useEffect(() => {
    hydrate();
  }, []);

  // אם Clerk או האפליקציה עדיין טוענים
  if (!clerkLoaded || isLoading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#2196F3" />
      </View>
    );
  }

  // אם המשתמש מחובר, הצג מסך ראשי
  if (isSignedIn || isAuthenticated) {
    return (
      <>
        <HomeScreen />
        <StatusBar style="dark" />
      </>
    );
  }

  // אם המשתמש לא מחובר
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

/**
 * Entry Point - RTL Configuration
 *
 * CRITICAL: This file initializes RTL BEFORE React loads
 * This ensures RTL works correctly in production builds
 */

import { I18nManager, Platform } from 'react-native';
import { registerRootComponent } from 'expo';
import App from './App';

// Force RTL for Hebrew - MUST be called before any React components render
if (!I18nManager.isRTL) {
  I18nManager.allowRTL(true);
  I18nManager.forceRTL(true);

  console.log('[RTL] Forcing RTL mode...');

  // In production, if RTL state changes, we need to reload
  // This is a React Native limitation
  if (Platform.OS === 'ios' || Platform.OS === 'android') {
    console.log('[RTL] ⚠️  RTL enabled. If layout is incorrect, completely CLOSE and REOPEN the app.');
  }
}

console.log('[RTL] Configuration:', {
  platform: Platform.OS,
  isRTL: I18nManager.isRTL,
  doLeftAndRightSwapInRTL: I18nManager.doLeftAndRightSwapInRTL,
});

// Register the main application component
registerRootComponent(App);

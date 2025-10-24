/**
 * Entry Point - Proper RTL Configuration
 *
 * Following React Native official RTL guidelines:
 * https://reactnative.dev/blog/2016/08/19/right-to-left-support-for-react-native-apps
 *
 * - allowRTL(true): Enables RTL layout when device language is RTL (Hebrew/Arabic)
 * - Layout automatically flips based on device language
 * - Components inherit RTL direction from parent
 */

import { I18nManager, Platform } from 'react-native';
import { registerRootComponent } from 'expo';
import App from './App';

// Enable RTL support - layout will flip automatically when device language is RTL
// This is the RECOMMENDED approach from React Native official docs
I18nManager.allowRTL(true);

// Note: Do NOT use forceRTL() in production - it's only for testing
// forceRTL() forces RTL even when device language is LTR, which breaks UX

console.log('[APP] ===== RTL ENABLED (Automatic) =====');
console.log('[APP] Platform:', Platform.OS);
console.log('[APP] isRTL:', I18nManager.isRTL);
console.log('[APP] allowRTL: true - Layout adapts to device language');
console.log('[APP] =====================================');

// Register the main application component
registerRootComponent(App);

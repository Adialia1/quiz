/**
 * Entry Point - FORCED RTL Configuration
 *
 * This app is Hebrew-only, so we ALWAYS force RTL regardless of device language.
 *
 * Why forceRTL?
 * - App content is 100% Hebrew
 * - Must be RTL even when device language is English
 * - Ensures consistent RTL behavior in production builds
 * - Matches Expo Go behavior which auto-detects Hebrew content
 */

import { I18nManager, Platform } from 'react-native';
import { registerRootComponent } from 'expo';
import App from './App';

// FORCE RTL - App is Hebrew-only and must always be RTL
I18nManager.allowRTL(true);
I18nManager.forceRTL(true);

console.log('[APP] ===== RTL FORCED (Hebrew-Only App) =====');
console.log('[APP] Platform:', Platform.OS);
console.log('[APP] allowRTL: true');
console.log('[APP] forceRTL: true');
console.log('[APP] isRTL:', I18nManager.isRTL);
console.log('[APP] Layout will ALWAYS be RTL');
console.log('[APP] ==========================================');

// Register the main application component
registerRootComponent(App);

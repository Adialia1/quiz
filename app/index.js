/**
 * Entry Point - RTL Configuration
 *
 * CRITICAL: This file initializes RTL BEFORE React loads
 * This ensures RTL works correctly in production builds
 */

import { I18nManager, Platform, NativeModules } from 'react-native';
import { registerRootComponent } from 'expo';
import App from './App';

// FORCE RTL - This is critical for Hebrew apps
// Must be set BEFORE any React components load
I18nManager.allowRTL(true);
I18nManager.forceRTL(true);

console.log('[RTL] ===== RTL INITIALIZATION =====');
console.log('[RTL] Platform:', Platform.OS);
console.log('[RTL] isRTL:', I18nManager.isRTL);
console.log('[RTL] allowRTL:', I18nManager.allowRTL);
console.log('[RTL] forceRTL:', I18nManager.forceRTL);
console.log('[RTL] doLeftAndRightSwapInRTL:', I18nManager.doLeftAndRightSwapInRTL);
console.log('[RTL] ==================================');

// Register the main application component
registerRootComponent(App);

/**
 * Entry Point - LTR Configuration
 *
 * RTL DISABLED - Using LTR mode
 */

import { I18nManager, Platform } from 'react-native';
import { registerRootComponent } from 'expo';
import App from './App';

// DISABLE RTL - Force LTR mode
I18nManager.allowRTL(false);
I18nManager.forceRTL(false);

console.log('[APP] ===== LTR MODE (RTL DISABLED) =====');
console.log('[APP] Platform:', Platform.OS);
console.log('[APP] isRTL:', I18nManager.isRTL);
console.log('[APP] RTL is DISABLED - using LTR mode');
console.log('[APP] =====================================');

// Register the main application component
registerRootComponent(App);

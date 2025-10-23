/**
 * Entry Point - LTR Configuration
 *
 * RTL DISABLED - Using LTR mode
 */

import { I18nManager, Platform } from 'react-native';
import { registerRootComponent } from 'expo';
import App from './App';

// ENABLE RTL - Force RTL mode for Hebrew
I18nManager.allowRTL(true);
I18nManager.forceRTL(true);

console.log('[APP] ===== RTL MODE ENABLED =====');
console.log('[APP] Platform:', Platform.OS);
console.log('[APP] isRTL:', I18nManager.isRTL);
console.log('[APP] RTL is ENABLED for Hebrew interface');
console.log('[APP] ==================================');

// Register the main application component
registerRootComponent(App);

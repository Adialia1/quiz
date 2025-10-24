/**
 * Entry Point - LTR Configuration
 *
 * RTL FULLY DISABLED - Using pure LTR mode
 * All RTL styling is handled manually in components
 */

import { I18nManager, Platform } from 'react-native';
import { registerRootComponent } from 'expo';
import App from './App';

// COMPLETELY DISABLE RTL at native level
// We will handle all RTL styling manually in components
I18nManager.allowRTL(false);
I18nManager.forceRTL(false);

// Ensure RTL is disabled
console.log('[APP] ===== RTL FULLY DISABLED =====');
console.log('[APP] Platform:', Platform.OS);
console.log('[APP] isRTL:', I18nManager.isRTL);
console.log('[APP] Using LTR mode - RTL handled manually in components');
console.log('[APP] ====================================');

// Register the main application component
registerRootComponent(App);

/**
 * Entry Point - LTR Configuration
 *
 * RTL DISABLED - Using LTR mode
 */

import { I18nManager, Platform } from 'react-native';
import { registerRootComponent } from 'expo';
import App from './App';

// Enable RTL support (but don't force it at native level)
// This allows RTL to work naturally without over-flipping the layout
I18nManager.allowRTL(true);

// Don't use forceRTL(true) - it causes layout issues in production builds
// Instead, we handle RTL at the component level

console.log('[APP] ===== RTL SUPPORT ENABLED =====');
console.log('[APP] Platform:', Platform.OS);
console.log('[APP] isRTL:', I18nManager.isRTL);
console.log('[APP] RTL allowed - handled at component level');
console.log('[APP] ====================================');

// Register the main application component
registerRootComponent(App);

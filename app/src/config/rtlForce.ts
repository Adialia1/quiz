import { I18nManager, Platform } from 'react-native';

/**
 * RTL Configuration for Expo
 *
 * IMPORTANT: I18nManager.forceRTL() does NOT work in Expo Go!
 * This is a known limitation - RTL only works in production builds (EAS)
 *
 * Solution: Use CSS-based RTL that works in both Expo Go and production
 */

export const ForceRTL = {
  /**
   * Initialize RTL configuration
   * In Expo Go: Will try to set but won't work
   * In Production: Will work correctly
   */
  async init() {
    try {
      console.log('🔄 RTL Configuration');
      console.log('  Platform:', Platform.OS);
      console.log('  I18nManager.isRTL:', I18nManager.isRTL);

      // Try to enable RTL (works in production builds only)
      I18nManager.allowRTL(true);
      I18nManager.forceRTL(true);

      if (I18nManager.isRTL) {
        console.log('✅ RTL enabled via I18nManager');
      } else {
        console.log('⚠️  I18nManager.forceRTL() not working (Expo Go limitation)');
        console.log('💡 Using CSS-based RTL instead');
      }
    } catch (error) {
      console.error('RTL initialization error:', error);
    }
  },

  /**
   * Get CSS-based RTL styles
   * These work in both Expo Go and production builds
   */
  getStyles() {
    return {
      // Container with RTL direction
      container: {
        direction: 'rtl' as const,
      },
      // RTL text alignment
      text: {
        textAlign: 'right' as const,
        writingDirection: 'rtl' as const,
      },
      // Reverse row layout for RTL
      row: {
        flexDirection: 'row-reverse' as const,
      },
      // Align items to end (right in RTL)
      alignStart: {
        alignItems: 'flex-end' as const,
      },
      // Align items to start (left in RTL)
      alignEnd: {
        alignItems: 'flex-start' as const,
      },
    };
  },

  /**
   * Check if app should use RTL
   * Always returns true for Hebrew app
   */
  isRTL() {
    return true;
  }
};
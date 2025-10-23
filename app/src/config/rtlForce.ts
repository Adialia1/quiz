import { I18nManager } from 'react-native';

/**
 * RTL Configuration Utilities
 *
 * NOTE: The actual RTL initialization happens in index.js BEFORE React loads
 * This file provides helper utilities for RTL layouts
 */

export const ForceRTL = {
  /**
   * Initialize RTL configuration (legacy - now handled in index.js)
   * Kept for backwards compatibility
   */
  async init() {
    // RTL is now initialized in index.js before React loads
    // This method is kept for backwards compatibility but does nothing
    console.log('[RTL] Already initialized in index.js');
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
import { I18nManager, ImageStyle } from 'react-native';

/**
 * RTL Configuration Utilities
 *
 * Following React Native official RTL guidelines:
 * https://reactnative.dev/blog/2016/08/19/right-to-left-support-for-react-native-apps
 *
 * NOTE: RTL is automatically enabled in index.js with I18nManager.allowRTL(true)
 * This file provides helper utilities for RTL-aware components
 */

export const RTL = {
  /**
   * Check if current layout is RTL
   * This reflects the device language setting
   */
  isRTL(): boolean {
    return I18nManager.isRTL;
  },

  /**
   * Get transform style to flip icons with directional meaning
   * Example: Back arrows, forward arrows, chevrons, etc.
   *
   * Usage:
   * <Image source={backIcon} style={RTL.flipIcon()} />
   */
  flipIcon(): ImageStyle {
    return {
      transform: [{ scaleX: I18nManager.isRTL ? -1 : 1 }]
    };
  },

  /**
   * Get text alignment based on RTL
   * Returns 'right' for RTL, 'left' for LTR
   */
  textAlign(): 'left' | 'right' {
    return I18nManager.isRTL ? 'right' : 'left';
  },

  /**
   * Get flex direction for rows
   * Returns 'row-reverse' for RTL, 'row' for LTR
   */
  flexDirection(): 'row' | 'row-reverse' {
    return I18nManager.isRTL ? 'row-reverse' : 'row';
  },

  /**
   * Get align items for start position
   * Returns 'flex-end' for RTL, 'flex-start' for LTR
   */
  alignStart(): 'flex-start' | 'flex-end' {
    return I18nManager.isRTL ? 'flex-end' : 'flex-start';
  },

  /**
   * Get align items for end position
   * Returns 'flex-start' for RTL, 'flex-end' for LTR
   */
  alignEnd(): 'flex-start' | 'flex-end' {
    return I18nManager.isRTL ? 'flex-start' : 'flex-end';
  },

  /**
   * Force RTL for testing purposes (requires app reload)
   * WARNING: Only use this for development testing!
   */
  forceRTL(enable: boolean): void {
    I18nManager.forceRTL(enable);
  },

  /**
   * Get writing direction
   */
  writingDirection(): 'rtl' | 'ltr' {
    return I18nManager.isRTL ? 'rtl' : 'ltr';
  }
};

// Legacy export for backwards compatibility
export const ForceRTL = {
  async init() {
    console.log('[RTL] Already initialized in index.js');
  },
  isRTL() {
    return I18nManager.isRTL;
  },
  getStyles() {
    return {
      container: {
        direction: RTL.writingDirection() as any,
      },
      text: {
        textAlign: RTL.textAlign(),
        writingDirection: RTL.writingDirection() as any,
      },
      row: {
        flexDirection: RTL.flexDirection(),
      },
      alignStart: {
        alignItems: RTL.alignStart(),
      },
      alignEnd: {
        alignItems: RTL.alignEnd(),
      },
    };
  }
};
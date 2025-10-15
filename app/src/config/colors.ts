/**
 * Quiz App Color Palette
 *
 * This file contains the official brand colors for the Quiz App.
 * Use these constants throughout the app for consistent theming.
 */

export const Colors = {
  // Primary Brand Colors
  primary: '#0A76F3',           // 💙 Main blue - Trust, knowledge, innovation
  primaryLight: '#E3F2FD',      // 🩵 Secondary light - Calm and focus
  success: '#3CCF4E',           // 🟢 Success green - Growth and progress
  accent: '#FFC107',            // 🟡 Gold accent - Motivation and achievement
  background: '#FFFFFF',        // ⚪ Background - Clean and breathable

  // Usage Guidelines:
  // - primary: Use for titles, icons, main action buttons
  // - primaryLight: Use for secondary sections, cards, unanswered questions
  // - success: Use for "Completed", "Passed", "Success" states
  // - accent: Use for key buttons like "Start Learning", "Save", "Submit Test"
  // - background: Main background color

  // System Colors
  warning: '#FF9800',
  error: '#F44336',
  info: '#0A76F3',

  // Neutral Colors
  white: '#FFFFFF',
  black: '#000000',
  textPrimary: '#212121',
  textSecondary: '#757575',
  textDark: '#212121',
  textLight: '#757575',
  lightGray: '#E0E0E0',
  secondaryLight: '#E3F2FD',
  gray: {
    50: '#FAFAFA',
    100: '#F5F5F5',
    200: '#EEEEEE',
    300: '#E0E0E0',
    400: '#BDBDBD',
    500: '#9E9E9E',
    600: '#757575',
    700: '#616161',
    800: '#424242',
    900: '#212121',
  },
} as const;

export type ColorType = typeof Colors;

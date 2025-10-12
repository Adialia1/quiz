import { createConfig } from '@gluestack-ui/themed';

/**
 * Quiz App Color Scheme
 *
 * Primary: #0A76F3 - Trust, knowledge, and innovation
 * Background: #FFFFFF - Clean and breathable
 * Secondary Light: #E3F2FD - Calm and focus
 * Success/Progress: #3CCF4E - Growth and progress
 * Accent/Highlight: #FFC107 - Motivation and achievement
 */
export const config = createConfig({
  aliases: {
    bg: 'backgroundColor',
    bgColor: 'backgroundColor',
    h: 'height',
    w: 'width',
    p: 'padding',
    px: 'paddingHorizontal',
    py: 'paddingVertical',
    pt: 'paddingTop',
    pb: 'paddingBottom',
    pr: 'paddingRight',
    pl: 'paddingLeft',
    m: 'margin',
    mx: 'marginHorizontal',
    my: 'marginVertical',
    mt: 'marginTop',
    mb: 'marginBottom',
    mr: 'marginRight',
    ml: 'marginLeft',
  },
  tokens: {
    colors: {
      // Brand Colors - Quiz App Theme
      primary: '#0A76F3',           // Main blue - titles, icons, main action buttons
      primaryLight: '#E3F2FD',      // Secondary light - cards, unanswered questions
      success: '#3CCF4E',           // Success green - completed, passed, success
      accent: '#FFC107',            // Gold accent - start learning, save, submit
      background: '#FFFFFF',        // Main background

      // Primary variations
      primary50: '#E3F2FD',
      primary100: '#BBDEFB',
      primary200: '#90CAF9',
      primary300: '#64B5F6',
      primary400: '#42A5F5',
      primary500: '#0A76F3',        // Main primary
      primary600: '#0966D6',
      primary700: '#0856B9',
      primary800: '#06469C',
      primary900: '#053680',

      // Success variations
      success50: '#E8F9EA',
      success100: '#C6F0CA',
      success200: '#9EE6A5',
      success300: '#76DC81',
      success400: '#55D366',
      success500: '#3CCF4E',        // Main success
      success600: '#35B945',
      success700: '#2DA03B',
      success800: '#268831',
      success900: '#1A6320',

      // Accent variations
      accent50: '#FFF8E1',
      accent100: '#FFECB3',
      accent200: '#FFE082',
      accent300: '#FFD54F',
      accent400: '#FFCA28',
      accent500: '#FFC107',        // Main accent
      accent600: '#FFB300',
      accent700: '#FFA000',
      accent800: '#FF8F00',
      accent900: '#FF6F00',

      // System colors
      warning: '#FF9800',
      error: '#F44336',
      info: '#0A76F3',

      // Neutral colors
      white: '#FFFFFF',
      black: '#000000',
      gray50: '#FAFAFA',
      gray100: '#F5F5F5',
      gray200: '#EEEEEE',
      gray300: '#E0E0E0',
      gray400: '#BDBDBD',
      gray500: '#9E9E9E',
      gray600: '#757575',
      gray700: '#616161',
      gray800: '#424242',
      gray900: '#212121',
    },
    space: {
      '0': 0,
      '1': 4,
      '2': 8,
      '3': 12,
      '4': 16,
      '5': 20,
      '6': 24,
      '7': 28,
      '8': 32,
      '9': 36,
      '10': 40,
      '12': 48,
      '16': 64,
      '20': 80,
      '24': 96,
      '32': 128,
    },
    fontSizes: {
      '2xs': 10,
      'xs': 12,
      'sm': 14,
      'md': 16,
      'lg': 18,
      'xl': 20,
      '2xl': 24,
      '3xl': 30,
      '4xl': 36,
      '5xl': 48,
      '6xl': 60,
    },
    fonts: {
      // Can add Hebrew fonts here
      heading: 'System',
      body: 'System',
      mono: 'System',
    },
  },
  // RTL support
  globalStyle: {
    direction: 'rtl',
  },
});

export type Config = typeof config;

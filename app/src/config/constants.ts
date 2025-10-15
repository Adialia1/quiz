/**
 * Application Constants
 * Global constants used throughout the app
 */

// API Configuration
export const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

// App Configuration
export const APP_NAME = 'קוויז מבחנים';
export const APP_VERSION = '1.0.0';

// Exam Configuration
export const PASSING_THRESHOLD = 85; // Minimum score to pass (85%)
export const MAX_EXAM_DURATION_MINUTES = 90; // Maximum exam duration

// Colors (matching brand colors from CLAUDE.md)
export const COLORS = {
  primary: '#0A76F3',
  background: '#FFFFFF',
  secondaryLight: '#E3F2FD',
  success: '#3CCF4E',
  accent: '#FFC107',
  warning: '#FF9800',
  error: '#F44336',
  info: '#0A76F3',
};

// Timeouts
export const API_TIMEOUT = 30000; // 30 seconds
export const UPLOAD_TIMEOUT = 120000; // 2 minutes for file uploads

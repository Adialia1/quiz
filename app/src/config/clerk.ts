/**
 * הגדרות Clerk
 * Clerk Configuration
 *
 * הוראות התקנה:
 * 1. צור חשבון ב-Clerk: https://clerk.com
 * 2. צור אפליקציה חדשה
 * 3. העתק את ה-Publishable Key
 * 4. הוסף את המפתח למטה
 * 5. הגדר את כתובות ה-Redirect URLs בלוח הבקרה של Clerk
 */

import Constants from 'expo-constants';

// Get Clerk key from Expo config (works in production builds)
export const CLERK_PUBLISHABLE_KEY = Constants.expoConfig?.extra?.clerkPublishableKey || '';

if (!CLERK_PUBLISHABLE_KEY) {
  console.error(
    '❌ אזהרה: CLERK_PUBLISHABLE_KEY לא הוגדר. ' +
    'הוסף את המפתח בקובץ .env או ב-app.json'
  );
}

/**
 * הגדרות נוספות של Clerk
 */
export const clerkConfig = {
  publishableKey: CLERK_PUBLISHABLE_KEY,
  // ניתן להוסיף הגדרות נוספות כאן
};

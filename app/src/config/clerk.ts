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

// הוסף את ה-Publishable Key שלך מ-Clerk Dashboard
export const CLERK_PUBLISHABLE_KEY = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY || '';

if (!CLERK_PUBLISHABLE_KEY) {
  console.warn(
    'אזהרה: CLERK_PUBLISHABLE_KEY לא הוגדר. ' +
    'הוסף את המפתח בקובץ .env או בקובץ זה.'
  );
}

/**
 * הגדרות נוספות של Clerk
 */
export const clerkConfig = {
  publishableKey: CLERK_PUBLISHABLE_KEY,
  // ניתן להוסיף הגדרות נוספות כאן
};

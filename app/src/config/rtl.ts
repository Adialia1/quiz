import { I18nManager, Platform } from 'react-native';

/**
 * הגדרות RTL (Right-to-Left) עבור האפליקציה
 * RTL Configuration for the application
 */
export const setupRTL = () => {
  // אפשר RTL
  I18nManager.allowRTL(true);

  // אכוף RTL
  I18nManager.forceRTL(true);

  // בדוק אם RTL מופעל
  console.log('RTL enabled:', I18nManager.isRTL);

  // אזהרה: שינויים ב-RTL דורשים הפעלה מחדש של האפליקציה
  if (!I18nManager.isRTL && Platform.OS !== 'web') {
    console.warn('RTL is not enabled. App restart may be required.');
  }
};

export const isRTL = I18nManager.isRTL;

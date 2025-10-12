import { TokenCache } from '@clerk/clerk-expo/dist/cache';
import { StorageUtils } from './storage';

/**
 * מטמון טוקנים עבור Clerk באמצעות AsyncStorage
 * Token cache for Clerk using AsyncStorage
 */
export const tokenCache: TokenCache = {
  async getToken(key: string) {
    try {
      return await StorageUtils.getString(key) || null;
    } catch (error) {
      console.error('שגיאה בקבלת טוקן:', error);
      return null;
    }
  },

  async saveToken(key: string, value: string) {
    try {
      await StorageUtils.setString(key, value);
    } catch (error) {
      console.error('שגיאה בשמירת טוקן:', error);
    }
  },

  async clearToken(key: string) {
    try {
      await StorageUtils.delete(key);
    } catch (error) {
      console.error('שגיאה במחיקת טוקן:', error);
    }
  },
};

import AsyncStorage from '@react-native-async-storage/async-storage';

/**
 * Fast local storage using AsyncStorage
 * Note: Using AsyncStorage for Expo Go compatibility
 * When building with EAS/bare workflow, can switch to MMKV for better performance
 */

// Storage keys
export const StorageKeys = {
  AUTH_TOKEN: 'auth_token',
  USER_DATA: 'user_data',
  IS_FIRST_LAUNCH: 'is_first_launch',
  LANGUAGE: 'language',
} as const;

/**
 * Helper functions for storage operations
 */
export const StorageUtils = {
  // Save string
  setString: async (key: string, value: string) => {
    try {
      await AsyncStorage.setItem(key, value);
    } catch (error) {
      console.error('Error saving string:', error);
    }
  },

  // Get string
  getString: async (key: string): Promise<string | undefined> => {
    try {
      return await AsyncStorage.getItem(key) || undefined;
    } catch (error) {
      console.error('Error getting string:', error);
      return undefined;
    }
  },

  // Save object as JSON
  setObject: async (key: string, value: object) => {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error saving object:', error);
    }
  },

  // Get object from JSON
  getObject: async <T>(key: string): Promise<T | undefined> => {
    try {
      const value = await AsyncStorage.getItem(key);
      return value ? JSON.parse(value) : undefined;
    } catch (error) {
      console.error('Error getting object:', error);
      return undefined;
    }
  },

  // Save boolean
  setBoolean: async (key: string, value: boolean) => {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error saving boolean:', error);
    }
  },

  // Get boolean
  getBoolean: async (key: string): Promise<boolean | undefined> => {
    try {
      const value = await AsyncStorage.getItem(key);
      return value ? JSON.parse(value) : undefined;
    } catch (error) {
      console.error('Error getting boolean:', error);
      return undefined;
    }
  },

  // Save number
  setNumber: async (key: string, value: number) => {
    try {
      await AsyncStorage.setItem(key, JSON.stringify(value));
    } catch (error) {
      console.error('Error saving number:', error);
    }
  },

  // Get number
  getNumber: async (key: string): Promise<number | undefined> => {
    try {
      const value = await AsyncStorage.getItem(key);
      return value ? JSON.parse(value) : undefined;
    } catch (error) {
      console.error('Error getting number:', error);
      return undefined;
    }
  },

  // Delete key
  delete: async (key: string) => {
    try {
      await AsyncStorage.removeItem(key);
    } catch (error) {
      console.error('Error deleting key:', error);
    }
  },

  // Clear all storage
  clearAll: async () => {
    try {
      await AsyncStorage.clear();
    } catch (error) {
      console.error('Error clearing storage:', error);
    }
  },

  // Check if key exists
  contains: async (key: string): Promise<boolean> => {
    try {
      const value = await AsyncStorage.getItem(key);
      return value !== null;
    } catch (error) {
      console.error('Error checking key:', error);
      return false;
    }
  },
};

/**
 * Notification utilities for study reminders
 * Uses Expo Notifications for local scheduled notifications
 *
 * NOTE: Notifications don't work in Expo Go on SDK 53+
 * Need development build for full functionality
 */
import { Platform } from 'react-native';

// Try to import expo-notifications - it won't work in Expo Go
let Notifications: any = null;
let Device: any = null;
let AndroidImportance: any = null;

try {
  Notifications = require('expo-notifications');
  Device = require('expo-device');
  AndroidImportance = Notifications?.AndroidImportance;

  // Configure notification behavior (only if available)
  if (Notifications?.setNotificationHandler) {
    Notifications.setNotificationHandler({
      handleNotification: async () => ({
        shouldShowBanner: true,
        shouldShowList: true,
        shouldPlaySound: true,
        shouldSetBadge: true,
      }),
    });
  }
} catch (error) {
  console.warn('[Notifications] expo-notifications not available (Expo Go limitation)');
}

/**
 * Get Expo push token for server-side notifications
 * Returns token string or null if failed
 */
export async function getExpoPushToken(): Promise<string | null> {
  if (!Notifications || !Device) {
    console.warn('[Notifications] Not available in Expo Go');
    return null;
  }

  if (!Device.isDevice) {
    console.log('Push tokens only work on physical devices');
    return null;
  }

  // Use the project ID from app.json
  const projectId = 'c4d773b3-b1ec-40d7-9c5c-6d8af489b238';

  try {
    const token = await Notifications.getExpoPushTokenAsync({
      projectId,
    });
    console.log('Expo Push Token:', token.data);
    return token.data;
  } catch (error) {
    console.error('Error getting push token:', error);
    return null;
  }
}

/**
 * Request notification permissions
 * Returns object with granted status and push token
 */
export async function requestNotificationPermissions(): Promise<{ granted: boolean; pushToken: string | null }> {
  if (!Notifications || !Device) {
    console.warn('[Notifications] Not available in Expo Go - returning mock success');
    return { granted: true, pushToken: null };
  }

  if (!Device.isDevice) {
    console.log('Notifications only work on physical devices');
    return { granted: false, pushToken: null };
  }

  try {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;

    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }

    if (finalStatus !== 'granted') {
      console.log('Notification permission denied');
      return { granted: false, pushToken: null };
    }

    // Configure Android notification channel
    if (Platform.OS === 'android' && AndroidImportance) {
      await Notifications.setNotificationChannelAsync('study-reminders', {
        name: 'תזכורות לימוד',
        description: 'תזכורות יומיות ללמוד למבחן',
        importance: AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#0A76F3',
        sound: 'default',
      });
    }

    // Get push token for server-side notifications
    const pushToken = await getExpoPushToken();

    return { granted: true, pushToken };
  } catch (error) {
    console.error('[Notifications] Error requesting permissions:', error);
    return { granted: false, pushToken: null };
  }
}

/**
 * Schedule daily study reminder notifications
 * @param hours - Array of hours (0-23) to send notifications
 * Example: [8, 18] = 8 AM and 6 PM
 */
export async function scheduleStudyReminders(hours: number[]): Promise<void> {
  if (!Notifications) {
    console.warn('[Notifications] Scheduling not available in Expo Go');
    return;
  }

  try {
    // Cancel all existing notifications first
    await Notifications.cancelAllScheduledNotificationsAsync();

    // Schedule notification for each hour
    for (const hour of hours) {
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'זמן ללמוד! 📚',
          body: 'הגיע הזמן להתכונן למבחן שלך',
          data: { type: 'study_reminder' },
          sound: 'default',
        },
        trigger: {
          hour,
          minute: 0,
          repeats: true,
        },
      });

      console.log(`Scheduled daily reminder at ${hour}:00`);
    }
  } catch (error) {
    console.error('[Notifications] Error scheduling reminders:', error);
  }
}

/**
 * Schedule exam countdown notification
 * @param examDate - Date of the exam
 */
export async function scheduleExamReminder(examDate: Date): Promise<void> {
  if (!Notifications) {
    console.warn('[Notifications] Scheduling not available in Expo Go');
    return;
  }

  try {
    const now = new Date();
    const daysUntilExam = Math.ceil((examDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

    // Schedule reminders for 7 days, 3 days, 1 day before
    const reminderDays = [7, 3, 1];

    for (const days of reminderDays) {
      if (daysUntilExam > days) {
        const triggerDate = new Date(examDate);
        triggerDate.setDate(examDate.getDate() - days);
        triggerDate.setHours(9, 0, 0, 0); // 9 AM

        await Notifications.scheduleNotificationAsync({
          content: {
            title: `המבחן בעוד ${days} ימים! 🎯`,
            body: 'זכור להתכונן היטב ולחזור על החומר',
            data: { type: 'exam_countdown', daysUntil: days },
            sound: 'default',
          },
          trigger: { type: 'date', date: triggerDate } as any,
        });

        console.log(`Scheduled exam reminder for ${days} days before`);
      }
    }

    // Schedule notification on exam day
    const examDayTime = new Date(examDate);
    examDayTime.setHours(7, 0, 0, 0); // 7 AM on exam day

    if (examDayTime > now) {
      await Notifications.scheduleNotificationAsync({
        content: {
          title: 'המבחן היום! 🚀',
          body: 'בהצלחה! אתה מוכן 💪',
          data: { type: 'exam_day' },
          sound: 'default',
        },
        trigger: { type: 'date', date: examDayTime } as any,
      });

      console.log('Scheduled exam day notification');
    }
  } catch (error) {
    console.error('[Notifications] Error scheduling exam reminders:', error);
  }
}

/**
 * Cancel all scheduled notifications
 */
export async function cancelAllNotifications(): Promise<void> {
  if (!Notifications) {
    console.warn('[Notifications] Not available in Expo Go');
    return;
  }

  try {
    await Notifications.cancelAllScheduledNotificationsAsync();
    console.log('Cancelled all notifications');
  } catch (error) {
    console.error('[Notifications] Error cancelling notifications:', error);
  }
}

/**
 * Get all scheduled notifications (for debugging)
 */
export async function getScheduledNotifications() {
  if (!Notifications) {
    console.warn('[Notifications] Not available in Expo Go');
    return [];
  }

  try {
    const scheduled = await Notifications.getAllScheduledNotificationsAsync();
    console.log('Scheduled notifications:', scheduled);
    return scheduled;
  } catch (error) {
    console.error('[Notifications] Error getting scheduled notifications:', error);
    return [];
  }
}

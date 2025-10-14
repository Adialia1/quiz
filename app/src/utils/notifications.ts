/**
 * Notification utilities for study reminders
 * Uses Expo Notifications for local scheduled notifications
 */
import * as Notifications from 'expo-notifications';
import * as Device from 'expo-device';
import { Platform } from 'react-native';

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowBanner: true,
    shouldShowList: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
  }),
});

/**
 * Get Expo push token for server-side notifications
 * Returns token string or null if failed
 */
export async function getExpoPushToken(): Promise<string | null> {
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
  if (!Device.isDevice) {
    console.log('Notifications only work on physical devices');
    return { granted: false, pushToken: null };
  }

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
  if (Platform.OS === 'android') {
    await Notifications.setNotificationChannelAsync('study-reminders', {
      name: 'תזכורות לימוד',
      description: 'תזכורות יומיות ללמוד למבחן',
      importance: Notifications.AndroidImportance.HIGH,
      vibrationPattern: [0, 250, 250, 250],
      lightColor: '#0A76F3',
      sound: 'default',
    });
  }

  // Get push token for server-side notifications
  const pushToken = await getExpoPushToken();

  return { granted: true, pushToken };
}

/**
 * Schedule daily study reminder notifications
 * @param hours - Array of hours (0-23) to send notifications
 * Example: [8, 18] = 8 AM and 6 PM
 */
export async function scheduleStudyReminders(hours: number[]): Promise<void> {
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
}

/**
 * Schedule exam countdown notification
 * @param examDate - Date of the exam
 */
export async function scheduleExamReminder(examDate: Date): Promise<void> {
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
}

/**
 * Cancel all scheduled notifications
 */
export async function cancelAllNotifications(): Promise<void> {
  await Notifications.cancelAllScheduledNotificationsAsync();
  console.log('Cancelled all notifications');
}

/**
 * Get all scheduled notifications (for debugging)
 */
export async function getScheduledNotifications() {
  const scheduled = await Notifications.getAllScheduledNotificationsAsync();
  console.log('Scheduled notifications:', scheduled);
  return scheduled;
}

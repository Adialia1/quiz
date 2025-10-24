import React, { useState } from 'react';
import { StyleSheet, SafeAreaView, StatusBar, View, Text, Pressable, ScrollView, Platform, Alert } from 'react-native';
import { Image } from 'expo-image';
import DateTimePicker from '@react-native-community/datetimepicker';
import * as Notifications from 'expo-notifications';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';
import { StorageUtils } from '../utils/storage';
import { requestNotificationPermissions } from '../utils/notifications';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000';

interface OnboardingScreenProps {
  onComplete: () => void;
}

/**
 * Onboarding Screen - Multi-page flow for new users
 *
 * Flow:
 * 1. Welcome
 * 2. Exam date selection
 * 3. Study time selection
 * 4. Notification permission request
 * 5. Complete
 */
export const OnboardingScreen: React.FC<OnboardingScreenProps> = ({ onComplete }) => {
  const { getToken } = useAuth();

  const [currentPage, setCurrentPage] = useState(0);
  const [examDate, setExamDate] = useState(new Date());
  const [showDatePicker, setShowDatePicker] = useState(false);
  const [selectedHours, setSelectedHours] = useState<number[]>([]);

  // Study time options
  const studyTimes = [
    { hour: 6, label: '06:00', emoji: '🌅' },
    { hour: 7, label: '07:00', emoji: '🌄' },
    { hour: 8, label: '08:00', emoji: '☀️' },
    { hour: 9, label: '09:00', emoji: '☕' },
    { hour: 12, label: '12:00', emoji: '🌞' },
    { hour: 14, label: '14:00', emoji: '📖' },
    { hour: 16, label: '16:00', emoji: '📚' },
    { hour: 18, label: '18:00', emoji: '🌇' },
    { hour: 20, label: '20:00', emoji: '🌙' },
    { hour: 21, label: '21:00', emoji: '⭐' },
    { hour: 22, label: '22:00', emoji: '🌃' },
  ];

  const toggleHour = (hour: number) => {
    setSelectedHours(prev =>
      prev.includes(hour)
        ? prev.filter(h => h !== hour)
        : [...prev, hour]
    );
  };

  const handleNext = async () => {
    if (currentPage === 0) {
      // Welcome -> Exam Date
      setCurrentPage(1);
    } else if (currentPage === 1) {
      // Exam Date -> Study Times
      if (examDate <= new Date()) {
        Alert.alert('שגיאה', 'תאריך המבחן חייב להיות בעתיד');
        return;
      }
      setCurrentPage(2);
    } else if (currentPage === 2) {
      // Study Times -> Notifications
      if (selectedHours.length === 0) {
        Alert.alert('שגיאה', 'בחר לפחות שעה אחת');
        return;
      }
      setCurrentPage(3);
    } else if (currentPage === 3) {
      // Request permissions and complete
      await handleComplete();
    }
  };

  const handleComplete = async () => {
    console.log('🟢 Starting onboarding completion...');
    try {
      // Request notification permissions and get push token
      console.log('🔔 Requesting notification permissions...');
      const { granted, pushToken } = await requestNotificationPermissions();

      console.log('✅ Notification permission granted:', granted);
      console.log('✅ Push token:', pushToken ? pushToken.substring(0, 20) + '...' : 'null');

      // Note: We don't schedule local notifications here anymore
      // The server will send push notifications based on user's schedule
      // This prevents immediate notifications during onboarding

      // Save to database
      console.log('🔐 Getting auth token...');
      const token = await getToken();

      if (!token) {
        console.log('❌ No auth token found');
        Alert.alert('שגיאה', 'לא נמצא טוקן אימות. נא להתחבר מחדש.');
        return;
      }

      console.log('✅ Token obtained');

      const requestData = {
        exam_date: examDate.toISOString().split('T')[0], // YYYY-MM-DD format
        study_hours: selectedHours,
        expo_push_token: pushToken,
        notification_preferences: {
          study_reminders_enabled: true,
          exam_countdown_enabled: true,
          achievement_notifications_enabled: true,
        }
      };

      console.log('📡 Sending onboarding data to:', `${API_URL}/api/users/me/onboarding`);
      console.log('📦 Request data:', {
        exam_date: requestData.exam_date,
        study_hours: requestData.study_hours,
        expo_push_token: requestData.expo_push_token ? 'SET' : 'NULL',
        notification_preferences: requestData.notification_preferences,
      });

      const response = await fetch(`${API_URL}/api/users/me/onboarding`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      console.log('📊 Response status:', response.status);

      if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
        console.error('❌ API Error Response:', error);
        console.error('❌ Response Status:', response.status);
        throw new Error(error.detail || `Failed to save onboarding data (Status: ${response.status})`);
      }

      console.log('✅ Onboarding data saved to server');

      // Also save locally (for offline access)
      console.log('💾 Saving onboarding data locally...');
      await StorageUtils.setBoolean('onboarding_completed', true);
      await StorageUtils.setString('exam_date', examDate.toISOString());
      await StorageUtils.setString('study_hours', JSON.stringify(selectedHours));
      console.log('✅ Local data saved');

      // Show success notification
      if (granted) {
        console.log('🔔 Scheduling welcome notification...');
        // Send a single welcome notification
        await Notifications.scheduleNotificationAsync({
          content: {
            title: 'הכל מוכן! 🎉',
            body: 'התזכורות שלך הוגדרו בהצלחה',
            data: { type: 'onboarding_complete' },
            sound: 'default',
          },
          trigger: null, // Send immediately
        });
        console.log('✅ Welcome notification scheduled');
      }

      // Complete onboarding
      console.log('✅ Onboarding completed successfully');
      onComplete();
    } catch (error: any) {
      console.error('❌ Error completing onboarding:', error);
      console.error('❌ Error message:', error.message);
      console.error('❌ Error stack:', error.stack);

      const errorMessage = error.message || 'אירעה שגיאה בהשלמת ההרשמה';
      Alert.alert('שגיאה', errorMessage + '\nנסה שוב.');
    } finally {
      console.log('🏁 handleComplete completed');
    }
  };

  const handleSkip = () => {
    Alert.alert(
      'דלג על הגדרות',
      'האם אתה בטוח? תוכל להגדיר תזכורות מאוחר יותר מההגדרות',
      [
        { text: 'ביטול', style: 'cancel' },
        {
          text: 'דלג',
          style: 'destructive',
          onPress: async () => {
            await StorageUtils.setBoolean('onboarding_completed', true);
            onComplete();
          }
        },
      ]
    );
  };

  const onDateChange = (event: any, selectedDate?: Date) => {
    // On Android, hide picker after selection or dismissal
    // On iOS, keep picker visible (inline display)
    if (Platform.OS === 'android') {
      setShowDatePicker(false);
    }

    // Update date only if user selected a date (not dismissed)
    if (event.type === 'set' && selectedDate) {
      setExamDate(selectedDate);
    }
  };

  // Page 0: Welcome
  const renderWelcome = () => (
    <View style={styles.pageContainer}>
      <Image
        source={require('../../assets/logo_blue.png')}
        style={styles.logoLarge}
        contentFit="contain"
      />
      <Text style={styles.welcomeTitle}>ברוכים הבאים! 👋</Text>
      <Text style={styles.welcomeText}>
        בואו נגדיר את האפליקציה כדי שתוכל להתכונן בצורה הטובה ביותר למבחן שלך
      </Text>
      <View style={styles.featureList}>
        <View style={styles.featureItem}>
          <Text style={styles.featureEmoji}>📅</Text>
          <Text style={styles.featureText}>הגדר תאריך מבחן</Text>
        </View>
        <View style={styles.featureItem}>
          <Text style={styles.featureEmoji}>⏰</Text>
          <Text style={styles.featureText}>קבל תזכורות יומיות</Text>
        </View>
        <View style={styles.featureItem}>
          <Text style={styles.featureEmoji}>📊</Text>
          <Text style={styles.featureText}>עקוב אחר ההתקדמות</Text>
        </View>
      </View>
    </View>
  );

  // Page 1: Exam Date
  const renderExamDate = () => (
    <View style={styles.pageContainer}>
      <Text style={styles.questionTitle}>מתי המבחן שלך? 📅</Text>
      <Text style={styles.questionSubtitle}>
        נשלח לך תזכורות לפני המבחן
      </Text>

      <Pressable onPress={() => setShowDatePicker(true)} style={styles.dateButton}>
        <Text style={styles.dateButtonText}>
          {examDate.toLocaleDateString('he-IL', {
            year: 'numeric',
            month: 'long',
            day: 'numeric',
          })}
        </Text>
        <Text style={styles.dateButtonIcon}>📅</Text>
      </Pressable>

      {showDatePicker && (
        <DateTimePicker
          value={examDate}
          mode="date"
          display={Platform.OS === 'ios' ? 'spinner' : 'default'}
          onChange={onDateChange}
          minimumDate={new Date()}
          locale="he-IL"
        />
      )}
    </View>
  );

  // Page 2: Study Times
  const renderStudyTimes = () => (
    <View style={styles.pageContainer}>
      <Text style={styles.questionTitle}>באיזה שעות תרצה ללמוד? ⏰</Text>
      <Text style={styles.questionSubtitle}>
        בחר את השעות שבהן נשלח לך תזכורת
      </Text>

      <ScrollView style={styles.timesContainer} showsVerticalScrollIndicator={false}>
        <View style={styles.timesGrid}>
          {studyTimes.map(({ hour, label, emoji }) => (
            <Pressable
              key={hour}
              onPress={() => toggleHour(hour)}
              style={[
                styles.timeButton,
                selectedHours.includes(hour) && styles.timeButtonSelected
              ]}
            >
              <Text style={styles.timeEmoji}>{emoji}</Text>
              <Text
                style={[
                  styles.timeLabel,
                  selectedHours.includes(hour) && styles.timeLabelSelected
                ]}
              >
                {label}
              </Text>
            </Pressable>
          ))}
        </View>
      </ScrollView>

      {selectedHours.length > 0 && (
        <View style={styles.selectedCount}>
          <Text style={styles.selectedCountText}>
            נבחרו {selectedHours.length} שעות
          </Text>
        </View>
      )}
    </View>
  );

  // Page 3: Notifications Permission
  const renderNotifications = () => (
    <View style={styles.pageContainer}>
      <Text style={styles.questionTitle}>אפשר התראות 🔔</Text>
      <Text style={styles.questionSubtitle}>
        כדי לקבל תזכורות, נצטרך הרשאה להתראות
      </Text>

      <View style={styles.permissionBox}>
        <Text style={styles.permissionIcon}>📱</Text>
        <Text style={styles.permissionTitle}>למה אנחנו צריכים הרשאות?</Text>
        <Text style={styles.permissionText}>
          • תזכורות יומיות ללימוד{'\n'}
          • ספירה לאחור למבחן{'\n'}
          • עדכונים על התקדמות{'\n'}
          • אפשר לבטל בכל רגע
        </Text>
      </View>
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      {/* Progress Indicator */}
      <View style={styles.progressContainer}>
        {[0, 1, 2, 3].map((page) => (
          <View
            key={page}
            style={[
              styles.progressDot,
              page === currentPage && styles.progressDotActive,
              page < currentPage && styles.progressDotCompleted,
            ]}
          />
        ))}
      </View>

      {/* Content */}
      <ScrollView
        style={styles.scrollView}
        contentContainerStyle={styles.scrollContent}
        showsVerticalScrollIndicator={false}
      >
        {currentPage === 0 && renderWelcome()}
        {currentPage === 1 && renderExamDate()}
        {currentPage === 2 && renderStudyTimes()}
        {currentPage === 3 && renderNotifications()}
      </ScrollView>

      {/* Bottom Buttons */}
      <View style={styles.bottomButtons}>
        {/* Back button - show on pages 1-3 */}
        {currentPage > 0 && (
          <Pressable
            onPress={() => setCurrentPage(currentPage - 1)}
            style={styles.backButton}
          >
            <Text style={styles.backButtonText}>← חזור</Text>
          </Pressable>
        )}

        {/* Skip button - show on pages 1-3 */}
        {currentPage > 0 && (
          <Pressable onPress={handleSkip} style={styles.skipButton}>
            <Text style={styles.skipButtonText}>דלג</Text>
          </Pressable>
        )}

        {/* Continue/Finish button */}
        <Pressable onPress={handleNext} style={styles.nextButton}>
          <Text style={styles.nextButtonText}>
            {currentPage === 3 ? 'סיים' : currentPage === 0 ? 'בואו נתחיל' : 'המשך'}
          </Text>
        </Pressable>
      </View>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  progressContainer: {
    flexDirection: 'row',
    justifyContent: 'center',
    alignItems: 'center',
    paddingVertical: 20,
    gap: 8,
  },
  progressDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: '#E5E7EB',
  },
  progressDotActive: {
    width: 24,
    backgroundColor: Colors.primary,
  },
  progressDotCompleted: {
    backgroundColor: Colors.success,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    flexGrow: 1,
    paddingHorizontal: 24,
  },
  pageContainer: {
    flex: 1,
    paddingVertical: 20,
  },
  logoLarge: {
    width: 220,
    height: 140,
    alignSelf: 'center',
    marginBottom: 32,
  },
  welcomeTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    textAlign: 'center',
    marginBottom: 16,
  },
  welcomeText: {
    fontSize: 18,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 26,
    marginBottom: 48,
  },
  featureList: {
    gap: 24,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: Colors.white,
    padding: 20,
    borderRadius: 16,
    gap: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
  },
  featureEmoji: {
    fontSize: 32,
  },
  featureText: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  questionTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    textAlign: 'center',
    marginBottom: 12,
  },
  questionSubtitle: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'center',
    lineHeight: 24,
    marginBottom: 40,
  },
  dateButton: {
    backgroundColor: Colors.white,
    padding: 24,
    borderRadius: 16,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  dateButtonText: {
    fontSize: 20,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
  dateButtonIcon: {
    fontSize: 32,
  },
  timesContainer: {
    flex: 1,
  },
  timesGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    justifyContent: 'space-between',
    paddingBottom: 20,
  },
  timeButton: {
    width: '48%',
    aspectRatio: 1.2,
    backgroundColor: Colors.white,
    padding: 16,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 2,
    borderColor: 'transparent',
    marginBottom: 12,
  },
  timeButtonSelected: {
    borderColor: Colors.primary,
    backgroundColor: Colors.secondaryLight,
  },
  timeEmoji: {
    fontSize: 24,
  },
  timeLabel: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  timeLabelSelected: {
    color: Colors.primary,
  },
  selectedCount: {
    backgroundColor: Colors.success,
    padding: 12,
    borderRadius: 12,
    marginTop: 16,
  },
  selectedCountText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.white,
    textAlign: 'center',
  },
  permissionBox: {
    backgroundColor: Colors.white,
    padding: 32,
    borderRadius: 16,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
    elevation: 3,
  },
  permissionIcon: {
    fontSize: 64,
    marginBottom: 20,
  },
  permissionTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.textPrimary,
    marginBottom: 16,
  },
  permissionText: {
    fontSize: 16,
    color: Colors.textSecondary,
    textAlign: 'right',
    lineHeight: 28,
  },
  bottomButtons: {
    flexDirection: 'row',
    paddingHorizontal: 24,
    paddingVertical: 20,
    gap: 12,
    borderTopWidth: 1,
    borderTopColor: '#E5E7EB',
  },
  backButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#E5E7EB',
  },
  backButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  skipButton: {
    flex: 1,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: '#F3F4F6',
    alignItems: 'center',
  },
  skipButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textSecondary,
  },
  nextButton: {
    flex: 2,
    paddingVertical: 16,
    borderRadius: 12,
    backgroundColor: Colors.primary,
    alignItems: 'center',
  },
  nextButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.white,
  },
});

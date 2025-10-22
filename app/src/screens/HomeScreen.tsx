import React, { useState, useEffect } from 'react';
import { StyleSheet, SafeAreaView, StatusBar, View, Text, Pressable, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { Image } from 'expo-image';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';
import { DrawerMenu } from '../components/DrawerMenu';
import { examApi } from '../utils/examApi';
import { useExamStore } from '../stores/examStore';
import { useAuthStore } from '../stores/authStore';
import { fetchUserProfile } from '../utils/userApi';
import { getTimeBasedGreeting } from '../utils/greetings';

interface MenuCardProps {
  title: string;
  iconSource: any; // Image source (require)
  onPress: () => void;
}

/**
 * קומפוננט כרטיס תפריט
 * Menu card component
 */
const MenuCard: React.FC<MenuCardProps> = ({ title, iconSource, onPress }) => {
  return (
    <Pressable onPress={onPress} style={styles.menuCard}>
      <Image source={iconSource} style={styles.cardIcon} contentFit="contain" />
      <Text style={styles.menuTitle}>{title}</Text>
    </Pressable>
  );
};

/**
 * מסך ראשי - דשבורד
 * Home Screen - Dashboard
 */
export const HomeScreen: React.FC = () => {
  const navigation = useNavigation();
  const { getToken } = useAuth();
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const { setCurrentExam } = useExamStore();
  const { user, setUser } = useAuthStore();
  const [greeting, setGreeting] = useState<string>('');

  // Fetch user data and set greeting
  useEffect(() => {
    const loadUserData = async () => {
      try {
        // Always fetch fresh user profile to ensure we have latest data (including is_admin)
        const userData = await fetchUserProfile(getToken);
        setUser({
          id: userData.id,
          email: userData.email,
          first_name: userData.first_name,
          last_name: userData.last_name,
          is_admin: userData.is_admin,
        });
        // Set greeting with fetched name
        setGreeting(getTimeBasedGreeting(userData.first_name));
      } catch (error) {
        // Log silently without triggering error screen
        console.log('Unable to load user data, using default greeting');
        // Set greeting without name if error
        setGreeting(getTimeBasedGreeting());
      }
    };

    loadUserData();
  }, []);

  const handleMenuPress = async (menuItem: string) => {
    console.log(`Pressed: ${menuItem}`);

    // Handle different menu items
    switch (menuItem) {
      case 'practice':
        // Navigate to practice topic selection screen
        navigation.navigate('PracticeTopicSelection');
        break;
      case 'full-exam':
        await createAndStartExam('full_simulation');
        break;
      case 'review-mistakes':
        // Navigate to mistake review selection screen
        navigation.navigate('MistakeReviewSelection');
        break;
      case 'ai-instructor':
        // Navigate to AI Mentor chat history
        navigation.navigate('ChatHistory');
        break;
      case 'concepts-laws':
        navigation.navigate('TopicSelection');
        break;
      case 'starred':
        navigation.navigate('StarredConcepts');
        break;
      case 'history':
        navigation.navigate('ExamHistory');
        break;
      case 'progress':
        navigation.navigate('Progress');
        break;
      default:
        console.log('Unknown menu item:', menuItem);
    }
  };

  /**
   * Create exam and navigate to ExamScreen
   */
  const createAndStartExam = async (examType: 'practice' | 'full_simulation' | 'review_mistakes') => {
    try {
      setLoading(true);

      // Create exam via API
      const examData = await examApi.createExam(
        {
          exam_type: examType,
          question_count: 25, // Default
        },
        getToken
      );

      // Set exam in store
      setCurrentExam(examData);

      // Navigate to ExamScreen
      navigation.navigate('Exam');
    } catch (error: any) {
      console.error('Create exam error:', error);
      Alert.alert('שגיאה', error.message || 'שגיאה ביצירת מבחן. נסה שוב.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      <DrawerMenu isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} />

      {/* Loading overlay */}
      {loading && (
        <View style={styles.loadingOverlay}>
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={Colors.primary} />
            <Text style={styles.loadingText}>יוצר מבחן...</Text>
          </View>
        </View>
      )}

      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <View style={styles.headerContent}>
            {/* Personalized Greeting */}
            {greeting && (
              <Text style={styles.greetingText}>{greeting}</Text>
            )}

            {/* Menu Icon - Left Side */}
            <Pressable onPress={() => setIsDrawerOpen(true)} style={styles.menuButton}>
              <Text style={styles.menuIcon}>☰</Text>
            </Pressable>
          </View>
        </View>

        {/* Menu Grid */}
        <View style={styles.menuGrid}>
          <View style={styles.menuRow}>
            <MenuCard title="תרגול שאלות" iconSource={require('../../assets/survey.png')} onPress={() => handleMenuPress('practice')} />
            <MenuCard title="סימולציית מבחן" iconSource={require('../../assets/law-book.png')} onPress={() => handleMenuPress('full-exam')} />
          </View>
          <View style={styles.menuRow}>
            <MenuCard title="חזרה על טעויות" iconSource={require('../../assets/close.png')} onPress={() => handleMenuPress('review-mistakes')} />
            <MenuCard title="מרצה חכם" iconSource={require('../../assets/owl.png')} onPress={() => handleMenuPress('ai-instructor')} />
          </View>
          <View style={styles.menuRow}>
            <MenuCard title="מושגים וחוקים" iconSource={require('../../assets/law.png')} onPress={() => handleMenuPress('concepts-laws')} />
            <MenuCard title="מועדפים" iconSource={require('../../assets/star.png')} onPress={() => handleMenuPress('starred')} />
          </View>
          <View style={styles.menuRow}>
            <MenuCard title="היסטוריית מבחנים" iconSource={require('../../assets/test.png')} onPress={() => handleMenuPress('history')} />
            <MenuCard title="מעקב התקדמות" iconSource={require('../../assets/trophy.png')} onPress={() => handleMenuPress('progress')} />
          </View>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    paddingBottom: 24,
  },
  header: {
    paddingHorizontal: 24,
    paddingTop: 16,
    paddingBottom: 32,
    backgroundColor: Colors.background,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  greetingContainer: {
    marginTop: 16,
    width: '100%',
    alignItems: 'flex-start', // In RTL, flex-start is the right side
  },
  greetingText: {
    fontSize: 28,
    fontWeight: '700',
    color: Colors.black,
    textAlign: 'right',
  },
  menuButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuIcon: {
    fontSize: 24,
  },
  logo: {
    width: 120,
    height: 70,
  },
  menuGrid: {
    paddingHorizontal: 24,
    gap: 16,
  },
  menuRow: {
    flexDirection: 'row',
    gap: 16,
  },
  menuCard: {
    flex: 1,
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 24,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 140,
    // iOS shadow
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 6,
    // Android shadow
    elevation: 4,
  },
  cardIcon: {
    width: 56,
    height: 56,
    marginBottom: 12,
  },
  menuIcon: {
    fontSize: 48,
    marginBottom: 12,
  },
  menuTitle: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
    textAlign: 'center',
  },
  loadingOverlay: {
    position: 'absolute',
    top: 0,
    left: 0,
    right: 0,
    bottom: 0,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1000,
  },
  loadingContainer: {
    backgroundColor: Colors.white,
    borderRadius: 16,
    padding: 32,
    alignItems: 'center',
    gap: 16,
  },
  loadingText: {
    fontSize: 16,
    fontWeight: '600',
    color: Colors.textPrimary,
  },
});

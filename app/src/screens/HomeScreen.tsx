import React, { useState } from 'react';
import { StyleSheet, SafeAreaView, StatusBar, View, Text, Pressable, ScrollView, ActivityIndicator, Alert } from 'react-native';
import { Image } from 'expo-image';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';
import { DrawerMenu } from '../components/DrawerMenu';
import { examApi } from '../utils/examApi';
import { useExamStore } from '../stores/examStore';

interface MenuCardProps {
  title: string;
  icon: string;
  onPress: () => void;
}

/**
 * קומפוננט כרטיס תפריט
 * Menu card component
 */
const MenuCard: React.FC<MenuCardProps> = ({ title, icon, onPress }) => {
  return (
    <Pressable onPress={onPress} style={styles.menuCard}>
      <Text style={styles.menuIcon}>{icon}</Text>
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
        await createAndStartExam('review_mistakes');
        break;
      case 'ai-instructor':
        Alert.alert('בקרוב', 'תכונה זו תהיה זמינה בקרוב');
        break;
      case 'concepts-laws':
        Alert.alert('בקרוב', 'תכונה זו תהיה זמינה בקרוב');
        break;
      case 'history':
        navigation.navigate('ExamHistory');
        break;
      case 'progress':
        Alert.alert('בקרוב', 'תכונה זו תהיה זמינה בקרוב');
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
            {/* Menu Icon */}
            <Pressable onPress={() => setIsDrawerOpen(true)} style={styles.menuButton}>
              <Text style={styles.menuIcon}>☰</Text>
            </Pressable>

            {/* Logo */}
            <Image
              source={require('../../assets/logo.png')}
              style={styles.logo}
              contentFit="contain"
            />
          </View>
        </View>

        {/* Menu Grid */}
        <View style={styles.menuGrid}>
          <View style={styles.menuRow}>
            <MenuCard title="תרגול שאלות" icon="❓" onPress={() => handleMenuPress('practice')} />
            <MenuCard title="סימולציית מבחן" icon="📋" onPress={() => handleMenuPress('full-exam')} />
          </View>
          <View style={styles.menuRow}>
            <MenuCard title="חזרה על טעויות" icon="⚠️" onPress={() => handleMenuPress('review-mistakes')} />
            <MenuCard title="מרצה AI" icon="👨‍🏫" onPress={() => handleMenuPress('ai-instructor')} />
          </View>
          <View style={styles.menuRow}>
            <MenuCard title="מושגים וחוקים" icon="📇" onPress={() => handleMenuPress('concepts-laws')} />
            <MenuCard title="היסטוריית מבחנים" icon="📝" onPress={() => handleMenuPress('history')} />
          </View>
          <View style={styles.menuRow}>
            <MenuCard title="מעקב התקדמות" icon="🏆" onPress={() => handleMenuPress('progress')} />
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
    paddingBottom: 24,
    backgroundColor: Colors.background,
  },
  headerContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
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
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 4,
    elevation: 2,
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

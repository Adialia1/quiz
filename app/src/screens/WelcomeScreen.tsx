import React from 'react';
import { StyleSheet, View, Text, Pressable, Dimensions } from 'react-native';
import { Image } from 'expo-image';
import { LinearGradient } from 'expo-linear-gradient';
import { Colors } from '../config/colors';

const { width, height } = Dimensions.get('window');

interface WelcomeScreenProps {
  onGetStarted: () => void;
}

/**
 * מסך ברוכים הבאים
 * Welcome Screen
 */
export const WelcomeScreen: React.FC<WelcomeScreenProps> = ({ onGetStarted }) => {
  return (
    <View style={styles.container}>
      <LinearGradient
        colors={[Colors.primary, '#0966D6', '#0856B9']}
        style={styles.gradient}
        start={{ x: 0, y: 0 }}
        end={{ x: 1, y: 1 }}
      >
        {/* Logo and Title */}
        <View style={styles.logoContainer}>
          <View style={styles.logoWrapper}>
            <Image
              source={require('../../assets/logo2.png')}
              style={styles.logo}
              contentFit="contain"
            />
          </View>
          <Text style={styles.appTitle}>אתיקה פלוס</Text>
          <Text style={styles.appSubtitle}>התכונן למבחנים בצורה החכמה ביותר</Text>
        </View>

        {/* תכונות */}
        <View style={styles.featuresContainer}>
          <FeatureItem
            icon="✓"
            title="אלפי שאלות"
            description="בנק שאלות מקיף לכל הנושאים"
          />
          <FeatureItem
            icon="📊"
            title="מעקב התקדמות"
            description="עקוב אחר ההתקדמות שלך בזמן אמת"
          />
          <FeatureItem
            icon="🎯"
            title="תרגול חכם"
            description="תרגל את השאלות שאתה צריך ביותר"
          />
        </View>

        {/* כפתור התחלה */}
        <View style={styles.buttonContainer}>
          <Pressable
            style={({ pressed }) => [
              styles.button,
              pressed && styles.buttonPressed,
            ]}
            onPress={onGetStarted}
          >
            <Text style={styles.buttonText}>בואו נתחיל</Text>
          </Pressable>
        </View>
      </LinearGradient>
    </View>
  );
};

interface FeatureItemProps {
  icon: string;
  title: string;
  description: string;
}

const FeatureItem: React.FC<FeatureItemProps> = ({ icon, title, description }) => (
  <View style={styles.featureItem}>
    <View style={styles.featureTextContainer}>
      <Text style={styles.featureTitle}>{title}</Text>
      <Text style={styles.featureDescription}>{description}</Text>
    </View>
    <Text style={styles.featureIcon}>{icon}</Text>
  </View>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  gradient: {
    flex: 1,
    paddingHorizontal: 24,
    paddingTop: 60,
    paddingBottom: 40,
  },
  logoContainer: {
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 60,
  },
  logoWrapper: {
    width: 140,
    height: 140,
    borderRadius: 70,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 24,
    padding: 20,
  },
  logo: {
    width: '100%',
    height: '100%',
  },
  appTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: Colors.white,
    marginBottom: 8,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  appSubtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  featuresContainer: {
    flex: 1,
    justifyContent: 'center',
    gap: 20,
  },
  featureItem: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(255, 255, 255, 0.15)',
    padding: 16,
    borderRadius: 12,
    gap: 16,
  },
  featureIcon: {
    fontSize: 32,
  },
  featureTextContainer: {
    flex: 1,
    alignItems: 'flex-end',
  },
  featureTitle: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.white,
    marginBottom: 4,
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  featureDescription: {
    fontSize: 14,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'right',
    writingDirection: 'rtl',
  },
  buttonContainer: {
    marginTop: 'auto',
  },
  button: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  buttonPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.98 }],
  },
  buttonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.white,
  },
});

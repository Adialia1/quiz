import React from 'react';
import { View, ScrollView, StyleSheet, Text, Pressable, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Colors } from '../config/colors';

interface GuestHomeScreenProps {
  navigation: any;
  onSignUp: () => void;
}

/**
 * מסך בית למשתמשי אורח
 * Guest Home Screen - Limited features for users without account
 */
export const GuestHomeScreen: React.FC<GuestHomeScreenProps> = ({ navigation, onSignUp }) => {
  const handleFeaturePress = (featureName: string, requiresAuth: boolean = true) => {
    if (requiresAuth) {
      Alert.alert(
        'נדרשת הרשמה',
        `כדי להשתמש בתכונה "${featureName}" יש להירשם לאפליקציה`,
        [
          { text: 'ביטול', style: 'cancel' },
          { text: 'הירשם עכשיו', onPress: onSignUp },
        ]
      );
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      <ScrollView style={styles.scrollView} contentContainerStyle={styles.scrollContent}>
        {/* Header */}
        <View style={styles.header}>
          <Text style={styles.headerTitle}>אתיקה פלוס</Text>
          <Text style={styles.headerSubtitle}>משתמש אורח</Text>
        </View>

        {/* Sign up banner */}
        <View style={styles.signupBanner}>
          <Text style={styles.bannerTitle}>קבל גישה מלאה לכל התכונות!</Text>
          <Text style={styles.bannerText}>
            צור חשבון כדי לעקוב אחר ההתקדמות שלך, לשמור שאלות אהובות ולהשתמש בכל התכונות
          </Text>
          <Pressable
            style={({ pressed }) => [
              styles.signupButton,
              pressed && styles.buttonPressed,
            ]}
            onPress={onSignUp}
          >
            <Text style={styles.signupButtonText}>הירשם עכשיו</Text>
          </Pressable>
        </View>

        {/* Features Grid */}
        <View style={styles.featuresGrid}>
          {/* Available for Guest - Learning Content Only */}
          <FeatureCard
            title="מושגים וחוקים"
            description="צפה במושגים חשובים וחוקים בסיסיים (עד 10 מושגים לנושא)"
            icon="📚"
            onPress={() => navigation?.navigate('TopicSelection')}
            available={true}
          />

          {/* Locked Features - Require Account */}
          <FeatureCard
            title="תרגול שאלות"
            description="תרגול חופשי של שאלות מהבנק שלנו"
            icon="📝"
            onPress={() => handleFeaturePress('תרגול שאלות')}
            available={false}
          />

          <FeatureCard
            title="מבחני תרגול"
            description="בצע מבחנים מלאים כהכנה למבחן האמיתי"
            icon="📋"
            onPress={() => handleFeaturePress('מבחני תרגול')}
            available={false}
          />

          <FeatureCard
            title="מעקב התקדמות"
            description="עקוב אחר ההתקדמות והישגים שלך"
            icon="📊"
            onPress={() => handleFeaturePress('מעקב התקדמות')}
            available={false}
          />

          <FeatureCard
            title="מנטור AI"
            description="קבל עזרה אישית ממנטור בינה מלאכותית"
            icon="🤖"
            onPress={() => handleFeaturePress('מנטור AI')}
            available={false}
          />

          <FeatureCard
            title="סקירת טעויות"
            description="חזור על השאלות שטעית בהן"
            icon="🔍"
            onPress={() => handleFeaturePress('סקירת טעויות')}
            available={false}
          />
        </View>

        {/* Footer CTA */}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            רוצה לקבל גישה לכל התכונות? הירשם עכשיו וקבל גישה מלאה!
          </Text>
          <Pressable
            style={({ pressed }) => [
              styles.footerButton,
              pressed && styles.buttonPressed,
            ]}
            onPress={onSignUp}
          >
            <Text style={styles.footerButtonText}>צור חשבון חינם</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

interface FeatureCardProps {
  title: string;
  description: string;
  icon: string;
  onPress: () => void;
  available: boolean;
}

const FeatureCard: React.FC<FeatureCardProps> = ({
  title,
  description,
  icon,
  onPress,
  available
}) => (
  <Pressable
    style={({ pressed }) => [
      styles.featureCard,
      !available && styles.featureCardLocked,
      pressed && styles.cardPressed,
    ]}
    onPress={onPress}
  >
    <View style={styles.featureCardContent}>
      <View style={styles.featureCardHeader}>
        <Text style={styles.featureCardIcon}>{icon}</Text>
        {!available && (
          <View style={styles.lockBadge}>
            <Text style={styles.lockIcon}>🔒</Text>
          </View>
        )}
      </View>
      <Text style={[styles.featureCardTitle, !available && styles.textMuted]}>
        {title}
      </Text>
      <Text style={[styles.featureCardDescription, !available && styles.textMuted]}>
        {description}
      </Text>
    </View>
  </Pressable>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  scrollView: {
    flex: 1,
  },
  scrollContent: {
    padding: 16,
  },
  header: {
    alignItems: 'center',
    paddingVertical: 24,
  },
  headerTitle: {
    fontSize: 28,
    fontWeight: 'bold',
    color: Colors.primary,
    textAlign: 'center',
    marginBottom: 4,
  },
  headerSubtitle: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
  },
  signupBanner: {
    backgroundColor: Colors.primary,
    borderRadius: 16,
    padding: 20,
    marginBottom: 24,
  },
  bannerTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: Colors.white,
    textAlign: 'center',
    marginBottom: 8,
  },
  bannerText: {
    fontSize: 14,
    color: Colors.white,
    textAlign: 'center',
    marginBottom: 16,
    lineHeight: 20,
    opacity: 0.9,
  },
  signupButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 12,
    paddingHorizontal: 24,
    borderRadius: 10,
    alignItems: 'center',
  },
  signupButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.white,
  },
  featuresGrid: {
    gap: 12,
  },
  featureCard: {
    backgroundColor: Colors.white,
    borderRadius: 12,
    padding: 16,
    borderWidth: 1,
    borderColor: Colors.border,
  },
  featureCardLocked: {
    opacity: 0.7,
    backgroundColor: Colors.secondaryLight,
  },
  featureCardContent: {
    gap: 8,
  },
  featureCardHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  featureCardIcon: {
    fontSize: 32,
  },
  lockBadge: {
    backgroundColor: 'rgba(0, 0, 0, 0.1)',
    borderRadius: 12,
    padding: 4,
  },
  lockIcon: {
    fontSize: 16,
  },
  featureCardTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.text,
    textAlign: 'right',
  },
  featureCardDescription: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'right',
    lineHeight: 20,
  },
  textMuted: {
    opacity: 0.6,
  },
  footer: {
    marginTop: 32,
    marginBottom: 16,
    alignItems: 'center',
  },
  footerText: {
    fontSize: 14,
    color: Colors.textSecondary,
    textAlign: 'center',
    marginBottom: 16,
    lineHeight: 20,
  },
  footerButton: {
    backgroundColor: Colors.primary,
    paddingVertical: 14,
    paddingHorizontal: 32,
    borderRadius: 10,
  },
  footerButtonText: {
    fontSize: 16,
    fontWeight: 'bold',
    color: Colors.white,
  },
  buttonPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.98 }],
  },
  cardPressed: {
    transform: [{ scale: 0.98 }],
  },
});

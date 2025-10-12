import React, { useState } from 'react';
import { StyleSheet, SafeAreaView, StatusBar, View, Text, Pressable, ScrollView } from 'react-native';
import { Image } from 'expo-image';
import { Colors } from '../config/colors';
import { DrawerMenu } from '../components/DrawerMenu';

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
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

  const handleMenuPress = (menuItem: string) => {
    console.log(`Pressed: ${menuItem}`);
    // TODO: Navigate to respective screens
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" />

      <DrawerMenu isOpen={isDrawerOpen} onClose={() => setIsDrawerOpen(false)} />

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
});

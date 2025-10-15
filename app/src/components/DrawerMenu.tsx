import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  Animated,
  Dimensions,
  Alert,
} from 'react-native';
import { useUser, useClerk } from '@clerk/clerk-expo';
import { useNavigation } from '@react-navigation/native';
import { MaterialIcons, Ionicons } from '@expo/vector-icons';
import { Colors } from '../config/colors';
import { useAuthStore } from '../stores/authStore';
import { StorageUtils } from '../utils/storage';

const SCREEN_WIDTH = Dimensions.get('window').width;
const DRAWER_WIDTH = SCREEN_WIDTH * 0.75;

interface DrawerMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

interface MenuItemProps {
  iconName: string;
  iconLibrary: 'MaterialIcons' | 'Ionicons';
  title: string;
  onPress: () => void;
  iconColor: string;
}

const MenuItem: React.FC<MenuItemProps> = ({ iconName, iconLibrary, title, onPress, iconColor }) => {
  const IconComponent = iconLibrary === 'MaterialIcons' ? MaterialIcons : Ionicons;

  return (
    <Pressable onPress={onPress} style={styles.menuItem}>
      <View style={[styles.iconContainer, { backgroundColor: `${iconColor}15` }]}>
        <IconComponent name={iconName as any} size={24} color={iconColor} />
      </View>
      <Text style={styles.menuItemText}>{title}</Text>
    </Pressable>
  );
};

export const DrawerMenu: React.FC<DrawerMenuProps> = ({ isOpen, onClose }) => {
  const slideAnim = useRef(new Animated.Value(DRAWER_WIDTH)).current;
  const navigation = useNavigation();
  const { user: clerkUser } = useUser();
  const { signOut } = useClerk();
  const { logout } = useAuthStore();

  useEffect(() => {
    if (isOpen) {
      Animated.timing(slideAnim, {
        toValue: 0,
        duration: 300,
        useNativeDriver: true,
      }).start();
    } else {
      Animated.timing(slideAnim, {
        toValue: DRAWER_WIDTH,
        duration: 250,
        useNativeDriver: true,
      }).start();
    }
  }, [isOpen]);

  const handleLogout = async () => {
    try {
      // Show confirmation alert
      Alert.alert(
        'התנתקות',
        'האם אתה בטוח שברצונך להתנתק?',
        [
          {
            text: 'ביטול',
            style: 'cancel',
          },
          {
            text: 'התנתק',
            style: 'destructive',
            onPress: async () => {
              onClose(); // Close drawer first

              // Clear all local storage
              await StorageUtils.clearAll();

              // Clear local state
              await logout();

              // Sign out from Clerk
              await signOut();

              // User will be redirected to auth screen automatically by Clerk
            },
          },
        ],
        { cancelable: true }
      );
    } catch (error) {
      console.error('שגיאה בהתנתקות:', error);
      Alert.alert('שגיאה', 'אירעה שגיאה בהתנתקות. אנא נסה שוב.');
    }
  };

  const userName = clerkUser?.firstName && clerkUser?.lastName
    ? `${clerkUser.firstName} ${clerkUser.lastName}`
    : clerkUser?.primaryEmailAddress?.emailAddress?.split('@')[0] || 'משתמש';

  if (!isOpen) return null;

  return (
    <>
      {/* Overlay */}
      <Pressable
        style={[
          StyleSheet.absoluteFill,
          {
            backgroundColor: 'rgba(0, 0, 0, 0.5)',
            zIndex: 998,
          },
        ]}
        onPress={onClose}
      />

      {/* Drawer */}
      <Animated.View
        pointerEvents="box-none"
        style={[
          styles.drawer,
          {
            transform: [{ translateX: slideAnim }],
          },
        ]}
      >
        {/* Header */}
        <View style={styles.header}>
          <Pressable onPress={onClose} style={styles.closeButton}>
            <MaterialIcons name="arrow-forward" size={28} color={Colors.white} />
          </Pressable>
          <Text style={styles.greeting}>שלום {userName}</Text>
        </View>

        {/* Menu Items */}
        <View style={styles.menuItems}>
          <MenuItem
            iconName="lock"
            iconLibrary="MaterialIcons"
            title="שנה סיסמא"
            iconColor={Colors.primary}
            onPress={() => {
              onClose();
              navigation.navigate('ChangePassword' as never);
            }}
          />
          <MenuItem
            iconName="card"
            iconLibrary="Ionicons"
            title="ניהול מנוי"
            iconColor={Colors.accent}
            onPress={() => {
              onClose();
              navigation.navigate('SubscriptionManagement' as never);
            }}
          />
          <MenuItem
            iconName="description"
            iconLibrary="MaterialIcons"
            title="תנאי שימוש"
            iconColor={Colors.gray[600]}
            onPress={() => {
              onClose();
              navigation.navigate('TermsAndConditions' as never);
            }}
          />
          <MenuItem
            iconName="logout"
            iconLibrary="MaterialIcons"
            title="התנתק"
            iconColor={Colors.error}
            onPress={handleLogout}
          />
        </View>
      </Animated.View>
    </>
  );
};

const styles = StyleSheet.create({
  drawer: {
    position: 'absolute',
    right: 0,
    top: 0,
    bottom: 0,
    width: DRAWER_WIDTH,
    backgroundColor: Colors.white,
    zIndex: 999,
    shadowColor: '#000',
    shadowOffset: { width: -2, height: 0 },
    shadowOpacity: 0.25,
    shadowRadius: 8,
    elevation: 5,
  },
  header: {
    backgroundColor: Colors.primary,
    paddingTop: 60,
    paddingBottom: 30,
    paddingHorizontal: 24,
    position: 'relative',
  },
  closeButton: {
    position: 'absolute',
    left: 24,
    top: 60,
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    zIndex: 1,
  },
  greeting: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.white,
    textAlign: 'right',
  },
  menuItems: {
    paddingTop: 20,
  },
  menuItem: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: 16,
    paddingHorizontal: 24,
    gap: 16,
  },
  iconContainer: {
    width: 48,
    height: 48,
    borderRadius: 24,
    alignItems: 'center',
    justifyContent: 'center',
  },
  menuItemText: {
    fontSize: 18,
    color: Colors.textPrimary,
    flex: 1,
    textAlign: 'right',
  },
});

import React, { useEffect, useRef } from 'react';
import {
  View,
  Text,
  Pressable,
  StyleSheet,
  Animated,
  Dimensions,
  Alert,
  ScrollView,
  Linking,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { Image } from 'expo-image';
import { useUser, useClerk } from '@clerk/clerk-expo';
import { useNavigation } from '@react-navigation/native';
import { MaterialIcons, Ionicons } from '@expo/vector-icons';
import { Colors } from '../config/colors';
import { useAuthStore } from '../stores/authStore';
import { StorageUtils } from '../utils/storage';

const SCREEN_WIDTH = Dimensions.get('window').width;
const DRAWER_WIDTH = SCREEN_WIDTH * 0.8;

interface DrawerMenuProps {
  isOpen: boolean;
  onClose: () => void;
}

interface MenuItemProps {
  iconName: string;
  iconLibrary: 'MaterialIcons' | 'Ionicons';
  title: string;
  subtitle?: string;
  onPress: () => void;
  isDestructive?: boolean;
}

const MenuItem: React.FC<MenuItemProps> = ({
  iconName,
  iconLibrary,
  title,
  subtitle,
  onPress,
  isDestructive = false
}) => {
  const IconComponent = iconLibrary === 'MaterialIcons' ? MaterialIcons : Ionicons;

  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.menuItem,
        pressed && styles.menuItemPressed
      ]}
    >
      <IconComponent
        name={iconName as any}
        size={24}
        color={isDestructive ? Colors.error : Colors.gray[700]}
      />
      <View style={styles.menuItemTextContainer}>
        <Text style={[
          styles.menuItemText,
          isDestructive && styles.menuItemTextDestructive
        ]}>
          {title}
        </Text>
        {subtitle && (
          <Text style={styles.menuItemSubtitle}>{subtitle}</Text>
        )}
      </View>
    </Pressable>
  );
};

const MenuSeparator: React.FC = () => (
  <View style={styles.separator} />
);

export const DrawerMenu: React.FC<DrawerMenuProps> = ({ isOpen, onClose }) => {
  const slideAnim = useRef(new Animated.Value(DRAWER_WIDTH)).current;
  const navigation = useNavigation();
  const { user: clerkUser } = useUser();
  const { signOut } = useClerk();
  const { logout, user } = useAuthStore();

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

  const userEmail = clerkUser?.primaryEmailAddress?.emailAddress || '';
  const userImageUrl = clerkUser?.imageUrl;

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
        <SafeAreaView style={styles.safeArea} edges={['top']}>
          {/* Profile Section */}
          <View style={styles.profileSection}>
            <View style={styles.profileHeader}>
              {userImageUrl ? (
                <Image
                  source={{ uri: userImageUrl }}
                  style={styles.profileImage}
                  contentFit="cover"
                />
              ) : (
                <View style={styles.profileImagePlaceholder}>
                  <Text style={styles.profileImagePlaceholderText}>
                    {userName.charAt(0).toUpperCase()}
                  </Text>
                </View>
              )}
              <View style={styles.profileInfo}>
                <Text style={styles.profileName}>{userName}</Text>
                <Text style={styles.profileEmail}>{userEmail}</Text>
              </View>
              <Pressable onPress={onClose} style={styles.closeButton}>
                <MaterialIcons name="close" size={24} color={Colors.gray[600]} />
              </Pressable>
            </View>
          </View>

          <MenuSeparator />

          {/* Menu Items */}
          <ScrollView style={styles.menuItems} showsVerticalScrollIndicator={false}>
            <MenuItem
              iconName="card-outline"
              iconLibrary="Ionicons"
              title="ניהול מנוי"
              subtitle="תוכניות ותשלומים"
              onPress={() => {
                onClose();
                navigation.navigate('SubscriptionManagement' as never);
              }}
            />

            <MenuItem
              iconName="lock-closed-outline"
              iconLibrary="Ionicons"
              title="שנה סיסמא"
              onPress={() => {
                onClose();
                navigation.navigate('ChangePassword' as never);
              }}
            />

            <MenuItem
              iconName="settings-outline"
              iconLibrary="Ionicons"
              title="הגדרות חשבון"
              subtitle="ניהול פרטים אישיים ומחיקת חשבון"
              onPress={() => {
                onClose();
                navigation.navigate('Settings' as never);
              }}
            />

            <MenuSeparator />

            {/* Admin Panel - Only visible to admins */}
            {user?.is_admin && (
              <>
                <MenuItem
                  iconName="build-outline"
                  iconLibrary="Ionicons"
                  title="ניהול מערכת"
                  subtitle="פאנל ניהול למנהלים"
                  onPress={() => {
                    onClose();
                    navigation.navigate('Admin' as never);
                  }}
                />
                <MenuSeparator />
              </>
            )}

            <MenuItem
              iconName="document-text-outline"
              iconLibrary="Ionicons"
              title="תנאי שימוש"
              onPress={() => {
                onClose();
                navigation.navigate('TermsAndConditions' as never);
              }}
            />

            <MenuItem
              iconName="help-circle-outline"
              iconLibrary="Ionicons"
              title="עזרה ותמיכה"
              onPress={async () => {
                onClose();
                const email = 'ebaymosko@gmail.com';
                const subject = 'תמיכה - קוויז מבחנים';
                const url = `mailto:${email}?subject=${encodeURIComponent(subject)}`;

                const canOpen = await Linking.canOpenURL(url);
                if (canOpen) {
                  await Linking.openURL(url);
                } else {
                  Alert.alert('שגיאה', 'לא ניתן לפתוח את אפליקציית המייל');
                }
              }}
            />

            <MenuSeparator />

            <MenuItem
              iconName="log-out-outline"
              iconLibrary="Ionicons"
              title="התנתק"
              onPress={handleLogout}
              isDestructive
            />

            {/* Bottom padding */}
            <View style={{ height: 24 }} />
          </ScrollView>
        </SafeAreaView>
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
    shadowOpacity: 0.15,
    shadowRadius: 12,
    elevation: 8,
  },
  safeArea: {
    flex: 1,
  },
  profileSection: {
    paddingHorizontal: 20,
    paddingVertical: 16,
  },
  profileHeader: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    gap: 12,
  },
  profileImage: {
    width: 56,
    height: 56,
    borderRadius: 28,
  },
  profileImagePlaceholder: {
    width: 56,
    height: 56,
    borderRadius: 28,
    backgroundColor: Colors.primary,
    alignItems: 'center',
    justifyContent: 'center',
  },
  profileImagePlaceholderText: {
    fontSize: 24,
    fontWeight: 'bold',
    color: Colors.white,
  },
  profileInfo: {
    flex: 1,
    alignItems: 'flex-end',
  },
  profileName: {
    fontSize: 18,
    fontWeight: '600',
    color: Colors.textPrimary,
    textAlign: 'right',
    marginBottom: 2,
  },
  profileEmail: {
    fontSize: 14,
    color: Colors.gray[600],
    textAlign: 'right',
  },
  closeButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginLeft: -8,
  },
  menuItems: {
    flex: 1,
  },
  menuItem: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    paddingVertical: 14,
    paddingHorizontal: 20,
    gap: 16,
  },
  menuItemPressed: {
    backgroundColor: Colors.gray[100],
  },
  menuItemTextContainer: {
    flex: 1,
    alignItems: 'flex-end',
  },
  menuItemText: {
    fontSize: 16,
    fontWeight: '500',
    color: Colors.textPrimary,
    textAlign: 'right',
  },
  menuItemTextDestructive: {
    color: Colors.error,
  },
  menuItemSubtitle: {
    fontSize: 13,
    color: Colors.gray[500],
    textAlign: 'right',
    marginTop: 2,
  },
  separator: {
    height: 1,
    backgroundColor: Colors.gray[200],
    marginVertical: 8,
    marginHorizontal: 20,
  },
});

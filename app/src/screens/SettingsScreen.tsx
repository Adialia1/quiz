import React, { useState } from 'react';
import { ScrollView, Alert, Pressable, StyleSheet, View, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { useNavigation } from '@react-navigation/native';
import { useAuth, useClerk } from '@clerk/clerk-expo';
import {
  Box,
  VStack,
  Text,
  Heading,
} from '@gluestack-ui/themed';
import { Colors } from '../config/colors';
import { useAuthStore } from '../stores/authStore';
import { deleteUserAccount } from '../utils/userApi';

/**
 * Settings Screen
 * User settings and account management
 */
export const SettingsScreen: React.FC = () => {
  const navigation = useNavigation();
  const { getToken } = useAuth();
  const { user: clerkUser } = useClerk();
  const { user, clearAllData } = useAuthStore();
  const [isDeleting, setIsDeleting] = useState(false);

  /**
   * Handle account deletion
   */
  const handleDeleteAccount = async () => {
    // Show confirmation dialog
    Alert.alert(
      'האם אתה בטוח?',
      'פעולה זו תמחק את החשבון שלך לצמיתות ולא ניתן לשחזר אותו. כל הנתונים שלך יימחקו.',
      [
        {
          text: 'ביטול',
          style: 'cancel',
        },
        {
          text: 'מחק חשבון',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsDeleting(true);

              // 1. Backend handles COMPLETE deletion:
              //    - Cancels RevenueCat subscription
              //    - Deletes Clerk account
              //    - Deletes all database records
              await deleteUserAccount(getToken);

              // 2. Fallback: Try to delete Clerk account from client
              //    (in case backend deletion failed)
              try {
                await clerkUser.user?.delete();
              } catch (clerkError) {
                console.log('Clerk deletion from client failed (may have been deleted by backend):', clerkError);
              }

              // 3. Clear all local storage and auth store
              await clearAllData();

              // 4. Show success message
              Alert.alert(
                'החשבון נמחק',
                'החשבון שלך נמחק בהצלחה',
                [
                  {
                    text: 'אישור',
                    onPress: () => {
                      // Navigation will automatically redirect to auth screen
                      // because user is no longer authenticated
                    },
                  },
                ]
              );
            } catch (error: any) {
              console.error('Error deleting account:', error);

              let errorMessage = 'שגיאה במחיקת החשבון. אנא נסה שנית מאוחר יותר.';

              if (error.message) {
                errorMessage = error.message;
              }

              Alert.alert('שגיאה', errorMessage);
            } finally {
              setIsDeleting(false);
            }
          },
        },
      ]
    );
  };

  return (
    <Box flex={1} bg="$white">
      <LinearGradient
        colors={[Colors.primary, '#0966D6', '#0856B9']}
        style={styles.gradient}
      >
        <ScrollView>
          <VStack p="$6" pb="$10">
            {/* Header with Back Button */}
            <View style={styles.headerRow}>
              <View style={styles.spacer} />
              <Pressable
                style={({ pressed }) => [
                  styles.backButton,
                  pressed && styles.buttonPressed,
                ]}
                onPress={() => navigation.goBack()}
              >
                <Text style={styles.backIcon}>→</Text>
              </Pressable>
            </View>

            {/* Title */}
            <Heading size="2xl" color="white" textAlign="right" mt="$4" mb="$2">
              הגדרות
            </Heading>

            <Text size="md" color="white" opacity={0.9} textAlign="right" mb="$6">
              ניהול חשבון והגדרות
            </Text>
          </VStack>
        </ScrollView>
      </LinearGradient>

      {/* Content Section */}
      <ScrollView style={styles.content}>
        <VStack p="$6" space="lg">
          {/* Account Information Section */}
          <Box>
            <Heading size="lg" color={Colors.textPrimary} textAlign="right" mb="$3">
              פרטי חשבון
            </Heading>

            {user && (
              <VStack space="sm" bg={Colors.primaryLight} p="$4" borderRadius="$lg">
                {user.email && (
                  <View style={styles.infoRow}>
                    <Text size="md" color={Colors.textPrimary} textAlign="right">
                      {user.email}
                    </Text>
                    <Text size="sm" color={Colors.textSecondary} textAlign="right" mb="$1">
                      אימייל:
                    </Text>
                  </View>
                )}

                {(user.first_name || user.firstName) && (
                  <View style={styles.infoRow}>
                    <Text size="md" color={Colors.textPrimary} textAlign="right">
                      {user.first_name || user.firstName}
                    </Text>
                    <Text size="sm" color={Colors.textSecondary} textAlign="right" mb="$1">
                      שם פרטי:
                    </Text>
                  </View>
                )}
              </VStack>
            )}
          </Box>

          {/* Danger Zone Section */}
          <Box mt="$8">
            <Heading size="lg" color={Colors.error} textAlign="right" mb="$3">
              אזור מסוכן
            </Heading>

            <Text size="sm" color={Colors.textSecondary} textAlign="right" mb="$4">
              פעולות בלתי הפיכות שישפיעו על החשבון שלך
            </Text>

            {/* Delete Account Button */}
            <Pressable
              style={({ pressed }) => [
                styles.deleteButton,
                pressed && styles.deleteButtonPressed,
                isDeleting && styles.deleteButtonDisabled,
              ]}
              onPress={handleDeleteAccount}
              disabled={isDeleting}
            >
              {isDeleting ? (
                <ActivityIndicator size="small" color="white" />
              ) : (
                <Text style={styles.deleteButtonText}>
                  מחיקת חשבון
                </Text>
              )}
            </Pressable>

            <Text size="xs" color={Colors.textSecondary} textAlign="right" mt="$2">
              פעולה זו תמחק את החשבון שלך ואת כל הנתונים שלך לצמיתות
            </Text>
          </Box>
        </VStack>
      </ScrollView>
    </Box>
  );
};

const styles = StyleSheet.create({
  gradient: {
    paddingTop: 60,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 16,
  },
  spacer: {
    width: 40,
  },
  backButton: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(255, 255, 255, 0.2)',
    justifyContent: 'center',
    alignItems: 'center',
  },
  buttonPressed: {
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
  },
  backIcon: {
    color: 'white',
    fontSize: 24,
    fontWeight: 'bold',
  },
  content: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  infoRow: {
    marginBottom: 12,
  },
  deleteButton: {
    backgroundColor: Colors.error,
    paddingVertical: 16,
    paddingHorizontal: 24,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 56,
  },
  deleteButtonPressed: {
    backgroundColor: '#D32F2F',
    opacity: 0.8,
  },
  deleteButtonDisabled: {
    opacity: 0.6,
  },
  deleteButtonText: {
    color: 'white',
    fontSize: 18,
    fontWeight: '600',
    textAlign: 'center',
  },
});

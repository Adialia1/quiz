import React, { useState } from 'react';
import { ScrollView, Alert, Pressable, StyleSheet, View, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Image } from 'expo-image';
import { useNavigation } from '@react-navigation/native';
import {
  Box,
  VStack,
  Text,
  Input,
  InputField,
} from '@gluestack-ui/themed';
import { useUser } from '@clerk/clerk-expo';
import { Colors } from '../config/colors';

/**
 * Change Password Screen
 * Allows users to change their password using Clerk
 */
export const ChangePasswordScreen: React.FC = () => {
  const navigation = useNavigation();
  const { user } = useUser();

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleChangePassword = async () => {
    // Validation
    if (!currentPassword || !newPassword || !confirmPassword) {
      Alert.alert('שגיאה', 'נא למלא את כל השדות');
      return;
    }

    if (newPassword.length < 8) {
      Alert.alert('שגיאה', 'הסיסמה החדשה חייבת להכיל לפחות 8 תווים');
      return;
    }

    if (newPassword !== confirmPassword) {
      Alert.alert('שגיאה', 'הסיסמאות אינן תואמות');
      return;
    }

    try {
      setIsLoading(true);

      // Update password using Clerk
      await user?.updatePassword({
        currentPassword,
        newPassword,
      });

      Alert.alert(
        'הצלחה!',
        'הסיסמה שונתה בהצלחה',
        [
          {
            text: 'אישור',
            onPress: () => navigation.goBack(),
          },
        ]
      );
    } catch (error: any) {
      console.error('Password change error:', error);

      let errorMessage = 'שגיאה בשינוי הסיסמה';

      if (error.errors && error.errors.length > 0) {
        const firstError = error.errors[0];
        if (firstError.code === 'form_password_incorrect') {
          errorMessage = 'הסיסמה הנוכחית שגויה';
        } else if (firstError.message) {
          errorMessage = firstError.message;
        }
      }

      Alert.alert('שגיאה', errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <Box flex={1} bg="$white">
      <LinearGradient
        colors={[Colors.primary, '#0966D6', '#0856B9']}
        style={styles.gradient}
      >
        <ScrollView>
          <VStack p="$6" pb="$10">
            {/* Back Button */}
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

            {/* Header */}
            <VStack space="md" alignItems="center">
              <Box style={styles.logoWrapper}>
                <Image
                  source={require('../../assets/icon.png.jpeg')}
                  style={styles.logo}
                  contentFit="contain"
                />
              </Box>
              <Text style={styles.title}>שינוי סיסמה</Text>
              <Text style={styles.subtitle}>
                הזן את הסיסמה הנוכחית והסיסמה החדשה
              </Text>
            </VStack>

            {/* Form Card */}
            <Box style={styles.formCard}>
              <VStack space="lg">
                {/* Current Password */}
                <VStack space="xs">
                  <Text style={styles.label}>סיסמה נוכחית</Text>
                  <View style={styles.inputContainer}>
                    <Input variant="outline" size="lg" style={styles.input}>
                      <InputField
                        placeholder="הזן סיסמה נוכחית"
                        placeholderTextColor={Colors.gray[400]}
                        value={currentPassword}
                        onChangeText={setCurrentPassword}
                        secureTextEntry
                        autoCapitalize="none"
                        style={styles.inputField}
                      />
                    </Input>
                  </View>
                </VStack>

                {/* New Password */}
                <VStack space="xs">
                  <Text style={styles.label}>סיסמה חדשה</Text>
                  <View style={styles.inputContainer}>
                    <Input variant="outline" size="lg" style={styles.input}>
                      <InputField
                        placeholder="הזן סיסמה חדשה (לפחות 8 תווים)"
                        placeholderTextColor={Colors.gray[400]}
                        value={newPassword}
                        onChangeText={setNewPassword}
                        secureTextEntry
                        autoCapitalize="none"
                        style={styles.inputField}
                      />
                    </Input>
                  </View>
                </VStack>

                {/* Confirm Password */}
                <VStack space="xs">
                  <Text style={styles.label}>אימות סיסמה חדשה</Text>
                  <View style={styles.inputContainer}>
                    <Input variant="outline" size="lg" style={styles.input}>
                      <InputField
                        placeholder="הזן שוב את הסיסמה החדשה"
                        placeholderTextColor={Colors.gray[400]}
                        value={confirmPassword}
                        onChangeText={setConfirmPassword}
                        secureTextEntry
                        autoCapitalize="none"
                        style={styles.inputField}
                      />
                    </Input>
                  </View>
                </VStack>

                {/* Submit Button */}
                <Pressable
                  style={({ pressed }) => [
                    styles.submitButton,
                    pressed && styles.buttonPressed,
                    isLoading && styles.submitButtonDisabled,
                  ]}
                  onPress={handleChangePassword}
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <ActivityIndicator color={Colors.white} />
                  ) : (
                    <Text style={styles.submitButtonText}>שנה סיסמה</Text>
                  )}
                </Pressable>
              </VStack>
            </Box>

            {/* Info Note */}
            <Box style={styles.infoNote}>
              <Text style={styles.infoNoteText}>
                הסיסמה החדשה חייבת להכיל לפחות 8 תווים
              </Text>
            </Box>
          </VStack>
        </ScrollView>
      </LinearGradient>
    </Box>
  );
};

/**
 * Styles
 */
const styles = StyleSheet.create({
  gradient: {
    flex: 1,
    paddingTop: 20,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginTop: 40,
    marginBottom: 16,
  },
  spacer: {
    width: 40,
  },
  backButton: {
    padding: 8,
  },
  backIcon: {
    fontSize: 32,
    color: Colors.white,
    fontWeight: 'bold',
  },
  buttonPressed: {
    opacity: 0.7,
  },
  logoWrapper: {
    width: 100,
    height: 100,
    borderRadius: 50,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    justifyContent: 'center',
    alignItems: 'center',
    marginBottom: 16,
    padding: 15,
  },
  logo: {
    width: '100%',
    height: '100%',
  },
  title: {
    fontSize: 28,
    fontWeight: 'bold',
    color: Colors.white,
    textAlign: 'center',
    marginBottom: 8,
    writingDirection: 'rtl',
  },
  subtitle: {
    fontSize: 16,
    color: 'rgba(255, 255, 255, 0.9)',
    textAlign: 'center',
    writingDirection: 'rtl',
  },
  formCard: {
    backgroundColor: Colors.white,
    borderRadius: 20,
    padding: 24,
    marginTop: 24,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.1,
    shadowRadius: 12,
    elevation: 5,
  },
  label: {
    fontSize: 14,
    fontWeight: '600',
    color: Colors.textDark,
    textAlign: 'right',
    writingDirection: 'rtl',
    marginBottom: 8,
  },
  inputContainer: {
    width: '100%',
  },
  input: {
    backgroundColor: Colors.white,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: Colors.gray[300],
    minHeight: 52,
    height: 52,
  },
  inputField: {
    textAlign: 'right',
    writingDirection: 'rtl',
    fontSize: 16,
    color: Colors.textDark,
    paddingHorizontal: 16,
    height: '100%',
  },
  submitButton: {
    backgroundColor: Colors.accent,
    paddingVertical: 16,
    paddingHorizontal: 32,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
    marginTop: 8,
  },
  submitButtonDisabled: {
    opacity: 0.6,
  },
  submitButtonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.white,
    writingDirection: 'rtl',
  },
  infoNote: {
    backgroundColor: 'rgba(255, 255, 255, 0.1)',
    padding: 16,
    borderRadius: 12,
    marginTop: 24,
  },
  infoNoteText: {
    fontSize: 13,
    color: 'rgba(255, 255, 255, 0.8)',
    textAlign: 'center',
    lineHeight: 20,
    writingDirection: 'rtl',
  },
});

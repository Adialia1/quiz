import React, { useState } from 'react';
import {
  StyleSheet,
  View,
  Text,
  TextInput,
  Pressable,
  KeyboardAvoidingView,
  Platform,
  ScrollView,
  ActivityIndicator,
  Alert,
  Linking,
} from 'react-native';
import { useSignIn, useSignUp, useOAuth } from '@clerk/clerk-expo';
import { useAuthStore } from '../stores/authStore';
import { Colors } from '../config/colors';
import * as WebBrowser from 'expo-web-browser';

interface AuthScreenProps {
  onAuthSuccess: () => void;
  onBack?: () => void;
}

/**
 * תרגום הודעות שגיאה של Clerk לעברית
 * Translate Clerk error messages to Hebrew
 */
const translateClerkError = (errorMessage: string): string => {
  const errorMap: Record<string, string> = {
    "Couldn't find your account.": "לא נמצא חשבון עם פרטים אלו",
    "Password is incorrect. Try again, or use another method.": "הסיסמה שגויה. נסה שוב או השתמש בשיטה אחרת",
    "Enter a valid email address": "הזן כתובת אימייל תקינה",
    "Password is too short": "הסיסמה קצרה מדי",
    "Password must be at least 8 characters": "הסיסמה חייבת להכיל לפחות 8 תווים",
    "Passwords must be 8 characters or more.": "הסיסמה חייבת להכיל לפחות 8 תווים",
    "Password has been found in an online data breach. For account safety, please use a different password.": "הסיסמה נמצאה בדליפת מידע מקוונת. לביטחון החשבון, אנא השתמש בסיסמה אחרת",
    "That email address is taken. Please try another.": "כתובת האימייל כבר קיימת במערכת. נסה כתובת אחרת",
    "Incorrect email or password": "אימייל או סיסמה שגויים",
    "Too many requests": "יותר מדי ניסיונות. נסה שוב מאוחר יותר",
    "Invalid verification code": "קוד אימות שגוי",
    "Verification code is incorrect": "קוד אימות שגוי",
    "Code has expired": "פג תוקף הקוד",
    "The code you entered is invalid": "הקוד שהזנת אינו תקין",
  };

  // חיפוש תרגום מדויק
  if (errorMap[errorMessage]) {
    return errorMap[errorMessage];
  }

  // חיפוש חלקי
  for (const [englishError, hebrewError] of Object.entries(errorMap)) {
    if (errorMessage.includes(englishError)) {
      return hebrewError;
    }
  }

  // ברירת מחדל
  return 'שגיאה בתהליך. אנא נסה שוב';
};

// Complete OAuth sign-in/up flow
WebBrowser.maybeCompleteAuthSession();

/**
 * מסך התחברות והרשמה
 * Authentication Screen (Login & Register)
 */
export const AuthScreen: React.FC<AuthScreenProps> = ({ onAuthSuccess, onBack }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [loading, setLoading] = useState(false);
  const [socialLoading, setSocialLoading] = useState<'google' | 'apple' | null>(null);
  const [error, setError] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [pendingVerification, setPendingVerification] = useState(false);

  const { signIn, setActive: setActiveSignIn } = useSignIn();
  const { signUp, setActive: setActiveSignUp } = useSignUp();
  const { login } = useAuthStore();

  // OAuth hooks for social login
  const googleOAuth = useOAuth({ strategy: 'oauth_google' });
  const appleOAuth = useOAuth({ strategy: 'oauth_apple' });

  // התחברות - Login
  const handleLogin = async () => {
    if (!email || !password) {
      setError('אנא מלא את כל השדות');
      return;
    }

    try {
      setLoading(true);
      setError('');

      const result = await signIn?.create({
        identifier: email,
        password,
      });

      if (result?.status === 'complete') {
        await setActiveSignIn?.({ session: result.createdSessionId });

        // עדכון חנות המצב
        login({
          id: result.createdSessionId || '',
          email: email,
        });

        onAuthSuccess();
      }
    } catch (err: any) {
      console.log('Login error:', err);
      console.log('Error details:', JSON.stringify(err, null, 2));
      const errorMessage = err.errors?.[0]?.message || err.message || 'שגיאה בהתחברות';
      console.log('Error message:', errorMessage);
      setError(translateClerkError(errorMessage));
    } finally {
      setLoading(false);
    }
  };

  // הרשמה - Register
  const handleRegister = async () => {
    console.log('🔵 handleRegister called');
    console.log('📧 Email:', email);
    console.log('👤 First Name:', firstName);
    console.log('👤 Last Name:', lastName);
    console.log('🔒 Password length:', password.length);

    if (!email || !password || !firstName || !lastName) {
      console.log('❌ Missing fields');
      setError('אנא מלא את כל השדות');
      return;
    }

    try {
      setLoading(true);
      setError('');

      console.log('📤 Calling Clerk signUp.create...');
      const result = await signUp?.create({
        emailAddress: email,
        password,
        firstName,
        lastName,
      });

      console.log('📥 SignUp result status:', result?.status);
      console.log('📥 SignUp result createdSessionId:', result?.createdSessionId);

      // אימות אימייל (אם נדרש)
      if (result?.status === 'missing_requirements') {
        console.log('📧 Email verification required');
        // שלח קוד אימות
        await signUp?.prepareEmailAddressVerification({ strategy: 'email_code' });
        setPendingVerification(true);
        setError('');
        console.log('✅ Verification email sent! Check your inbox.');
        return; // Wait for user to enter code
      }

      if (result?.status === 'complete') {
        console.log('✅ Registration successful!');
        await setActiveSignUp?.({ session: result.createdSessionId });

        // עדכון חנות המצב
        await login({
          id: result.createdSessionId || '',
          email: email,
          firstName,
          lastName,
        });

        console.log('✅ User saved to storage');
        onAuthSuccess();
      }
    } catch (err: any) {
      console.log('❌ Registration error:', err.message);
      console.log('❌ Error errors array:', err.errors);
      const errorMessage = err.errors?.[0]?.message || err.message || 'שגיאה בהרשמה';
      console.log('❌ Final error message:', errorMessage);
      setError(translateClerkError(errorMessage));
    } finally {
      setLoading(false);
    }
  };

  // אימות קוד אימייל - Verify Email Code
  const handleVerifyEmail = async () => {
    if (!verificationCode || verificationCode.length !== 6) {
      setError('אנא הזן קוד בן 6 ספרות');
      return;
    }

    try {
      setLoading(true);
      setError('');

      console.log('🔐 Verifying email with code:', verificationCode);
      const result = await signUp?.attemptEmailAddressVerification({
        code: verificationCode,
      });

      console.log('📥 Verification result status:', result?.status);

      if (result?.status === 'complete') {
        console.log('✅ Email verified successfully!');
        await setActiveSignUp?.({ session: result.createdSessionId });

        // עדכון חנות המצב
        await login({
          id: result.createdSessionId || '',
          email: email,
          firstName,
          lastName,
        });

        console.log('✅ User saved to storage');
        onAuthSuccess();
      }
    } catch (err: any) {
      console.log('❌ Verification error:', err.message);
      console.log('❌ Error errors array:', err.errors);
      const errorMessage = err.errors?.[0]?.message || err.message || 'שגיאה באימות';
      setError(translateClerkError(errorMessage));
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setIsLogin(!isLogin);
    setError('');
    setPendingVerification(false);
    setVerificationCode('');
  };

  // Social Login Handlers
  const handleSocialLogin = async (strategy: 'google' | 'apple') => {
    try {
      setSocialLoading(strategy);
      setError('');

      if (__DEV__) {
        console.log(`🔵 Starting ${strategy} OAuth flow...`);
        console.log(`📱 Platform: ${Platform.OS}, Device: ${Platform.isPad ? 'iPad' : 'iPhone'}`);
      }

      const oAuthFlow = strategy === 'google' ? googleOAuth : appleOAuth;

      // Ensure OAuth flow is ready
      if (!oAuthFlow || !oAuthFlow.startOAuthFlow) {
        throw new Error(`OAuth provider for ${strategy} is not initialized`);
      }

      // Start OAuth flow with timeout protection (30 seconds)
      const oauthPromise = oAuthFlow.startOAuthFlow();
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('OAuth timeout - please try again')), 30000)
      );

      const { createdSessionId, setActive, signIn, signUp } = await Promise.race([
        oauthPromise,
        timeoutPromise
      ]) as any;

      if (__DEV__) {
        console.log(`📥 OAuth response:`, { createdSessionId, hasSetActive: !!setActive });
      }

      if (createdSessionId && setActive) {
        // OAuth successful
        await setActive({ session: createdSessionId });

        // Get user info and save to store
        await login({
          id: createdSessionId,
          email: '',  // Will be filled by Clerk
          firstName: '',
          lastName: '',
        });

        if (__DEV__) {
          console.log(`✅ ${strategy} sign-in successful`);
        }

        onAuthSuccess();
      } else {
        if (__DEV__) {
          console.error(`❌ ${strategy} OAuth incomplete - missing session or setActive`);
        }
        throw new Error('OAuth flow did not complete successfully');
      }
    } catch (err: any) {
      if (__DEV__) {
        console.error(`❌ ${strategy} sign-in error:`, err);
        console.error(`❌ Error details:`, JSON.stringify(err, null, 2));
      }

      // Handle specific OAuth errors
      if (err.message?.includes('cancelled') ||
          err.message?.includes('canceled') ||
          err.code === 'user_cancelled' ||
          err.code === 'user_canceled' ||
          err.message?.includes("The operation couldn't be completed")) {
        // User cancelled - silently ignore
        if (__DEV__) {
          console.log('User cancelled OAuth flow');
        }
        return;
      }

      // Handle timeout
      if (err.message?.includes('timeout')) {
        setError('הזמן תם. אנא נסה שוב');
        return;
      }

      // Handle network errors
      if (err.message?.includes('network') || err.message?.includes('Network')) {
        setError('שגיאת רשת. בדוק את החיבור לאינטרנט ונסה שוב');
        return;
      }

      // Show generic error message (don't expose technical details in production)
      const errorMessage = err.errors?.[0]?.message || err.message || 'Unknown error';
      if (__DEV__) {
        console.error(`❌ Final error message:`, errorMessage);
      }

      // Use a friendlier error message
      setError(
        strategy === 'google'
          ? 'שגיאה בהתחברות עם Google. אנא נסה שוב'
          : 'שגיאה בהתחברות עם Apple. אנא נסה שוב'
      );
    } finally {
      setSocialLoading(null);
    }
  };

  // Helper function to open URLs
  const openURL = async (url: string) => {
    const canOpen = await Linking.canOpenURL(url);
    if (canOpen) {
      await Linking.openURL(url);
    } else {
      Alert.alert('שגיאה', 'לא ניתן לפתוח את הקישור');
    }
  };

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <ScrollView
        contentContainerStyle={styles.scrollContainer}
        keyboardShouldPersistTaps="handled"
      >
        {/* Back button (if onBack provided - for guest mode) */}
        {onBack && (
          <Pressable
            style={styles.backToGuestButton}
            onPress={onBack}
          >
            <Text style={styles.backToGuestButtonText}>← חזור למצב אורח</Text>
          </Pressable>
        )}

        <View style={styles.header}>
          <Text style={styles.title}>
            {pendingVerification ? 'אימות אימייל' : (isLogin ? 'התחברות' : 'הרשמה')}
          </Text>
          <Text style={styles.subtitle}>
            {pendingVerification
              ? `שלחנו קוד אימות לכתובת ${email}\nאנא הזן את הקוד כדי להשלים את ההרשמה`
              : (isLogin
                ? 'ברוך שובך! אנא התחבר כדי להמשיך'
                : 'צור חשבון חדש כדי להתחיל')}
          </Text>
        </View>

        <View style={styles.form}>
          {/* טופס אימות אימייל */}
          {pendingVerification ? (
            <>
              <View style={styles.inputContainer}>
                <Text style={styles.label}>קוד אימות</Text>
                <TextInput
                  style={styles.input}
                  value={verificationCode}
                  onChangeText={setVerificationCode}
                  placeholder="הזן קוד בן 6 ספרות"
                  placeholderTextColor="#999"
                  keyboardType="number-pad"
                  maxLength={6}
                  textAlign="center"
                />
              </View>

              {/* הצגת שגיאה */}
              {error ? <Text style={styles.error}>{error}</Text> : null}

              {/* כפתור אימות */}
              <Pressable
                style={({ pressed }) => [
                  styles.button,
                  pressed && styles.buttonPressed,
                  loading && styles.buttonDisabled,
                ]}
                onPress={handleVerifyEmail}
                disabled={loading}
              >
                {loading ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <Text style={styles.buttonText}>אמת אימייל</Text>
                )}
              </Pressable>

              {/* כפתור חזרה */}
              <Pressable
                style={styles.backButton}
                onPress={() => {
                  setPendingVerification(false);
                  setVerificationCode('');
                  setError('');
                }}
              >
                <Text style={styles.backButtonText}>חזור לטופס הרשמה</Text>
              </Pressable>
            </>
          ) : (
            <>
              {/* שדות הרשמה בלבד */}
              {!isLogin && (
            <>
              <View style={styles.inputContainer}>
                <Text style={styles.label}>שם פרטי</Text>
                <TextInput
                  style={styles.input}
                  value={firstName}
                  onChangeText={setFirstName}
                  placeholder="הזן שם פרטי"
                  placeholderTextColor="#999"
                  textAlign="right"
                />
              </View>

              <View style={styles.inputContainer}>
                <Text style={styles.label}>שם משפחה</Text>
                <TextInput
                  style={styles.input}
                  value={lastName}
                  onChangeText={setLastName}
                  placeholder="הזן שם משפחה"
                  placeholderTextColor="#999"
                  textAlign="right"
                />
              </View>
            </>
          )}

          {/* שדות משותפים */}
          <View style={styles.inputContainer}>
            <Text style={styles.label}>אימייל</Text>
            <TextInput
              style={styles.input}
              value={email}
              onChangeText={setEmail}
              placeholder="הזן כתובת אימייל"
              placeholderTextColor="#999"
              keyboardType="email-address"
              autoCapitalize="none"
              textAlign="right"
            />
          </View>

          <View style={styles.inputContainer}>
            <Text style={styles.label}>סיסמה</Text>
            <TextInput
              style={styles.input}
              value={password}
              onChangeText={setPassword}
              placeholder="הזן סיסמה"
              placeholderTextColor="#999"
              secureTextEntry
              textAlign="right"
            />
          </View>

          {/* הצגת שגיאה */}
          {error ? <Text style={styles.error}>{error}</Text> : null}

          {/* כפתור פעולה */}
          <Pressable
            style={({ pressed }) => [
              styles.button,
              pressed && styles.buttonPressed,
              loading && styles.buttonDisabled,
            ]}
            onPress={() => {
              console.log('🟢 Button pressed! Mode:', isLogin ? 'Login' : 'Register');
              if (isLogin) {
                handleLogin();
              } else {
                handleRegister();
              }
            }}
            disabled={loading}
          >
            {loading ? (
              <ActivityIndicator color="#FFFFFF" />
            ) : (
              <Text style={styles.buttonText}>
                {isLogin ? 'התחבר' : 'הירשם'}
              </Text>
            )}
          </Pressable>

          {/* Privacy Policy & Terms - Only show for registration */}
          {!isLogin && (
            <View style={styles.legalTextContainer}>
              <Text style={styles.legalText}>
                בלחיצה על "הירשם" אתה מאשר את{' '}
              </Text>
              <View style={styles.legalLinksRow}>
                <Pressable onPress={() => openURL('https://www.ethicaplus.net/terms')}>
                  <Text style={styles.legalLink}>תנאי השימוש</Text>
                </Pressable>
                <Text style={styles.legalText}> ואת </Text>
                <Pressable onPress={() => openURL('https://www.ethicaplus.net/privacy-policy')}>
                  <Text style={styles.legalLink}>מדיניות הפרטיות</Text>
                </Pressable>
              </View>
            </View>
          )}

          {/* Social Login Section */}
          <View style={styles.socialSection}>
            {/* Divider */}
            <View style={styles.divider}>
              <View style={styles.dividerLine} />
              <Text style={styles.dividerText}>או</Text>
              <View style={styles.dividerLine} />
            </View>

            {/* Google Sign In */}
            <Pressable
              style={({ pressed }) => [
                styles.socialButton,
                pressed && styles.socialButtonPressed,
                socialLoading === 'google' && styles.buttonDisabled,
              ]}
              onPress={() => handleSocialLogin('google')}
              disabled={socialLoading !== null}
            >
              {socialLoading === 'google' ? (
                <ActivityIndicator color="#4285F4" />
              ) : (
                <>
                  <Text style={styles.googleIcon}>G</Text>
                  <Text style={styles.socialButtonText}>
                    {isLogin ? 'התחבר עם Google' : 'הירשם עם Google'}
                  </Text>
                </>
              )}
            </Pressable>

            {/* Apple Sign In - iOS and iPadOS */}
            {Platform.OS === 'ios' && (
              <Pressable
                style={({ pressed }) => [
                  styles.socialButton,
                  styles.appleButton,
                  pressed && styles.socialButtonPressed,
                  socialLoading === 'apple' && styles.buttonDisabled,
                ]}
                onPress={() => handleSocialLogin('apple')}
                disabled={socialLoading !== null}
                accessible={true}
                accessibilityLabel={isLogin ? 'התחבר עם Apple' : 'הירשם עם Apple'}
                accessibilityRole="button"
                accessibilityState={{ disabled: socialLoading !== null }}
              >
                {socialLoading === 'apple' ? (
                  <ActivityIndicator color="#FFFFFF" />
                ) : (
                  <>
                    <Text style={styles.appleIcon}></Text>
                    <Text style={styles.appleButtonText}>
                      {isLogin ? 'התחבר עם Apple' : 'הירשם עם Apple'}
                    </Text>
                  </>
                )}
              </Pressable>
            )}
          </View>

          {/* מעבר בין מצבים */}
          <View style={styles.toggleContainer}>
            <Pressable onPress={toggleMode}>
              <Text style={styles.toggleText}>
                {isLogin ? 'אין לך חשבון? ' : 'כבר יש לך חשבון? '}
                <Text style={styles.toggleLink}>
                  {isLogin ? 'הירשם' : 'התחבר'}
                </Text>
              </Text>
            </Pressable>
          </View>
            </>
          )}
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#FFFFFF',
  },
  scrollContainer: {
    flexGrow: 1,
    padding: 24,
    justifyContent: 'center',
  },
  backToGuestButton: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    marginBottom: 16,
    alignSelf: 'flex-start',
  },
  backToGuestButtonText: {
    fontSize: 16,
    color: Colors.primary,
    fontWeight: '600',
  },
  header: {
    marginBottom: 32,
  },
  title: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#212121',
    marginBottom: 8,
    textAlign: 'center',
  },
  subtitle: {
    fontSize: 16,
    color: '#757575',
    textAlign: 'center',
  },
  form: {
    gap: 16,
    alignItems: 'flex-end',
  },
  inputContainer: {
    gap: 8,
    width: '100%',
  },
  label: {
    fontSize: 16,
    fontWeight: '600',
    color: '#424242',
    alignSelf: 'flex-end',
    textAlign: 'right',
  },
  input: {
    backgroundColor: '#F5F5F5',
    borderRadius: 12,
    padding: 16,
    fontSize: 16,
    color: '#212121',
    borderWidth: 1,
    borderColor: '#E0E0E0',
    textAlign: 'right',
    width: '100%',
  },
  error: {
    color: '#F44336',
    fontSize: 14,
    textAlign: 'center',
    marginTop: 8,
    width: '100%',
    alignSelf: 'center',
  },
  button: {
    backgroundColor: Colors.primary,
    paddingVertical: 16,
    borderRadius: 12,
    alignItems: 'center',
    marginTop: 16,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
    width: '100%',
    alignSelf: 'stretch',
  },
  buttonPressed: {
    opacity: 0.8,
    transform: [{ scale: 0.98 }],
  },
  buttonDisabled: {
    opacity: 0.6,
  },
  buttonText: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.white,
  },
  toggleContainer: {
    marginTop: 24,
    alignItems: 'center',
    width: '100%',
    alignSelf: 'center',
  },
  toggleText: {
    fontSize: 14,
    color: Colors.gray[600],
    textAlign: 'center',
  },
  toggleLink: {
    color: Colors.primary,
    fontWeight: '600',
  },
  backButton: {
    marginTop: 16,
    paddingVertical: 12,
    alignItems: 'center',
  },
  backButtonText: {
    fontSize: 14,
    color: Colors.gray[600],
    textDecorationLine: 'underline',
  },
  socialSection: {
    width: '100%',
    marginTop: 20,
    gap: 12,
  },
  divider: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 10,
  },
  dividerLine: {
    flex: 1,
    height: 1,
    backgroundColor: '#E0E0E0',
  },
  dividerText: {
    marginHorizontal: 10,
    color: '#757575',
    fontSize: 14,
  },
  socialButton: {
    backgroundColor: '#FFFFFF',
    borderRadius: 12,
    padding: 14,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: '#E0E0E0',
    width: '100%',
    gap: 8,
  },
  socialButtonPressed: {
    backgroundColor: '#F5F5F5',
  },
  appleButton: {
    backgroundColor: '#000000',
    borderColor: '#000000',
    minHeight: 50, // Ensure minimum touch target on iPad
  },
  socialButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#424242',
  },
  appleButtonText: {
    fontSize: 16,
    fontWeight: '600',
    color: '#FFFFFF',
  },
  googleIcon: {
    fontSize: 20,
    fontWeight: 'bold',
    color: '#4285F4',
  },
  appleIcon: {
    fontSize: 20,
    color: '#FFFFFF',
  },
  legalTextContainer: {
    marginTop: 12,
    marginBottom: 8,
    width: '100%',
    alignItems: 'center',
  },
  legalLinksRow: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    justifyContent: 'center',
  },
  legalText: {
    fontSize: 12,
    color: Colors.gray[600],
    textAlign: 'center',
    lineHeight: 18,
  },
  legalLink: {
    fontSize: 12,
    color: Colors.primary,
    textDecorationLine: 'underline',
    fontWeight: '600',
  },
});

import React, { useState, useEffect } from 'react';
import {
  Box,
  VStack,
  HStack,
  Heading,
  Text,
  Button,
  ButtonText,
  Input,
  InputField,
  Textarea,
  TextareaInput,
  ScrollView,
  Spinner,
  Pressable,
  Center,
} from '@gluestack-ui/themed';
import { Alert, StyleSheet, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { MaterialIcons, Ionicons } from '@expo/vector-icons';
import * as DocumentPicker from 'expo-document-picker';
import axios from 'axios';
import { API_URL } from '../config/constants';
import { Colors } from '../config/colors';
import { useNavigation } from '@react-navigation/native';
import { useAuth } from '@clerk/clerk-expo';

/**
 * AdminScreen
 * פאנל ניהול למנהלים בלבד
 * Admin panel for sending notifications and ingesting data
 */
export const AdminScreen: React.FC = () => {
  const navigation = useNavigation();
  const { getToken } = useAuth();

  // Notification state
  const [notifTitle, setNotifTitle] = useState('');
  const [notifBody, setNotifBody] = useState('');
  const [sendingNotif, setSendingNotif] = useState(false);

  // Ingestion state
  const [ingesting, setIngesting] = useState(false);
  const [ingestionType, setIngestionType] = useState<'legal' | 'exam' | null>(null);

  // Stats state
  const [stats, setStats] = useState<any>(null);
  const [loadingStats, setLoadingStats] = useState(false);

  // Load stats on mount
  useEffect(() => {
    loadStats();
  }, []);

  /**
   * Load admin statistics
   */
  const loadStats = async () => {
    try {
      setLoadingStats(true);

      const token = await getToken();
      if (!token) {
        Alert.alert('שגיאה', 'לא נמצא טוקן אימות');
        return;
      }

      const response = await axios.get(`${API_URL}/api/admin/stats`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      });

      setStats(response.data.stats);
    } catch (error: any) {
      console.error('Failed to load stats:', error);
      Alert.alert('שגיאה', 'שגיאה בטעינת סטטיסטיקות. ודא שיש לך הרשאות מנהל.');
    } finally {
      setLoadingStats(false);
    }
  };

  /**
   * Send push notification to all users
   */
  const handleSendNotification = async () => {
    if (!notifTitle.trim() || !notifBody.trim()) {
      Alert.alert('שגיאה', 'נא למלא כותרת ותוכן');
      return;
    }

    try {
      setSendingNotif(true);

      const token = await getToken();
      if (!token) {
        Alert.alert('שגיאה', 'לא נמצא טוקן אימות');
        return;
      }

      const response = await axios.post(
        `${API_URL}/api/notifications/send`,
        {
          title: notifTitle,
          body: notifBody,
        },
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json',
          },
        }
      );

      Alert.alert('הצלחה! 🎉', `התראה נשלחה בהצלחה ל-${response.data.sent} משתמשים`);
      setNotifTitle('');
      setNotifBody('');
    } catch (error: any) {
      console.error('Failed to send notification:', error);
      Alert.alert('שגיאה', error.response?.data?.detail || 'שגיאה בשליחת התראה');
    } finally {
      setSendingNotif(false);
    }
  };

  /**
   * Pick and upload legal document
   */
  const handleIngestLegalDoc = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: 'application/pdf',
        copyToCacheDirectory: true,
      });

      if (result.canceled || !result.assets || result.assets.length === 0) {
        return;
      }

      const file = result.assets[0];

      setIngesting(true);
      setIngestionType('legal');

      const token = await getToken();
      if (!token) {
        Alert.alert('שגיאה', 'לא נמצא טוקן אימות');
        return;
      }

      const formData = new FormData();
      formData.append('file', {
        uri: file.uri,
        type: 'application/pdf',
        name: file.name,
      } as any);

      const response = await axios.post(
        `${API_URL}/api/admin/ingest/legal-docs`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            // Don't set Content-Type - axios will set it automatically with boundary
          },
          timeout: 120000, // 2 minutes
        }
      );

      Alert.alert('הצלחה! 🎉', `${response.data.total_inserted} חלקים הוכנסו למאגר`);
      loadStats(); // Refresh stats
    } catch (error: any) {
      console.error('Failed to ingest legal doc:', error);
      Alert.alert('שגיאה', error.response?.data?.detail || 'שגיאה בהכנסת מסמך');
    } finally {
      setIngesting(false);
      setIngestionType(null);
    }
  };

  /**
   * Pick and upload exam questions PDF
   */
  const handleIngestExamQuestions = async () => {
    try {
      const result = await DocumentPicker.getDocumentAsync({
        type: 'application/pdf',
        copyToCacheDirectory: true,
      });

      if (result.canceled || !result.assets || result.assets.length === 0) {
        return;
      }

      const file = result.assets[0];

      setIngesting(true);
      setIngestionType('exam');

      const token = await getToken();
      if (!token) {
        Alert.alert('שגיאה', 'לא נמצא טוקן אימות');
        return;
      }

      const formData = new FormData();
      formData.append('file', {
        uri: file.uri,
        type: 'application/pdf',
        name: file.name,
      } as any);

      const response = await axios.post(
        `${API_URL}/api/admin/ingest/exam-questions/pdf`,
        formData,
        {
          headers: {
            'Authorization': `Bearer ${token}`,
            // Don't set Content-Type - axios will set it automatically with boundary
          },
          timeout: 120000, // 2 minutes
        }
      );

      Alert.alert('הצלחה! 🎉', `${response.data.total_inserted} שאלות הוכנסו למאגר`);
      loadStats(); // Refresh stats
    } catch (error: any) {
      console.error('Failed to ingest exam questions:', error);
      Alert.alert('שגיאה', error.response?.data?.detail || 'שגיאה בהכנסת שאלות');
    } finally {
      setIngesting(false);
      setIngestionType(null);
    }
  };

  return (
    <SafeAreaView style={styles.container} edges={['top']}>
      {/* Header */}
      <View style={styles.header}>
        <Pressable onPress={() => navigation.goBack()} style={styles.backButton}>
          <MaterialIcons name="arrow-forward" size={24} color={Colors.textPrimary} />
        </Pressable>
        <View style={styles.headerTitle}>
          <Heading size="xl" color={Colors.textPrimary}>
            ניהול מערכת
          </Heading>
          <Text size="sm" color={Colors.textSecondary}>
            פאנל מנהל
          </Text>
        </View>
        <View style={{ width: 40 }} />
      </View>

      <ScrollView style={styles.content} showsVerticalScrollIndicator={false}>
        <Center>
          <VStack space="lg" w="$full" maxWidth={600}>
            {/* Statistics Card */}
          <Box bg={Colors.white} borderRadius="$xl" p="$5" style={styles.card}>
            <HStack justifyContent="space-between" alignItems="center" mb="$4">
              <HStack space="sm" alignItems="center">
                <View style={[styles.iconContainer, { backgroundColor: Colors.primary + '15' }]}>
                  <Ionicons name="stats-chart" size={20} color={Colors.primary} />
                </View>
                <Heading size="md">סטטיסטיקות מערכת</Heading>
              </HStack>
              <Button size="sm" variant="outline" onPress={loadStats} isDisabled={loadingStats}>
                <ButtonText>רענן</ButtonText>
              </Button>
            </HStack>

            {loadingStats && (
              <Box py="$4" alignItems="center">
                <Spinner size="large" color={Colors.primary} />
              </Box>
            )}

            {stats && !loadingStats && (
              <VStack space="sm">
                <StatRow label="מסמכים משפטיים" value={stats.legal_doc_chunks || 0} color={Colors.primary} />
                <StatRow label="שאלות מבחן" value={stats.exam_questions || 0} color={Colors.primary} />
                <StatRow label="שאלות AI" value={stats.ai_generated_questions || 0} color={Colors.primary} />
                <StatRow label="מושגים" value={stats.concepts || 0} color={Colors.primary} />
                <View style={styles.divider} />
                <StatRow label="משתמשים" value={stats.users || 0} color={Colors.success} />
                <StatRow label="מבחנים" value={stats.exams || 0} color={Colors.success} />
              </VStack>
            )}

            {!stats && !loadingStats && (
              <Text color={Colors.textSecondary} textAlign="center">
                לחץ על "רענן" לטעינת סטטיסטיקות
              </Text>
            )}
          </Box>

          {/* Send Notification Card */}
          <Box bg={Colors.white} borderRadius="$xl" p="$5" style={styles.card}>
            <HStack space="sm" alignItems="center" mb="$4">
              <View style={[styles.iconContainer, { backgroundColor: Colors.accent + '15' }]}>
                <Ionicons name="notifications" size={20} color={Colors.accent} />
              </View>
              <Heading size="md">שליחת התראה</Heading>
            </HStack>

            <VStack space="lg">
              <VStack space="xs">
                <Text size="sm" fontWeight="$medium" color={Colors.textPrimary}>
                  כותרת:
                </Text>
                <Input variant="outline" size="md">
                  <InputField
                    value={notifTitle}
                    onChangeText={setNotifTitle}
                    placeholder="לדוגמה: זמן ללמוד! 📚"
                    style={{ textAlign: 'right' }}
                  />
                </Input>
              </VStack>

              <VStack space="xs">
                <Text size="sm" fontWeight="$medium" color={Colors.textPrimary}>
                  תוכן:
                </Text>
                <Textarea size="md">
                  <TextareaInput
                    value={notifBody}
                    onChangeText={setNotifBody}
                    placeholder="לדוגמה: הגיע הזמן להתכונן למבחן שלך"
                    numberOfLines={4}
                    style={{ textAlign: 'right' }}
                  />
                </Textarea>
              </VStack>

              <Button
                onPress={handleSendNotification}
                isDisabled={sendingNotif}
                bg={Colors.success}
                size="md"
              >
                {sendingNotif ? (
                  <HStack space="sm" alignItems="center">
                    <Spinner size="small" color="$white" />
                    <ButtonText>שולח...</ButtonText>
                  </HStack>
                ) : (
                  <HStack space="sm" alignItems="center">
                    <Ionicons name="send" size={18} color="white" />
                    <ButtonText>שלח לכל המשתמשים</ButtonText>
                  </HStack>
                )}
              </Button>
            </VStack>
          </Box>

          {/* Data Ingestion Card */}
          <Box bg={Colors.white} borderRadius="$xl" p="$5" style={styles.card}>
            <HStack space="sm" alignItems="center" mb="$4">
              <View style={[styles.iconContainer, { backgroundColor: Colors.info + '15' }]}>
                <Ionicons name="cloud-upload" size={20} color={Colors.info} />
              </View>
              <Heading size="md">הכנסת נתונים</Heading>
            </HStack>

            <VStack space="md">
              <UploadButton
                label="מסמכים משפטיים (PDF)"
                description="OCR + חלוקה סמנטית + embeddings"
                icon="document-text"
                onPress={handleIngestLegalDoc}
                isLoading={ingesting && ingestionType === 'legal'}
                isDisabled={ingesting}
              />

              <UploadButton
                label="שאלות מבחן (PDF)"
                description="ניתוח AI + אימות + embeddings"
                icon="help-circle"
                onPress={handleIngestExamQuestions}
                isLoading={ingesting && ingestionType === 'exam'}
                isDisabled={ingesting}
              />

              <Box bg={Colors.secondaryLight} p="$3" borderRadius="$md">
                <Text size="sm" color={Colors.textSecondary}>
                  💡 הכנסת מסמכים עשויה לקחת מספר דקות
                </Text>
              </Box>
            </VStack>
          </Box>

            {/* Bottom spacing */}
            <Box height={32} />
          </VStack>
        </Center>
      </ScrollView>
    </SafeAreaView>
  );
};

/**
 * Stat Row Component
 */
interface StatRowProps {
  label: string;
  value: number;
  color: string;
}

const StatRow: React.FC<StatRowProps> = ({ label, value, color }) => (
  <HStack justifyContent="space-between" alignItems="center" py="$1">
    <Text color={Colors.textPrimary}>{label}</Text>
    <View style={[styles.statBadge, { backgroundColor: color + '15' }]}>
      <Text fontWeight="$bold" color={color}>
        {value.toLocaleString('he-IL')}
      </Text>
    </View>
  </HStack>
);

/**
 * Upload Button Component
 */
interface UploadButtonProps {
  label: string;
  description: string;
  icon: any;
  onPress: () => void;
  isLoading: boolean;
  isDisabled: boolean;
}

const UploadButton: React.FC<UploadButtonProps> = ({
  label,
  description,
  icon,
  onPress,
  isLoading,
  isDisabled,
}) => (
  <Pressable
    onPress={onPress}
    disabled={isDisabled}
    style={({ pressed }) => [
      styles.uploadButton,
      pressed && styles.uploadButtonPressed,
      isDisabled && styles.uploadButtonDisabled,
    ]}
  >
    <HStack space="md" alignItems="center" flex={1}>
      <View style={[styles.uploadIcon, { backgroundColor: Colors.primary + '15' }]}>
        <Ionicons name={icon} size={24} color={Colors.primary} />
      </View>
      <VStack flex={1}>
        <Text fontWeight="$semibold" color={Colors.textPrimary}>
          {label}
        </Text>
        <Text size="xs" color={Colors.textSecondary}>
          {description}
        </Text>
      </VStack>
      {isLoading ? (
        <Spinner size="small" color={Colors.primary} />
      ) : (
        <Ionicons name="chevron-back" size={20} color={Colors.textSecondary} />
      )}
    </HStack>
  </Pressable>
);

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: Colors.background,
  },
  header: {
    flexDirection: 'row-reverse',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    paddingVertical: 16,
    backgroundColor: Colors.white,
    borderBottomWidth: 1,
    borderBottomColor: Colors.gray[100],
  },
  backButton: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
  },
  headerTitle: {
    alignItems: 'center',
  },
  content: {
    flex: 1,
    padding: 20,
  },
  card: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  iconContainer: {
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: 'center',
    justifyContent: 'center',
  },
  divider: {
    height: 1,
    backgroundColor: Colors.gray[100],
    marginVertical: 8,
  },
  statBadge: {
    paddingHorizontal: 12,
    paddingVertical: 4,
    borderRadius: 12,
  },
  uploadButton: {
    backgroundColor: Colors.white,
    borderWidth: 1.5,
    borderColor: Colors.gray[200],
    borderRadius: 12,
    padding: 16,
    borderStyle: 'dashed',
  },
  uploadButtonPressed: {
    backgroundColor: Colors.gray[50],
    borderColor: Colors.primary,
  },
  uploadButtonDisabled: {
    opacity: 0.5,
  },
  uploadIcon: {
    width: 48,
    height: 48,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
});

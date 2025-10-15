import React from 'react';
import { ScrollView, Pressable, StyleSheet, View } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Image } from 'expo-image';
import { useNavigation } from '@react-navigation/native';
import { Box, VStack, Text } from '@gluestack-ui/themed';
import { Colors } from '../config/colors';

/**
 * Terms and Conditions Screen
 * Displays the app's terms of service and usage conditions
 */
export const TermsAndConditionsScreen: React.FC = () => {
  const navigation = useNavigation();

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
                  source={require('../../assets/logo2.png')}
                  style={styles.logo}
                  contentFit="contain"
                />
              </Box>
              <Text style={styles.title}>תנאי שימוש</Text>
              <Text style={styles.subtitle}>
                תנאים והגבלות לשימוש באפליקציה
              </Text>
            </VStack>

            {/* Content Card */}
            <Box style={styles.contentCard}>
              <VStack space="lg">
                {/* Section 1 */}
                <VStack space="sm">
                  <Text style={styles.sectionTitle}>1. כללי</Text>
                  <Text style={styles.paragraph}>
                    ברוכים הבאים לאפליקציית אתיקה פלוס. השימוש באפליקציה כפוף לתנאי השימוש המפורטים להלן. השימוש באפליקציה מהווה הסכמה מלאה לתנאים אלה.
                  </Text>
                </VStack>

                {/* Section 2 */}
                <VStack space="sm">
                  <Text style={styles.sectionTitle}>2. שירותי האפליקציה</Text>
                  <Text style={styles.paragraph}>
                    אפליקציית אתיקה פלוס מספקת שירותי למידה, תרגול ומבחנים בתחום האתיקה המקצועית עבור עורכי דין. השירות כולל:
                  </Text>
                  <Text style={styles.bulletPoint}>• מבחני תרגול באתיקה מקצועית</Text>
                  <Text style={styles.bulletPoint}>• סימולציית מבחני בחינה</Text>
                  <Text style={styles.bulletPoint}>• מעקב אחר התקדמות וביצועים</Text>
                  <Text style={styles.bulletPoint}>• תוכן לימודי ופלאשקארדס</Text>
                  <Text style={styles.bulletPoint}>• מנטור AI לליווי ותמיכה</Text>
                </VStack>

                {/* Section 3 */}
                <VStack space="sm">
                  <Text style={styles.sectionTitle}>3. רישיון שימוש</Text>
                  <Text style={styles.paragraph}>
                    האפליקציה מעניקה לך רישיון מוגבל, אישי ובלתי ניתן להעברה לשימוש באפליקציה למטרות אישיות בלבד. אסור להעתיק, לשנות, להפיץ או למכור חלק כלשהו מהאפליקציה או התוכן.
                  </Text>
                </VStack>

                {/* Section 4 */}
                <VStack space="sm">
                  <Text style={styles.sectionTitle}>4. מנויים ותשלומים</Text>
                  <Text style={styles.paragraph}>
                    השימוש באפליקציה כולל תכניות מנוי בתשלום. המנוי מתחדש באופן אוטומטי אלא אם כן בוטל לפני תום התקופה. ניתן לבטל את המנוי בכל עת דרך הגדרות החשבון.
                  </Text>
                  <Text style={styles.bulletPoint}>• תקופת ניסיון: 3 ימים ללא עלות</Text>
                  <Text style={styles.bulletPoint}>• מנוי חודשי: ₪19.99 לחודש</Text>
                  <Text style={styles.bulletPoint}>• מנוי רבעוני: ₪49.99 לרבעון</Text>
                  <Text style={styles.bulletPoint}>• ביטול המנוי אינו כולל החזר כספי</Text>
                </VStack>

                {/* Section 5 */}
                <VStack space="sm">
                  <Text style={styles.sectionTitle}>5. פרטיות ואבטחת מידע</Text>
                  <Text style={styles.paragraph}>
                    אנו מחויבים להגנה על פרטיותך. המידע שנאסף משמש אך ורק לשיפור השירות ולא ישותף עם צדדים שלישיים ללא הסכמתך. למידע נוסף ראה את מדיניות הפרטיות שלנו.
                  </Text>
                </VStack>

                {/* Section 6 */}
                <VStack space="sm">
                  <Text style={styles.sectionTitle}>6. תוכן ומדיניות שימוש</Text>
                  <Text style={styles.paragraph}>
                    כל התוכן באפליקציה מוגן בזכויות יוצרים ונועד למטרות חינוכיות בלבד. אסור להשתמש בתוכן למטרות מסחריות, להפיץ אותו או להעתיקו ללא אישור.
                  </Text>
                </VStack>

                {/* Section 7 */}
                <VStack space="sm">
                  <Text style={styles.sectionTitle}>7. הגבלת אחריות</Text>
                  <Text style={styles.paragraph}>
                    השימוש באפליקציה הוא על אחריותך הבלעדית. אנו לא נישא באחריות לנזקים ישירים או עקיפים הנובעים מהשימוש באפליקציה או מתכנים בה. התוכן מסופק "כמות שהוא" ללא אחריות מכל סוג.
                  </Text>
                </VStack>

                {/* Section 8 */}
                <VStack space="sm">
                  <Text style={styles.sectionTitle}>8. שינויים בתנאי השימוש</Text>
                  <Text style={styles.paragraph}>
                    אנו שומרים לעצמנו את הזכות לעדכן את תנאי השימוש מעת לעת. שינויים יכנסו לתוקף מיידית עם פרסומם באפליקציה. המשך השימוש לאחר השינויים מהווה הסכמה לתנאים המעודכנים.
                  </Text>
                </VStack>

                {/* Section 9 */}
                <VStack space="sm">
                  <Text style={styles.sectionTitle}>9. סיום השימוש</Text>
                  <Text style={styles.paragraph}>
                    אנו רשאים להשעות או לסיים את גישתך לאפליקציה בכל עת במקרה של הפרת תנאי השימוש. אתה רשאי להפסיק את השימוש בכל עת על ידי מחיקת החשבון.
                  </Text>
                </VStack>

                {/* Section 10 */}
                <VStack space="sm">
                  <Text style={styles.sectionTitle}>10. יצירת קשר</Text>
                  <Text style={styles.paragraph}>
                    לשאלות או הערות בנוגע לתנאי השימוש, ניתן ליצור קשר דרך האפליקציה או בכתובת המייל: support@ethicsplus.co.il
                  </Text>
                </VStack>

                {/* Last Updated */}
                <Box style={styles.lastUpdated}>
                  <Text style={styles.lastUpdatedText}>
                    עדכון אחרון: 15 באוקטובר 2025
                  </Text>
                </Box>
              </VStack>
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
  contentCard: {
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
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: Colors.primary,
    textAlign: 'right',
    writingDirection: 'rtl',
    marginBottom: 8,
  },
  paragraph: {
    fontSize: 15,
    color: Colors.textDark,
    textAlign: 'right',
    writingDirection: 'rtl',
    lineHeight: 24,
  },
  bulletPoint: {
    fontSize: 15,
    color: Colors.textDark,
    textAlign: 'right',
    writingDirection: 'rtl',
    lineHeight: 24,
    paddingRight: 8,
  },
  lastUpdated: {
    backgroundColor: Colors.gray[100],
    padding: 16,
    borderRadius: 12,
    marginTop: 16,
  },
  lastUpdatedText: {
    fontSize: 13,
    color: Colors.gray[600],
    textAlign: 'center',
    writingDirection: 'rtl',
  },
});

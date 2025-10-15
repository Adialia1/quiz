# מבנה הפרויקט - קוויז מבחנים

## 📁 מבנה תיקיות

```
app/
├── src/
│   ├── components/          # קומפוננטות משותפות (לעתיד)
│   ├── screens/            # מסכים
│   │   ├── WelcomeScreen.tsx      # מסך ברוכים הבאים
│   │   └── AuthScreen.tsx         # מסך התחברות/הרשמה
│   ├── stores/             # Zustand stores
│   │   └── authStore.ts           # ניהול מצב אימות
│   ├── config/             # קבצי הגדרות
│   │   ├── clerk.ts              # הגדרות Clerk
│   │   ├── gluestack.tsx         # הגדרות Gluestack UI
│   │   └── rtl.ts                # הגדרות RTL
│   ├── hooks/              # Custom React Hooks (לעתיד)
│   ├── utils/              # פונקציות עזר
│   │   ├── storage.ts            # MMKV storage utilities
│   │   └── tokenCache.ts         # Clerk token cache
│   └── types/              # TypeScript types
│       └── index.ts              # הגדרות טיפוסים
├── assets/                 # תמונות, אייקונים, פונטים
├── .env.example           # דוגמה למשתני סביבה
├── .gitignore            # קבצים להתעלם מהם ב-Git
├── App.tsx               # נקודת כניסה ראשית
├── app.json              # הגדרות Expo
├── package.json          # תלויות ופקודות
├── README.md             # תיעוד ראשי
├── SETUP.md              # מדריך התקנה מהירה
└── PROJECT_STRUCTURE.md  # קובץ זה
```

## 🎯 קבצים מרכזיים

### `App.tsx`
נקודת הכניסה הראשית של האפליקציה. מכיל:
- הגדרת ClerkProvider לאימות
- הגדרת GluestackUIProvider ל-UI
- לוגיקת ניתוב בין מסכים
- ניהול מצב אימות

### `src/stores/authStore.ts`
חנות Zustand לניהול מצב האימות:
- מצב התחברות (isAuthenticated)
- נתוני משתמש (user)
- פעולות (login, logout, hydrate)
- שמירה אוטומטית ב-MMKV

### `src/config/rtl.ts`
הגדרות RTL לתמיכה בעברית:
- אפשור RTL באפליקציה
- אכיפת RTL
- פונקציות עזר ל-RTL

### `src/utils/storage.ts`
פונקציות עזר לעבודה עם MMKV:
- שמירה וקריאה של מחרוזות
- שמירה וקריאה של אובייקטים JSON
- שמירה וקריאה של מספרים ובוליאנים
- ניקוי אחסון

### `src/screens/WelcomeScreen.tsx`
מסך ברוכים הבאים:
- עיצוב עם gradient
- הצגת תכונות עיקריות
- כפתור "בואו נתחיל"
- טקסט בעברית עם RTL

### `src/screens/AuthScreen.tsx`
מסך התחברות והרשמה:
- מעבר בין התחברות להרשמה
- טפסים עם validation
- אינטגרציה עם Clerk
- שמירת מצב ב-Zustand
- טקסט בעברית עם RTL

## 🔧 הגדרות

### `app.json`
הגדרות Expo:
- שם האפליקציה בעברית
- הגדרות iOS ו-Android
- הרשאות
- Bundle identifiers
- הגדרות EAS

### `.env.example`
משתני סביבה נדרשים:
- EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY
- EXPO_PUBLIC_REVENUECAT_API_KEY (אופציונלי)
- EXPO_PUBLIC_API_URL (אופציונלי)

## 📚 ספריות מותקנות

### Core
- `react` - React library
- `react-native` - React Native framework
- `expo` - Expo SDK
- `typescript` - TypeScript

### UI
- `@gluestack-ui/themed` - Gluestack UI v3
- `@gluestack-style/react` - Gluestack styling
- `expo-image` - מיטוב תמונות
- `expo-linear-gradient` - גרדיאנטים

### State Management
- `zustand` - ניהול מצב

### Authentication
- `@clerk/clerk-expo` - Clerk authentication
- `expo-secure-store` - אחסון מאובטח

### Storage
- `react-native-mmkv` - אחסון מהיר

### Forms
- `react-hook-form` - ניהול טפסים

### Lists
- `@shopify/flash-list` - רשימות מהירות

### Menus
- `zeego` - תפריטים

### Monetization
- `react-native-purchases` - RevenueCat

## 🚀 פקודות זמינות

```bash
# פיתוח
npm start           # פתיחת Expo Dev Server
npm run ios         # הרצה על iOS
npm run android     # הרצה על Android
npm run web         # הרצה על Web

# בדיקות (לעתיד)
npm test

# בנייה
eas build --platform ios      # בנייה ל-iOS
eas build --platform android   # בנייה ל-Android
```

## 🎨 עיצוב ו-UI

### צבעים
מוגדרים ב-`src/config/gluestack.tsx`:
- Primary: גוונים של כחול (#2196F3)
- Secondary: גוונים של ורוד
- Success, Warning, Error, Info
- Gray scale

### RTL
- כל הטקסטים מיושרים לימין
- אייקונים מותאמים ל-RTL
- פריסה הפוכה לאנגלית

## 🔒 אבטחה

- משתני סביבה לא נשמרים ב-Git
- טוקנים מוצפנים ב-MMKV
- Clerk מנהל אימות בצורה מאובטחת
- הרשאות מוגדרות במפורש

## 📱 תמיכה בפלטפורמות

- ✅ iOS
- ✅ Android
- ✅ Web (חלקית)

## 🔄 תהליך האימות

1. אפליקציה נטענת → טוען מצב מ-MMKV
2. אם משתמש מחובר → מסך ראשי
3. אם לא → מסך Welcome
4. לחיצה על "בואו נתחיל" → מסך Auth
5. הרשמה/התחברות → שמירה ב-Clerk ו-Zustand
6. מעבר למסך ראשי

## 🔜 שלבים הבאים

1. **מסכי קוויז**
   - רשימת קוויזים
   - מסך שאלות
   - מסך תוצאות

2. **אינטגרציה עם Backend**
   - חיבור ל-API
   - שליפת שאלות
   - שמירת תוצאות

3. **מוניטיזציה**
   - הגדרת RevenueCat
   - מסך מנויים
   - חסימת תוכן פרימיום

4. **בדיקות**
   - Maestro E2E tests
   - Unit tests
   - Integration tests

5. **פריסה**
   - EAS Build
   - App Store
   - Google Play

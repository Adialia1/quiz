# קוויז מבחנים - אפליקציית React Native

אפליקציית מבחנים בעברית עם תמיכה מלאה ב-RTL, נבנתה עם React Native ו-Expo.

## 🚀 טכנולוגיות

### Framework
- **React Native** - פריימוורק לפיתוח אפליקציות מובייל
- **Expo** - כלים לפיתוח ופריסה
- **TypeScript** - שפת תכנות מוקלדת

### UI & Styling
- **Gluestack UI v3** - ספריית קומפוננטות UI
- **Expo Image** - אופטימיזציה של תמונות
- **Expo Linear Gradient** - גרדיאנטים

### ניהול מצב (State Management)
- **Zustand** - ניהול מצב גלובלי פשוט ויעיל

### אימות (Authentication)
- **Clerk** - פתרון אימות מקיף
- **React Native MMKV** - אחסון מקומי מהיר

### טפסים (Forms)
- **React Hook Form** - ניהול טפסים

### רשימות (Lists)
- **FlashList** - רשימות מהירות ויעילות

### תפריטים (Menus)
- **Zeego** - תפריטים נפתחים וקונטקסטואליים

### מוניטיזציה (Monetization)
- **RevenueCat** - ניהול מנויים ורכישות

### בדיקות (Testing)
- **Maestro** - בדיקות E2E

## 📦 התקנה

### דרישות מקדימות

- Node.js (גרסה 18 ומעלה)
- npm או yarn
- Expo CLI
- iOS Simulator (למק) או Android Studio (לאנדרואיד)

### שלבי התקנה

1. **התקנת תלויות:**
```bash
npm install --legacy-peer-deps
```

2. **הגדרת משתני סביבה:**
```bash
cp .env.example .env
```

ערוך את קובץ `.env` והוסף את המפתחות שלך:
- `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` - קבל מ-[Clerk Dashboard](https://dashboard.clerk.com)
- `EXPO_PUBLIC_REVENUECAT_API_KEY` - קבל מ-[RevenueCat Dashboard](https://app.revenuecat.com)

3. **הרצת האפליקציה:**
```bash
# פיתוח
npm start

# iOS
npm run ios

# Android
npm run android

# Web
npm run web
```

## 🔧 הגדרת Clerk

1. צור חשבון ב-[Clerk](https://clerk.com)
2. צור אפליקציה חדשה
3. העתק את ה-Publishable Key
4. הוסף אותו לקובץ `.env`:
```
EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_your_key_here
```

5. הגדר את ה-Redirect URLs בלוח הבקרה של Clerk:
```
exp://localhost:8081
myapp://
```

## 📱 מבנה הפרויקט

```
app/
├── src/
│   ├── components/      # קומפוננטות משותפות
│   ├── screens/         # מסכים
│   │   ├── WelcomeScreen.tsx
│   │   └── AuthScreen.tsx
│   ├── stores/          # Zustand stores
│   │   └── authStore.ts
│   ├── config/          # הגדרות
│   │   ├── clerk.ts
│   │   ├── gluestack.tsx
│   │   └── rtl.ts
│   ├── hooks/           # Custom hooks
│   ├── utils/           # פונקציות עזר
│   │   ├── storage.ts
│   │   └── tokenCache.ts
│   └── types/           # TypeScript types
├── assets/              # תמונות ואייקונים
├── App.tsx             # נקודת כניסה ראשית
├── app.json            # הגדרות Expo
└── package.json        # תלויות
```

## 🌍 תמיכה ב-RTL

האפליקציה תומכת באופן מלא ב-RTL (Right-to-Left):

- כל הטקסטים בעברית
- פריסה מותאמת מימין לשמאל
- אייקונים ותמונות מותאמים ל-RTL
- ניווט RTL-aware

ההגדרות נמצאות בקובץ `src/config/rtl.ts`.

## 🔐 ניהול מצב אימות

האפליקציה משתמשת ב-Zustand לניהול מצב האימות:

```typescript
import { useAuthStore } from './stores/authStore';

// שימוש
const { isAuthenticated, user, login, logout } = useAuthStore();
```

המצב נשמר באופן אוטומטי ב-MMKV לשמירה מתמשכת.

## 📲 פריסה (Deployment)

### הגדרת EAS

1. התקן EAS CLI:
```bash
npm install -g eas-cli
```

2. התחבר ל-Expo:
```bash
eas login
```

3. הגדר את הפרויקט:
```bash
eas build:configure
```

4. בנה את האפליקציה:
```bash
# iOS
eas build --platform ios

# Android
eas build --platform android

# שניהם
eas build --platform all
```

### פריסה לחנויות

```bash
# iOS App Store
eas submit --platform ios

# Google Play Store
eas submit --platform android
```

## 🧪 בדיקות

### Maestro

התקן Maestro:
```bash
curl -Ls "https://get.maestro.mobile.dev" | bash
```

הרץ בדיקות:
```bash
maestro test .maestro/
```

## 📚 תיעוד נוסף

- [Expo Documentation](https://docs.expo.dev/)
- [Clerk Documentation](https://clerk.com/docs)
- [Gluestack UI Documentation](https://ui.gluestack.io/)
- [Zustand Documentation](https://docs.pmnd.rs/zustand)
- [React Hook Form Documentation](https://react-hook-form.com/)
- [RevenueCat Documentation](https://docs.revenuecat.com/)

## 🤝 תרומה

נשמח לקבל תרומות! אנא פתח issue או PR.

## 📄 רישיון

MIT

## 📞 תמיכה

לשאלות ותמיכה, צור קשר דרך [GitHub Issues](https://github.com/your-repo/issues).

---

**הערה חשובה:** זכור להוסיף את קובץ `.env` ל-`.gitignore` כדי לא לחשוף מפתחות API!

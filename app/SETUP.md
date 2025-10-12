# מדריך התקנה מהירה

## צעדים ראשונים

### 1. התקנת תלויות
```bash
cd app
npm install --legacy-peer-deps
```

### 2. הגדרת Clerk (אימות)

1. היכנס ל-[Clerk Dashboard](https://dashboard.clerk.com)
2. צור אפליקציה חדשה
3. בחר "Email & Password" כשיטת אימות
4. העתק את ה-Publishable Key

### 3. הגדרת משתני סביבה

צור קובץ `.env` בתיקיית `app/`:

```bash
cp .env.example .env
```

ערוך את קובץ `.env` והוסף את המפתחות:

```
EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_YOUR_KEY_HERE
```

### 4. הרצת האפליקציה

```bash
# פתח את Expo Dev Server
npm start

# או הרץ ישירות על מכשיר:
npm run ios      # iOS
npm run android  # Android
npm run web      # Web
```

### 5. בדיקה

1. האפליקציה תיפתח עם מסך Welcome
2. לחץ על "בואו נתחיל"
3. תגיע למסך Login/Register
4. צור חשבון חדש או התחבר

## פתרון בעיות נפוצות

### שגיאת Clerk
אם אתה מקבל שגיאה של Clerk:
- ודא שהוספת את ה-Publishable Key בקובץ `.env`
- ודא שהקובץ `.env` נמצא בתיקיית `app/`
- הפעל מחדש את Expo Dev Server

### שגיאת RTL
אם הטקסטים לא מוצגים מימין לשמאל:
- הפעל מחדש את האפליקציה לחלוטין
- נקה את ה-cache: `npm start -- --clear`

### שגיאות Dependencies
אם יש שגיאות בהתקנת תלויות:
```bash
# נקה node_modules
rm -rf node_modules
rm package-lock.json

# התקן מחדש
npm install --legacy-peer-deps
```

## מבנה קבצים חשובים

```
app/
├── src/
│   ├── screens/         # המסכים של האפליקציה
│   ├── stores/          # ניהול מצב עם Zustand
│   ├── config/          # הגדרות (RTL, Clerk, Gluestack)
│   ├── utils/           # פונקציות עזר
│   └── types/           # הגדרות TypeScript
├── .env                 # משתני סביבה (אל תעלה ל-Git!)
├── .env.example         # דוגמה למשתני סביבה
└── App.tsx             # נקודת כניסה ראשית
```

## שלבים הבאים

1. הוסף מסכי קוויז
2. התחבר ל-API של הבקאנד
3. הוסף RevenueCat למוניטיזציה
4. הגדר EAS Build לפריסה

## צריך עזרה?

פתח issue ב-GitHub או צור קשר עם הצוות.

# Authentication Flow Documentation

## Overview

The app uses **Clerk** for authentication with email verification. The flow supports both login and registration, with automatic email verification for new users.

---

## Registration Flow (with Email Verification)

### Step 1: User Fills Registration Form
- שם פרטי (First Name)
- שם משפחה (Last Name)
- אימייל (Email)
- סיסמה (Password - minimum 8 characters)

### Step 2: Submit Registration
When user clicks "הירשם" (Register):

```typescript
const result = await signUp.create({
  emailAddress: email,
  password,
  firstName,
  lastName,
});
```

### Step 3: Clerk Sends Verification Email
- `result.status === 'missing_requirements'`
- `result.createdSessionId === null`
- Clerk automatically sends a 6-digit verification code to the email
- App calls: `await signUp.prepareEmailAddressVerification({ strategy: 'email_code' })`
- App switches to verification UI: `setPendingVerification(true)`

### Step 4: User Enters Verification Code
UI shows:
- Title: "אימות אימייל" (Email Verification)
- Message: "שלחנו קוד אימות לכתובת [email]" (We sent a verification code to [email])
- Input field for 6-digit code
- "אמת אימייל" (Verify Email) button
- "חזור לטופס הרשמה" (Back to registration form) button

### Step 5: Verify Email Code
When user enters code and clicks "אמת אימייל":

```typescript
const result = await signUp.attemptEmailAddressVerification({
  code: verificationCode,
});
```

### Step 6: Complete Registration
If code is correct:
- `result.status === 'complete'`
- `result.createdSessionId` contains session ID
- Set active session: `await setActive({ session: result.createdSessionId })`
- Save user to local store: `await login({ id, email, firstName, lastName })`
- Redirect to home: `onAuthSuccess()`

### Error Handling

**Invalid Code:**
```
Error: "Invalid verification code" → "קוד אימות שגוי"
```

**Expired Code:**
```
Error: "Code has expired" → "פג תוקף הקוד"
```

**Missing Fields:**
```
Error: "אנא הזן קוד בן 6 ספרות"
```

---

## Login Flow (No Verification Needed)

### Step 1: User Fills Login Form
- אימייל (Email)
- סיסמה (Password)

### Step 2: Submit Login
When user clicks "התחבר" (Login):

```typescript
const result = await signIn.create({
  identifier: email,
  password,
});
```

### Step 3: Complete Login
If credentials are correct:
- `result.status === 'complete'`
- Set active session: `await setActive({ session: result.createdSessionId })`
- Save user to local store: `await login({ id, email })`
- Redirect to home: `onAuthSuccess()`

### Error Handling

**Wrong Credentials:**
```
Error: "Incorrect email or password" → "אימייל או סיסמה שגויים"
```

**Account Not Found:**
```
Error: "Couldn't find your account" → "לא נמצא חשבון עם פרטים אלו"
```

---

## State Management

### AuthStore (Zustand + MMKV)

**State:**
```typescript
{
  user: User | null,
  isAuthenticated: boolean,
  isLoading: boolean
}
```

**Actions:**
```typescript
login(user: User): Promise<void>   // Saves to MMKV
logout(): Promise<void>             // Clears MMKV
hydrate(): Promise<void>            // Restores from MMKV on app start
```

**MMKV Keys:**
- `USER_DATA` - User object
- `AUTH_TOKEN` - Boolean flag

### Clerk Token Cache

Clerk stores its JWT tokens using MMKV via `tokenCache`:

```typescript
export const tokenCache = {
  async getToken(key: string) {
    return StorageUtils.getString(key);
  },
  async saveToken(key: string, value: string) {
    StorageUtils.setString(key, value);
  },
};
```

---

## UI States

### 1. Loading State
- Shows while checking authentication status
- `isLoading === true`

### 2. Unauthenticated State
- Shows WelcomeScreen → AuthScreen
- `isAuthenticated === false`

### 3. Login Mode
- Title: "התחברות" (Login)
- Fields: Email, Password
- Button: "התחבר" (Login)
- Toggle: "אין לך חשבון? הירשם" (Don't have account? Register)

### 4. Register Mode
- Title: "הרשמה" (Register)
- Fields: First Name, Last Name, Email, Password
- Button: "הירשם" (Register)
- Toggle: "כבר יש לך חשבון? התחבר" (Already have account? Login)

### 5. Verification Mode
- Title: "אימות אימייל" (Email Verification)
- Message: "שלחנו קוד אימות לכתובת {email}" (We sent verification code to {email})
- Field: 6-digit code input
- Button: "אמת אימייל" (Verify Email)
- Back: "חזור לטופס הרשמה" (Back to registration)

### 6. Authenticated State
- Shows HomeScreen with drawer menu
- `isAuthenticated === true`

---

## Component Structure

### AuthScreen.tsx

**States:**
```typescript
const [isLogin, setIsLogin] = useState(true);              // Login/Register mode
const [email, setEmail] = useState('');
const [password, setPassword] = useState('');
const [firstName, setFirstName] = useState('');
const [lastName, setLastName] = useState('');
const [verificationCode, setVerificationCode] = useState('');
const [pendingVerification, setPendingVerification] = useState(false);
const [loading, setLoading] = useState(false);
const [error, setError] = useState('');
```

**Functions:**
- `handleLogin()` - Process login
- `handleRegister()` - Process registration → triggers verification
- `handleVerifyEmail()` - Verify email code → complete registration
- `toggleMode()` - Switch between login/register modes
- `translateClerkError()` - Translate error messages to Hebrew

---

## Testing the Flow

### Test Registration with Email Verification

1. Open app → Tap "הירשם" (Register)
2. Fill form:
   - שם פרטי: "עדי"
   - שם משפחה: "אליה"
   - אימייל: "test@example.com"
   - סיסמה: "TestPass123"
3. Tap "הירשם" (Register)
4. **Expected:** Screen changes to verification mode
5. Check email for 6-digit code
6. Enter code in app
7. Tap "אמת אימייל" (Verify Email)
8. **Expected:** Redirected to HomeScreen

### Test Login (Existing User)

1. Open app → Already on login screen
2. Fill form:
   - אימייל: "test@example.com"
   - סיסמה: "TestPass123"
3. Tap "התחבר" (Login)
4. **Expected:** Redirected to HomeScreen immediately (no verification)

### Test Logout

1. Open drawer menu (hamburger icon)
2. Tap "התנתק" (Logout)
3. Confirm in dialog
4. **Expected:** Redirected to WelcomeScreen/AuthScreen

---

## Logs Reference

### Successful Registration Flow

```
🟢 Button pressed! Mode: Register
🔵 handleRegister called
📧 Email: test@example.com
👤 First Name: עדי
👤 Last Name: אליה
🔒 Password length: 8
📤 Calling Clerk signUp.create...
📥 SignUp result status: missing_requirements
📥 SignUp result createdSessionId: null
📧 Email verification required
✅ Verification email sent! Check your inbox.
```

### Successful Verification

```
🔐 Verifying email with code: 123456
📥 Verification result status: complete
✅ Email verified successfully!
✅ User saved to storage
```

### Successful Login

```
Login successful!
User logged in: test@example.com
```

---

## Error Messages (Hebrew)

| English | Hebrew |
|---------|--------|
| Invalid verification code | קוד אימות שגוי |
| Code has expired | פג תוקף הקוד |
| Incorrect email or password | אימייל או סיסמה שגויים |
| Couldn't find your account | לא נמצא חשבון עם פרטים אלו |
| Password must be at least 8 characters | הסיסמה חייבת להכיל לפחות 8 תווים |
| That email address is taken | כתובת האימייל כבר קיימת במערכת |
| Too many requests | יותר מדי ניסיונות. נסה שוב מאוחר יותר |

---

## Backend Integration (Next Steps)

After successful registration/login, Clerk will trigger a webhook to sync the user with your Supabase database.

### Webhook Flow:
1. User completes registration in Clerk
2. Clerk triggers webhook: `POST /api/users/webhook`
3. Webhook handler creates user in Supabase:
   ```sql
   INSERT INTO users (clerk_user_id, email, first_name, last_name)
   VALUES ('user_...', 'test@example.com', 'עדי', 'אליה')
   ```
4. User can now make authenticated API calls using Clerk JWT token

### API Authentication:
```typescript
// App sends request with Clerk token
const token = await getToken(); // From Clerk
fetch('http://localhost:8000/api/users/me', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

// Backend verifies token and extracts clerk_user_id
// Then queries Supabase: SELECT * FROM users WHERE clerk_user_id = 'user_...'
```

---

## Related Files

- `app/src/screens/AuthScreen.tsx` - Main auth UI and logic
- `app/src/stores/authStore.ts` - Auth state management
- `app/src/utils/storage.ts` - MMKV storage utilities
- `app/src/utils/tokenCache.ts` - Clerk token persistence
- `app/src/components/DrawerMenu.tsx` - Logout functionality
- `api/routes/users.py` - User management endpoints
- `api/auth.py` - JWT verification middleware

---

**Last Updated:** 2025-10-12
**Status:** ✅ Fully Implemented with Email Verification

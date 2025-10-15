# Logout Flow Documentation

## Overview

The logout functionality is fully integrated with Clerk authentication and local state management.

## Implementation

### Components Involved

1. **DrawerMenu** (`src/components/DrawerMenu.tsx`)
   - Contains the logout button
   - Handles user confirmation
   - Triggers logout process

2. **AuthStore** (`src/stores/authStore.ts`)
   - Manages local authentication state
   - Clears user data from MMKV storage

3. **Clerk**
   - Handles session termination
   - Redirects to auth screen

---

## Logout Process

### Step 1: User Clicks "התנתק" (Logout)

User taps the logout button in the drawer menu.

### Step 2: Confirmation Dialog

```typescript
Alert.alert(
  'התנתקות',
  'האם אתה בטוח שברצונך להתנתק?',
  [
    { text: 'ביטול', style: 'cancel' },
    { text: 'התנתק', style: 'destructive', onPress: async () => { ... } }
  ]
);
```

Dialog shows:
- **Title:** "התנתקות" (Logout)
- **Message:** "האם אתה בטוח שברצונך להתנתק?" (Are you sure you want to logout?)
- **Cancel Button:** "ביטול" (Cancel)
- **Logout Button:** "התנתק" (Logout) - Destructive style (red)

### Step 3: Execute Logout (if confirmed)

```typescript
// 1. Close drawer
onClose();

// 2. Clear local state (Zustand + MMKV)
await logout();

// 3. Sign out from Clerk
await signOut();

// 4. Clerk automatically redirects to auth screen
```

**What Gets Cleared:**

From `authStore.logout()`:
```typescript
- user: null
- isAuthenticated: false
- isLoading: false
- MMKV storage keys deleted:
  - USER_DATA
  - AUTH_TOKEN
```

From Clerk `signOut()`:
```typescript
- Clerk session terminated
- JWT tokens invalidated
- Automatic redirect to SignIn screen
```

---

## Error Handling

If logout fails:

```typescript
catch (error) {
  console.error('שגיאה בהתנתקות:', error);
  Alert.alert('שגיאה', 'אירעה שגיאה בהתנתקות. אנא נסה שוב.');
}
```

Shows error alert:
- **Title:** "שגיאה" (Error)
- **Message:** "אירעה שגיאה בהתנתקות. אנא נסה שוב." (An error occurred during logout. Please try again.)

---

## User Experience Flow

```
1. User opens drawer menu
   ↓
2. User taps "התנתק" button
   ↓
3. Confirmation dialog appears
   ↓
4a. User taps "ביטול" → Dialog closes, stays logged in
   ↓
4b. User taps "התנתק" → Logout process starts
   ↓
5. Drawer closes
   ↓
6. Local state cleared (instant)
   ↓
7. Clerk signs out (1-2 seconds)
   ↓
8. Redirect to WelcomeScreen/AuthScreen
```

---

## Testing

### Manual Test

1. Run the app
2. Sign in with a user
3. Open drawer menu (tap hamburger icon)
4. Tap "התנתק"
5. Verify confirmation dialog shows
6. Tap "התנתק" in dialog
7. Verify:
   - Drawer closes
   - App redirects to auth screen
   - User cannot access authenticated screens
   - Next login requires credentials again

### Test Scenarios

#### Scenario 1: Cancel Logout
1. Click logout button
2. Click "ביטול" in dialog
3. ✅ Should stay logged in
4. ✅ Drawer should remain open

#### Scenario 2: Confirm Logout
1. Click logout button
2. Click "התנתק" in dialog
3. ✅ Should clear local state
4. ✅ Should sign out from Clerk
5. ✅ Should redirect to auth screen

#### Scenario 3: Network Error
1. Disconnect from internet
2. Try to logout
3. ✅ Should show error message
4. ✅ Should stay on same screen
5. ✅ Local state should remain unchanged

---

## Code Reference

### DrawerMenu.tsx (Logout Handler)

```typescript
const handleLogout = async () => {
  try {
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
            onClose();
            await logout();
            await signOut();
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
```

### authStore.ts (Logout Action)

```typescript
logout: async () => {
  set({
    user: null,
    isAuthenticated: false,
    isLoading: false,
  });
  await StorageUtils.delete(StorageKeys.USER_DATA);
  await StorageUtils.delete(StorageKeys.AUTH_TOKEN);
}
```

---

## Security Notes

### What Happens to User Data

**Cleared:**
- ✅ Local user object (Zustand store)
- ✅ MMKV storage (USER_DATA, AUTH_TOKEN)
- ✅ Clerk session (JWT tokens invalidated)

**NOT Cleared (stays in database):**
- ❌ User profile in Supabase database
- ❌ Exam history
- ❌ Question history
- ❌ User statistics

This is by design - user data is preserved for when they log back in.

### Security Implications

- JWT tokens are invalidated by Clerk
- API requests with old tokens will return 401 Unauthorized
- User must re-authenticate to access protected endpoints
- Local storage is cleared to prevent data persistence on shared devices

---

## Future Improvements

### Possible Enhancements

1. **Loading State**
   ```typescript
   const [isLoggingOut, setIsLoggingOut] = useState(false);
   ```
   Show loading indicator during logout process

2. **Logout Confirmation Setting**
   ```typescript
   const skipLogoutConfirmation = await StorageUtils.getBoolean('SKIP_LOGOUT_CONFIRM');
   ```
   Allow users to skip confirmation dialog

3. **Analytics**
   ```typescript
   analytics.track('user_logged_out', {
     user_id: user.id,
     duration: sessionDuration,
   });
   ```
   Track logout events for analytics

4. **Session Timeout**
   ```typescript
   // Auto-logout after X hours of inactivity
   const lastActive = await StorageUtils.getNumber('LAST_ACTIVE');
   if (Date.now() - lastActive > SESSION_TIMEOUT) {
     await logout();
   }
   ```

---

## Troubleshooting

### Issue: "Drawer doesn't close after logout"

**Cause:** Drawer animation interfering with logout process

**Fix:** Call `onClose()` before logout operations:
```typescript
onClose(); // ← Close drawer first
await logout();
await signOut();
```

### Issue: "User stays logged in after logout"

**Cause:** Clerk signOut not called or failed

**Fix:** Ensure `await signOut()` is called and check for errors:
```typescript
try {
  await signOut();
  console.log('Clerk signOut successful');
} catch (error) {
  console.error('Clerk signOut failed:', error);
}
```

### Issue: "Error: Cannot read property 'signOut' of undefined"

**Cause:** useClerk hook not initialized

**Fix:** Ensure component is wrapped in ClerkProvider:
```typescript
// App.tsx
<ClerkProvider publishableKey={...}>
  <YourApp />
</ClerkProvider>
```

---

## Related Files

- `app/src/components/DrawerMenu.tsx` - Logout UI and handler
- `app/src/stores/authStore.ts` - Local state management
- `app/src/utils/storage.ts` - MMKV storage utilities
- `app/src/config/colors.ts` - UI colors

---

**Last Updated:** 2025-01-12
**Status:** ✅ Fully Implemented

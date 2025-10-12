# CLAUDE.md - Quiz App Project

This file contains all project specifications and standards for working with Claude Code.

## 🎯 Project Overview

**Project Name:** Quiz App (קוויז מבחנים)
**Target Market:** Israel
**Language:** Hebrew (100%)
**Text Direction:** RTL (Right-to-Left) ONLY

## ⚠️ CRITICAL RULES - MUST READ!

### 1. Language and Directionality (MOST IMPORTANT!)
- **ALL app content MUST be in Hebrew**
- **ALL UI MUST be RTL (right-to-left)**
- **NO EXCEPTIONS!** Error messages, temporary texts, placeholders - EVERYTHING in Hebrew
- Use `I18nManager.allowRTL(true)` and `I18nManager.forceRTL(true)`
- All layouts must be RTL-aware

### 2. RTL Configuration File
RTL settings are located in `app/src/config/rtl.ts`

### 3. Communication Language
- **App UI/UX:** Hebrew only
- **Code comments:** English (or Hebrew + English for critical parts)
- **Documentation:** English
- **Communication with user:** English

### 4. Dependency Installation (CRITICAL!)
- **BEFORE importing ANY library, ALWAYS check if it's installed in package.json**
- **ALWAYS install dependencies with `--legacy-peer-deps` flag**
- If you see "Unable to resolve" error, install the missing package immediately
- Check the "Complete Dependencies List" section below for all required packages

## 📦 Complete Dependencies List

### Currently Installed (package.json)
```json
{
  "@clerk/clerk-expo": "2.16.1",
  "@gluestack-style/react": "1.0.57",
  "@gluestack-ui/themed": "1.1.73",
  "@react-native-async-storage/async-storage": "2.2.0",
  "@shopify/flash-list": "2.1.0",
  "expo": "~54.0.13",
  "expo-constants": "18.0.9",
  "expo-image": "3.0.9",
  "expo-linear-gradient": "~15.0.7",
  "expo-linking": "8.0.8",
  "expo-secure-store": "15.0.7",
  "expo-status-bar": "~3.0.8",
  "expo-web-browser": "15.0.8",
  "react": "19.1.0",
  "react-hook-form": "7.65.0",
  "react-native": "0.81.4",
  "react-native-gesture-handler": "2.28.0",
  "react-native-mmkv": "3.3.3",
  "react-native-purchases": "9.5.4",
  "react-native-reanimated": "4.1.3",
  "react-native-safe-area-context": "5.6.1",
  "react-native-screens": "4.16.0",
  "react-native-svg": "15.14.0",
  "zeego": "3.0.6",
  "zustand": "5.0.8"
}
```

### Required Dependencies by Library

**Clerk (@clerk/clerk-expo):**
- expo-web-browser ✅
- expo-linking ✅
- expo-constants ✅
- expo-secure-store ✅
- expo-auth-session ✅
- react-dom ✅

**Gluestack UI (@gluestack-ui/themed):**
- react-native-svg ✅
- @gluestack-style/react ✅

**Zeego:**
- react-native-reanimated ✅
- react-native-gesture-handler ✅

**Common/Shared:**
- react-native-safe-area-context ✅
- react-native-screens ✅
- @react-native-async-storage/async-storage ✅

## 📱 Project Structure

```
quiz/
├── app/                    # React Native Application
│   ├── src/
│   │   ├── screens/       # Screen components
│   │   ├── stores/        # Zustand stores
│   │   ├── config/        # Configuration files
│   │   ├── utils/         # Utility functions
│   │   ├── components/    # Shared components
│   │   ├── hooks/         # Custom hooks
│   │   └── types/         # TypeScript types
│   └── App.tsx           # Entry point
└── backend/              # Backend API (Python/FastAPI)
```

## 🛠 Tech Stack - React Native App

### Core Framework
- **React Native** - Mobile framework
- **Expo SDK 54** - Development and deployment tools
- **TypeScript** - Typed programming language
- **Deployment:** Expo EAS

### UI Framework & Components
- **Gluestack UI v3** ⭐ (Primary UI Library - REQUIRED!)
  - **IMPORTANT:** Always use Gluestack components instead of basic React Native components
  - Use Gluestack components MCP if available
  - All styling through Gluestack
- **Expo Image** - Image optimization
- **Expo Linear Gradient** - Gradients

### State Management
- **Zustand** - Global state management
  - Simple, fast, and lightweight
  - Stores located in `src/stores/`
  - Current: `authStore.ts` for authentication

### Authentication
- **Clerk** - Complete authentication solution
  - Email & Password
  - OAuth (Google, Apple, etc.)
  - Session management
  - **Configuration:** `src/config/clerk.ts`
  - **Required:** `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` in `.env` file

### Storage
- **React Native MMKV** - Fast local storage
  - **Version:** 2.x (NOT 3.x - requires old architecture)
  - 30x faster than AsyncStorage
  - Synchronous API
  - Encryption support
  - **Utilities:** `src/utils/storage.ts`
  - Uses: Auth state, preferences, cache

### Forms
- **React Hook Form** - Form management
  - Validation
  - Error handling
  - Performance optimized

### Lists
- **FlashList** (@shopify/flash-list) - High-performance lists
  - **REQUIRED:** Use FlashList instead of FlatList
  - Significantly improved performance
  - RTL support

### Menus
- **Zeego** - Native dropdowns and context menus
  - Native look & feel
  - iOS and Android
  - Dropdowns, context menus

### Monetization
- **RevenueCat** (react-native-purchases)
  - Subscription management
  - In-app purchases
  - Stripe integration (already set up in system)
  - Analytics

### Testing
- **Maestro** - E2E testing
  - Easy to write
  - Native support
  - CI/CD friendly

## 🎨 Design & Styling

### Brand Colors (defined in `src/config/colors.ts` and `src/config/gluestack.tsx`)

**Official Quiz App Color Palette:**

- 💙 **Primary: #0A76F3**
  - Use for: Titles, icons, main action buttons
  - Represents: Trust, knowledge, and innovation

- ⚪ **Background: #FFFFFF**
  - Use for: Main background
  - Creates perfect contrast and keeps interface clean

- 🩵 **Secondary Light: #E3F2FD**
  - Use for: Secondary sections, cards, unanswered questions
  - Gives a sense of calm and focus

- 🟢 **Success/Progress: #3CCF4E**
  - Use for: "Completed", "Passed", "Success" states
  - Symbolizes growth and progress

- 🟡 **Accent/Highlight: #FFC107**
  - Use for: Key buttons like "Start Learning", "Save", "Submit Test"
  - Adds motivation and achievement feel

**System Colors:**
- Warning: #FF9800
- Error: #F44336
- Info: #0A76F3

### Branding Assets
- **Logo:** `app/assets/logo.png`
- Always use the logo on splash screens and welcome screens
- Logo should be displayed with proper spacing and sizing

### Typography
- **Fonts:** System fonts (can add Hebrew fonts)
- **Sizes:** 2xs (10) → 6xl (60)
- **All text:** Right-aligned (RTL)

### Spacing
- Spacing system based on 4px
- `space.1` = 4px, `space.2` = 8px, etc.

## 🔒 Authentication Flow

### Authentication States
1. **Loading** - Loading state from storage
2. **Unauthenticated** - Show Welcome → Auth screens
3. **Authenticated** - Show Main app

### State Persistence
- Clerk manages sessions
- Tokens stored in MMKV via `tokenCache`
- User data in Zustand store
- Auto-restore on app launch

### Relevant Files
- `src/stores/authStore.ts` - Zustand store
- `src/utils/tokenCache.ts` - Clerk token cache
- `src/utils/storage.ts` - MMKV utilities
- `src/config/clerk.ts` - Clerk config

## 📝 Coding Standards

### TypeScript
- **ALWAYS** use TypeScript
- Define interfaces/types in `src/types/`
- Avoid `any` - use `unknown` if needed

### Components
- Functional components with hooks
- Props interface defined above component
- JSDoc comments (in English) for important functions

```typescript
/**
 * Main button component
 * Note: All visible text must be in Hebrew
 */
interface ButtonProps {
  title: string;
  onPress: () => void;
}

export const Button: React.FC<ButtonProps> = ({ title, onPress }) => {
  // ...
}
```

### File Structure
```typescript
// 1. Imports
import React from 'react';
import { View, Text } from 'react-native';

// 2. Types/Interfaces
interface Props {
  // ...
}

// 3. Component
export const MyComponent: React.FC<Props> = (props) => {
  // 4. Hooks
  const [state, setState] = useState();

  // 5. Functions
  const handlePress = () => {
    // ...
  };

  // 6. Render
  return (
    // ...
  );
};

// 7. Styles (if using StyleSheet)
const styles = StyleSheet.create({
  // ...
});
```

### Naming Conventions
- **Components:** PascalCase (`WelcomeScreen`, `AuthButton`)
- **Functions:** camelCase (`handleLogin`, `validateEmail`)
- **Constants:** UPPER_SNAKE_CASE (`API_URL`, `STORAGE_KEYS`)
- **Files:** PascalCase for components, camelCase for others

### Comments
- Important code: Comments in English
- Exported public functions: JSDoc comments
- Complex logic: Explain what and why

## 🗂 File Organization

### Screens (`src/screens/`)
Each screen = separate file
- `WelcomeScreen.tsx` - Welcome screen
- `AuthScreen.tsx` - Login/Register
- `HomeScreen.tsx` - Main screen (future)
- `QuizScreen.tsx` - Quiz screen (future)

### Stores (`src/stores/`)
Zustand stores for global state
- `authStore.ts` - Authentication management
- `quizStore.ts` - Quiz management (future)
- `userStore.ts` - User data (future)

### Config (`src/config/`)
Configuration files
- `clerk.ts` - Clerk configuration
- `gluestack.tsx` - Gluestack UI config
- `rtl.ts` - RTL setup
- `constants.ts` - Global constants (future)

### Utils (`src/utils/`)
Helper functions
- `storage.ts` - MMKV utilities
- `tokenCache.ts` - Clerk token cache
- `validation.ts` - Form validation (future)
- `api.ts` - API calls (future)

## 🌐 Environment Variables

### Required (`.env`)
```bash
# Clerk - REQUIRED!
EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx

# RevenueCat - Optional (for monetization)
EXPO_PUBLIC_REVENUECAT_API_KEY=xxxxx

# API Backend - Optional
EXPO_PUBLIC_API_URL=http://localhost:8000
```

### Important!
- **NEVER** commit `.env` to Git
- Always update `.env.example` with new keys
- Use `EXPO_PUBLIC_` prefix for client-side variables

## 📦 Package Management

### Installing Packages
```bash
# Always use legacy-peer-deps due to Gluestack
npm install --legacy-peer-deps <package-name>

# Or
npx expo install <package-name>
```

### Remember
- Gluestack UI v3 requires `--legacy-peer-deps`
- Prefer `expo install` for Expo packages
- Check compatibility with Expo SDK 54

## 🚀 Scripts

```bash
# Development
npm start              # Start Expo dev server
npm run ios           # Run on iOS simulator
npm run android       # Run on Android emulator
npm run web           # Run on web browser

# Clean start
npm start -- --clear  # Clear cache and start

# Build (EAS)
eas build --platform ios
eas build --platform android
eas build --platform all

# Submit to stores
eas submit --platform ios
eas submit --platform android
```

## 🎯 Development Workflow

### When adding a new feature:
1. **Planning** - Plan structure and files
2. **Types** - Define interfaces in `src/types/`
3. **Store** - Create/update store if global state needed
4. **Components** - Build components with Gluestack UI
5. **Screen** - Build the screen
6. **Integration** - Integrate with App.tsx/navigation
7. **Testing** - Test on iOS and Android
8. **RTL Check** - Ensure RTL works correctly

### When adding a new screen:
1. Create file in `src/screens/`
2. Use Gluestack UI components
3. Ensure text is in Hebrew
4. Check RTL layout
5. Add to navigation flow

## 🐛 Debugging

### Common Issues

**1. RTL not working:**
```bash
# Completely restart
npm start -- --clear
# Close app on device and restart
```

**2. Clerk errors:**
- Check `CLERK_PUBLISHABLE_KEY` is correct
- Ensure `.env` file is in correct location
- Restart Expo

**3. Dependency conflicts:**
```bash
rm -rf node_modules package-lock.json
npm install --legacy-peer-deps
```

**4. Metro bundler issues:**
```bash
npm start -- --clear
# or
watchman watch-del-all
rm -rf /tmp/metro-*
```

## 📚 Important Files Reference

### Must Know Files
- `App.tsx` - Entry point, routing logic
- `app.json` - Expo configuration
- `src/stores/authStore.ts` - Auth state
- `src/config/rtl.ts` - RTL configuration
- `src/utils/storage.ts` - Storage utilities

### Configuration Files
- `.env` - Environment variables (not in Git)
- `.env.example` - Example env file
- `tsconfig.json` - TypeScript config
- `package.json` - Dependencies

## 🔜 Next Steps / Roadmap

### Phase 1: Core Features (Current)
- ✅ Project setup
- ✅ Authentication (Clerk)
- ✅ Welcome + Auth screens
- ✅ RTL support
- ✅ State management (Zustand)
- ✅ Storage (MMKV)

### Phase 2: Quiz Features (Next)
- [ ] Quiz listing screen
- [ ] Quiz taking screen
- [ ] Results screen
- [ ] Backend API integration
- [ ] Question types support

### Phase 3: User Features
- [ ] User profile screen
- [ ] Statistics/Progress tracking
- [ ] Favorites/Bookmarks
- [ ] Search functionality

### Phase 4: Monetization
- [ ] RevenueCat integration
- [ ] Subscription screen
- [ ] Premium content gating
- [ ] Payment flow

### Phase 5: Polish & Launch
- [ ] Onboarding flow
- [ ] App icons & splash screens
- [ ] Analytics integration
- [ ] Error tracking (Sentry?)
- [ ] E2E tests (Maestro)
- [ ] App Store submission
- [ ] Google Play submission

## 🎓 Learning Resources

- [Expo Docs](https://docs.expo.dev/)
- [Clerk Docs](https://clerk.com/docs)
- [Gluestack UI Docs](https://ui.gluestack.io/)
- [Zustand Docs](https://docs.pmnd.rs/zustand)
- [MMKV Docs](https://github.com/mrousavy/react-native-mmkv)
- [FlashList Docs](https://shopify.github.io/flash-list/)

## 💡 Best Practices

### Performance
- Use FlashList for long lists
- Lazy load images with Expo Image
- Memoize expensive calculations
- Use `useCallback` and `useMemo` wisely

### Security
- Don't store sensitive data in plain text
- Use MMKV encryption for sensitive data
- Validate all user input
- Don't commit `.env` to Git

### UX
- Loading states for all async operations
- Clear error messages (in Hebrew!)
- Haptic feedback for important actions
- Smooth animations (but not excessive)

### RTL
- Test every screen in RTL
- Flip icons if relevant
- Animations should work right-to-left
- Test on both iOS and Android

## 🤝 Contributing Guidelines

When working on the project:
1. Maintain consistency with existing code
2. Update CLAUDE.md if standards change
3. Add comments for complex code
4. Check RTL before committing
5. Update documentation if needed

## 🔑 Key Reminders for Claude Code

1. **ALWAYS check if dependencies are installed before importing** - Check package.json first!
2. **ALWAYS use `--legacy-peer-deps` when installing packages**
3. **ALWAYS use Hebrew for all user-facing text**
4. **ALWAYS ensure RTL layout**
5. **ALWAYS use Gluestack UI components**
6. **ALWAYS use the brand colors from `src/config/colors.ts`** - Never hardcode colors!
7. **ALWAYS use the logo from `app/assets/logo.png`** for branding
8. **ALWAYS check RTL before considering a feature complete**

---

**Last Updated:** 2025-10-11
**Expo SDK:** 54
**React Native:** 0.81.4
**Recommended Node.js Version:** 18+

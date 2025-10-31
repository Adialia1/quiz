# How to Build and Test on iPad Simulator

## 🎯 Quick Start (Easiest Way)

### Option 1: Use the Test Script
```bash
cd /Users/adialia/Desktop/quiz/app
./test-ipad.sh
```

This will automatically:
- Start Expo dev server
- Open iPad Air (5th generation) simulator
- Load your app

---

## 📱 Manual Testing (Step by Step)

### Step 1: Navigate to Your App
```bash
cd /Users/adialia/Desktop/quiz/app
```

### Step 2: Start Expo with iPad Simulator
```bash
EXPO_IOS_SIMULATOR_DEVICE_NAME="iPad Air (5th generation)" npx expo start --ios
```

**What happens:**
- Expo starts bundling your app
- iPad Air (5th generation) simulator opens automatically
- App installs and launches on the simulator

### Step 3: Wait for App to Load
- First time: ~30-60 seconds
- Subsequent times: ~10-20 seconds

---

## 🧪 Testing Checklist for Apple Sign-In

### 1. Launch and Basic Navigation
- [ ] App launches without errors
- [ ] Welcome screen appears
- [ ] Click "התחל עכשיו" (Get Started)
- [ ] Auth screen appears correctly

### 2. Test Apple Sign-In Button
- [ ] "התחבר עם Apple" button is visible
- [ ] Button is black with white text
- [ ] Button is large enough to tap easily
- [ ] No layout issues in portrait mode

### 3. Test Apple Sign-In Flow

**Important:** In the simulator, Apple Sign-In works differently than on a real device.

**Option A - Simulator Test (Limited):**
Click the Apple Sign-In button and observe:
- [ ] Loading spinner appears
- [ ] No error messages appear immediately
- [ ] If modal appears, it's working correctly

**Note:** Full OAuth flow may not work in simulator without Apple Developer account configured.

**Option B - Real Device Test (Recommended):**
1. Connect your iPhone/iPad via USB
2. Trust the device on your Mac
3. Run:
   ```bash
   npx expo start --device
   ```
4. Select your device from the list
5. Test Apple Sign-In on real device

### 4. Test iPad Landscape Mode
- [ ] Rotate iPad to landscape (Cmd + Left/Right Arrow)
- [ ] Auth screen still looks good
- [ ] Apple button still works
- [ ] No layout issues

### 5. Test Error Handling
Try these scenarios:
- [ ] Click Apple Sign-In and cancel immediately
  - **Expected:** No error message, button returns to normal
- [ ] Enable Airplane Mode and try signing in
  - **Expected:** "שגיאת רשת. בדוק את החיבור לאינטרנט ונסה שוב"

### 6. Test Other Features
- [ ] Try email/password sign-in (should work)
- [ ] Try Google Sign-In (if configured)
- [ ] Click "חזור למצב אורח" (back to guest)
- [ ] Guest mode works correctly

---

## 🛠 Simulator Controls

### Useful Keyboard Shortcuts:
- **Cmd + R** - Reload app
- **Cmd + D** - Open developer menu
- **Cmd + Left/Right Arrow** - Rotate device
- **Cmd + Shift + H** - Go to home screen
- **Cmd + Shift + H + H** - Show multitasking
- **Ctrl + Cmd + Z** - Shake device

### Rotate iPad:
```
Device → Rotate Left (Cmd + Left)
Device → Rotate Right (Cmd + Right)
```

### Reset Simulator (if needed):
```bash
# Close simulator first, then:
xcrun simctl erase all
```

---

## 🐛 Common Issues & Solutions

### Issue 1: Simulator Doesn't Open
**Solution:**
```bash
# Open simulator first manually
open -a Simulator

# Then run:
cd /Users/adialia/Desktop/quiz/app
npx expo start
# Press 'i' to open on iOS simulator
```

### Issue 2: Wrong iPad Model Opens
**Solution:**
```bash
# List all available simulators:
xcrun simctl list devices | grep iPad

# Use the exact name:
EXPO_IOS_SIMULATOR_DEVICE_NAME="iPad Air (5th generation)" npx expo start --ios
```

### Issue 3: "Unable to Boot Device"
**Solution:**
```bash
# Shutdown all simulators:
xcrun simctl shutdown all

# Boot the specific iPad:
xcrun simctl boot "iPad Air (5th generation)"

# Then start Expo:
npx expo start --ios
```

### Issue 4: App Crashes on Launch
**Solution:**
```bash
# Clear Metro cache and restart:
npx expo start --clear
```

### Issue 5: Apple Sign-In Doesn't Work
**This is NORMAL in simulator!** Apple Sign-In requires:
- Real device OR
- Properly configured Apple Developer account

**For testing purposes:**
- Check that button appears correctly ✅
- Check that no errors appear on click ✅
- Check loading spinner works ✅
- Full OAuth test needs real device

---

## 📦 Building Production Version (For App Store)

### Step 1: Build with EAS
```bash
cd /Users/adialia/Desktop/quiz/app
eas build --platform ios --profile production
```

**What happens:**
- Code uploaded to EAS servers
- Built in the cloud with proper certificates
- ~15-20 minutes build time
- Download link provided when done

### Step 2: Download the Build
```bash
# After build completes, download .ipa file
# Link will be shown in terminal
```

### Step 3: Submit to App Store
```bash
eas submit --platform ios
```

**OR manually in App Store Connect:**
1. Go to https://appstoreconnect.apple.com
2. Your App → TestFlight
3. Upload build (Transporter app or Xcode)

---

## 🎯 Quick Commands Reference

```bash
# Test on iPad Air (5th generation)
./test-ipad.sh

# OR manually:
cd /Users/adialia/Desktop/quiz/app
EXPO_IOS_SIMULATOR_DEVICE_NAME="iPad Air (5th generation)" npx expo start --ios

# Test on real iPhone/iPad
npx expo start --device

# Clear cache and restart
npx expo start --clear

# Build for production
eas build --platform ios --profile production

# Submit to App Store
eas submit --platform ios

# List all simulators
xcrun simctl list devices

# Open simulator manually
open -a Simulator
```

---

## ✅ What to Check Before Submitting

### Visual Checks:
- [ ] App loads without errors on iPad Air (5th generation)
- [ ] Welcome screen looks good in portrait
- [ ] Auth screen looks good in portrait and landscape
- [ ] Apple Sign-In button is visible and properly styled
- [ ] No console errors appear (disable with `console.log = () => {}`)

### Functional Checks:
- [ ] Apple Sign-In button can be clicked
- [ ] Loading spinner appears when clicked
- [ ] No error messages appear immediately
- [ ] Cancel doesn't show error
- [ ] Email/password sign-in works
- [ ] Guest mode works

### Build Checks:
- [ ] Build number is 2 in app.json
- [ ] Version is 1.0.0
- [ ] All recent changes are included

---

## 📞 Testing on Real Device (Recommended!)

### Step 1: Connect Device
1. Connect iPhone/iPad via USB cable
2. Trust the computer on your device
3. Trust the developer on device (Settings → General → Device Management)

### Step 2: Run on Device
```bash
cd /Users/adialia/Desktop/quiz/app
npx expo start
```

Then:
- Press **Shift + i** in the terminal
- Or scan QR code with Expo Go app
- Or select device from list

### Step 3: Test Apple Sign-In
On real device, Apple Sign-In will work fully:
- [ ] Click "התחבר עם Apple"
- [ ] Apple Sign-In modal appears
- [ ] Sign in with Apple ID (or use test account)
- [ ] Returns to app successfully
- [ ] User is logged in

---

## 🎬 Final Testing Workflow

1. **Local Testing on iPad Simulator:**
   ```bash
   ./test-ipad.sh
   ```
   - Check UI looks good ✅
   - Check no errors on launch ✅
   - Check button appears correctly ✅

2. **Test on Real iPhone/iPad (Recommended):**
   ```bash
   npx expo start --device
   ```
   - Full Apple Sign-In flow ✅
   - Real network conditions ✅
   - Real user experience ✅

3. **Build Production Version:**
   ```bash
   eas build --platform ios --profile production
   ```
   - Wait ~15-20 minutes
   - Download build when complete

4. **Submit to App Store:**
   ```bash
   eas submit --platform ios
   ```
   - Or upload via App Store Connect

---

**Good luck! 🚀**

If you encounter any issues, check the troubleshooting section above or let me know!

#!/bin/bash

echo "🧹 Clearing app cache..."

# Clear iOS simulator data
echo "Clearing iOS simulator data..."
xcrun simctl shutdown all 2>/dev/null
rm -rf ~/Library/Developer/CoreSimulator/Caches/* 2>/dev/null

# Clear Android emulator data
echo "Clearing Android data..."
adb shell pm clear com.quizapp.mobile 2>/dev/null

# Clear Expo cache
echo "Clearing Expo cache..."
rm -rf ~/Library/Caches/Expo 2>/dev/null
rm -rf .expo 2>/dev/null
rm -rf node_modules/.cache 2>/dev/null

# Clear Metro bundler cache
echo "Clearing Metro cache..."
rm -rf /tmp/metro-* 2>/dev/null
rm -rf /tmp/haste-* 2>/dev/null

echo "✅ Cache cleared! Please restart the app."
echo ""
echo "Note: The app will now check onboarding status from the database API."

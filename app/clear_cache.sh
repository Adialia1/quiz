#!/bin/bash

# Script to clear all app cache and force fresh login
# This clears Expo cache, Metro bundler cache, and app storage

echo "🧹 Clearing all caches..."

# Stop any running Expo processes
echo "1. Stopping Expo processes..."
pkill -9 -f "expo|metro" 2>/dev/null || true

# Clear Expo cache
echo "2. Clearing Expo cache..."
rm -rf .expo
rm -rf node_modules/.cache

# Clear Metro bundler cache
echo "3. Clearing Metro bundler cache..."
rm -rf /tmp/metro-* 2>/dev/null || true
rm -rf /tmp/haste-map-* 2>/dev/null || true
rm -rf $TMPDIR/metro-* 2>/dev/null || true
rm -rf $TMPDIR/haste-map-* 2>/dev/null || true

# Clear watchman (if installed)
if command -v watchman &> /dev/null; then
    echo "4. Clearing watchman cache..."
    watchman watch-del-all
fi

echo ""
echo "✅ Cache cleared successfully!"
echo ""
echo "📱 To clear app data on your device/simulator:"
echo ""
echo "iOS Simulator:"
echo "  1. Device → Erase All Content and Settings"
echo "  OR"
echo "  2. Long press the app icon → Delete App"
echo ""
echo "Android Emulator:"
echo "  1. Settings → Apps → Quiz App → Storage → Clear Data"
echo "  OR"
echo "  2. Long press the app icon → App Info → Storage → Clear Data"
echo ""
echo "Physical Device:"
echo "  - Uninstall and reinstall the app"
echo ""
echo "Now restart with: npm start -- --clear"

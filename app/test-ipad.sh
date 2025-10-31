#!/bin/bash

echo "🧪 Testing on iPad Air (5th generation) - Apple's review device"
echo "=================================================="
echo ""

cd /Users/adialia/Desktop/quiz/app

echo "📱 Starting Expo on iPad Air (5th generation)..."
echo ""
echo "This will:"
echo "1. Start Metro bundler"
echo "2. Open iPad Air (5th generation) simulator"
echo "3. Build and install the app"
echo ""
echo "⏳ This may take 1-2 minutes on first run..."
echo ""

# Use expo run:ios which builds the native app
npx expo run:ios --device "iPad Air (5th generation)"

echo ""
echo "✅ Test complete!"

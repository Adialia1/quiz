#!/bin/bash

# iOS Device Testing Script
# Tests the app on multiple iOS devices and versions

echo "======================================"
echo "iOS Multi-Device Testing Script"
echo "======================================"
echo ""

# Define devices to test (matching Apple's review devices)
declare -a DEVICES=(
    # iPhones
    "iPhone 17 Pro"
    "iPhone 17"
    "iPhone 16e"

    # iPads - CRITICAL since review failed on iPad
    "iPad Pro 13-inch (M4)"
    "iPad Pro 11-inch (M4)"
    "iPad Air (5th generation)"
    "iPad (A16)"
)

# Build the app first
echo "📦 Building development app..."
echo "This may take a few minutes..."
echo ""

npx expo prebuild --clean
npx expo run:ios --device "iPhone 17 Pro" &
BUILD_PID=$!

# Wait for build to complete
wait $BUILD_PID

if [ $? -ne 0 ]; then
    echo "❌ Build failed. Please fix errors and try again."
    exit 1
fi

echo ""
echo "✅ Build completed successfully!"
echo ""
echo "======================================"
echo "Testing on Multiple Devices"
echo "======================================"
echo ""

# Function to test on a device
test_device() {
    local device=$1
    echo "📱 Testing on: $device"
    echo "   Starting simulator..."

    # Boot the simulator
    xcrun simctl boot "$device" 2>/dev/null

    # Give it a moment to boot
    sleep 3

    # Launch the app
    EXPO_IOS_SIMULATOR_DEVICE_NAME="$device" npx expo start --ios --no-dev --minify 2>&1 | grep -E "(error|Error|ERROR|crash|Crash|CRASH)" &
    APP_PID=$!

    # Wait for app to launch
    sleep 10

    # Kill the app process
    kill $APP_PID 2>/dev/null

    # Check simulator logs for errors
    echo "   Checking for errors..."
    xcrun simctl spawn "$device" log show --predicate 'process == "Expo Go" OR process == "אתיקה פלוס"' --last 30s --style compact 2>&1 | grep -iE "(error|exception|crash)" > "/tmp/test-$device.log"

    if [ -s "/tmp/test-$device.log" ]; then
        echo "   ⚠️  Errors detected on $device!"
        echo "   Log: /tmp/test-$device.log"
    else
        echo "   ✅ No errors detected on $device"
    fi

    # Shutdown the simulator
    xcrun simctl shutdown "$device" 2>/dev/null

    echo ""
}

# Test on each device
for device in "${DEVICES[@]}"; do
    test_device "$device"
done

echo "======================================"
echo "Testing Complete!"
echo "======================================"
echo ""
echo "Check the logs in /tmp/ for any errors:"
ls -la /tmp/test-*.log 2>/dev/null
echo ""
echo "Manual Testing Recommendations:"
echo "1. Test landscape orientation on iPads"
echo "2. Test with VoiceOver enabled"
echo "3. Test with large text sizes"
echo "4. Test with RTL layout"
echo "5. Test authentication flow"
echo "6. Test guest mode flow"
echo ""

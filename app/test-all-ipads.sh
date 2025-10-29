#!/bin/bash

# Comprehensive iPad Testing Script
# Tests the app on ALL available iPad models

set -e  # Exit on error

echo "================================================"
echo "📱 Comprehensive iPad Testing Script"
echo "================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Create logs directory
LOGS_DIR="./test-logs"
mkdir -p "$LOGS_DIR"

# Get current timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

# Log file for summary
SUMMARY_LOG="$LOGS_DIR/test-summary-$TIMESTAMP.txt"

echo "Test started at: $(date)" > "$SUMMARY_LOG"
echo "==================================================" >> "$SUMMARY_LOG"
echo "" >> "$SUMMARY_LOG"

# Get ALL iPad simulators available
echo -e "${BLUE}🔍 Finding all available iPad simulators...${NC}"
IPADS=$(xcrun simctl list devices available | grep -i "ipad" | grep -v "unavailable" | sed 's/^[[:space:]]*//' || true)

if [ -z "$IPADS" ]; then
    echo -e "${RED}❌ No iPad simulators found!${NC}"
    echo ""
    echo "Please install iPad simulators from Xcode:"
    echo "Xcode → Settings → Platforms → Download iOS Simulators"
    exit 1
fi

echo -e "${GREEN}Found iPad simulators:${NC}"
echo "$IPADS"
echo ""

# Parse iPad devices into array
declare -a IPAD_DEVICES=()
while IFS= read -r line; do
    # Extract device name and ID
    DEVICE_NAME=$(echo "$line" | sed -E 's/^([^(]+).*/\1/' | xargs)
    DEVICE_ID=$(echo "$line" | grep -oE '\([A-Z0-9-]+\)' | head -1 | tr -d '()')

    if [ ! -z "$DEVICE_NAME" ] && [ ! -z "$DEVICE_ID" ]; then
        IPAD_DEVICES+=("$DEVICE_NAME|$DEVICE_ID")
    fi
done <<< "$IPADS"

TOTAL_DEVICES=${#IPAD_DEVICES[@]}
echo -e "${BLUE}📊 Total iPad devices to test: $TOTAL_DEVICES${NC}"
echo ""

# Initialize counters
PASSED=0
FAILED=0
CURRENT=0

# Function to test on a specific iPad
test_ipad() {
    local device_info=$1
    local device_name=$(echo "$device_info" | cut -d'|' -f1)
    local device_id=$(echo "$device_info" | cut -d'|' -f2)

    CURRENT=$((CURRENT + 1))

    echo ""
    echo "================================================"
    echo -e "${BLUE}📱 Testing ($CURRENT/$TOTAL_DEVICES): $device_name${NC}"
    echo "================================================"

    local device_log="$LOGS_DIR/test-$device_name-$TIMESTAMP.log"
    local device_errors="$LOGS_DIR/errors-$device_name-$TIMESTAMP.log"

    # Boot the simulator
    echo -e "${YELLOW}⏳ Booting simulator...${NC}"
    xcrun simctl boot "$device_id" 2>/dev/null || true
    sleep 3

    # Check if booted
    local state=$(xcrun simctl list devices | grep "$device_id" | grep -o "Booted" || echo "Shutdown")

    if [ "$state" != "Booted" ]; then
        echo -e "${RED}❌ Failed to boot simulator${NC}"
        echo "FAILED - Failed to boot: $device_name" >> "$SUMMARY_LOG"
        FAILED=$((FAILED + 1))
        return 1
    fi

    echo -e "${GREEN}✅ Simulator booted${NC}"

    # Build and install app (only once for first device)
    if [ $CURRENT -eq 1 ]; then
        echo -e "${YELLOW}📦 Building app for first device...${NC}"
        echo "This may take a few minutes..."

        # Use expo to build and install
        if EXPO_IOS_SIMULATOR_DEVICE_NAME="$device_name" npx expo run:ios --device "$device_id" > "$device_log" 2>&1; then
            echo -e "${GREEN}✅ App built and installed${NC}"
        else
            echo -e "${RED}❌ Build failed!${NC}"
            echo "Check log: $device_log"
            echo "FAILED - Build error: $device_name" >> "$SUMMARY_LOG"
            FAILED=$((FAILED + 1))
            xcrun simctl shutdown "$device_id" 2>/dev/null || true
            return 1
        fi
    else
        # For subsequent devices, just launch the app
        echo -e "${YELLOW}🚀 Installing app...${NC}"

        # Install the built app (it should be in DerivedData)
        local app_path=$(find ~/Library/Developer/Xcode/DerivedData -name "אתיקה פלוס.app" -o -name "EthicsPlus.app" | head -1)

        if [ ! -z "$app_path" ]; then
            xcrun simctl install "$device_id" "$app_path" 2>/dev/null || true
        fi
    fi

    # Wait for app to launch
    sleep 5

    # Launch the app
    echo -e "${YELLOW}🚀 Launching app...${NC}"
    xcrun simctl launch "$device_id" com.ethicsplus.mobile > /dev/null 2>&1 || true

    # Wait for app to initialize
    echo -e "${YELLOW}⏳ Waiting for app to initialize (30 seconds)...${NC}"
    sleep 30

    # Check for errors in device logs
    echo -e "${YELLOW}🔍 Checking for errors...${NC}"
    xcrun simctl spawn "$device_id" log show --last 30s --predicate 'process CONTAINS "ethicsplus" OR process CONTAINS "אתיקה"' --style compact 2>&1 | \
        grep -iE "(error|exception|crash|fatal|abort)" > "$device_errors" || true

    # Analyze results
    if [ -s "$device_errors" ]; then
        echo -e "${RED}❌ ERRORS DETECTED${NC}"
        echo ""
        echo "Error summary:"
        head -5 "$device_errors"
        echo ""
        echo "Full log: $device_errors"
        echo "FAILED - Errors detected: $device_name" >> "$SUMMARY_LOG"
        echo "  See: $device_errors" >> "$SUMMARY_LOG"
        FAILED=$((FAILED + 1))
    else
        echo -e "${GREEN}✅ NO ERRORS DETECTED${NC}"
        echo "PASSED: $device_name" >> "$SUMMARY_LOG"
        PASSED=$((PASSED + 1))
        rm -f "$device_errors"  # Clean up empty error log
    fi

    # Take screenshot
    local screenshot="$LOGS_DIR/screenshot-$device_name-$TIMESTAMP.png"
    xcrun simctl io "$device_id" screenshot "$screenshot" 2>/dev/null || true

    if [ -f "$screenshot" ]; then
        echo -e "${GREEN}📸 Screenshot saved: $screenshot${NC}"
    fi

    # Shutdown simulator
    echo -e "${YELLOW}🛑 Shutting down simulator...${NC}"
    xcrun simctl shutdown "$device_id" 2>/dev/null || true

    sleep 2
}

# Test on each iPad
for device_info in "${IPAD_DEVICES[@]}"; do
    test_ipad "$device_info"
done

# Print summary
echo ""
echo "================================================"
echo -e "${BLUE}📊 TEST SUMMARY${NC}"
echo "================================================"
echo ""
echo -e "${GREEN}✅ Passed: $PASSED${NC}"
echo -e "${RED}❌ Failed: $FAILED${NC}"
echo -e "${BLUE}📝 Total Tested: $TOTAL_DEVICES${NC}"
echo ""

# Write summary to log
echo "" >> "$SUMMARY_LOG"
echo "==================================================" >> "$SUMMARY_LOG"
echo "SUMMARY:" >> "$SUMMARY_LOG"
echo "  Passed: $PASSED" >> "$SUMMARY_LOG"
echo "  Failed: $FAILED" >> "$SUMMARY_LOG"
echo "  Total:  $TOTAL_DEVICES" >> "$SUMMARY_LOG"
echo "" >> "$SUMMARY_LOG"
echo "Test completed at: $(date)" >> "$SUMMARY_LOG"

# Show summary log location
echo -e "${BLUE}📄 Summary log: $SUMMARY_LOG${NC}"
echo ""

# Show screenshots
if ls "$LOGS_DIR"/screenshot-*.png 1> /dev/null 2>&1; then
    echo -e "${BLUE}📸 Screenshots saved in: $LOGS_DIR${NC}"
    echo ""
fi

# Show error logs if any
if ls "$LOGS_DIR"/errors-*.log 1> /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Error logs:${NC}"
    ls -lh "$LOGS_DIR"/errors-*.log
    echo ""
fi

# Display detailed results
echo "================================================"
echo "DETAILED RESULTS:"
echo "================================================"
cat "$SUMMARY_LOG"
echo ""

# Exit with error if any tests failed
if [ $FAILED -gt 0 ]; then
    echo -e "${RED}⚠️  Some tests failed! Review the error logs above.${NC}"
    exit 1
else
    echo -e "${GREEN}🎉 All tests passed!${NC}"
    exit 0
fi

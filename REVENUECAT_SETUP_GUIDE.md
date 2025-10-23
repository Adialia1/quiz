# 🎯 RevenueCat & App Store Connect Setup Guide

**Last Updated:** 2025-10-23
**App:** אתיקה פלוס (Ethics Plus)
**Bundle ID:** com.ethicsplus.mobile

---

## ❗ CURRENT STATUS

Your app has:
- ✅ RevenueCat SDK installed (`react-native-purchases` v9.5.4)
- ✅ RevenueCat API Key configured (in `app.json`)
- ✅ Subscription screen implemented
- ❌ Products NOT configured in RevenueCat dashboard
- ❌ IAP products NOT created in App Store Connect

**Current Error:** "Plans not found" = RevenueCat offerings are empty

---

## 📋 STEP-BY-STEP SETUP

### STEP 1: RevenueCat Dashboard Configuration

#### 1.1 Login to RevenueCat
Go to: https://app.revenuecat.com

#### 1.2 Create Products

**Navigate to:** Projects → [Your Project] → Products

**Create Product #1: Monthly Subscription**
- Click "+ New" button
- **Product ID:** `quiz_monthly_1999` (MUST match exactly!)
- **Type:** Subscription
- **Store:** iOS App Store
- **Description:** Monthly subscription with 3-day trial
- Click "Save"

**Create Product #2: Quarterly Subscription**
- Click "+ New" button
- **Product ID:** `quiz_quarterly_4999` (MUST match exactly!)
- **Type:** Subscription
- **Store:** iOS App Store
- **Description:** 3-month subscription (best value)
- Click "Save"

#### 1.3 Create Entitlement

**Navigate to:** Projects → [Your Project] → Entitlements

- Click "+ New"
- **Entitlement ID:** `premium` (MUST match exactly!)
- **Display Name:** Premium Access
- Click "Save"

#### 1.4 Create Offering

**Navigate to:** Projects → [Your Project] → Offerings

**Create Default Offering:**
- Click "+ New"
- **Offering ID:** `default`
- **Description:** Default subscription offering
- Click "Save"

**Attach Products to Offering:**
- Click on the "default" offering
- Click "+ Add Package"
- For Monthly:
  - **Package Type:** Custom
  - **Package Identifier:** monthly
  - **Product:** quiz_monthly_1999
  - Click "Add"
- Click "+ Add Package" again
- For Quarterly:
  - **Package Type:** Custom
  - **Package Identifier:** quarterly
  - **Product:** quiz_quarterly_4999
  - Click "Add"

**Make Offering Current:**
- Toggle "Set as current" for the default offering

---

### STEP 2: App Store Connect - Create IAP Products

#### 2.1 Login to App Store Connect
Go to: https://appstoreconnect.apple.com

#### 2.2 Navigate to Your App
- Click on "My Apps"
- Select "אתיקה פלוס" (Ethics Plus)
- Go to **Features** → **In-App Purchases**

#### 2.3 Create Subscription Group

**First time only:**
- Click "+ Subscription Group"
- **Reference Name:** Premium Subscriptions
- **Group ID:** premium_subscriptions
- Click "Create"

#### 2.4 Create Monthly Subscription

**Click "+ Add Subscription"**

**Reference Information:**
- **Reference Name:** Monthly Premium Subscription with Trial
- **Product ID:** `quiz_monthly_1999` (MUST match exactly!)
- **Subscription Group:** Premium Subscriptions

**Subscription Duration:**
- Select: **1 month**

**Subscription Prices:**
- Click "+ Add Pricing"
- Select all territories or just Israel (IL)
- **Price:** Choose tier (suggest: $39.99 or ₪149.90)
- Click "Next" → "Add"

**Subscription Free Trial:**
- Click "Add" under Free Trial
- **Duration:** 3 days
- Click "Done"

**Localizations - HEBREW (CRITICAL!):**
- Click "+ Add Localization"
- **Language:** Hebrew (עברית)
- **Display Name:** מנוי חודשי פרימיום
- **Description:**
  ```
  גישה מלאה לכל שאלות המבחן, תרגול ללא הגבלה, ומעקב אחר התקדמות

  • גישה לבנק שאלות מלא
  • מבחנים ללא הגבלה
  • מנטור AI מותאם אישית
  • משחקי קלפים ומעקב התקדמות

  3 ימי ניסיון חינם, לאחר מכן ₪149.90 לחודש
  ניתן לבטל בכל עת
  ```
- Click "Done"

**Add English Localization (backup):**
- Click "+ Add Localization"
- **Language:** English (US)
- **Display Name:** Monthly Premium Subscription
- **Description:**
  ```
  Full access to all exam questions, unlimited practice, and progress tracking

  • Access to complete question bank
  • Unlimited full exams
  • AI mentor for personalized help
  • Flashcard games and progress tracking

  3-day free trial, then $39.99/month
  Cancel anytime
  ```
- Click "Done"

**App Store Information:**
- **Screenshot:** (We'll add this in Step 3)
- Click "Save"

**IMPORTANT:** Click "Submit for Review" button for this IAP

---

#### 2.5 Create Quarterly Subscription

**Click "+ Add Subscription"**

**Reference Information:**
- **Reference Name:** 3-Month Premium Subscription (Best Value)
- **Product ID:** `quiz_quarterly_4999` (MUST match exactly!)
- **Subscription Group:** Premium Subscriptions

**Subscription Duration:**
- Select: **3 months**

**Subscription Prices:**
- Click "+ Add Pricing"
- Select all territories or just Israel (IL)
- **Price:** Choose tier (suggest: $99.99 or ₪379.90)
- Click "Next" → "Add"

**Subscription Free Trial:**
- Leave empty (no trial for quarterly)

**Localizations - HEBREW:**
- Click "+ Add Localization"
- **Language:** Hebrew (עברית)
- **Display Name:** מנוי 3 חודשים פרימיום
- **Description:**
  ```
  גישה מלאה לכל שאלות המבחן ל-3 חודשים - הכי משתלם!

  • גישה לבנק שאלות מלא
  • מבחנים ללא הגבלה
  • מנטור AI מותאם אישית
  • משחקי קלפים ומעקב התקדמות

  ₪379.90 ל-3 חודשים (₪126.63 לחודש)
  חיסכון של 15% לעומת מנוי חודשי
  ניתן לבטל בכל עת
  ```
- Click "Done"

**Add English Localization:**
- **Language:** English (US)
- **Display Name:** 3-Month Premium Subscription
- **Description:**
  ```
  Full access to all exam questions for 3 months - Best Value!

  • Access to complete question bank
  • Unlimited full exams
  • AI mentor for personalized help
  • Flashcard games and progress tracking

  $99.99 for 3 months ($33.33/month)
  Save 15% vs monthly subscription
  Cancel anytime
  ```
- Click "Done"

**App Store Information:**
- **Screenshot:** (We'll add this in Step 3)
- Click "Save"

**IMPORTANT:** Click "Submit for Review" button for this IAP

---

### STEP 3: Create Screenshots for IAP Review

Apple requires screenshots showing how each IAP appears in your app.

#### 3.1 Take Screenshots

**On iOS Simulator:**
1. Open your app
2. Navigate to the subscription screen
3. Take screenshot (⌘S or Cmd+S)
4. Screenshot should show:
   - Both subscription plans clearly visible
   - Prices displayed
   - "התחל ניסיון חינם" / "התחל עכשיו" buttons
   - Plan details

**Required Sizes:**
- iPad Pro 12.9" (2732 x 2048 px) - Required
- iPhone 15 Pro Max (2796 x 1290 px) - Recommended

#### 3.2 Upload Screenshots to Each IAP

**For Monthly Subscription:**
1. Go to App Store Connect → Your App → In-App Purchases
2. Click on "Monthly Premium Subscription"
3. Scroll to "App Store Information"
4. Click "+ Add Screenshot"
5. Upload the screenshot
6. Click "Save"

**For Quarterly Subscription:**
1. Same steps as above
2. Click on "3-Month Premium Subscription"
3. Upload screenshot
4. Click "Save"

---

### STEP 4: Link RevenueCat to App Store Connect

#### 4.1 Get App Store Connect API Key

**In App Store Connect:**
1. Go to Users and Access → Keys
2. Under "In-App Purchase", click "Generate API Key" or use existing key
3. Copy the **Key ID** and download the **.p8 file**
4. Note your **Issuer ID** (shown at top of page)

#### 4.2 Add to RevenueCat

**In RevenueCat Dashboard:**
1. Go to Project Settings → Integrations → Apple App Store
2. Click "Configure"
3. Enter:
   - **Issuer ID:** [from App Store Connect]
   - **Key ID:** [from App Store Connect]
   - **Private Key:** Upload the .p8 file
4. Click "Save"

---

### STEP 5: Submit IAPs for Review

**Critical Steps:**

1. **Verify Both IAPs Have:**
   - ✅ Product ID matches exactly (`quiz_monthly_1999`, `quiz_quarterly_4999`)
   - ✅ Pricing set
   - ✅ Hebrew localizations
   - ✅ Screenshots uploaded
   - ✅ Descriptions complete

2. **Submit Each IAP:**
   - Click "Submit for Review" for monthly subscription
   - Click "Submit for Review" for quarterly subscription
   - Wait for status to change to "Waiting for Review" or "In Review"

3. **DO NOT submit the app yet** - Wait for IAPs to be approved first

---

### STEP 6: Resubmit App Binary

After IAPs are approved:

1. Go to your app version in App Store Connect
2. If previously rejected, respond: "In-app purchases have been submitted for review and approved"
3. Click "Resubmit for Review"

**If you need to update the app binary:**
```bash
# Build new version
eas build --platform ios --profile production

# Wait for build to complete
# Submit to App Store
eas submit --platform ios
```

---

## 🧪 TESTING IN DEVELOPMENT

### Test Mode (For UI Development)

While waiting for IAP approval, you can test the UI:

**The app already handles Expo Go mode** - it will show the subscription screen but with a development message.

### Sandbox Testing (After Products Created)

Once IAPs are created in App Store Connect:

1. **Create Sandbox Tester Account:**
   - App Store Connect → Users and Access → Sandbox Testers
   - Click "+"
   - Create test account with unique email
   - **IMPORTANT:** Don't use real Apple ID!

2. **Configure iOS Device:**
   - Settings → App Store → Sandbox Account
   - Sign in with sandbox tester account

3. **Test Purchases:**
   - Run development build: `npm run ios`
   - Navigate to subscription screen
   - Select plan and purchase
   - Use sandbox credentials when prompted
   - **Note:** Sandbox subscriptions expire quickly:
     - 3-day trial = 3 minutes in sandbox
     - 1 month = 5 minutes in sandbox

4. **Check Logs:**
   ```bash
   # Watch RevenueCat logs
   npx expo start
   # Then in the app, check console for RevenueCat debug logs
   ```

---

## ✅ VERIFICATION CHECKLIST

Use this checklist to verify everything is set up:

### RevenueCat Dashboard:
- [ ] Logged into https://app.revenuecat.com
- [ ] Product `quiz_monthly_1999` created
- [ ] Product `quiz_quarterly_4999` created
- [ ] Entitlement `premium` created
- [ ] Offering `default` created and set as current
- [ ] Both products attached to `default` offering
- [ ] App Store Connect API key connected

### App Store Connect:
- [ ] Logged into https://appstoreconnect.apple.com
- [ ] Subscription group "Premium Subscriptions" created
- [ ] IAP `quiz_monthly_1999` created with:
  - [ ] 3-day free trial
  - [ ] Pricing set (e.g., $39.99 or ₪149.90)
  - [ ] Hebrew localization
  - [ ] English localization
  - [ ] Screenshot uploaded
  - [ ] **Submitted for Review**
- [ ] IAP `quiz_quarterly_4999` created with:
  - [ ] No trial
  - [ ] Pricing set (e.g., $99.99 or ₪379.90)
  - [ ] Hebrew localization
  - [ ] English localization
  - [ ] Screenshot uploaded
  - [ ] **Submitted for Review**

### App Code:
- [ ] RevenueCat API key in `app.json`: `appl_bszHXHXrgbpGQdAwAHHELLKLIxQ` ✅
- [ ] Product IDs in code match exactly ✅
- [ ] Entitlement ID matches ✅
- [ ] App builds successfully

### Testing:
- [ ] Sandbox tester account created
- [ ] Test purchase with monthly plan works
- [ ] Test purchase with quarterly plan works
- [ ] Restore purchases works
- [ ] Subscription status syncs to backend

---

## 🔧 TROUBLESHOOTING

### "Plans not found" Error

**Cause:** RevenueCat offerings are empty

**Solution:**
1. Verify products created in RevenueCat dashboard
2. Verify products attached to "default" offering
3. Verify "default" offering is set as current
4. Wait 5 minutes for RevenueCat to sync
5. Restart the app

**Debug:**
```typescript
// In useSubscription.ts, check logs:
[SUBSCRIPTION] Looking for entitlement ID: premium
[SUBSCRIPTION] Available entitlements: []
[SUBSCRIPTION] No active entitlement found
```

### "Payment disabled in Expo" Message

**Cause:** Running in Expo Go

**Solution:**
- Expo Go doesn't support native modules like RevenueCat
- Build development build:
  ```bash
  eas build --profile development --platform ios
  # Install on device and test
  ```

### Products Not Showing in App

**Causes:**
1. Products not synced to RevenueCat
2. API key mismatch
3. Product IDs don't match

**Debug Steps:**
1. Check RevenueCat dashboard - Products tab
2. Verify product IDs match exactly
3. Check console logs for errors
4. Try: `await Purchases.syncPurchases()`

### Sandbox Purchase Fails

**Common Issues:**
- Using wrong Apple ID (must use sandbox tester)
- IAP not approved in App Store Connect
- Device not configured for sandbox testing
- Network issues

---

## 📞 SUPPORT

**RevenueCat Support:**
- Dashboard: https://app.revenuecat.com
- Docs: https://docs.revenuecat.com
- Support: support@revenuecat.com

**App Store Connect Support:**
- Dashboard: https://appstoreconnect.apple.com
- Developer Support: https://developer.apple.com/support

**Your Configuration:**
- Bundle ID: `com.ethicsplus.mobile`
- RevenueCat API Key: `appl_bszHXHXrgbpGQdAwAHHELLKLIxQ`
- Products: `quiz_monthly_1999`, `quiz_quarterly_4999`
- Entitlement: `premium`

---

## 🎯 NEXT STEPS

**RIGHT NOW:**

1. **[ ] Create products in RevenueCat dashboard** (15 min)
   - Follow STEP 1 above exactly

2. **[ ] Create IAPs in App Store Connect** (30 min)
   - Follow STEP 2 above exactly
   - Make sure product IDs match EXACTLY

3. **[ ] Take screenshots** (10 min)
   - Run app, go to subscription screen
   - Take screenshot (⌘S)

4. **[ ] Upload screenshots and submit IAPs** (10 min)
   - Upload to each IAP
   - Click "Submit for Review" for each

5. **[ ] Test in development build** (if available)
   - Create sandbox tester
   - Test purchases

**TOTAL TIME: ~1-2 hours**

**EXPECTED TIMELINE:**
- IAP review: 24-48 hours
- App review (after IAP approval): 24-72 hours
- **Total: 2-5 days typically**

---

**Good luck! 🚀**

After completing STEP 1 (RevenueCat dashboard), you should see the plans in your app immediately.

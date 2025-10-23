# 🎨 RevenueCat Paywall Setup Guide

**Status:** ✅ SDK Installed and Configured

---

## ✅ What's Done

1. **Package Installed:** `react-native-purchases-ui` v9.6.0
2. **Screen Created:** `RevenueCatPaywallScreen.tsx`
3. **App Updated:** Using RevenueCat Paywall instead of custom screen
4. **Code Fixed:** Fallback to "all" offering if no current offering

---

## 🎯 Next Steps

### 1. Set "all" Offering as Current (CRITICAL!)

**Go to RevenueCat Dashboard:**
- URL: https://app.revenuecat.com
- Navigate to: **Offerings** tab
- Click on the **"all"** offering
- **Toggle "Set as Current"** or **"Make Current"**
- Save

**This is the most important step!** Your app looks for the "current" offering.

---

### 2. Configure Your Paywall Design in RevenueCat Dashboard

**Navigate to:** Paywalls tab in RevenueCat dashboard

You already have a paywall created called **"all"**. Now you can customize it:

#### A. Edit the Paywall
- Click on your "all" paywall
- Click "Edit"

#### B. Customize Design
- **Template:** Choose from templates or create custom
- **Colors:** Match your app (Primary: #0A76F3)
- **Text:** Add Hebrew text for:
  - Title: "קבל גישה מלאה"
  - Subtitle: "בחר תוכנית והתחל ללמוד"
  - Features list in Hebrew
  - Button text: "התחל עכשיו"

#### C. Add Localizations
- Click "+ Add Localization"
- Select **Hebrew (עברית)**
- Fill in all text fields in Hebrew
- Add **English** as fallback

#### D. Configure Packages
Make sure both packages are displayed:
- Monthly: `quiz_monthly_1999`
- Quarterly: `quiz_quarterly_4999`

#### E. Preview & Publish
- Use the preview to see how it looks
- Click **"Publish"** when ready

---

## 📱 How It Works Now

### User Flow:

1. **User registers** → Sees onboarding
2. **Onboarding completes** → Checks subscription status
3. **No active subscription** → Shows RevenueCat Paywall (managed from dashboard)
4. **User purchases** → Redirected to home screen
5. **User can logout** → Button at bottom of paywall

### Benefits:

✅ **No app updates needed** for paywall changes
✅ **A/B testing** from dashboard
✅ **Professional UI** from RevenueCat
✅ **Hebrew support** built-in
✅ **Conversion analytics** automatic

---

## 🎨 Paywall Customization Tips

### Colors to Use (Match Your App):
- Primary: `#0A76F3`
- Success: `#3CCF4E`
- Background: `#FFFFFF`
- Secondary: `#E3F2FD`

### Text Recommendations:

**Title (Hebrew):**
```
קבל גישה מלאה לכל התכנים
```

**Subtitle (Hebrew):**
```
בחר תוכנית והתחל ללמוד היום
```

**Features (Hebrew):**
```
✓ גישה לכל בנק השאלות
✓ מבחנים מלאים ללא הגבלה
✓ מנטור חכם לעזרה מותאמת אישית
✓ משחקי קלפים ומעקב אחר התקדמות
```

**Monthly Plan:**
```
Title: מנוי חודשי
Price: $39.99 לחודש
Trial: 3 ימי ניסיון חינם
```

**Quarterly Plan:**
```
Title: 3 חודשים - הכי משתלם!
Price: $99.99 ל-3 חודשים
Savings: חיסכון של 15%
```

**Button Text:**
```
התחל ניסיון חינם (for monthly with trial)
התחל עכשיו (for quarterly)
```

---

## 🧪 Testing

### In Development Build:

1. Build the app:
```bash
npm run ios
```

2. Navigate to subscription screen
3. You should see the RevenueCat paywall with your design
4. Try purchasing (use sandbox account)
5. Try restoring purchases

### Expected Behavior:

- ✅ Paywall displays with your design from dashboard
- ✅ Both plans show with correct prices
- ✅ All text is in Hebrew
- ✅ Purchase works
- ✅ Restore works
- ✅ After purchase, user goes to home screen
- ✅ Logout button at bottom works

---

## 🔄 Switching Back to Custom Paywall

If you want to use your custom paywall instead:

**Edit App.tsx:**

Change line 345:
```typescript
// FROM:
<RevenueCatPaywallScreen
  onComplete={() => setShowSubscriptionPaywall(false)}
  showSkip={false}
/>

// TO:
<SubscriptionPlansScreen
  onComplete={() => setShowSubscriptionPaywall(false)}
  showSkip={false}
/>
```

---

## 📊 RevenueCat Paywall vs Custom Paywall

| Feature | RevenueCat Paywall | Custom Paywall |
|---------|-------------------|----------------|
| Design Control | Medium (templates) | Full |
| Update Speed | Instant (no app update) | Requires app update |
| A/B Testing | Built-in | Manual |
| RTL Support | Automatic | Manual |
| Analytics | Built-in | Manual |
| Maintenance | Low | High |
| Customization | Templates + tweaks | Unlimited |

---

## 🔗 Resources

**RevenueCat Dashboard:**
- Main: https://app.revenuecat.com
- Paywalls: https://app.revenuecat.com/paywalls
- Offerings: https://app.revenuecat.com/offerings

**Documentation:**
- Creating Paywalls: https://www.revenuecat.com/docs/tools/paywalls/creating-paywalls
- Displaying Paywalls: https://www.revenuecat.com/docs/tools/paywalls/displaying-paywalls
- Customization: https://www.revenuecat.com/docs/tools/paywalls/creating-paywalls/components

**Your Configuration:**
- Bundle ID: `com.ethicsplus.mobile`
- API Key: `appl_bszHXHXrgbpGQdAwAHHELLKLIxQ`
- Offering: `all`
- Products: `quiz_monthly_1999`, `quiz_quarterly_4999`
- Entitlement: `premium`

---

## ✅ Checklist

Before testing:
- [ ] "all" offering is set as "current" in RevenueCat dashboard
- [ ] Paywall design is customized with Hebrew text
- [ ] Both products are attached to the offering
- [ ] Paywall is published (not draft)
- [ ] App is rebuilt with latest changes

---

**That's it! Your app now uses RevenueCat's managed paywalls.** 🎉

Test it out and customize the design from the dashboard!

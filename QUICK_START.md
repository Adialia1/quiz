# 🚀 RevenueCat Quick Start - FIX "Plans Not Found"

**Problem:** You're seeing "plans not found" in your development build.

**Cause:** Products aren't configured in RevenueCat dashboard yet.

---

## ✅ 30-MINUTE FIX

### 1️⃣ RevenueCat Dashboard (10 min)

**Go to:** https://app.revenuecat.com

**Create 2 Products:**
- Product ID: `quiz_monthly_1999`
- Product ID: `quiz_quarterly_4999`

**Create 1 Entitlement:**
- Entitlement ID: `premium`

**Create 1 Offering:**
- Offering ID: `default`
- Add both products to this offering
- **Set as current** ← CRITICAL!

### 2️⃣ App Store Connect (20 min)

**Go to:** https://appstoreconnect.apple.com

**Create 2 Subscriptions:**

**Monthly:**
- Product ID: `quiz_monthly_1999` (EXACT!)
- Duration: 1 month
- Free Trial: 3 days
- Price: $39.99 or ₪149.90
- Hebrew localization: "מנוי חודשי פרימיום"
- **Submit for Review**

**Quarterly:**
- Product ID: `quiz_quarterly_4999` (EXACT!)
- Duration: 3 months
- No trial
- Price: $99.99 or ₪379.90
- Hebrew localization: "מנוי 3 חודשים פרימיום"
- **Submit for Review**

---

## ✨ Test Immediately

After completing Step 1 (RevenueCat), your app should work!

**Check logs:**
```
[SUBSCRIPTION] Current offering has 2 packages
```

If you see this ↑, it's working! 🎉

---

## 📖 Full Guide

See `REVENUECAT_SETUP_GUIDE.md` for:
- Detailed step-by-step instructions
- Screenshots examples
- Troubleshooting
- Sandbox testing setup

---

## 🆘 Still Having Issues?

**Check console for:**
```
⚠️ [SUBSCRIPTION] No current offering found!
```

**Common fixes:**
1. Make sure offering is set as "current" in RevenueCat
2. Product IDs must match EXACTLY
3. Wait 2-3 minutes for RevenueCat to sync
4. Restart the app

**Product IDs MUST BE:**
- `quiz_monthly_1999`
- `quiz_quarterly_4999`

**Entitlement MUST BE:**
- `premium`

---

**Good luck! 🎯**

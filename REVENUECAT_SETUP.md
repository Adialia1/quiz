# RevenueCat Subscription Setup Guide

Complete guide for setting up RevenueCat subscriptions with Stripe integration for the Quiz App.

## 📋 Overview

**Subscription Plans:**
- **Monthly Plan**: ₪69/month with 3-day free trial
- **Quarterly Plan**: ₪189/3 months (~₪63/month, 9% discount)

**Payment Methods:**
- Apple Pay (iOS via App Store)
- Google Pay (Android via Google Play)
- Credit Card (via Stripe for web/direct)

---

## 🚀 Quick Start

### 1. Database Migration

Run this SQL in your Supabase SQL Editor:

```bash
# Location: api/migrations/add_subscription_fields.sql
```

This adds the necessary subscription fields to your `users` table:
- `subscription_period` (monthly/quarterly)
- `is_in_trial` (boolean)
- `subscription_will_renew` (boolean)

### 2. RevenueCat Dashboard Setup

#### A. Create Account & Project
1. Go to https://app.revenuecat.com
2. Create an account or sign in
3. Create a new project: "Quiz App"

#### B. Configure Stripe Integration
1. In RevenueCat Dashboard → **Integrations** → **Stripe**
2. Click "Connect Stripe Account"
3. Authorize your Stripe account
4. Map your products (see step 3)

#### C. Create Products

In RevenueCat Dashboard → **Products**:

**Monthly Plan:**
- Product ID: `quiz_monthly_69`
- Price: ₪69
- Duration: 1 month
- Trial: 3 days

**Quarterly Plan:**
- Product ID: `quiz_quarterly_189`
- Price: ₪189
- Duration: 3 months
- Trial: None

#### D. Create Entitlement

1. Go to **Entitlements** → **Create Entitlement**
2. Name: `premium`
3. Attach both products to this entitlement

#### E. Create Offering

1. Go to **Offerings** → **Create Offering**
2. Identifier: `default`
3. Add both packages:
   - Monthly package (quiz_monthly_69)
   - Quarterly package (quiz_quarterly_189)
4. Set as current offering

#### F. Get API Keys

1. Go to **Project Settings** → **API Keys**
2. Copy your **Public API Key**
3. Add to `.env`:
   ```bash
   EXPO_PUBLIC_REVENUECAT_API_KEY=your_public_key_here
   ```

### 3. App Store Connect Setup (iOS)

#### A. Prerequisites
- Apple Developer Account ($99/year)
- App registered in App Store Connect

#### B. Create In-App Purchases

1. Go to App Store Connect → Your App → **In-App Purchases**
2. Create **Auto-Renewable Subscriptions**:

**Monthly Subscription:**
- Product ID: `quiz_monthly_69`
- Reference Name: "Quiz Monthly Premium"
- Subscription Group: "Quiz Premium"
- Price: ₪69/month
- Free Trial: 3 days

**Quarterly Subscription:**
- Product ID: `quiz_quarterly_189`
- Reference Name: "Quiz Quarterly Premium"
- Subscription Group: "Quiz Premium"
- Price: ₪189/3 months

#### C. Link to RevenueCat

1. In RevenueCat Dashboard → **Project Settings** → **Apps**
2. Add iOS app
3. Enter Bundle ID
4. Add App Store Shared Secret:
   - Get from App Store Connect → Users and Access → Keys → In-App Purchase
   - Paste in RevenueCat

### 4. Google Play Console Setup (Android)

#### A. Prerequisites
- Google Play Developer Account ($25 one-time)
- App registered in Google Play Console

#### B. Create Subscriptions

1. Go to Google Play Console → Your App → **Monetization** → **Subscriptions**
2. Create products:

**Monthly Subscription:**
- Product ID: `quiz_monthly_69`
- Name: "Quiz Monthly Premium"
- Price: ₪69/month
- Free Trial: 3 days

**Quarterly Subscription:**
- Product ID: `quiz_quarterly_189`
- Name: "Quiz Quarterly Premium"
- Price: ₪189/3 months

#### C. Link to RevenueCat

1. In RevenueCat Dashboard → **Project Settings** → **Apps**
2. Add Android app
3. Enter Package Name
4. Service Account:
   - Create in Google Cloud Console
   - Grant permissions in Play Console
   - Upload JSON to RevenueCat

### 5. Configure Webhooks

#### A. RevenueCat → Backend Webhook

1. In RevenueCat Dashboard → **Integrations** → **Webhooks**
2. Add webhook URL:
   ```
   https://your-api-url.com/api/subscriptions/webhook
   ```
3. Copy webhook secret
4. Add to backend `.env`:
   ```bash
   REVENUECAT_WEBHOOK_SECRET=your_webhook_secret_here
   ```

This webhook will automatically:
- Update user subscription status in database
- Track trial periods
- Handle renewals and cancellations
- Sync expiration dates

---

## 📱 Integration in the App

### Screens Created

1. **SubscriptionPlansScreen** (`app/src/screens/SubscriptionPlansScreen.tsx`)
   - Beautiful plan selection UI
   - Shows monthly (with trial) and quarterly (best value) options
   - Integrated purchase flow
   - Restore purchases

2. **SubscriptionManagementScreen** (`app/src/screens/SubscriptionManagementScreen.tsx`)
   - View current subscription
   - Change plans
   - Manage in App Store/Play Store
   - View trial status and expiration

### Hook Usage

```typescript
import { useSubscription } from '../hooks/useSubscription';

const {
  subscriptionInfo,     // Current subscription details
  isPremium,           // Boolean: active subscription?
  isInTrial,           // Boolean: in trial period?
  isLoading,           // Loading state
  error,               // Error message

  // Actions
  purchaseSubscription,  // Purchase a plan
  restorePurchases,     // Restore previous purchases
  fetchSubscriptionStatus, // Refresh status
  getOfferings,         // Get available plans
} = useSubscription();
```

### Navigation

```typescript
// Show subscription plans
navigation.navigate('SubscriptionPlans');

// Show subscription management
navigation.navigate('SubscriptionManagement');
```

---

## 🔧 API Endpoints

### GET /api/subscriptions/status
Get current user's subscription status

**Response:**
```json
{
  "subscription_status": "active",
  "subscription_period": "quarterly",
  "subscription_expires_at": "2025-01-15T00:00:00Z",
  "is_in_trial": false,
  "will_renew": true,
  "days_remaining": 45
}
```

### POST /api/subscriptions/status
Update subscription status (called by app after purchase)

**Body:**
```json
{
  "subscription_status": "active",
  "subscription_period": "monthly",
  "subscription_expires_at": "2025-01-15T00:00:00Z",
  "is_in_trial": true,
  "will_renew": true
}
```

### POST /api/subscriptions/purchase
Track a purchase for analytics

**Body:**
```json
{
  "plan_id": "quiz_monthly_69",
  "price": 69,
  "currency": "ILS",
  "revenuecat_transaction_id": "txn_123"
}
```

### POST /api/subscriptions/webhook
RevenueCat webhook for automatic sync

Handles events:
- `INITIAL_PURCHASE`
- `RENEWAL`
- `CANCELLATION`
- `EXPIRATION`
- `BILLING_ISSUE`

---

## 🎨 UI Components

### Plan Cards
- Visual comparison between monthly and quarterly
- "Best Value" badge on quarterly plan
- Shows trial period on monthly
- Shows savings on quarterly
- Checkmarks for selected plan

### Features List
- All included features
- Checkmark icons
- RTL-aligned

### Colors
- Primary: `#0A76F3` (titles, selected)
- Accent: `#FFC107` (subscribe button)
- Success: `#3CCF4E` (badges, savings)
- Background: `#FFFFFF`

---

## 🧪 Testing

### Test in Development

RevenueCat provides sandbox testing:

**iOS:**
1. Create sandbox tester in App Store Connect
2. Sign out of App Store on device
3. Use sandbox account when prompted

**Android:**
1. Add test account in Google Play Console
2. Download app from Internal Testing track
3. Purchase will be test transaction

### Testing Checklist

- [ ] Monthly plan purchase works
- [ ] Quarterly plan purchase works
- [ ] Trial period activates correctly
- [ ] Restore purchases works
- [ ] Plan change works (monthly ↔ quarterly)
- [ ] Webhook updates database
- [ ] Subscription status displays correctly
- [ ] Expiration date shows correctly
- [ ] Days remaining calculates correctly

---

## 🔐 Security Notes

1. **Never commit secrets**
   - `.env` is in `.gitignore`
   - RevenueCat API key is public (safe)
   - Webhook secret is private (backend only)

2. **Validate webhooks**
   - Use webhook secret to verify authenticity
   - Currently placeholder in code (TODO)

3. **Server-side verification**
   - RevenueCat handles receipt validation
   - Your backend trusts RevenueCat webhooks

---

## 📊 Analytics

RevenueCat automatically tracks:
- Revenue
- MRR (Monthly Recurring Revenue)
- Churn rate
- Trial conversion
- LTV (Lifetime Value)

Access in RevenueCat Dashboard → **Analytics**

---

## 🐛 Troubleshooting

### "No offerings available"
- Check RevenueCat API key in `.env`
- Verify offerings are published in dashboard
- Check network connection

### "Purchase failed"
- iOS: Verify App Store Connect products are approved
- Android: Verify Google Play products are active
- Check product IDs match exactly

### "Webhook not firing"
- Verify webhook URL is correct
- Check webhook secret is configured
- Test with RevenueCat webhook testing tool

### "Database not updating"
- Check webhook endpoint is accessible
- Verify CORS if needed
- Check backend logs for errors

---

## 📚 Resources

- [RevenueCat Docs](https://docs.revenuecat.com/)
- [RevenueCat React Native SDK](https://docs.revenuecat.com/docs/reactnative)
- [Stripe Dashboard](https://dashboard.stripe.com/)
- [App Store Connect](https://appstoreconnect.apple.com/)
- [Google Play Console](https://play.google.com/console/)

---

## ✅ Go-Live Checklist

Before launching to production:

**RevenueCat:**
- [ ] Switch to production API key
- [ ] Test all purchase flows
- [ ] Configure webhook URL

**iOS:**
- [ ] In-app purchases approved
- [ ] Prices set in all regions
- [ ] Privacy policy linked
- [ ] Terms of service linked

**Android:**
- [ ] Subscriptions approved
- [ ] Service account configured
- [ ] Prices set in all regions

**Backend:**
- [ ] Database migration run
- [ ] Webhook secret configured
- [ ] API endpoints tested

**App:**
- [ ] Test purchase flow
- [ ] Test restore purchases
- [ ] Test subscription management
- [ ] Test trial period

---

## 💬 Support

For issues:
1. Check RevenueCat Dashboard → Customers → find user
2. Check backend logs for webhook events
3. Check Supabase database for subscription data
4. Contact RevenueCat support (excellent!)

---

**Created:** 2025-10-14
**Version:** 1.0
**Author:** Claude Code

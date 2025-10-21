# Railway Deployment - Quick Start Guide

**⚡ TL;DR: Deploy in 15 minutes**

---

## 🎯 What You Need

- [ ] Railway account (sign up at [railway.app](https://railway.app))
- [ ] GitHub repository with your code
- [ ] Your `.env` file values ready

---

## 🚀 Step-by-Step (15 minutes)

### 1. Railway Setup (5 minutes)

```bash
# Go to railway.app and:
1. Sign up with GitHub
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your quiz repository
4. Wait for initial build
```

### 2. Add Databases (3 minutes)

```bash
# In Railway project:
1. Click "+ New" → "Database" → "PostgreSQL"
2. Click "+ New" → "Database" → "Redis"
3. Done! Railway auto-connects them
```

### 3. Set Environment Variables (5 minutes)

Click your FastAPI service → "Variables" → Add these:

```bash
OPENROUTER_API_KEY=your_key
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_key
SUPABASE_SERVICE_KEY=your_key
CLERK_SECRET_KEY=sk_test_your_key
CLERK_WEBHOOK_SECRET=whsec_your_key
NOTIFICATION_API_KEY=your_key
REDIS_ENABLED=true
POSTGRES_URL=${{Postgres.DATABASE_URL}}
```

### 4. Get Your API URL (1 minute)

```bash
# Option A: Use Railway's free domain (Quick)
Settings → Domains → Generate Domain
Copy: https://your-app.railway.app

# Option B: Use your custom domain (Recommended)
Settings → Domains → + Add Domain → api.yourdomain.com
Then add CNAME record at your DNS provider
See: CUSTOM_DOMAIN_SETUP.md for detailed guide
```

### 5. Setup GitHub Actions (1 minute)

```bash
# In GitHub repo → Settings → Secrets:
1. Add RAILWAY_TOKEN (get from railway.app/account/tokens)
2. Add RAILWAY_SERVICE_NAME (your service ID)
3. Done! Auto-deploy on push to master
```

---

## ✅ Test Deployment

```bash
# Test your API:
curl https://your-app.railway.app/health

# View API docs:
open https://your-app.railway.app/docs
```

---

## 💰 Expected Cost

**Hobby Plan ($5/month includes $5 credits):**
- Development: $3-8/month
- Production MVP: $9-22/month
- Save 70% vs AWS! 🎉

---

## 🐛 Quick Troubleshooting

**Build failed?**
- Check Railway logs in Deployments tab
- Verify `requirements.txt` is correct

**Database errors?**
- Use `${{Postgres.DATABASE_URL}}` for POSTGRES_URL
- Check PostgreSQL service is running

**GitHub Actions failed?**
- Verify RAILWAY_TOKEN secret is set
- Check token hasn't expired

---

## 📚 Need More Help?

Read the full guide: `RAILWAY_DEPLOYMENT_SETUP.md`

---

**You're done! Your API is live on Railway! 🚀**

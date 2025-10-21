# Railway Deployment Setup Guide

Complete step-by-step guide to deploy your FastAPI Quiz App to Railway with GitHub Actions.

---

## 📋 Prerequisites

- GitHub account with your quiz project
- Railway account (sign up at [railway.app](https://railway.app))
- Your `.env` file with all required credentials

---

## 🚀 Part 1: Railway Initial Setup (One-Time)

### Step 1: Create Railway Account & Project

1. Go to [railway.app](https://railway.app) and sign up with GitHub
2. Click **"New Project"**
3. Select **"Deploy from GitHub repo"**
4. Authorize Railway to access your GitHub account
5. Select your `quiz` repository
6. Railway will detect the Dockerfile and start building

### Step 2: Add PostgreSQL Database

1. In your Railway project dashboard, click **"+ New"**
2. Select **"Database"** → **"PostgreSQL"**
3. Railway will provision a PostgreSQL database
4. Click on the PostgreSQL service
5. Go to **"Variables"** tab
6. Copy the `DATABASE_URL` value (you'll need this)

### Step 3: Add Redis Cache

1. In your Railway project dashboard, click **"+ New"**
2. Select **"Database"** → **"Redis"**
3. Railway will provision a Redis instance
4. Click on the Redis service
5. Go to **"Variables"** tab
6. Note the `REDIS_URL` (Railway auto-creates this)

### Step 4: Configure Environment Variables for API Service

1. Click on your **FastAPI service** (main app)
2. Go to **"Variables"** tab
3. Click **"+ New Variable"** and add each of these:

```bash
# OpenRouter API
OPENROUTER_API_KEY=your_openrouter_api_key

# Embedding Model
EMBEDDING_MODEL=intfloat/multilingual-e5-large

# Supabase (Vector Database)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key

# Clerk Authentication
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret

# RevenueCat (Optional - for monetization)
REVENUE_CAT_API_KEY=your_revenuecat_api_key

# Notification API Key
NOTIFICATION_API_KEY=your_notification_api_key

# Redis Configuration (Railway auto-provides REDIS_URL)
REDIS_ENABLED=true
# REDIS_HOST, REDIS_PORT automatically set by Railway via REDIS_URL

# Database Configuration (Railway auto-provides DATABASE_URL)
# POSTGRES_URL automatically set by Railway
# Or reference PostgreSQL service:
POSTGRES_URL=${{Postgres.DATABASE_URL}}

# Database Pool Settings (optional)
DB_MIN_POOL_SIZE=5
DB_MAX_POOL_SIZE=20
DB_COMMAND_TIMEOUT=60
```

**💡 Pro Tip:** For `POSTGRES_URL` and Redis, you can reference Railway services:
- `${{Postgres.DATABASE_URL}}` - References your PostgreSQL service
- `${{Redis.REDIS_URL}}` - References your Redis service

### Step 5: Configure Domain (Railway or Custom)

You have two options for your API domain:

#### Option A: Use Railway's Free Domain (Quick Start)

1. In your FastAPI service, go to **"Settings"** tab
2. Scroll to **"Domains"**
3. Click **"Generate Domain"**
4. Copy the domain (e.g., `your-app.railway.app`)
5. Update your mobile app's `API_URL` to this domain

#### Option B: Use Your Custom Domain (Recommended for Production)

1. In your FastAPI service, go to **"Settings"** tab
2. Scroll to **"Domains"**
3. Click **"+ Add Domain"**
4. Enter your custom domain (e.g., `api.yourdomain.com`)

5. **Configure DNS Records at Your Domain Provider:**
   - Go to your domain registrar (e.g., GoDaddy, Namecheap, Cloudflare)
   - Add a **CNAME record**:
     - **Type:** CNAME
     - **Name:** `api` (or your preferred subdomain like `backend`, `quiz-api`)
     - **Value:** (Railway will show you the target, usually something like `your-service.railway.app`)
     - **TTL:** 3600 (or Auto)

6. **Wait for DNS Propagation** (5-60 minutes)
   - Railway will automatically provision a free SSL certificate
   - Status will show "Active" with a green checkmark when ready

7. **Verify Your Domain:**
   ```bash
   # Test that your custom domain works
   curl https://api.yourdomain.com/health

   # Should return: {"status": "healthy", ...}
   ```

8. **Update Your Mobile App:**
   - Update `app/.env`:
     ```bash
     EXPO_PUBLIC_API_URL=https://api.yourdomain.com
     ```
   - Restart your app: `npm start -- --clear`

**💡 Pro Tips for Custom Domains:**
- Use a subdomain (e.g., `api.yourdomain.com`) rather than root domain
- Railway provides **free SSL/HTTPS** automatically
- CNAME changes can take up to 48 hours but usually work in 5-10 minutes
- You can add multiple domains (e.g., `api.yourdomain.com` and `backend.yourdomain.com`)

**🔒 SSL Certificate:**
Railway automatically issues and renews SSL certificates via Let's Encrypt. No configuration needed!

---

## 🔄 Part 2: GitHub Actions Setup for Auto-Deployment

### Step 1: Get Railway Token

1. Go to [railway.app/account/tokens](https://railway.app/account/tokens)
2. Click **"Create New Token"**
3. Give it a name: "GitHub Actions Deploy"
4. Copy the token (you'll only see it once!)

### Step 2: Get Railway Service Name

1. In your Railway project, click on your FastAPI service
2. Go to **"Settings"** tab
3. Copy the **Service ID** (or you can use service name from URL)

### Step 3: Add GitHub Secrets

1. Go to your GitHub repository
2. Click **"Settings"** → **"Secrets and variables"** → **"Actions"**
3. Click **"New repository secret"**
4. Add these two secrets:

**Secret 1:**
- Name: `RAILWAY_TOKEN`
- Value: (paste the token from Step 1)

**Secret 2:**
- Name: `RAILWAY_SERVICE_NAME`
- Value: (paste the service ID from Step 2, or leave blank to deploy all services)

### Step 4: Test GitHub Actions Deployment

1. Make a small change to your code (e.g., update a comment in `api/main.py`)
2. Commit and push to `master` branch:
   ```bash
   git add .
   git commit -m "test: trigger railway deployment"
   git push origin master
   ```
3. Go to GitHub → **"Actions"** tab
4. Watch your deployment workflow run!
5. Once completed, your changes will be live on Railway

---

## ✅ Part 3: Verify Deployment

### Test Your API Endpoints

```bash
# Replace with your Railway domain
RAILWAY_URL="https://your-app.railway.app"

# Test health check
curl $RAILWAY_URL/health

# Test root endpoint
curl $RAILWAY_URL/

# Test API docs (should open in browser)
open $RAILWAY_URL/docs
```

### Check Logs

1. In Railway dashboard, click your FastAPI service
2. Go to **"Deployments"** tab
3. Click on the latest deployment
4. View logs to debug any issues

---

## 🎯 Part 4: Connect Mobile App to Railway

### Update Your React Native App

1. Open `app/.env` (or create if not exists)
2. Update the API URL:

```bash
# Railway API URL
EXPO_PUBLIC_API_URL=https://your-app.railway.app

# Keep other vars
EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
EXPO_PUBLIC_REVENUECAT_API_KEY=xxxxx
```

3. Restart your Expo app:
```bash
cd app
npm start -- --clear
```

---

## 🔧 Troubleshooting

### Issue: Build Failed

**Solution:**
1. Check Railway deployment logs
2. Verify all dependencies in `requirements.txt` are correct
3. Ensure `Dockerfile` is in project root
4. Check if Python version matches (3.12)

### Issue: Database Connection Failed

**Solution:**
1. Verify `POSTGRES_URL` is set correctly in Railway
2. Use Railway's internal reference: `${{Postgres.DATABASE_URL}}`
3. Check if PostgreSQL service is running (green status)
4. Review logs for connection errors

### Issue: Redis Connection Failed

**Solution:**
1. Verify Redis service is running in Railway
2. Check `REDIS_ENABLED=true` is set
3. Railway should auto-provide `REDIS_URL`
4. Check if `REDIS_URL` is in environment variables

### Issue: GitHub Actions Failed

**Solution:**
1. Verify `RAILWAY_TOKEN` secret is correct
2. Check `RAILWAY_SERVICE_NAME` matches your service
3. Ensure Railway CLI installed correctly
4. Check GitHub Actions logs for specific error

### Issue: 500 Errors After Deployment

**Solution:**
1. Check Railway logs for Python errors
2. Verify all environment variables are set
3. Ensure Supabase credentials are correct
4. Test endpoints locally first with same env vars

---

## 📊 Monitoring & Costs

### View Usage & Costs

1. Go to Railway dashboard
2. Click your project
3. Go to **"Usage"** tab
4. Monitor:
   - Compute hours (CPU/Memory)
   - Database storage
   - Egress (data transfer)

### Expected Costs (Hobby Plan - $5/month)

**Low Traffic (Development):**
- API Service: ~$2-5/month
- PostgreSQL: ~$1-2/month
- Redis: ~$0.50-1/month
- **Total: ~$3.50-8/month**

**Medium Traffic (Production MVP):**
- API Service: ~$5-15/month
- PostgreSQL: ~$3-5/month
- Redis: ~$1-2/month
- **Total: ~$9-22/month**

### Cost Optimization Tips

1. **Pause when not in use**: Right-click service → "Pause" (saves money)
2. **Set resource limits**: In `railway.toml`, limit memory/CPU
3. **Monitor logs**: Remove excessive logging in production
4. **Upgrade when needed**: Switch to Pro plan ($20) when traffic grows

---

## 🚦 Deployment Workflow Summary

### Manual Deployment (Web UI)
1. Push code to GitHub
2. Railway auto-detects changes
3. Builds new Docker image
4. Deploys automatically
5. Zero downtime deployment

### Automated Deployment (GitHub Actions)
1. Push to `master` branch
2. GitHub Actions triggers
3. Railway CLI deploys via API
4. Build → Deploy → Live
5. Get notification on success/failure

---

## 🎓 Next Steps

### Production Checklist

- [ ] Set up custom domain in Railway (see Step 5 above)
- [ ] Verify SSL certificate is active (automatic via Railway)
- [ ] Update DNS records at your domain provider (CNAME)
- [ ] Test custom domain: `curl https://api.yourdomain.com/health`
- [ ] Set up monitoring/alerts
- [ ] Configure backup schedule for PostgreSQL
- [ ] Test all API endpoints on production domain
- [ ] Update mobile app with production API URL (`https://api.yourdomain.com`)
- [ ] Update Clerk webhook URLs to use custom domain
- [ ] Set up staging environment (optional: `staging.yourdomain.com`)
- [ ] Configure rate limiting (if needed)

### Scaling Checklist (When You Grow)

- [ ] Upgrade to Pro plan ($20/month) for more resources
- [ ] Add horizontal scaling (multiple instances)
- [ ] Set up load balancing
- [ ] Enable Redis persistence
- [ ] Optimize database queries
- [ ] Add CDN for static files
- [ ] Consider migrating to AWS (if needed)

---

## 📞 Support & Resources

- **Railway Docs**: [docs.railway.app](https://docs.railway.app)
- **Railway Discord**: [discord.gg/railway](https://discord.gg/railway)
- **Railway Status**: [status.railway.app](https://status.railway.app)
- **GitHub Actions Docs**: [docs.github.com/actions](https://docs.github.com/actions)

---

## 🎉 Congratulations!

Your FastAPI backend is now deployed to Railway with automatic deployments via GitHub Actions!

**What you've accomplished:**
✅ FastAPI app running on Railway
✅ PostgreSQL database provisioned
✅ Redis cache configured
✅ GitHub Actions auto-deployment
✅ Production-ready infrastructure
✅ Cost-effective hosting ($5-25/month)

**Your API is live at:** `https://your-app.railway.app`

Now you can focus on building features instead of managing infrastructure! 🚀

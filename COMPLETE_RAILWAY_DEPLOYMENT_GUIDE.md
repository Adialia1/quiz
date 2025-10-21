# Complete Railway Deployment Guide - Quiz App Backend

**Everything you need to deploy your FastAPI backend from scratch to production.**

Complete step-by-step guide: Railway account → Deployment → Custom Domain → GitHub Actions → Mobile App Integration

---

## 📋 What You'll Need

- [ ] GitHub account with your quiz repository
- [ ] Credit/debit card for Railway (required even for free trial)
- [ ] Your `.env` file with all credentials ready
- [ ] Custom domain (optional, but recommended for production)
- [ ] 30-45 minutes of your time

---

## 🚀 PART 1: Railway Account Setup (5 minutes)

### Step 1.1: Create Railway Account

1. **Go to Railway website**
   - Visit: [railway.app](https://railway.app)
   - Click **"Start a New Project"** or **"Login"**

2. **Sign up with GitHub**
   - Click **"Login with GitHub"**
   - Authorize Railway to access your GitHub account
   - Grant necessary permissions

3. **Add Payment Method**
   - Railway requires a card even for the free trial
   - Go to **Account Settings** → **Billing**
   - Click **"Add Payment Method"**
   - Enter your credit/debit card details
   - You'll get **$5 free credits** to start

**✅ You now have a Railway account with $5 free credits!**

---

## 🏗️ PART 2: Create Railway Project & Deploy (10 minutes)

### Step 2.1: Create New Project

1. **From Railway Dashboard**
   - Click **"New Project"**
   - Select **"Deploy from GitHub repo"**

2. **Connect GitHub Repository**
   - If first time: Click **"Configure GitHub App"**
   - Select repositories to give Railway access to
   - Choose **"Only select repositories"**
   - Select your `quiz` repository
   - Click **"Install & Authorize"**

3. **Select Repository**
   - Back in Railway, select your `quiz` repository
   - Railway will automatically detect the `Dockerfile`
   - Click **"Deploy Now"**

4. **Wait for Initial Build**
   - Railway will start building your Docker container
   - This takes 3-5 minutes for first deployment
   - You'll see build logs in real-time
   - Wait for status to show **"Success"** or **"Active"**

**✅ Your FastAPI app is building!**

---

### Step 2.2: Add PostgreSQL Database

1. **In your Railway project dashboard**
   - You should see your FastAPI service card
   - Click **"+ New"** button (top right)

2. **Add PostgreSQL**
   - Select **"Database"**
   - Click **"Add PostgreSQL"**
   - Railway provisions a database instantly

3. **Note Database Info**
   - Click on the **PostgreSQL** service card
   - Go to **"Variables"** tab
   - You'll see `DATABASE_URL` automatically created
   - Copy this value (or we'll reference it later)

**✅ PostgreSQL database is ready!**

---

### Step 2.3: Add Redis Cache

1. **In your Railway project dashboard**
   - Click **"+ New"** button again

2. **Add Redis**
   - Select **"Database"**
   - Click **"Add Redis"**
   - Railway provisions Redis instantly

3. **Note Redis Info**
   - Click on the **Redis** service card
   - Go to **"Variables"** tab
   - You'll see `REDIS_URL` automatically created

**✅ Redis cache is ready!**

---

### Step 2.4: Configure Environment Variables

1. **Click on your FastAPI service** (the main app, not database)

2. **Go to "Variables" tab**

3. **Click "New Variable"** and add each of these:

```bash
# ============================================================================
# AI & LLM Configuration
# ============================================================================
OPENROUTER_API_KEY=your_openrouter_api_key_here
EMBEDDING_MODEL=intfloat/multilingual-e5-large

# ============================================================================
# Supabase Vector Database
# ============================================================================
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_supabase_anon_key_here
SUPABASE_SERVICE_KEY=your_supabase_service_key_here

# ============================================================================
# Clerk Authentication
# ============================================================================
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key_here
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret_here

# ============================================================================
# Notifications
# ============================================================================
NOTIFICATION_API_KEY=your_notification_api_key_here

# ============================================================================
# RevenueCat (Optional - for monetization)
# ============================================================================
REVENUE_CAT_API_KEY=your_revenuecat_api_key_here

# ============================================================================
# Redis Configuration
# ============================================================================
REDIS_ENABLED=true

# ============================================================================
# PostgreSQL Database
# ============================================================================
# Use Railway's service reference (recommended)
POSTGRES_URL=${{Postgres.DATABASE_URL}}

# ============================================================================
# Database Pool Settings (Optional)
# ============================================================================
DB_MIN_POOL_SIZE=5
DB_MAX_POOL_SIZE=20
DB_COMMAND_TIMEOUT=60
```

**💡 Important Notes:**
- For `POSTGRES_URL`: Use exactly `${{Postgres.DATABASE_URL}}` - Railway will auto-fill this
- Railway auto-provides `REDIS_URL` and `DATABASE_URL` - no need to set them manually
- Each variable is a separate entry - don't paste all at once
- Click **"Add"** after each variable

4. **After adding all variables**
   - Railway will automatically trigger a new deployment
   - Wait for deployment to complete (2-3 minutes)

**✅ Environment variables configured!**

---

### Step 2.5: Get Your API Domain

#### Option A: Use Railway's Free Domain (Quick Start)

1. **In your FastAPI service**
   - Go to **"Settings"** tab
   - Scroll to **"Networking"** section
   - Find **"Domains"**

2. **Generate Domain**
   - Click **"Generate Domain"**
   - Railway creates: `your-app-name.up.railway.app`
   - Copy this URL

3. **Test Your API**
   ```bash
   # Replace with your Railway domain
   curl https://your-app-name.up.railway.app/health

   # Should return: {"status": "healthy", ...}
   ```

4. **Test in Browser**
   - Visit: `https://your-app-name.up.railway.app/docs`
   - You should see FastAPI Swagger documentation
   - Try the `/health` endpoint

**✅ Your API is live with Railway domain!**

---

#### Option B: Use Your Custom Domain (Recommended for Production)

**If you have a custom domain, follow these steps:**

1. **In your FastAPI service**
   - Go to **"Settings"** tab
   - Scroll to **"Networking"** → **"Domains"**
   - Click **"+ Add Domain"**

2. **Enter Your Custom Domain**
   - Type: `api.yourdomain.com` (or your preferred subdomain)
   - Click **"Add"**

3. **Copy CNAME Target**
   - Railway will show you a CNAME target
   - Example: `your-service-name.up.railway.app`
   - **Copy this value** - you'll need it for DNS

4. **Configure DNS at Your Domain Provider**

   **For Cloudflare:**
   - Login to [dash.cloudflare.com](https://dash.cloudflare.com)
   - Select your domain
   - Go to **DNS** → **Records**
   - Click **"Add record"**
   - Configure:
     - Type: `CNAME`
     - Name: `api`
     - Target: `your-service-name.up.railway.app` (from Railway)
     - Proxy status: **DNS only** (gray cloud, NOT orange)
     - TTL: `Auto`
   - Click **"Save"**

   **For GoDaddy:**
   - Login to [godaddy.com](https://godaddy.com)
   - Go to **My Products** → **DNS**
   - Click **"Add"**
   - Configure:
     - Type: `CNAME`
     - Name: `api`
     - Value: `your-service-name.up.railway.app`
     - TTL: `600 seconds`
   - Click **"Save"**

   **For Namecheap:**
   - Login to [namecheap.com](https://namecheap.com)
   - Go to **Domain List** → **Manage** → **Advanced DNS**
   - Click **"Add New Record"**
   - Configure:
     - Type: `CNAME Record`
     - Host: `api`
     - Value: `your-service-name.up.railway.app`
     - TTL: `Automatic`
   - Click the checkmark to save

   **For Google Domains:**
   - Login to [domains.google.com](https://domains.google.com)
   - Click your domain → **DNS**
   - Scroll to **Custom resource records**
   - Configure:
     - Name: `api`
     - Type: `CNAME`
     - TTL: `1H`
     - Data: `your-service-name.up.railway.app`
   - Click **"Add"**

   **For Other Providers:**
   - Find DNS management section
   - Add CNAME record:
     - Type: `CNAME`
     - Name/Host: `api`
     - Value/Target: `your-service-name.up.railway.app`
     - TTL: `3600` or `Auto`

5. **Wait for DNS Propagation**
   - Typical wait: 5-30 minutes
   - Maximum: Up to 48 hours (rare)

   **Check DNS propagation:**
   ```bash
   # macOS/Linux
   dig api.yourdomain.com CNAME

   # Windows/macOS/Linux
   nslookup api.yourdomain.com

   # Online tool
   # Visit: https://dnschecker.org
   # Enter: api.yourdomain.com
   # Type: CNAME
   ```

6. **Verify in Railway**
   - Go back to Railway → Your service → Settings → Domains
   - Your custom domain should show **"Active"** with green checkmark
   - SSL status should show **"Active"** (Railway auto-provisions SSL)
   - This can take 5-10 minutes after DNS is active

7. **Test Your Custom Domain**
   ```bash
   # Test health endpoint
   curl https://api.yourdomain.com/health

   # Should return: {"status": "healthy", ...}

   # Test in browser
   open https://api.yourdomain.com/docs
   ```

**✅ Your API is live on your custom domain with free SSL!**

---

## 🔄 PART 3: Setup GitHub Actions for Auto-Deployment (5 minutes)

### Step 3.1: Get Railway Token

1. **Go to Railway Account Settings**
   - Click your profile picture (top right)
   - Click **"Account Settings"**
   - Or visit: [railway.app/account/tokens](https://railway.app/account/tokens)

2. **Create New Token**
   - Click **"Create New Token"**
   - Give it a name: `GitHub Actions Deploy`
   - Click **"Create"**
   - **Copy the token** (you'll only see it once!)
   - Save it somewhere safe temporarily

**⚠️ Important:** Copy this token now! You won't be able to see it again.

---

### Step 3.2: Get Railway Service Name (Optional)

1. **In your Railway project**
   - Click on your FastAPI service
   - Look at the URL in your browser
   - It will look like: `railway.app/project/xxx/service/yyy`
   - The `yyy` part is your service ID

**Note:** You can also leave `RAILWAY_SERVICE_NAME` empty to deploy all services.

---

### Step 3.3: Add GitHub Secrets

1. **Go to Your GitHub Repository**
   - Visit: `github.com/yourusername/quiz`

2. **Navigate to Settings**
   - Click **"Settings"** tab (in the repository)

3. **Go to Secrets**
   - Click **"Secrets and variables"** (left sidebar)
   - Click **"Actions"**

4. **Add First Secret: RAILWAY_TOKEN**
   - Click **"New repository secret"**
   - Name: `RAILWAY_TOKEN`
   - Value: (paste the token from Step 3.1)
   - Click **"Add secret"**

5. **Add Second Secret: RAILWAY_SERVICE_NAME (Optional)**
   - Click **"New repository secret"** again
   - Name: `RAILWAY_SERVICE_NAME`
   - Value: (your service ID from Step 3.2, or leave blank)
   - Click **"Add secret"**

**✅ GitHub secrets configured!**

---

### Step 3.4: Verify GitHub Actions Workflow

The workflow file is already in your repository: `.github/workflows/railway-deploy.yml`

**This workflow will:**
- ✅ Trigger on push to `master` branch
- ✅ Deploy automatically to Railway
- ✅ Show success/failure notifications
- ✅ Can be triggered manually from GitHub UI

**You don't need to create this file - it's already there!**

---

### Step 3.5: Test Auto-Deployment

1. **Make a Small Change**
   ```bash
   # In your local project
   cd ~/Desktop/quiz

   # Make a small change (example)
   echo "# Auto-deploy test" >> README.md
   ```

2. **Commit and Push**
   ```bash
   git add .
   git commit -m "test: railway auto-deployment"
   git push origin master
   ```

3. **Watch GitHub Actions**
   - Go to your GitHub repository
   - Click **"Actions"** tab
   - You'll see your workflow running
   - Click on it to see live logs

4. **Verify Deployment**
   - Once completed (green checkmark)
   - Test your API:
     ```bash
     curl https://api.yourdomain.com/health
     # or
     curl https://your-app.railway.app/health
     ```

**✅ Auto-deployment working! Every push to master now deploys automatically!**

---

## 📱 PART 4: Connect Your Mobile App (5 minutes)

### Step 4.1: Update Mobile App Environment Variables

1. **Open your mobile app directory**
   ```bash
   cd ~/Desktop/quiz/app
   ```

2. **Edit `.env` file**
   ```bash
   nano .env
   # or use any text editor
   ```

3. **Update API URL**
   ```bash
   # If using custom domain:
   EXPO_PUBLIC_API_URL=https://api.yourdomain.com

   # Or if using Railway domain:
   # EXPO_PUBLIC_API_URL=https://your-app.railway.app

   # Keep other variables as is:
   EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY=pk_test_xxxxx
   EXPO_PUBLIC_REVENUECAT_API_KEY=xxxxx
   ```

4. **Save the file**
   - Press `Ctrl + O` (save)
   - Press `Enter`
   - Press `Ctrl + X` (exit)

---

### Step 4.2: Update Clerk Webhook URL

1. **Go to Clerk Dashboard**
   - Visit: [dashboard.clerk.com](https://dashboard.clerk.com)
   - Select your application

2. **Navigate to Webhooks**
   - Click **"Webhooks"** in the left sidebar
   - Find your webhook or create new one

3. **Update Endpoint URL**
   - Old: `https://old-url/api/users/webhook`
   - New: `https://api.yourdomain.com/api/users/webhook`
   - (or use Railway URL if not using custom domain)

4. **Save Changes**
   - Click **"Update"** or **"Create"**
   - Test the webhook if possible

**✅ Clerk webhooks updated!**

---

### Step 4.3: Restart and Test Mobile App

1. **Clear Expo cache and restart**
   ```bash
   cd ~/Desktop/quiz/app
   npm start -- --clear
   ```

2. **Test the app**
   - Press `i` for iOS simulator (or scan QR code)
   - Test login/authentication
   - Try creating an exam
   - Verify all features work

3. **Check Network Requests**
   - In Expo console, you should see requests to your new domain
   - Example: `https://api.yourdomain.com/api/users/me`

**✅ Mobile app connected to production API!**

---

## 🔍 PART 5: Verify Everything is Working (5 minutes)

### Step 5.1: Test All API Endpoints

```bash
# Replace with your actual domain
API_URL="https://api.yourdomain.com"

# 1. Health check
curl $API_URL/health

# 2. Root endpoint
curl $API_URL/

# 3. API documentation (open in browser)
open $API_URL/docs
```

**Expected results:**
- Health: `{"status": "healthy", "timestamp": "...", "agents": {...}}`
- Root: Should show API info with all endpoints
- Docs: Opens Swagger UI in browser

---

### Step 5.2: Test Database Connection

```bash
# Test an endpoint that uses database
# Example: Get user profile (requires authentication)
curl $API_URL/api/users/me \
  -H "Authorization: Bearer YOUR_CLERK_TOKEN"
```

If you get a response (not 500 error), database is working!

---

### Step 5.3: Test Redis Cache

Check Railway logs:
1. Go to Railway dashboard
2. Click your FastAPI service
3. Go to **"Deployments"** tab
4. Click latest deployment
5. Check logs for: `✅ Redis cache ready`

---

### Step 5.4: Check SSL Certificate

```bash
# Test SSL certificate
curl -vI https://api.yourdomain.com 2>&1 | grep -i "ssl\|tls"

# Or visit in browser and click padlock icon
open https://api.yourdomain.com
```

Should show:
- ✅ Valid SSL certificate
- ✅ Issued by Let's Encrypt
- ✅ Valid for your domain

---

### Step 5.5: Test Mobile App End-to-End

**Test checklist:**
- [ ] App opens without errors
- [ ] Login works (Clerk authentication)
- [ ] Can fetch user profile
- [ ] Can create an exam
- [ ] Can view exam history
- [ ] Can submit answers
- [ ] Can view results
- [ ] All API calls go to your domain (check Expo console)

**✅ Everything is working!**

---

## 📊 PART 6: Monitor Your Deployment (Optional)

### Step 6.1: View Railway Logs

1. **In Railway Dashboard**
   - Click your FastAPI service
   - Go to **"Deployments"** tab
   - Click on the latest deployment
   - View real-time logs

2. **Check for errors**
   - Look for red error messages
   - Check database connections
   - Verify all services started

---

### Step 6.2: Monitor Usage & Costs

1. **Go to Project Settings**
   - Click **"Settings"** (project level, not service)
   - Or click **"Usage"** tab

2. **Check Current Usage**
   - See compute hours
   - Memory usage
   - Database storage
   - Egress (data transfer)

3. **Estimate Monthly Cost**
   - Railway shows estimated cost based on current usage
   - Typical: $5-25/month for low-medium traffic
   - You have $5 free credits to start!

---

### Step 6.3: Set Up Alerts (Optional)

1. **In Railway Project**
   - Go to **"Settings"**
   - Scroll to **"Notifications"**

2. **Enable Notifications**
   - Deployment failures
   - Service crashes
   - Usage alerts

**✅ Monitoring set up!**

---

## 🐛 TROUBLESHOOTING

### Issue: Build Failed on Railway

**Symptoms:**
- Deployment shows "Failed" status
- Red error in build logs

**Solutions:**
1. **Check build logs:**
   - Click deployment → View logs
   - Look for the error message

2. **Common causes:**
   - Missing dependencies in `requirements.txt`
   - Python version mismatch
   - Dockerfile errors

3. **Fix:**
   ```bash
   # Ensure all dependencies are listed
   pip freeze > requirements.txt

   # Commit and push
   git add requirements.txt
   git commit -m "fix: update requirements"
   git push origin master
   ```

---

### Issue: Database Connection Failed

**Symptoms:**
- API returns 500 errors
- Logs show "Could not connect to database"

**Solutions:**
1. **Check environment variable:**
   - Railway → Service → Variables
   - Verify `POSTGRES_URL=${{Postgres.DATABASE_URL}}`

2. **Check PostgreSQL service:**
   - Is it running? (green status)
   - Click PostgreSQL service → Check status

3. **Restart services:**
   - Click FastAPI service → Settings
   - Click **"Restart"**

---

### Issue: Redis Connection Failed

**Symptoms:**
- Logs show Redis connection errors
- Cache not working

**Solutions:**
1. **Check Redis service:**
   - Is it running? (green status)
   - Click Redis service → Check status

2. **Check environment variable:**
   - `REDIS_ENABLED=true` is set
   - Railway should auto-provide `REDIS_URL`

3. **Restart:**
   - Restart FastAPI service

---

### Issue: Custom Domain Not Working

**Symptoms:**
- Domain shows "DNS not configured"
- Can't access via custom domain

**Solutions:**
1. **Check DNS propagation:**
   ```bash
   dig api.yourdomain.com CNAME
   # Should show Railway's target
   ```

2. **Wait longer:**
   - DNS can take up to 48 hours
   - Usually works in 5-30 minutes

3. **Verify CNAME record:**
   - Go to your DNS provider
   - Check CNAME is correct
   - Ensure no typos

4. **For Cloudflare:**
   - Turn OFF proxy (gray cloud, not orange)
   - Wait 5 minutes and refresh

---

### Issue: SSL Certificate Error

**Symptoms:**
- Browser shows "Not Secure"
- Certificate error

**Solutions:**
1. **Wait for certificate:**
   - Railway takes 5-10 minutes to provision SSL
   - Check: Service → Settings → Domains
   - Should show "Active" with green checkmark

2. **Verify DNS:**
   - DNS must be fully propagated first
   - Then Railway provisions SSL

3. **Check domain status:**
   - In Railway, domain should show "Active"
   - SSL should show "Active"

---

### Issue: GitHub Actions Failed

**Symptoms:**
- GitHub Actions shows red X
- Deployment didn't trigger

**Solutions:**
1. **Check secrets:**
   - GitHub → Settings → Secrets
   - Verify `RAILWAY_TOKEN` is set correctly

2. **Check token validity:**
   - Token might have expired
   - Create new token in Railway
   - Update GitHub secret

3. **Check workflow file:**
   - File: `.github/workflows/railway-deploy.yml`
   - Verify it exists and is correct

4. **Manual trigger:**
   - GitHub → Actions → Railway Deploy
   - Click "Run workflow"

---

### Issue: Mobile App Can't Connect

**Symptoms:**
- App shows network errors
- API calls fail

**Solutions:**
1. **Check API URL in `.env`:**
   ```bash
   # Should be:
   EXPO_PUBLIC_API_URL=https://api.yourdomain.com
   # NOT:
   # EXPO_PUBLIC_API_URL=http://api.yourdomain.com (missing 's')
   ```

2. **Clear Expo cache:**
   ```bash
   cd app
   npm start -- --clear
   ```

3. **Check CORS:**
   - API should allow all origins for now
   - Check `api/main.py` CORS configuration

4. **Test API separately:**
   ```bash
   curl https://api.yourdomain.com/health
   ```
   If this works but app doesn't, issue is in mobile app

---

### Issue: 500 Internal Server Error

**Symptoms:**
- API returns 500 errors
- No specific error message

**Solutions:**
1. **Check Railway logs:**
   - Service → Deployments → Latest → Logs
   - Look for Python errors

2. **Common causes:**
   - Missing environment variables
   - Database connection failed
   - AI API keys invalid

3. **Verify environment variables:**
   - Check all required vars are set
   - No typos in keys
   - Values are correct

4. **Test locally first:**
   ```bash
   cd ~/Desktop/quiz
   python -m uvicorn api.main:app --reload
   ```
   If works locally, issue is in Railway config

---

## 💰 COST BREAKDOWN

### Railway Pricing (Your Expected Costs)

**Hobby Plan: $5/month (includes $5 credits)**

**Expected monthly costs:**

**Development/Testing:**
- FastAPI service: ~$2-4/month
- PostgreSQL: ~$1-2/month
- Redis: ~$0.50-1/month
- **Total: $3.50-7/month** (within free credits!)

**Production (Low-Medium Traffic):**
- FastAPI service: ~$5-12/month
- PostgreSQL: ~$2-4/month
- Redis: ~$1-2/month
- **Total: $8-18/month**

**Production (High Traffic):**
- FastAPI service: ~$15-30/month
- PostgreSQL: ~$5-10/month
- Redis: ~$2-3/month
- **Total: $22-43/month**

**💡 Tips to save money:**
- Pause services when not in use (right-click → Pause)
- Optimize database queries
- Use caching effectively (Redis)
- Monitor usage regularly
- Upgrade to Pro plan ($20/month) only when needed

---

## ✅ DEPLOYMENT CHECKLIST

### Initial Setup
- [ ] Created Railway account
- [ ] Added payment method
- [ ] Connected GitHub repository
- [ ] Deployed FastAPI service
- [ ] Added PostgreSQL database
- [ ] Added Redis cache
- [ ] Configured all environment variables
- [ ] Verified deployment succeeded

### Domain Setup
- [ ] Generated Railway domain OR
- [ ] Added custom domain to Railway
- [ ] Configured DNS CNAME record
- [ ] Waited for DNS propagation
- [ ] Verified SSL certificate is active
- [ ] Tested domain in browser

### GitHub Actions
- [ ] Created Railway token
- [ ] Added RAILWAY_TOKEN to GitHub secrets
- [ ] Added RAILWAY_SERVICE_NAME to GitHub secrets (optional)
- [ ] Tested auto-deployment with git push
- [ ] Verified workflow runs successfully

### Mobile App Integration
- [ ] Updated app/.env with API URL
- [ ] Updated Clerk webhook URL
- [ ] Cleared Expo cache
- [ ] Tested app login
- [ ] Tested exam creation
- [ ] Verified all API calls work

### Final Verification
- [ ] Tested /health endpoint
- [ ] Tested /docs endpoint
- [ ] Verified database connection
- [ ] Verified Redis cache working
- [ ] Checked SSL certificate valid
- [ ] Tested mobile app end-to-end
- [ ] Checked Railway logs for errors
- [ ] Monitored usage and costs

**✅ If all checked, you're live in production!**

---

## 🎉 CONGRATULATIONS!

Your Quiz App backend is now deployed to Railway with:

- ✅ **FastAPI backend** - Running on Railway
- ✅ **PostgreSQL database** - Managed and backed up
- ✅ **Redis cache** - For fast performance
- ✅ **Custom domain** - Professional branding (if configured)
- ✅ **Free SSL certificate** - Auto-renewing HTTPS
- ✅ **Auto-deployment** - Push to master = instant deploy
- ✅ **Zero-downtime deploys** - No interruptions
- ✅ **Cost-effective** - $5-25/month (vs $50-200 on AWS)
- ✅ **Production-ready** - Scales automatically

---

## 📚 QUICK REFERENCE

### Essential URLs

**Railway:**
- Dashboard: https://railway.app
- Account Tokens: https://railway.app/account/tokens
- Documentation: https://docs.railway.app

**Your API:**
- Production: https://api.yourdomain.com
- Railway URL: https://your-app.railway.app
- API Docs: https://api.yourdomain.com/docs

**GitHub:**
- Repository: https://github.com/yourusername/quiz
- Actions: https://github.com/yourusername/quiz/actions

### Common Commands

```bash
# Test API
curl https://api.yourdomain.com/health

# Check DNS
dig api.yourdomain.com CNAME

# Deploy manually
git add .
git commit -m "deploy: update"
git push origin master

# View Railway logs
railway logs

# Restart Expo app
cd app && npm start -- --clear
```

### Railway Commands (via CLI - Optional)

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Link to project
railway link

# Deploy
railway up

# View logs
railway logs

# Open in browser
railway open
```

---

## 🆘 GETTING HELP

**Documentation:**
- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com
- GitHub Actions: https://docs.github.com/actions

**Community:**
- Railway Discord: https://discord.gg/railway
- Railway Community: https://community.railway.app

**Support:**
- Railway Status: https://status.railway.app
- Your logs: Railway Dashboard → Deployments

---

## 🚀 NEXT STEPS

### Immediate (This Week)
1. **Test thoroughly:**
   - All API endpoints
   - Mobile app features
   - Edge cases

2. **Monitor:**
   - Check logs daily
   - Watch for errors
   - Monitor costs

3. **Document:**
   - Save your domain
   - Note your Railway URLs
   - Keep credentials safe

### Short Term (This Month)
1. **Optimize:**
   - Review slow queries
   - Optimize API responses
   - Use caching effectively

2. **Security:**
   - Review CORS settings
   - Set up rate limiting
   - Monitor for abuse

3. **Monitoring:**
   - Set up uptime monitoring (e.g., UptimeRobot)
   - Configure alerts
   - Track error rates

### Long Term (3-6 Months)
1. **Scale:**
   - Upgrade to Pro if needed
   - Add horizontal scaling
   - Optimize database

2. **Features:**
   - Add more API endpoints
   - Improve mobile app
   - Add analytics

3. **Production:**
   - Set up staging environment
   - Implement CI/CD tests
   - Add database backups

---

## 📝 NOTES

**Important things to remember:**

1. **Railway auto-deploys** on every push to master
2. **Don't commit `.env`** to Git (already in `.gitignore`)
3. **Railway provides free SSL** - no configuration needed
4. **Database backups** - Railway backs up automatically
5. **Costs are pay-as-you-go** - you only pay for what you use
6. **Logs are temporary** - download important logs

**Keep these safe:**
- Railway account credentials
- Railway API tokens
- Database credentials (in Railway dashboard)
- Custom domain and DNS settings

---

**🎊 Your Quiz App is LIVE! Now go build something amazing! 🚀**

---

**Last Updated:** October 2025
**Railway Version:** V3
**Estimated Setup Time:** 30-45 minutes
**Difficulty:** Beginner-Friendly ⭐⭐☆☆☆

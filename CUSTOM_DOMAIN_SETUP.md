# Custom Domain Setup for Railway

Complete guide to setting up your custom domain with Railway for your Quiz App API.

---

## 🌐 Why Use a Custom Domain?

**Benefits:**
- ✅ Professional appearance (`api.yourdomain.com` vs `random-name.railway.app`)
- ✅ Brand consistency across your app
- ✅ Better for production/enterprise clients
- ✅ Easier to remember and share
- ✅ Free SSL certificate (automatic)
- ✅ Better SEO if you build a marketing site

**Recommended Subdomain Structure:**
- `api.yourdomain.com` - Your FastAPI backend
- `app.yourdomain.com` - Your mobile app's web version (future)
- `www.yourdomain.com` - Marketing website (future)
- `admin.yourdomain.com` - Admin dashboard (future)

---

## 📋 Prerequisites

- ✅ Domain purchased (e.g., from GoDaddy, Namecheap, Google Domains, Cloudflare)
- ✅ Railway project deployed and running
- ✅ Access to your domain's DNS settings

---

## 🚀 Step-by-Step Setup

### Step 1: Add Custom Domain in Railway

1. **Go to Railway Dashboard**
   - Navigate to your project
   - Click on your **FastAPI service**

2. **Access Domain Settings**
   - Go to **"Settings"** tab
   - Scroll down to **"Networking"** section
   - Click on **"Domains"**

3. **Add Your Custom Domain**
   - Click **"+ Add Domain"**
   - Enter your custom domain:
     - For subdomain: `api.yourdomain.com`
     - For root domain: `yourdomain.com` (not recommended for APIs)
   - Click **"Add"**

4. **Copy the CNAME Target**
   - Railway will show you a CNAME target value
   - Example: `your-service-name.up.railway.app`
   - **Copy this value** - you'll need it for DNS setup

---

### Step 2: Configure DNS Records

Choose your domain provider and follow the instructions:

#### Option A: Cloudflare (Recommended)

1. **Login to Cloudflare Dashboard**
   - Go to [dash.cloudflare.com](https://dash.cloudflare.com)
   - Select your domain

2. **Add CNAME Record**
   - Click **"DNS"** in the left menu
   - Click **"+ Add record"**
   - Configure:
     - **Type:** CNAME
     - **Name:** `api` (or your preferred subdomain)
     - **Target:** `your-service-name.up.railway.app` (from Railway)
     - **Proxy status:** 🟠 DNS only (turn off orange cloud for Railway)
     - **TTL:** Auto
   - Click **"Save"**

**⚠️ Important for Cloudflare:**
- **Turn OFF the proxy** (gray cloud, not orange) for Railway domains
- Orange cloud (proxied) can interfere with Railway's SSL certificates
- You can enable proxy later once domain is verified

#### Option B: GoDaddy

1. **Login to GoDaddy**
   - Go to [godaddy.com](https://www.godaddy.com)
   - Navigate to **"My Products"** → **"DNS"**

2. **Add CNAME Record**
   - Click **"Add"** button
   - Configure:
     - **Type:** CNAME
     - **Name:** `api`
     - **Value:** `your-service-name.up.railway.app`
     - **TTL:** 600 seconds (or default)
   - Click **"Save"**

#### Option C: Namecheap

1. **Login to Namecheap**
   - Go to [namecheap.com](https://www.namecheap.com)
   - Navigate to **"Domain List"** → Select your domain → **"Manage"**

2. **Add CNAME Record**
   - Go to **"Advanced DNS"** tab
   - Click **"Add New Record"**
   - Configure:
     - **Type:** CNAME Record
     - **Host:** `api`
     - **Value:** `your-service-name.up.railway.app`
     - **TTL:** Automatic
   - Click the green checkmark to save

#### Option D: Google Domains

1. **Login to Google Domains**
   - Go to [domains.google.com](https://domains.google.com)
   - Click on your domain

2. **Add CNAME Record**
   - Go to **"DNS"** in left menu
   - Scroll to **"Custom resource records"**
   - Configure:
     - **Name:** `api`
     - **Type:** CNAME
     - **TTL:** 1H
     - **Data:** `your-service-name.up.railway.app`
   - Click **"Add"**

#### Option E: Other DNS Providers

**General Instructions (works for any provider):**
1. Find the DNS management section
2. Add a new record with these details:
   - **Type:** CNAME
   - **Name/Host:** `api` (or your subdomain)
   - **Value/Points to:** `your-service-name.up.railway.app`
   - **TTL:** 3600 (1 hour) or automatic

---

### Step 3: Wait for DNS Propagation

**Typical Wait Times:**
- Cloudflare: 2-5 minutes ⚡
- Most providers: 5-30 minutes
- Maximum: Up to 48 hours (rare)

**Check DNS Propagation:**

```bash
# Method 1: Using dig (macOS/Linux)
dig api.yourdomain.com CNAME

# Method 2: Using nslookup (Windows/macOS/Linux)
nslookup api.yourdomain.com

# Method 3: Online tool
# Visit: https://dnschecker.org
# Enter: api.yourdomain.com
# Type: CNAME
```

**What to expect:**
- Before: "No records found" or old value
- After: Shows `your-service-name.up.railway.app`

---

### Step 4: Verify Domain in Railway

1. **Back to Railway Dashboard**
   - Go to your FastAPI service → Settings → Domains

2. **Check Domain Status**
   - Your domain should show **"Active"** with a green checkmark
   - SSL certificate status: **"Active"** (auto-provisioned by Railway)
   - If still pending, wait a few more minutes and refresh

3. **SSL Certificate (Automatic)**
   - Railway automatically provisions an SSL certificate via Let's Encrypt
   - No action required from you
   - Certificate auto-renews every 90 days

---

### Step 5: Test Your Custom Domain

**Test via Command Line:**

```bash
# Test health endpoint
curl https://api.yourdomain.com/health

# Expected response:
# {
#   "status": "healthy",
#   "timestamp": "2025-10-21T...",
#   "agents": {...}
# }

# Test root endpoint
curl https://api.yourdomain.com/

# Test API docs (open in browser)
open https://api.yourdomain.com/docs
```

**Test via Browser:**
1. Visit `https://api.yourdomain.com/docs`
2. You should see the FastAPI Swagger documentation
3. Check the SSL certificate (padlock icon in browser)

---

### Step 6: Update Your Mobile App

**Update Environment Variables:**

1. **Edit `app/.env`:**
   ```bash
   # Old (Railway subdomain)
   # EXPO_PUBLIC_API_URL=https://your-app.railway.app

   # New (Custom domain)
   EXPO_PUBLIC_API_URL=https://api.yourdomain.com
   ```

2. **Restart Expo:**
   ```bash
   cd app
   npm start -- --clear
   ```

3. **Test the App:**
   - Open your React Native app
   - Test login/authentication
   - Test creating an exam
   - Verify all API calls work

---

### Step 7: Update External Services

**Services that need your new domain:**

#### 1. Clerk (Authentication)

Update webhook URLs in Clerk Dashboard:

1. Go to [dashboard.clerk.com](https://dashboard.clerk.com)
2. Select your application
3. Navigate to **"Webhooks"**
4. Update webhook endpoint:
   - Old: `https://your-app.railway.app/api/users/webhook`
   - New: `https://api.yourdomain.com/api/users/webhook`

#### 2. Supabase (If using webhooks)

If you have any Supabase webhooks pointing to your API, update them:
1. Go to Supabase Dashboard
2. Database → Webhooks
3. Update URLs to use your custom domain

#### 3. RevenueCat (If using server-side validation)

Update server URL in RevenueCat dashboard if configured.

---

## 🔒 Security & SSL

### SSL Certificate Details

**Automatic Features:**
- ✅ Railway auto-provisions SSL via Let's Encrypt
- ✅ Certificates auto-renew every 90 days
- ✅ TLS 1.2 and 1.3 supported
- ✅ A+ SSL rating by default
- ✅ HTTPS enforced (HTTP auto-redirects to HTTPS)

**Verify SSL Certificate:**

```bash
# Check SSL certificate details
openssl s_client -connect api.yourdomain.com:443 -servername api.yourdomain.com

# Or use online tool:
# https://www.ssllabs.com/ssltest/
```

---

## 🐛 Troubleshooting

### Issue: "Domain not found" after 24 hours

**Solutions:**
1. **Check CNAME record:**
   ```bash
   dig api.yourdomain.com CNAME
   ```
   Should show Railway's target

2. **Verify you added the record to the correct zone:**
   - Make sure it's under the right domain
   - Check you're in the correct DNS provider account

3. **Clear DNS cache (on your computer):**
   ```bash
   # macOS
   sudo dscacheutil -flushcache; sudo killall -HUP mDNSResponder

   # Windows
   ipconfig /flushdns

   # Linux
   sudo systemd-resolve --flush-caches
   ```

### Issue: SSL Certificate Error

**Solutions:**
1. **Wait for certificate provisioning:** Can take 5-10 minutes after DNS is active
2. **Check Cloudflare proxy:** Must be OFF (gray cloud) during initial setup
3. **Verify CNAME is correct:** Double-check Railway's target value
4. **Check Railway status:** Go to Settings → Domains in Railway

### Issue: "NET::ERR_CERT_COMMON_NAME_INVALID"

**Cause:** SSL certificate doesn't match your domain

**Solutions:**
1. Wait for Railway to provision the SSL certificate (5-10 mins)
2. Verify domain is showing "Active" in Railway
3. Check DNS is fully propagated: `dig api.yourdomain.com`

### Issue: Works on some devices, not others

**Cause:** DNS propagation incomplete

**Solutions:**
1. Wait longer (DNS can take up to 48 hours globally)
2. Test from different networks
3. Use DNS propagation checker: [dnschecker.org](https://dnschecker.org)

### Issue: Cloudflare shows "Too many redirects"

**Cause:** Cloudflare proxy enabled (orange cloud)

**Solution:**
1. Go to Cloudflare DNS
2. Click on the orange cloud next to your `api` record
3. Change to **"DNS only"** (gray cloud)

---

## 📊 Multiple Environments

### Setup Staging Environment

**Recommended structure:**
- Production API: `api.yourdomain.com`
- Staging API: `staging.yourdomain.com` or `api-staging.yourdomain.com`

**Steps:**
1. Create a new Railway project for staging
2. Deploy your code to staging project
3. Add domain `staging.yourdomain.com` in Railway
4. Add CNAME record in DNS:
   - Name: `staging`
   - Value: `your-staging-service.up.railway.app`
5. Use different env vars for staging

### Mobile App Configuration

```bash
# app/.env.production
EXPO_PUBLIC_API_URL=https://api.yourdomain.com

# app/.env.staging
EXPO_PUBLIC_API_URL=https://staging.yourdomain.com

# app/.env.development
EXPO_PUBLIC_API_URL=http://localhost:8000
```

---

## 💡 Best Practices

### Domain Naming

**Good:**
- `api.yourdomain.com` ✅
- `backend.yourdomain.com` ✅
- `quiz-api.yourdomain.com` ✅

**Avoid:**
- `yourdomain.com/api` (harder to manage)
- `www.yourdomain.com` (should be for website, not API)
- `api1.yourdomain.com` (unprofessional)

### DNS Management

- **Use Cloudflare** if possible (free, fast, additional security features)
- **Keep TTL low** (600-3600s) for flexibility
- **Document your DNS records** (take screenshots)
- **Set up DNS monitoring** (e.g., UptimeRobot)

### Security

- ✅ Always use HTTPS (Railway enforces this)
- ✅ Enable CORS only for your app domain
- ✅ Set up rate limiting for API endpoints
- ✅ Monitor SSL certificate expiry (Railway handles this)
- ✅ Use environment-specific domains

---

## ✅ Custom Domain Checklist

- [ ] Purchase domain from registrar
- [ ] Add custom domain in Railway
- [ ] Copy CNAME target from Railway
- [ ] Add CNAME record in DNS provider
- [ ] Wait for DNS propagation (5-30 mins)
- [ ] Verify domain is "Active" in Railway
- [ ] Test domain: `curl https://api.yourdomain.com/health`
- [ ] Check SSL certificate in browser
- [ ] Update mobile app `.env` with new domain
- [ ] Test mobile app with new domain
- [ ] Update Clerk webhook URLs
- [ ] Update any other external services
- [ ] Document your domain setup
- [ ] Set up monitoring for domain/SSL

---

## 🎓 Advanced: Multiple Domains

You can add multiple domains to the same Railway service:

**Example:**
- `api.yourdomain.com` (primary)
- `backend.yourdomain.com` (alternative)
- `quiz-api.yourdomain.com` (branded)

All will point to the same Railway service with the same SSL certificates.

---

## 📞 Need Help?

**DNS Issues:**
- Check [dnschecker.org](https://dnschecker.org)
- Contact your domain registrar's support

**Railway Issues:**
- Railway Docs: [docs.railway.app/deploy/exposing-your-app](https://docs.railway.app/deploy/exposing-your-app)
- Railway Discord: [discord.gg/railway](https://discord.gg/railway)

**SSL Issues:**
- SSL Test: [ssllabs.com/ssltest](https://www.ssllabs.com/ssltest/)
- Let's Encrypt Status: [letsencrypt.status.io](https://letsencrypt.status.io/)

---

## 🎉 Success!

Your API is now live at `https://api.yourdomain.com` with professional branding and automatic SSL! 🚀

**Benefits you now have:**
- ✅ Professional custom domain
- ✅ Free SSL certificate (auto-renewing)
- ✅ Better branding for your app
- ✅ Production-ready infrastructure
- ✅ Easy to remember and share

**Your custom domain is ready for production!**

# 📚 Deployment Documentation Index

Complete guide to deploying your Quiz App FastAPI backend to Railway.

---

## 🚀 Getting Started

Start here based on your needs:

### 1. **Quick Deploy (15 minutes)** ⚡
**File:** `RAILWAY_QUICK_START.md`

Perfect for:
- Getting started quickly
- Testing Railway for the first time
- Development environment

What you'll learn:
- Railway account setup
- Database provisioning (PostgreSQL + Redis)
- Basic deployment
- Quick domain setup

---

### 2. **Complete Setup Guide (30 minutes)** 📖
**File:** `RAILWAY_DEPLOYMENT_SETUP.md`

Perfect for:
- Production deployment
- Understanding the full process
- Setting up GitHub Actions
- Comprehensive configuration

What you'll learn:
- Detailed Railway setup
- Environment variables configuration
- GitHub Actions auto-deployment
- Monitoring and troubleshooting
- Cost optimization
- Production checklist

---

### 3. **Custom Domain Setup (15 minutes)** 🌐
**File:** `CUSTOM_DOMAIN_SETUP.md`

Perfect for:
- Professional branding
- Production deployments
- Setting up `api.yourdomain.com`

What you'll learn:
- Add custom domain to Railway
- Configure DNS records (Cloudflare, GoDaddy, Namecheap, etc.)
- SSL certificate setup (automatic)
- DNS troubleshooting
- Multi-environment setup (staging/production)
- Update mobile app configuration

---

## 📋 Configuration Files Reference

### Core Deployment Files

| File | Purpose | When to Edit |
|------|---------|--------------|
| `Dockerfile` | Docker container configuration | Rarely (already optimized) |
| `.dockerignore` | Files to exclude from Docker build | When adding new folders to ignore |
| `railway.toml` | Railway service configuration | To adjust resource limits |
| `.github/workflows/railway-deploy.yml` | GitHub Actions auto-deploy | To change deployment triggers |
| `.env.railway.example` | Environment variables template | Reference only, copy to Railway UI |

### Documentation Files

| File | Purpose | Audience |
|------|---------|----------|
| `RAILWAY_QUICK_START.md` | 15-minute quick setup | Beginners, rapid deployment |
| `RAILWAY_DEPLOYMENT_SETUP.md` | Complete deployment guide | Production setup, detailed learning |
| `CUSTOM_DOMAIN_SETUP.md` | Custom domain configuration | Production, professional branding |
| `DEPLOYMENT_DOCS_INDEX.md` | This file - documentation index | Everyone (start here!) |

---

## 🎯 Common Scenarios

### Scenario 1: First-time Railway User
**Path:**
1. Read `RAILWAY_QUICK_START.md` (15 mins)
2. Deploy and test
3. If moving to production → Read `CUSTOM_DOMAIN_SETUP.md`

### Scenario 2: Production Deployment
**Path:**
1. Read `RAILWAY_DEPLOYMENT_SETUP.md` (30 mins)
2. Complete all setup steps
3. Read `CUSTOM_DOMAIN_SETUP.md` (15 mins)
4. Configure custom domain
5. Follow Production Checklist

### Scenario 3: Adding Custom Domain (Already Deployed)
**Path:**
1. Go directly to `CUSTOM_DOMAIN_SETUP.md`
2. Follow Step 1-7
3. Update mobile app configuration

### Scenario 4: Setting Up Auto-Deployment
**Path:**
1. Read Part 2 of `RAILWAY_DEPLOYMENT_SETUP.md`
2. Configure GitHub Actions
3. Test by pushing to master branch

---

## 🔧 Troubleshooting Guides

### Deployment Issues
**See:** `RAILWAY_DEPLOYMENT_SETUP.md` → "Troubleshooting" section

Common fixes:
- Build failed
- Database connection errors
- Redis connection errors
- GitHub Actions failures
- 500 errors after deployment

### Domain Issues
**See:** `CUSTOM_DOMAIN_SETUP.md` → "Troubleshooting" section

Common fixes:
- Domain not found after 24 hours
- SSL certificate errors
- DNS propagation issues
- Cloudflare redirect loops

---

## 📊 Cost Information

### Railway Pricing (2025)

**Hobby Plan: $5/month**
- Includes $5 usage credits
- Pay-per-second after credits
- Expected cost: **$5-25/month**

**Pro Plan: $20/month**
- Includes $20 usage credits
- More resources (32 GB RAM / 32 vCPU)
- Expected cost: **$20-60/month**

**Detailed breakdown:** See `RAILWAY_DEPLOYMENT_SETUP.md` → "Monitoring & Costs"

---

## ✅ Complete Deployment Checklist

### Initial Setup
- [ ] Read `RAILWAY_QUICK_START.md` or `RAILWAY_DEPLOYMENT_SETUP.md`
- [ ] Create Railway account
- [ ] Deploy from GitHub repository
- [ ] Add PostgreSQL database
- [ ] Add Redis cache
- [ ] Configure environment variables
- [ ] Verify deployment works

### Custom Domain (Optional but Recommended)
- [ ] Purchase domain (if not already owned)
- [ ] Read `CUSTOM_DOMAIN_SETUP.md`
- [ ] Add custom domain in Railway
- [ ] Configure DNS records (CNAME)
- [ ] Verify SSL certificate is active
- [ ] Test custom domain endpoints

### Mobile App Integration
- [ ] Update `app/.env` with API URL
- [ ] Test authentication (Clerk)
- [ ] Test exam creation
- [ ] Test all API endpoints
- [ ] Verify app works on iOS
- [ ] Verify app works on Android

### GitHub Actions (Optional)
- [ ] Get Railway token
- [ ] Add GitHub secrets
- [ ] Test auto-deployment
- [ ] Configure deployment triggers

### Production Readiness
- [ ] Update Clerk webhook URLs
- [ ] Configure monitoring/alerts
- [ ] Test all features end-to-end
- [ ] Set up database backups
- [ ] Document your setup
- [ ] Plan for scaling

---

## 🆘 Getting Help

### Documentation
- **Railway Quick Start:** `RAILWAY_QUICK_START.md`
- **Full Setup Guide:** `RAILWAY_DEPLOYMENT_SETUP.md`
- **Custom Domain:** `CUSTOM_DOMAIN_SETUP.md`

### External Resources
- **Railway Docs:** [docs.railway.app](https://docs.railway.app)
- **Railway Discord:** [discord.gg/railway](https://discord.gg/railway)
- **Railway Status:** [status.railway.app](https://status.railway.app)
- **GitHub Actions Docs:** [docs.github.com/actions](https://docs.github.com/actions)

### Community Support
- Railway Discord (very responsive)
- GitHub Discussions (for code issues)
- Stack Overflow (tag: railway)

---

## 📝 Quick Reference

### Essential URLs

**Railway:**
- Dashboard: [railway.app](https://railway.app)
- Account Tokens: [railway.app/account/tokens](https://railway.app/account/tokens)
- Pricing: [railway.app/pricing](https://railway.app/pricing)

**DNS Tools:**
- DNS Checker: [dnschecker.org](https://dnschecker.org)
- SSL Test: [ssllabs.com/ssltest](https://www.ssllabs.com/ssltest/)
- Whois Lookup: [whois.net](https://whois.net)

### Common Commands

```bash
# Test API health
curl https://api.yourdomain.com/health

# Test API docs
open https://api.yourdomain.com/docs

# Check DNS propagation
dig api.yourdomain.com CNAME

# Clear local DNS cache (macOS)
sudo dscacheutil -flushcache

# Deploy via Railway CLI
railway up

# View Railway logs
railway logs
```

---

## 🎉 What You Get

After completing the full deployment:

**Infrastructure:**
- ✅ FastAPI backend on Railway
- ✅ PostgreSQL database (managed)
- ✅ Redis cache (managed)
- ✅ Auto-scaling
- ✅ Zero-downtime deployments

**Domain & Security:**
- ✅ Custom domain (`api.yourdomain.com`)
- ✅ Free SSL certificate (auto-renewing)
- ✅ HTTPS enforced
- ✅ Professional branding

**Automation:**
- ✅ GitHub Actions auto-deployment
- ✅ Deploy on push to master
- ✅ Automated testing (optional)

**Cost Efficiency:**
- ✅ Pay-per-second billing
- ✅ $5-25/month typical cost
- ✅ 70% cheaper than AWS
- ✅ No DevOps overhead

---

## 🚀 Next Steps

1. **Choose your path:**
   - Quick start → `RAILWAY_QUICK_START.md`
   - Detailed setup → `RAILWAY_DEPLOYMENT_SETUP.md`
   - Custom domain → `CUSTOM_DOMAIN_SETUP.md`

2. **Deploy your API**

3. **Configure custom domain** (recommended for production)

4. **Update mobile app** with production API URL

5. **Set up monitoring** and alerts

6. **Launch!** 🎉

---

**Ready to deploy? Start with `RAILWAY_QUICK_START.md`!**

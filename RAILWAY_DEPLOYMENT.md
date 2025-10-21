# Railway Deployment Guide & Troubleshooting

## Overview
This guide covers deploying the Quiz Generator & Legal Expert API to Railway, including common issues and their solutions.

## Prerequisites

### 1. Environment Variables (Required in Railway Dashboard)

```bash
# Required for API functionality
OPENROUTER_API_KEY=your_openrouter_api_key
EMBEDDING_MODEL=intfloat/multilingual-e5-large

# Supabase (Database)
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_role_key
POSTGRES_URL=postgresql://postgres:[PASSWORD]@db.[PROJECT_REF].supabase.co:5432/postgres

# Clerk (Authentication)
CLERK_SECRET_KEY=sk_test_your_clerk_secret_key
CLERK_WEBHOOK_SECRET=whsec_your_webhook_secret

# Optional - Disable if not available
REDIS_ENABLED=false  # Set to false if Redis not available on Railway
```

## Deployment Process

### 1. Connect GitHub Repository
1. Go to Railway dashboard
2. Create new project → "Deploy from GitHub repo"
3. Select your repository
4. Railway will auto-detect the Dockerfile

### 2. Configure Environment Variables
1. Click on your service in Railway
2. Go to "Variables" tab
3. Add all required environment variables from above
4. Railway automatically provides `PORT` variable

### 3. Monitor Deployment
1. Watch the build logs in Railway dashboard
2. Build typically takes 5-10 minutes (Python dependencies)
3. After build, healthcheck runs for up to 5 minutes

## Common Issues & Solutions

### Issue 1: "Service Unavailable" During Healthcheck

**Symptoms:**
```
Attempt #1 failed with service unavailable. Continuing to retry...
1/1 replicas never became healthy!
```

**Causes:**
- App not listening on Railway's PORT
- Import errors crashing the app
- Heavy initialization blocking startup

**Solutions Applied:**
1. ✅ Made all imports lazy-loaded (agents load on first use)
2. ✅ Health endpoint returns immediately without waiting for initialization
3. ✅ Database/Redis failures don't block startup
4. ✅ App runs in "minimal mode" if dependencies fail

### Issue 2: Build Takes Too Long

**Solutions:**
- Multi-stage Docker build (already implemented)
- Excluded React Native app/ folder from backend build
- Used Docker layer caching effectively

### Issue 3: First Request Times Out

**Expected Behavior:**
- First API request may take 10-20 seconds (agent initialization)
- Subsequent requests will be fast
- This is normal due to lazy-loading strategy

**Solutions:**
- Increased `--timeout-keep-alive 300` in startup command
- Could add a warm-up endpoint to pre-initialize agents after deployment

## Testing Locally

### Quick Startup Test
```bash
# Test if the app can start without dependencies
python test_startup.py
```

### Full Local Test with Docker
```bash
# Build Docker image
docker build -t quiz-api .

# Run with minimal environment
docker run -p 8000:8000 \
  -e PORT=8000 \
  -e REDIS_ENABLED=false \
  quiz-api

# Test health endpoint
curl http://localhost:8000/health
```

## Architecture Decisions

### 1. Lazy Loading Strategy
- **Why:** Railway healthcheck has 5-minute timeout
- **How:** Agents initialize on first API call, not during startup
- **Trade-off:** First request slower, but deployment always succeeds

### 2. Graceful Degradation
- **Why:** Missing dependencies shouldn't crash the app
- **How:** Try-catch around all imports, minimal mode fallback
- **Result:** Health endpoint always works, even if other features fail

### 3. Single Worker Process
- **Why:** Railway's hobby tier has memory limits
- **How:** `--workers 1` in uvicorn command
- **Benefit:** More stable, less memory usage

## Deployment Checklist

- [ ] All environment variables set in Railway dashboard
- [ ] GitHub repository connected to Railway
- [ ] Test locally with `python test_startup.py`
- [ ] Commit and push to trigger deployment
- [ ] Monitor build logs in Railway dashboard
- [ ] Wait for healthcheck to pass (up to 5 minutes)
- [ ] Test `/health` endpoint once deployed
- [ ] Test actual API endpoints (may be slow on first call)

## Monitoring & Debugging

### View Logs
1. Go to Railway dashboard
2. Click on your service
3. View "Logs" tab for real-time logs

### Expected Startup Logs
```
🚀 Starting Quiz Generator & Legal Expert API...
🏥 Health endpoint ready immediately for Railway healthcheck
📊 Initializing async database connection pool in background...
✅ Async database pool ready
📦 Initializing Redis cache in background...
⚠️  Running without cache layer  # Normal if Redis not configured
📝 Agents will initialize lazily on first use
🎉 API startup complete - ready for requests!
```

### Debug Failed Deployments
1. Check build logs for errors
2. Verify all environment variables are set
3. Test locally with minimal environment
4. Check Railway's status page for platform issues

## Performance Optimization

### Current Setup
- Lazy-loaded agents (10-20s first request)
- No Redis caching (if not configured)
- Single worker process

### Potential Improvements
1. Add Redis for caching (optional)
2. Add warm-up endpoint to pre-initialize agents
3. Upgrade to Railway Pro for more resources
4. Use CDN for static files

## Railway Configuration Files

### railway.toml
```toml
[build]
builder = "DOCKERFILE"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uvicorn api.main:app --host 0.0.0.0 --port $PORT --workers 1 --timeout-keep-alive 300"
healthcheckPath = "/health"
healthcheckTimeout = 300
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### Dockerfile Optimizations
- Multi-stage build for smaller image
- No HEALTHCHECK directive (Railway handles it)
- Non-root user for security
- Optimized layer caching

## Support & Resources

- [Railway Documentation](https://docs.railway.app/)
- [Railway Status](https://status.railway.app/)
- [FastAPI Deployment Guide](https://fastapi.tiangolo.com/deployment/)
- GitHub Issues for app-specific problems

## Emergency Recovery

If deployment consistently fails:

1. **Rollback to Previous Version**
   - Railway dashboard → Deployments → Rollback

2. **Deploy Minimal Version**
   - Comment out all routers except health
   - Deploy with minimal dependencies
   - Gradually add features back

3. **Contact Support**
   - Railway Discord community
   - GitHub Issues for app bugs

---

Last Updated: 2024
Deployment Time: ~10-15 minutes total (build + healthcheck)
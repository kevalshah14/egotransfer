# 🚀 Deploy to Railway - Complete Guide

## Current Status

✅ All configuration files are ready
✅ Python 3.12 specified correctly
✅ Dependencies listed in requirements.txt
✅ Start command configured
✅ Nixpacks configuration simplified

## 📋 Quick Deploy Checklist

### Step 1: Push to GitHub

```bash
cd /Users/keval/Documents/VSCode/egotransfer
git add .
git commit -m "Add Railway deployment configuration"
git push origin main
```

### Step 2: Railway Backend Service Setup

1. **Go to Railway Dashboard**: [railway.app](https://railway.app)

2. **Create/Select Project**: Click "New Project" or select existing

3. **Add Backend Service**:
   - Click "New Service"
   - Select "GitHub Repo"
   - Choose your repository

4. **⚠️ CRITICAL: Set Root Directory**:
   - Go to **Settings** → **Source**
   - Find **Root Directory** field
   - Type: `backend` (exactly, no slashes)
   - Wait for it to save

5. **Verify Start Command**:
   - Go to **Settings** → **Deploy**
   - Should show: `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - If not, set it manually

6. **Add Environment Variables**:
   - Go to **Variables** tab
   - Click "New Variable"
   - Add:
     ```
     GEMINI_API_KEY = your_actual_api_key_here
     ENVIRONMENT = production
     LOG_LEVEL = info
     ```

7. **Deploy**:
   - Go to **Deployments** tab
   - Click "Deploy" or it will auto-deploy
   - Watch the build logs

### Step 3: Railway Frontend Service Setup

1. **Add Frontend Service**:
   - Click "New Service" in your project
   - Select "GitHub Repo"
   - Choose same repository

2. **⚠️ CRITICAL: Set Root Directory**:
   - Go to **Settings** → **Source**
   - Find **Root Directory** field
   - Type: `frontend` (exactly, no slashes)
   - Wait for it to save

3. **Verify Commands**:
   - Build Command: `npm install && npm run build`
   - Start Command: `npm start`

4. **Add Environment Variables**:
   - Copy your Backend service URL from Railway (looks like: `https://backend-production-xxxx.up.railway.app`)
   - Go to Frontend **Variables** tab
   - Add:
     ```
     NODE_ENV = production
     BACKEND_URL = https://your-backend-url.railway.app
     ```

5. **Deploy**:
   - Should auto-deploy after adding variables

### Step 4: Configure CORS

Once frontend is deployed:

1. **Get Frontend URL** from Railway (e.g., `https://frontend-production-xxxx.up.railway.app`)

2. **Update Backend Variables**:
   - Go to Backend service → **Variables**
   - Add new variable:
     ```
     ALLOWED_ORIGINS = https://your-frontend-url.railway.app
     ```
   - Backend will auto-redeploy

### Step 5: Verify Deployment

1. **Backend Health Check**:
   ```
   https://your-backend-url.railway.app/health
   ```
   Should return: `{"status": "healthy", "service": "video-to-robot-processing"}`

2. **Backend API Docs**:
   ```
   https://your-backend-url.railway.app/docs
   ```
   Should show FastAPI documentation

3. **Frontend**:
   ```
   https://your-frontend-url.railway.app
   ```
   Should load your React app

## 🐛 Troubleshooting

### Build Fails: "pip: command not found"

**Solution**: Ensure Root Directory is set to `backend` (not empty, not `/`)

### Build Fails: "Could not determine how to build"

**Solution**: Root Directory must be set! Go to Settings → Source → Root Directory → `backend`

### Frontend Can't Connect

**Solution**: 
1. Check `BACKEND_URL` in frontend variables
2. Check `ALLOWED_ORIGINS` in backend variables
3. Ensure both services are deployed and running

### Environment Variables Not Working

**Solution**:
1. Variables should NOT have quotes (Railway adds them)
2. After adding variables, service will auto-redeploy
3. Check logs to verify variables are being read

## 📝 Key Configuration Files

All these files are already in your `backend/` directory:

- `requirements.txt` - Python dependencies ✅
- `runtime.txt` - Python version (3.12) ✅
- `Procfile` - Process type and start command ✅
- `nixpacks.toml` - Build configuration ✅
- `railway.json` - Railway settings ✅
- `main.py` - App exports `app` at module level ✅

## 🎯 What Railway Will Do

1. **Detect Python**: Railway sees `requirements.txt` and `runtime.txt`
2. **Install Python 3.12**: Based on `runtime.txt`
3. **Install Dependencies**: Runs `pip install -r requirements.txt`
4. **Start Server**: Runs `uvicorn main:app --host 0.0.0.0 --port $PORT`
5. **Expose Service**: Provides public URL with SSL

## ⚡ Expected Build Output

```
╭─────────────────╮
│ Railpack 0.11.0 │
╰─────────────────╯

Detected Python app
Using Python 3.12
Installing dependencies from requirements.txt...
✓ Dependencies installed
Starting server...
✓ Server started on port $PORT
```

## 🔗 Important URLs After Deployment

Save these for reference:

- Backend API: `https://[your-backend].railway.app`
- Backend Health: `https://[your-backend].railway.app/health`
- Backend Docs: `https://[your-backend].railway.app/docs`
- Frontend: `https://[your-frontend].railway.app`

## 💡 Pro Tips

1. **Auto-Deploy**: Railway auto-deploys when you push to GitHub
2. **Environment Variables**: Add them before deploying
3. **Logs**: Check Railway logs for any errors
4. **Rollback**: You can rollback to previous deployments
5. **Custom Domain**: Add custom domains in Settings

## 🆘 Need Help?

If deployment fails:
1. Share the Railway build logs (copy full log)
2. Verify Root Directory is set correctly
3. Check all files exist in the correct directories
4. Ensure all environment variables are set

Railway Discord: https://discord.gg/railway
Railway Docs: https://docs.railway.app


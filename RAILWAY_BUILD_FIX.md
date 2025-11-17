# Railway Build Fix - "pip: command not found"

## What Happened

The error `pip: command not found` occurs when Nixpacks can't properly set up Python in the build environment.

## The Fix

I've simplified the configuration. Here's what you need:

### Required Files in `backend/` Directory

1. ✅ `requirements.txt` - Python dependencies
2. ✅ `runtime.txt` - Contains `python-3.12`
3. ✅ `Procfile` - Contains `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
4. ✅ `nixpacks.toml` - Simplified Nixpacks configuration
5. ✅ `railway.json` - Railway deployment settings
6. ✅ `main.py` - Exports `app = create_app()`

## Steps to Deploy

### 1. Commit and Push Changes
```bash
cd /Users/keval/Documents/VSCode/egotransfer
git add backend/
git commit -m "Simplify Railway configuration for Python build"
git push origin main
```

### 2. In Railway Dashboard

#### Set Root Directory (CRITICAL)
1. Go to your Backend service
2. Click **Settings** → **Source**
3. Set **Root Directory** to: `backend`
4. Save (auto-saves)

#### Verify Start Command
1. In **Settings** → **Deploy**
2. Ensure **Start Command** is: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Set Environment Variables
1. Go to **Variables** tab
2. Add:
   ```
   GEMINI_API_KEY=your_api_key_here
   ENVIRONMENT=production
   ```

### 3. Redeploy
1. Go to **Deployments** tab
2. Click **Redeploy** or trigger new deployment
3. Watch build logs

## What Changed

- Simplified `nixpacks.toml` to let Railway auto-detect Python better
- Removed unnecessary `setup.py`
- Kept only essential configuration files

## Expected Build Output

You should see:
```
╭─────────────────╮
│ Railpack 0.11.0 │
╰─────────────────╯

Detected Python app
Using Python 3.12
Installing dependencies from requirements.txt...
Successfully built app
```

## If It Still Fails

### Option 1: Manual Configuration Override

In Railway Settings → Build, set:
- **Build Command**: Leave empty (let Railway auto-detect)
- **Install Command**: `pip install -r requirements.txt`

In Railway Settings → Deploy:
- **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### Option 2: Use Railway's Python Template

If auto-detection still fails:
1. Delete the service
2. Create new service
3. Select "Deploy Python App" template
4. Point it to your repository
5. Set Root Directory to `backend`

### Option 3: Check Python Version

Ensure `backend/runtime.txt` contains exactly (no extra spaces):
```
python-3.12
```

## Verification Checklist

Before redeploying, verify:

- [ ] Root Directory is set to `backend` in Railway
- [ ] `backend/requirements.txt` exists and is valid
- [ ] `backend/runtime.txt` contains `python-3.12`
- [ ] `backend/main.py` exports `app` at module level
- [ ] All changes are committed and pushed to GitHub
- [ ] Environment variables are set in Railway

## Still Having Issues?

If the build still fails, share:
1. The complete build log from Railway
2. Output of: `ls -la backend/` (to verify files)
3. Contents of `backend/runtime.txt`

This will help diagnose any remaining issues.


# Railway Deployment Troubleshooting

## Build Errors

### "Error creating build plan with Nixpacks"

This error typically occurs when Railway can't detect your project type or build configuration.

#### Solution 1: Verify File Structure
Ensure these files exist in your `backend` directory:
- ✅ `requirements.txt`
- ✅ `runtime.txt` (with `python-3.12`)
- ✅ `nixpacks.toml`
- ✅ `main.py` (with `app = create_app()` at module level)

#### Solution 2: Check Root Directory
In Railway:
1. Go to your Backend Service → Settings → Source
2. Verify **Root Directory** is set to `backend` (not empty or `/`)
3. Save and redeploy

#### Solution 3: Verify Build Configuration
Check that `backend/nixpacks.toml` contains:
```toml
[phases.setup]
nixPkgs = ["python312"]

[phases.install]
cmds = [
    "pip install --upgrade pip",
    "pip install -r requirements.txt"
]

[start]
cmd = "uvicorn main:app --host 0.0.0.0 --port $PORT"
```

#### Solution 4: Manual Build Command Override
If Nixpacks still fails:
1. Go to Service → Settings → Build
2. Add build command: `pip install --upgrade pip && pip install -r requirements.txt`
3. Ensure start command is: `uvicorn main:app --host 0.0.0.0 --port $PORT`

#### Solution 5: Check Python Version
Verify `backend/runtime.txt` contains exactly:
```
python-3.12
```

(No extra spaces or newlines)

### "Module not found" or Import Errors

**Problem**: Python can't find modules after deployment

**Solution**:
1. Ensure all dependencies are in `requirements.txt`
2. Check that `main.py` has proper imports:
   ```python
   from app import create_app
   ```
3. Verify the app is exported at module level:
   ```python
   app = create_app()
   ```

### "Port already in use" or Port Errors

**Problem**: Service won't start because of port issues

**Solution**:
- Railway automatically sets `$PORT` - don't hardcode port numbers
- Ensure start command uses `$PORT`: `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Never use `--reload` in production (Railway handles restarts)

## Deployment Errors

### Service Won't Start

1. **Check Logs**: Railway dashboard → Service → Logs
2. **Verify Start Command**: Should be `uvicorn main:app --host 0.0.0.0 --port $PORT`
3. **Check Environment Variables**: Ensure all required vars are set
4. **Verify Dependencies**: All packages in `requirements.txt` should install successfully

### Frontend Can't Connect to Backend

1. **Verify BACKEND_URL**: Must be the exact Railway URL (e.g., `https://backend-xxxx.up.railway.app`)
2. **Check CORS**: Backend `ALLOWED_ORIGINS` must include frontend URL
3. **Test Backend Health**: Visit `https://your-backend-url.railway.app/health`
4. **Check Network**: Both services must be deployed and running

## Common Configuration Mistakes

### ❌ Wrong Root Directory
- Setting root to `/` instead of `backend` or `frontend`
- **Fix**: Set Root Directory in Service Settings

### ❌ Hardcoded Ports
- Using `--port 8000` instead of `--port $PORT`
- **Fix**: Always use `$PORT` environment variable

### ❌ Missing Environment Variables
- Forgetting to set `BACKEND_URL` in frontend
- Forgetting to set `GEMINI_API_KEY` in backend
- **Fix**: Add all required environment variables

### ❌ Wrong Build Commands
- Using `python main.py` instead of `uvicorn main:app`
- **Fix**: Use the correct start command for production

## Debugging Steps

1. **Check Build Logs**
   - Railway Dashboard → Service → Deployments → Click on failed deployment
   - Look for error messages during build phase

2. **Check Runtime Logs**
   - Railway Dashboard → Service → Logs
   - Look for startup errors or import failures

3. **Test Locally**
   - Try building locally: `pip install -r requirements.txt`
   - Test start command: `uvicorn main:app --host 0.0.0.0 --port 8000`

4. **Verify Files**
   - Ensure all configuration files are committed to Git
   - Check that files are in the correct directories

5. **Recreate Service**
   - If all else fails, delete and recreate the service
   - This can resolve caching or configuration issues

## Getting Help

If you're still stuck:

1. **Check Railway Logs**: Most issues show up in the logs
2. **Railway Docs**: https://docs.railway.app
3. **Railway Discord**: https://discord.gg/railway
4. **GitHub Issues**: Check if others have similar problems

## Quick Fixes Checklist

- [ ] Root Directory set correctly (`backend` or `frontend`)
- [ ] `nixpacks.toml` exists in backend directory
- [ ] `runtime.txt` contains `python-3.12`
- [ ] `requirements.txt` is in backend root
- [ ] Start command uses `$PORT` not hardcoded port
- [ ] `main.py` exports `app` at module level
- [ ] All environment variables are set
- [ ] Both services are deployed
- [ ] Backend health check passes (`/health`)
- [ ] CORS configured correctly


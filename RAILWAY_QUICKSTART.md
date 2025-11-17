# Railway Deployment Quick Start

## TL;DR - Deploy in 5 Minutes

### 1. Push to GitHub
```bash
git add .
git commit -m "Add Railway deployment config"
git push origin main
```

### 2. Create Railway Project
1. Go to [railway.app](https://railway.app)
2. Click "New Project" → "Deploy from GitHub repo"
3. Select your repository

### 3. Deploy Backend
1. Click "New Service" → Select your repo
2. Set **Root Directory**: `backend`
3. Set **Start Command**: `uvicorn main:app --host 0.0.0.0 --port $PORT`
4. Add Environment Variables:
   ```
   GEMINI_API_KEY=your_key_here
   ENVIRONMENT=production
   ```

### 4. Deploy Frontend
1. Click "New Service" → Select your repo
2. Set **Root Directory**: `frontend`
3. Set **Start Command**: `npm start`
4. Add Environment Variables:
   ```
   NODE_ENV=production
   BACKEND_URL=https://your-backend-url.railway.app
   ```

### 5. Update Backend CORS
In Backend → Variables, add:
```
ALLOWED_ORIGINS=https://your-frontend-url.railway.app
```

### 6. Test
- Backend: `https://your-backend-url.railway.app/health`
- Frontend: `https://your-frontend-url.railway.app`

## Environment Variables Checklist

### Backend Required:
- ✅ `GEMINI_API_KEY`
- ✅ `ALLOWED_ORIGINS` (after frontend is deployed)

### Frontend Required:
- ✅ `BACKEND_URL`
- ✅ `NODE_ENV=production`

## Common Issues

**Backend won't start**: Check that `PORT` is available (Railway sets this automatically)

**Frontend can't connect**: Verify `BACKEND_URL` matches your backend Railway URL exactly

**CORS errors**: Ensure `ALLOWED_ORIGINS` includes your frontend URL

For detailed instructions, see [RAILWAY_DEPLOYMENT.md](./RAILWAY_DEPLOYMENT.md)


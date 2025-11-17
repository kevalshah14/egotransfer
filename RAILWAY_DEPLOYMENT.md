# Railway Deployment Guide

This guide will help you deploy the Video-to-Robot Processing System on Railway using GitHub integration.

## Prerequisites

1. A GitHub account with your code pushed to a repository
2. A Railway account (sign up at [railway.app](https://railway.app))
3. Google Gemini API key (for AI features)

## Architecture

This application consists of two services:
- **Backend**: Python FastAPI application (port 8000)
- **Frontend**: Node.js/Express server serving React app (port 5000)

## Step 1: Prepare Your Repository

Ensure your code is pushed to GitHub:

```bash
git add .
git commit -m "Prepare for Railway deployment"
git push origin main
```

## Step 2: Create Railway Project

1. Go to [railway.app](https://railway.app) and sign in
2. Click "New Project"
3. Select "Deploy from GitHub repo"
4. Choose your repository
5. Railway will detect your project structure

## Step 3: Deploy Backend Service

### 3.1 Create Backend Service

1. In your Railway project, click "New Service"
2. Select "GitHub Repo" and choose your repository
3. Railway will auto-detect it's a Python project

### 3.2 Configure Backend Service

1. **Set Root Directory**: 
   - Go to Settings → Source
   - Set Root Directory to `backend`

2. **Set Build Command** (if not auto-detected):
   - Go to Settings → Build
   - Build Command: `pip install -r requirements.txt`

3. **Set Start Command**:
   - Go to Settings → Deploy
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 3.3 Configure Backend Environment Variables

Go to Variables tab and add:

```
GEMINI_API_KEY=your_gemini_api_key_here
HOST=0.0.0.0
LOG_LEVEL=info
ENVIRONMENT=production
ALLOWED_ORIGINS=https://your-frontend-domain.railway.app
```

**Important**: Replace `your-frontend-domain.railway.app` with your actual frontend Railway URL (you'll get this after deploying the frontend).

### 3.4 Get Backend URL

After deployment, Railway will provide a public URL like:
```
https://your-backend-service.railway.app
```

Copy this URL - you'll need it for the frontend configuration.

## Step 4: Deploy Frontend Service

### 4.1 Create Frontend Service

1. In your Railway project, click "New Service"
2. Select "GitHub Repo" and choose your repository
3. Railway will auto-detect it's a Node.js project

### 4.2 Configure Frontend Service

1. **Set Root Directory**:
   - Go to Settings → Source
   - Set Root Directory to `frontend`

2. **Set Build Command**:
   - Go to Settings → Build
   - Build Command: `npm install && npm run build`

3. **Set Start Command**:
   - Go to Settings → Deploy
   - Start Command: `npm start`

### 4.3 Configure Frontend Environment Variables

Go to Variables tab and add:

```
NODE_ENV=production
BACKEND_URL=https://your-backend-service.railway.app
PORT=5000
```

**Important**: Replace `your-backend-service.railway.app` with the actual backend URL from Step 3.4.

## Step 5: Update Backend CORS Settings

After you have your frontend URL, update the backend's `ALLOWED_ORIGINS`:

1. Go to Backend Service → Variables
2. Update `ALLOWED_ORIGINS` to include your frontend URL:
   ```
   ALLOWED_ORIGINS=https://your-frontend-service.railway.app
   ```
3. Railway will automatically redeploy

## Step 6: Configure GitHub Integration (Auto-Deploy)

Railway automatically deploys when you push to your GitHub repository. To configure:

1. Go to your Service → Settings → Source
2. Ensure "Auto-Deploy" is enabled
3. Select the branch you want to deploy (usually `main` or `master`)

## Step 7: Verify Deployment

### Backend Health Check

Visit your backend URL:
```
https://your-backend-service.railway.app/health
```

You should see:
```json
{
  "status": "healthy",
  "service": "video-to-robot-processing"
}
```

### Frontend Check

Visit your frontend URL:
```
https://your-frontend-service.railway.app
```

The React app should load and connect to the backend.

### API Documentation

Visit:
```
https://your-backend-service.railway.app/docs
```

You should see the FastAPI interactive documentation.

## Step 8: Set Up Custom Domains (Optional)

1. Go to your Service → Settings → Domains
2. Click "Generate Domain" or "Add Custom Domain"
3. Follow Railway's instructions for DNS configuration

## Environment Variables Reference

### Backend Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `GEMINI_API_KEY` | Google Gemini API key for AI analysis | Yes | - |
| `HOST` | Server host | No | `0.0.0.0` |
| `PORT` | Server port (Railway sets this automatically) | No | `8000` |
| `LOG_LEVEL` | Logging level (debug, info, warning, error) | No | `info` |
| `ENVIRONMENT` | Environment (development, production) | No | `development` |
| `ALLOWED_ORIGINS` | Comma-separated list of allowed CORS origins | No | `*` |

### Frontend Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `NODE_ENV` | Node environment | No | `development` |
| `BACKEND_URL` | Backend API URL | Yes | `http://localhost:8000` |
| `PORT` | Server port (Railway sets this automatically) | No | `5000` |

## Troubleshooting

### Backend Issues

**Problem**: Build fails with "Error creating build plan with Nixpacks"
- Ensure `nixpacks.toml` exists in the backend directory
- Verify `runtime.txt` specifies Python version (should be `python-3.12`)
- Check that `requirements.txt` is in the backend root directory
- Make sure Root Directory is set to `backend` in Railway settings
- Try removing and recreating the service if the issue persists

**Problem**: Backend fails to start
- Check that `PORT` environment variable is set (Railway sets this automatically)
- Verify `requirements.txt` includes all dependencies
- Check logs in Railway dashboard
- Ensure `main.py` exports `app` at module level (should have `app = create_app()`)

**Problem**: CORS errors
- Ensure `ALLOWED_ORIGINS` includes your frontend URL
- Check that frontend is using the correct backend URL

**Problem**: AI analysis not working
- Verify `GEMINI_API_KEY` is set correctly
- Check API key has proper permissions

### Frontend Issues

**Problem**: Frontend can't connect to backend
- Verify `BACKEND_URL` environment variable is correct
- Check backend is deployed and healthy
- Ensure CORS is configured on backend

**Problem**: Build fails
- Check Node.js version compatibility
- Verify all dependencies in `package.json`
- Check build logs in Railway dashboard

**Problem**: Static files not loading
- Ensure `npm run build` completes successfully
- Check that `dist/public` directory exists after build

### General Issues

**Problem**: Services not deploying
- Check GitHub repository is connected
- Verify root directories are set correctly
- Check build and start commands are correct

**Problem**: Port conflicts
- Railway automatically sets `PORT` - don't override it
- Ensure start commands use `$PORT` variable

## Monitoring

Railway provides built-in monitoring:

1. **Logs**: View real-time logs in the Railway dashboard
2. **Metrics**: Monitor CPU, memory, and network usage
3. **Deployments**: Track deployment history and status

## Scaling

Railway allows you to scale your services:

1. Go to Service → Settings → Scaling
2. Adjust resources as needed
3. Railway will automatically handle load balancing

## Cost Optimization

- Railway offers a free tier with usage limits
- Monitor your usage in the dashboard
- Consider upgrading if you exceed free tier limits

## Security Best Practices

1. **Never commit secrets**: Use Railway's environment variables
2. **Use HTTPS**: Railway provides SSL certificates automatically
3. **Set proper CORS**: Restrict `ALLOWED_ORIGINS` to your frontend domain
4. **Rotate API keys**: Regularly update your `GEMINI_API_KEY`
5. **Monitor logs**: Check for suspicious activity

## Next Steps

After deployment:

1. Test all features end-to-end
2. Set up monitoring and alerts
3. Configure custom domains
4. Set up CI/CD workflows
5. Add database if needed (Railway supports PostgreSQL, MySQL, etc.)

## Support

- Railway Documentation: https://docs.railway.app
- Railway Discord: https://discord.gg/railway
- Project Issues: Check your GitHub repository


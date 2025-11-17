# Direct Backend Integration

## Architecture Change

The frontend now calls the FastAPI backend **directly** instead of going through an Express proxy. This simplifies the architecture and reduces latency.

### Old Architecture (Redundant)
```
React → Express Proxy → FastAPI Backend
```

### New Architecture (Simplified) ✅
```
React → FastAPI Backend (directly)
```

## Configuration

### Development
No configuration needed! Vite's dev proxy (in `vite.config.ts`) automatically forwards API calls to `localhost:8000`.

```bash
cd frontend
npm run dev  # React dev server on port 3000, proxies to backend on 8000
```

### Production

Set the `VITE_API_BASE_URL` environment variable to your backend URL:

**Railway Environment Variables:**
```
VITE_API_BASE_URL=https://backend-production-4ad1.up.railway.app
```

**Or in `.env`:**
```bash
VITE_API_BASE_URL=https://your-backend-url.com
```

### How it Works

1. **`frontend/client/src/lib/config.ts`** - Manages API base URL
2. **`frontend/client/src/lib/queryClient.ts`** - All API calls use `apiUrl()` helper
3. **Components** - Updated to use `apiUrl()` for fetch calls

## Deployment

### Option A: Keep Express (Current)
The Express server still exists for serving static files. It no longer proxies API calls.

**Deploy:** Push to Railway, it will auto-deploy both services.

### Option B: Remove Express Entirely (Recommended)
1. Deploy frontend as static files (Railway/Vercel/Netlify)
2. Serve from CDN
3. One less server to maintain!

## Backend CORS Configuration

The FastAPI backend already has CORS enabled (`backend/app.py`):

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

**Set allowed origins in production:**
```
ALLOWED_ORIGINS=https://frontend-production-1299.up.railway.app,https://yourdomain.com
```

## Testing

### Local Testing
```bash
# Terminal 1: Start backend
cd backend
uvicorn main:app --reload --port 8000

# Terminal 2: Start frontend  
cd frontend
npm run dev
```

Visit `http://localhost:3000` - API calls will be proxied to `localhost:8000`

### Production Testing
1. Set `VITE_API_BASE_URL` in Railway
2. Deploy
3. Frontend will call backend directly via the configured URL

## Benefits

✅ **Simpler architecture** - One less proxy layer  
✅ **Better performance** - Direct connection reduces latency  
✅ **Easier debugging** - Fewer moving parts  
✅ **Standard practice** - React → REST API is the norm  
✅ **Cost efficient** - Can deploy frontend to static hosting (cheaper)


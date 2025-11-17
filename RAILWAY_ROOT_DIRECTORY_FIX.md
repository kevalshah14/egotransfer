# Fix: "Railpack could not determine how to build the app"

## The Problem

Railway is looking at your repository root instead of the `backend` or `frontend` directories. This happens when the **Root Directory** is not configured.

## The Solution

Set the Root Directory for each service in Railway.

### Step-by-Step Instructions

#### For Backend Service:

1. **Open Railway Dashboard**: Go to [railway.app](https://railway.app)

2. **Select Your Project**: Click on your project

3. **Select Backend Service**: Click on the backend service (you may have named it)

4. **Go to Settings**: Click the "Settings" tab at the top

5. **Find Source Section**: Scroll down to the "Source" section

6. **Set Root Directory**:
   - You'll see a field labeled "Root Directory"
   - Type: `backend` (exactly, no slashes like `/backend` or `backend/`)
   - The field should show: `backend`

7. **Save**: The setting saves automatically

8. **Redeploy**: 
   - Go to "Deployments" tab
   - Click "Redeploy" or trigger a new deployment
   - Watch the build logs - it should now detect Python

#### For Frontend Service:

Repeat the same steps but set Root Directory to: `frontend`

## Visual Guide

### ❌ Wrong Setup
```
Root Directory: [empty] or "/" or not set

Railway sees:
./
├── backend/
├── frontend/
└── docs/

Result: "Could not determine how to build the app"
```

### ✅ Correct Setup
```
Root Directory: backend

Railway sees:
backend/
├── main.py
├── requirements.txt
├── nixpacks.toml
└── runtime.txt

Result: "Detected Python app!"
```

## Verification

After setting the Root Directory, check the build logs. You should see:

```
╭─────────────────╮
│ Railpack 0.11.0 │
╰─────────────────╯

Detected Python app
Using Python 3.12
Installing dependencies from requirements.txt...
```

## Still Not Working?

### Check These:

1. **Root Directory spelling**: Must be exactly `backend` or `frontend`
   - ✅ Correct: `backend`
   - ❌ Wrong: `/backend`, `backend/`, `Backend`, `./backend`

2. **Files in correct location**:
   ```
   backend/
   ├── main.py          ✅
   ├── requirements.txt ✅
   ├── nixpacks.toml    ✅
   └── runtime.txt      ✅
   ```

3. **Service Type**: Make sure you created a new service (not trying to deploy from project root)

4. **Redeploy**: After changing Root Directory, you MUST trigger a new deployment

## Alternative: Screenshot Guide

If you're having trouble finding the settings:

1. **Settings Tab**: Top of the service page, usually next to "Deployments" and "Logs"

2. **Source Section**: About halfway down the settings page

3. **Root Directory Field**: Looks like a text input box with a folder icon

4. **What to type**: Just the folder name: `backend` or `frontend`

## Need More Help?

Share a screenshot of:
1. Your Railway service Settings → Source section
2. The build error logs

This will help diagnose any remaining issues.


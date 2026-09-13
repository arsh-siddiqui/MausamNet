# Deploying MausamNet

MausamNet is designed for a decoupled cloud architecture. The prototype targets **Vercel** for the Next.js frontend and **Render** for the FastAPI backend, utilizing an embedded SQLite database.

## Architecture Flow
```
GitHub (main)
      │
      ├───────────────► Vercel
      │                  Next.js Frontend
      │                       │
      │                       │ HTTPS
      │                       ▼
      └───────────────► Render
                         FastAPI Backend
                              │
                              ▼
                           SQLite
```

## Step 1: Push to GitHub
Ensure all code is committed and pushed to the `main` branch of your GitHub repository.

## Step 2: Deploy Backend to Render
MausamNet includes a `render.yaml` Blueprint to fully automate backend deployment.

1. Create a free account on [Render](https://render.com).
2. Click **New +** and select **Blueprint**.
3. Connect your GitHub repository.
4. Render will automatically detect `render.yaml` and configure a Web Service (Python 3) using `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

### Backend Environment Variables
In your Render Dashboard, go to your Web Service -> Environment, and configure:

```env
# Required for production
APP_ENV=production
DEMO_MODE=true
JWT_SECRET=<generate-a-secure-random-string>

# Replace with your Vercel URL once generated
FRONTEND_URL=https://<your-vercel-domain>.vercel.app

# Open-Meteo Integration (Optional but recommended)
OPEN_METEO_API_URL=https://api.open-meteo.com/v1

# Other optional sources (IMD, EUMETSAT, News, Social) can be configured here as per backend/.env.example
```

## Step 3: Initialize Database and Seed Data
Once the Render backend is live, you must seed the SQLite database.
Render offers a "Shell" tab for your Web Service. Open it and run:

```bash
python scripts/seed_database.py
```
This will predictably generate the required prototype signals, anomalies, media items, and events.

## Step 4: Deploy Frontend to Vercel
1. Create a free account on [Vercel](https://vercel.com).
2. Click **Add New...** -> **Project**.
3. Import your GitHub repository.
4. Expand **Root Directory** and select `frontend/`.
5. Expand **Environment Variables** and add the following:

```env
NEXT_PUBLIC_API_URL=https://<your-render-service>.onrender.com
NEXT_PUBLIC_REALTIME_URL=https://<your-render-service>.onrender.com
```

Click **Deploy**. Vercel will automatically run `npm run build` and launch the frontend.

## Step 5: Final Configuration
1. Go back to Render.
2. Update the `FRONTEND_URL` environment variable with your new Vercel domain to ensure CORS works correctly.
3. Your deployment is complete! Visit your Vercel URL to access MausamNet.

## Troubleshooting

- **CORS Errors:** Verify `FRONTEND_URL` in Render matches your exact Vercel domain (with `https://` and no trailing slash).
- **Map Not Loading:** Ensure you have not bypassed the Next.js `dynamic(..., {ssr: false})` wrappers on Leaflet components.
- **Login Failing:** Double-check you set a secure `JWT_SECRET` in Render. If it defaults to the insecure one in production mode, the API will refuse to start.

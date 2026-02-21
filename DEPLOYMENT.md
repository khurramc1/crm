# Railway Deployment Guide

This Django CRM application is configured for easy deployment on [Railway.app](https://railway.app).

## Prerequisites

1. **Railway Account**: Sign up at https://railway.app
2. **GitHub Repository**: Push your code to GitHub
3. **Environment Variables**: Set up in Railway dashboard

## Deployment Steps

### 1. Connect GitHub Repository to Railway

1. Go to [Railway Dashboard](https://railway.app/dashboard)
2. Click "New Project"
3. Select "Deploy from GitHub"
4. Authorize Railway to access your GitHub account
5. Select your CRM repository
6. Railway will automatically detect it's a Python/Django app

### 2. Set Environment Variables

In Railway Dashboard, go to **Variables** and set the following:

```
DEBUG=False
SECRET_KEY=<generate-a-strong-random-key>
ALLOWED_HOSTS=<your-railway-domain>.railway.app,localhost
SENDGRID_API_KEY=<your-sendgrid-api-key>
DEFAULT_FROM_EMAIL=noreply@yourdomain.com
CORS_ALLOWED_ORIGINS=https://<your-railway-domain>.railway.app
```

**To generate a strong SECRET_KEY:**
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

### 3. Add PostgreSQL Database (Optional but Recommended)

1. In Railway Dashboard, click "Add a service"
2. Select "PostgreSQL"
3. Railway will automatically set `DATABASE_URL` environment variable

**If you skip this step:**
- The app will use SQLite (included by default)
- Data will be lost on deployment restarts

### 4. Add Redis (Optional, for Celery)

1. In Railway Dashboard, click "Add a service"
2. Select "Redis"
3. Railway will automatically set `REDIS_URL` environment variable

**If you skip this step:**
- Celery tasks will run synchronously (no background jobs)
- The app will still work normally

### 5. Deploy

1. Railway automatically deploys when you:
   - Push to your GitHub repository's main branch
   - Or manually trigger deployment from the Dashboard

2. View logs in Railway Dashboard to monitor deployment

## First Time Setup

After first deployment, Railway will run the `release` command from `Procfile`:
```
release: python manage.py migrate
```

This automatically:
- Runs database migrations
- Creates the necessary tables

## Accessing Your App

1. Go to Railway Dashboard
2. Click on your project
3. Find the "Domain" section
4. Click the generated URL (e.g., `crm-production-xyz.railway.app`)

## Creating Admin User (After First Deploy)

You'll need to create a superuser to access Django admin:

**Option A: Via Railway Console**
1. Go to Railway Dashboard → Your Project
2. Click "Console" tab
3. Run: `python manage.py createsuperuser`
4. Follow the prompts

**Option B: Via SSH (if available)**
```bash
railway run python manage.py createsuperuser
```

Then visit: `https://your-domain.railway.app/admin/`

## Troubleshooting

### Build Failed
Check the Build Logs in Railway Dashboard:
- Missing dependencies? Update `requirements.txt`
- Python version issue? Check `runtime.txt`
- Environment variables missing? Add them before deploying

### App Crashes After Deploy
Check the Deployment Logs:
1. Click "Logs" in Railway Dashboard
2. Look for error messages
3. Common issues:
   - Database migrations failed: Check `ALLOWED_HOSTS` setting
   - Static files missing: Run `python manage.py collectstatic` locally and commit
   - Environment variables wrong: Double-check spelling

### Static Files Not Loading
Built-in whitenoise handles this automatically. If issues persist:
```bash
python manage.py collectstatic --noinput
```

### Email Not Sending
1. Verify `SENDGRID_API_KEY` is set in Railway Variables
2. Check `DEFAULT_FROM_EMAIL` is correct
3. Review SendGrid dashboard for delivery status

## Scaling & Performance

- **Web Dyno**: Railway automatically scales worker processes
- **Celery Workers**: For background tasks (email, workflows), add custom service or use synchronous mode
- **Database**: PostgreSQL provides good performance; consider adding read replicas for scale

## Custom Domain

1. In Railway Dashboard → Project Settings
2. Add your custom domain under "Domains"
3. Update DNS records as instructed by Railway

## Environment Files Reference

See `.env.example` for all available configuration options.

## Support

- **Railway Docs**: https://docs.railway.app
- **Django Deployment**: https://docs.djangoproject.com/en/4.2/howto/deployment/
- **This Project README**: See README.md

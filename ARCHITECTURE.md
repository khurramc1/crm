# CRM System - Complete Implementation Guide

## 📊 Project Overview

A fully-featured Django-based CRM system with email automation, designed to rival HubSpot and Mailchimp. This is a production-ready application with:

- ✅ Complete contact and company management
- ✅ Sales pipeline with Kanban board
- ✅ Email template engine with merge tags
- ✅ Email campaigns with scheduling
- ✅ Email open/click tracking
- ✅ Workflow automation with triggers
- ✅ Dashboard with real-time analytics
- ✅ CSV contact import
- ✅ Celery task queue for async operations
- ✅ Docker containerization
- ✅ JWT authentication ready

## 🏗️ Architecture

### Technology Stack
```
Frontend:
  - Django Templates
  - Tailwind CSS (via crispy-tailwind)
  - HTMX for dynamic interactions
  - JavaScript for client-side features

Backend:
  - Django 4.2
  - Django REST Framework
  - Django Allauth (authentication)

Database:
  - SQLite (development)
  - PostgreSQL (production)

Async:
  - Celery 5.3
  - Redis (message broker & cache)
  - Celery Beat (scheduled tasks)

Email:
  - SendGrid API
  - Django mail backends

Deployment:
  - Docker & Docker Compose
  - Gunicorn (WSGI server)
```

### Directory Structure
```
crm/
├── .env                       # Environment configuration
├── .gitignore                 # Git ignore rules
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker services
├── Dockerfile                 # Docker image definition
├── manage.py                  # Django management
├── README.md                  # Project documentation
├── TESTING.md                 # Testing guide
├── ARCHITECTURE.md            # This file

├── crm_project/               # Main project settings
│   ├── __init__.py
│   ├── settings.py           # All Django configuration
│   ├── urls.py               # URL routing
│   ├── wsgi.py               # WSGI application
│   ├── asgi.py               # ASGI application
│   └── celery.py             # Celery configuration

├── contacts/                  # Contact management app
│   ├── models.py             # Company, Contact, Activity
│   ├── views.py              # CRUD views, import
│   ├── urls.py               # URL patterns
│   ├── forms.py              # Django forms
│   ├── admin.py              # Admin configuration
│   ├── apps.py               # App configuration
│   ├── tests.py              # Unit tests
│   ├── management/
│   │   └── commands/
│   │       └── populate_sample_data.py

├── deals/                     # Deal pipeline app
│   ├── models.py             # Pipeline, Stage, Deal
│   ├── views.py              # List, detail, Kanban views
│   ├── urls.py               # URL patterns
│   └── apps.py

├── emails/                    # Email campaigns app
│   ├── models.py             # EmailTemplate, Campaign, EmailLog
│   ├── views.py              # Template & campaign views
│   ├── urls.py               # URL patterns
│   ├── tasks.py              # Celery email tasks
│   ├── tracking_views.py     # Open/click tracking
│   ├── tracking_urls.py      # Tracking URL patterns
│   └── apps.py

├── automations/               # Workflow automation app
│   ├── models.py             # Workflow, Step, Execution
│   ├── views.py              # Workflow management views
│   ├── urls.py               # URL patterns
│   ├── tasks.py              # Celery workflow tasks
│   └── apps.py

├── dashboard/                 # Dashboard & analytics app
│   ├── models.py             # Dashboard customization
│   ├── views.py              # Dashboard view
│   ├── urls.py               # URL patterns
│   └── apps.py

├── templates/                 # HTML templates
│   ├── base.html             # Base template with sidebar
│   ├── dashboard/
│   │   └── dashboard.html
│   ├── contacts/
│   │   ├── contact_list.html
│   │   ├── contact_detail.html
│   │   ├── contact_form.html
│   │   └── ...
│   ├── deals/
│   │   ├── deal_list.html
│   │   └── ...
│   ├── emails/
│   │   ├── campaign_list.html
│   │   ├── campaign_form.html
│   │   └── ...
│   └── automations/
│       ├── workflow_list.html
│       └── ...

├── static/                    # Static files (CSS, JS)
│   └── .gitkeep

├── media/                     # User uploads
│   └── .gitkeep

├── logs/                      # Application logs
│   └── crm.log

└── db.sqlite3                 # SQLite database (dev only)
```

## 🗄️ Data Model Architecture

### Contact Management Layer
```
Company
├─ name, domain, industry, size
├─ created_at, updated_at
└─ relationships:
   ├─ Contact (1→M)
   └─ Deal (1→M)

Contact
├─ first_name, last_name, email (unique), phone
├─ company (FK), status, tags, notes
├─ assigned_to (FK → User)
├─ created_at, updated_at
└─ relationships:
   ├─ Activity (1→M)
   ├─ Deal (1→M)
   ├─ EmailLog (1→M)
   └─ WorkflowExecution (1→M)

Activity
├─ contact (FK)
├─ activity_type, title, description
├─ created_by (FK → User)
└─ created_at
```

### Sales Pipeline Layer
```
Pipeline
├─ name, description
├─ created_by (FK → User)
└─ Stage (1→M)

Stage
├─ pipeline (FK)
├─ name, order, probability
└─ Deal (1→M)

Deal
├─ title, description, value, currency
├─ contact (FK), company (FK)
├─ pipeline (FK), stage (FK)
├─ status (open/won/lost)
├─ assigned_to (FK → User)
├─ close_date, created_at, updated_at
└─ relationships:
   └─ EmailLog (1→M)
```

### Email Marketing Layer
```
EmailTemplate
├─ name, subject (with {{merge_tags}})
├─ html_body, plain_body
├─ from_email, from_name
├─ created_by (FK → User)
├─ created_at, updated_at
└─ relationships:
   ├─ Campaign (1→M)
   ├─ EmailLog (1→M)
   └─ WorkflowStep (1→M)

Campaign
├─ name, description
├─ template (FK)
├─ segment_filter (JSON: {status, tags, company_id})
├─ status (draft/scheduled/sending/sent/paused/cancelled)
├─ scheduled_at, started_at, completed_at
├─ sent_count, opened_count, clicked_count, failed_count
├─ created_by (FK → User)
├─ created_at, updated_at
└─ EmailLog (1→M)

EmailLog
├─ contact (FK), campaign (FK), template (FK)
├─ status (pending/sent/delivered/failed/bounced)
├─ sent_at, opened_at, clicked_at
├─ open_count, click_count
├─ rendered_subject, rendered_html
├─ email_id (SendGrid), error_message
├─ clicked_links (JSON)
└─ created_at, updated_at
```

### Workflow Automation Layer
```
Workflow
├─ name, description
├─ trigger_event (contact_created/deal_stage_changed/manual/tag_added/contact_updated)
├─ trigger_data (JSON)
├─ is_active
├─ created_by (FK → User)
├─ created_at, updated_at
└─ relationships:
   ├─ WorkflowStep (1→M)
   └─ WorkflowExecution (1→M)

WorkflowStep
├─ workflow (FK)
├─ order, action
├─ delay_days
├─ email_template (FK, nullable)
├─ action_data (JSON: {tag, status, user_id})
├─ is_enabled
└─ created_at

WorkflowExecution
├─ workflow (FK), contact (FK)
├─ status (pending/in_progress/completed/cancelled)
├─ started_at, completed_at
└─ WorkflowStepExecution (1→M)

WorkflowStepExecution
├─ workflow_execution (FK)
├─ step (FK)
├─ status (pending/completed/failed/skipped)
├─ scheduled_for, executed_at
├─ error_message
└─ created_at
```

## 🔄 Workflow Execution Flow

### Contact Created Workflow
```
1. New Contact Created
   ↓
2. Signal triggers workflow check
   ↓
3. automations.tasks.trigger_workflow(workflow_id, contact_id)
   ↓
4. Create WorkflowExecution (pending)
   ↓
5. For each step:
   - Create WorkflowStepExecution
   - Schedule execution via Celery (eta = now + delay_days)
   ↓
6. Celery Beat checks pending steps every 5 minutes
   ↓
7. execute_workflow_step(step_execution_id)
   ├─ If send_email: Create EmailLog, queue send_email_task
   ├─ If add_tag: Update contact.tags
   ├─ If change_status: Update contact.status
   ├─ If assign_to: Update contact.assigned_to
   ↓
8. Update WorkflowExecution status when all steps complete
```

### Email Campaign Flow
```
1. Create EmailTemplate with {{merge_tags}}
   ↓
2. Create Campaign (draft)
   ├─ Optional: Set segment_filter (JSON)
   ├─ Optional: Schedule for future date
   ↓
3. Send Campaign
   ├─ If scheduled_at in future: Save with status='scheduled'
   ├─ Else: Immediately execute
   ↓
4. process_campaign(campaign_id) - Celery task
   ├─ Get contacts matching segment_filter
   ├─ Create EmailLog for each contact (status=pending)
   ├─ Queue send_email_task for each
   ↓
5. send_email_task(email_log_id) - Celery task
   ├─ Render template with merge tags
   ├─ Add tracking pixel: <img src="/track/open/{log_id}/">
   ├─ Convert links: href="/track/click/{log_id}/?url=..."
   ├─ Send via SendGrid or Django email backend
   ├─ Store rendered_subject, rendered_html
   ├─ Update EmailLog.status='sent'
   ↓
6. User receives email and opens it
   ├─ Pixel loads: GET /track/open/{log_id}/
   ├─ Returns 1x1 transparent GIF
   ├─ Updates EmailLog.opened_at, open_count++
   ↓
7. User clicks link
   ├─ GET /track/click/{log_id}/?url=...
   ├─ Updates EmailLog.clicked_at, click_count++
   ├─ Records link in clicked_links JSON
   ├─ Redirects to original URL
   ↓
8. Campaign stats auto-update
   ├─ sent_count, opened_count, clicked_count
   ├─ Calculate open_rate, click_rate
```

## 🚀 Celery Tasks Structure

### Email Tasks (`emails/tasks.py`)
```python
send_email_task(email_log_id)
├─ Renders template with merge tags
├─ Adds tracking pixel
├─ Replaces links with tracking URLs
├─ Sends via SendGrid or Django mail
└─ Updates EmailLog & Campaign stats

process_campaign(campaign_id)
├─ Filters contacts by segment
├─ Creates EmailLog entries
└─ Queues send_email_task for each

process_scheduled_campaigns()
├─ FNRuns every 1 minute (Celery Beat)
├─ Finds campaigns with scheduled_at <= now
└─ Queues process_campaign for each
```

### Automation Tasks (`automations/tasks.py`)
```python
trigger_workflow(workflow_id, contact_id)
├─ Creates WorkflowExecution
├─ Creates WorkflowStepExecution for each step
└─ Queues execute_workflow_step with ETA

execute_workflow_step(step_execution_id)
├─ Handles action:
│  ├─ send_email: Creates EmailLog, queues send_email_task
│  ├─ add_tag: Updates contact tags
│  ├─ change_status: Updates contact status
│  ├─ assign_to: Updates assigned_to user
│  └─ wait: Just marks complete
├─ Updates WorkflowStepExecution status
└─ Completes WorkflowExecution if all steps done

process_pending_workflows()
├─ Runs every 5 minutes (Celery Beat)
├─ Finds pending steps with scheduled_for <= now
└─ Queues execute_workflow_step for each
```

## 🔐 Authentication & Authorization

### Authentication Methods
- **Django Auth:** Username/password login
- **Django Allauth:** Email registration, password reset, social auth
- **JWT Ready:** Settings configured for DRF JWT tokens

### User Roles (Implicit)
- **Superuser:** Full access (admin)
- **Staff:** Can manage certain models
- **Regular User:** Can see assigned contacts/deals, create campaigns

### Permission Model
- Contact.assigned_to = User (user can see/edit)
- Deal.assigned_to = User (user can see/edit)
- EmailLog filtered by user's contacts
- Workflows viewable  by creator

## 📊 Analytics & Reporting

### Dashboard Metrics
```
Contact Stats:
├─ Total Contacts
├─ Status breakdown (Lead/Prospect/Customer/Archived)
├─ Company count
└─ New this month

Deal Stats:
├─ Active Deal count
├─ Total pipeline value
├─ Average deal size
├─ Win/Loss rate

Email Stats:
├─ Emails sent this month
├─ Campaign count
├─ Average open rate
├─ Average click rate
└─ Top campaigns

Workflow Stats:
├─ Active workflows
├─ Completed executions
├─ Failed steps
└─ Recent activity
```

### Campaign Analytics
```
Per Campaign:
├─ Sent Count
├─ Opened Count & Rate
├─ Clicked Count & Rate
├─ Failed Count
├─ Bounced Contacts
└─ Individual email logs with:
   ├─ Status
   ├─ Open time & count
   ├─ Click time & count
   ├─ Clicked links
   └─ Error message (if failed)
```

## 🎯 API Endpoints (DRF)

### Contacts API
```
GET    /api/contacts/               - List contacts
POST   /api/contacts/               - Create contact
GET    /api/contacts/{id}/          - Contact detail
PUT    /api/contacts/{id}/          - Update contact
DELETE /api/contacts/{id}/          - Delete contact
```

### Deals API
```
GET    /api/deals/                  - List deals
POST   /api/deals/                  - Create deal
GET    /api/deals/{id}/             - Deal detail
```

### Campaigns API
```
GET    /api/campaigns/              - List campaigns
POST   /api/campaigns/              - Create campaign
GET    /api/campaigns/{id}/         - Campaign detail
POST   /api/campaigns/{id}/send/    - Send campaign
```

### Authentication
```
POST   /accounts/login/             - Login
POST   /accounts/logout/            - Logout
POST   /accounts/signup/            - Register
GET    /accounts/profile/           - User profile
```

## 🔧 Configuration Options

### Settings by Environment
```python
# .env configuration
DEBUG=True                    # Dev: True, Prod: False
SECRET_KEY=your-key           # Must be set in production
DATABASE_URL=...              # SQLite or PostgreSQL
REDIS_URL=...                 # Redis connection
SENDGRID_API_KEY=...          # For email sending
DEFAULT_FROM_EMAIL=...        # Email sender
EMAIL_BACKEND=...             # Console or SMTP
```

### Celery Configuration
```python
# In settings.py
CELERY_BROKER_URL = os.getenv('REDIS_URL')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL')
CELERY_BEAT_SCHEDULE = {
    'process-pending-workflows': {
        'task': 'automations.tasks.process_pending_workflows',
        'schedule': crontab(minute='*/5'),
    },
    'process-scheduled-campaigns': {
        'task': 'emails.tasks.process_scheduled_campaigns',
        'schedule': crontab(minute='*/1'),
    },
}
```

## 🐳 Docker Deployment

### Services in docker-compose.yml
```yaml
- web: Django application (port 8000)
- db: PostgreSQL (port 5432)
- redis: Redis broker (port 6379)
- celery_worker: Celery worker
- celery_beat: Celery Beat scheduler
```

### Volume Mounts
```
- Source: . (local)
- Target: /app (container)
- Persistence: PostgreSQL data volume
```

### Environment Variables (Docker)
```
DATABASE_URL: postgresql://user:pass@db:5432/crm_db
REDIS_URL: redis://redis:6379/0
DEBUG: True
SECRET_KEY: [set in production]
```

## 📈 Performance Optimization

### Database
- Use PostgreSQL in production
- Add indexes on:
  - Contact.email
  - Contact.status
  - Deal.status
  - EmailLog.status
  - EmailLog.campaign_id

### Caching Strategy
- Cache workflow definitions (rarely change)
- Cache email templates
- Cache company information
- Use Redis for cache/session store

### Celery Optimization
- Scale workers with: `docker-compose up -d --scale celery_worker=3`
- Monitor with Flower: `celery -A crm_project -B flower`
- Use task routing for prioritization
- Set task time limits

### Frontend Optimization
- Static file compression (Whitenoise in production)
- GZIP compression for responses
- Minimize CSS/JS
- Lazy load dashboard charts

## 🛡️ Security Best Practices

### In Production
- [ ] Set DEBUG=False
- [ ] Use strong SECRET_KEY
- [ ] Enable HTTPS/SSL
- [ ] Configure ALLOWED_HOSTS
- [ ] Use PostgreSQL with backups
- [ ] Set up firewall rules
- [ ] Monitor error logs
- [ ] Implement rate limiting
- [ ] Use CSRF protection
- [ ] Validate all user inputs
- [ ] Implement audit logging

### Sensitive Data
- [ ] Never log passwords or API keys
- [ ] Use environment variables for secrets
- [ ] Rotate credentials regularly
- [ ] Limit database user permissions
- [ ] Encrypt PII in database (optional)

## 📝 Maintenance

### Regular Tasks
- [ ] Backup PostgreSQL database daily
- [ ] Monitor Celery task queue
- [ ] Review error logs weekly
- [ ] Update dependencies monthly
- [ ] Clean up old data quarterly

### Monitoring
```bash
# Celery monitoring
celery -A crm_project events

# Or via Flower
pip install flower
celery -A crm_project -B flower  # http://localhost:5555

# Database monitoring
pg_stat_user_tables
```

## 🚀 Scaling Strategy

### Phase 1: Single Server
- Django + Celery on one server
- Shared PostgreSQL & Redis
- Good for < 1000 contacts

### Phase 2: Separate Services
- Django on app server
- Celery workers on worker server
- Shared PostgreSQL & Redis
- Good for < 10k contacts

### Phase 3: Distributed
- Multiple Django instances (load balanced)
- Multiple Celery worker pools
- Managed PostgreSQL (RDS, Cloud SQL)
- Managed Redis (ElastiCache, MemoryStore)
- Good for > 100k contacts

## 📚 Learning Resources

- Django: https://docs.djangoproject.com
- Celery: https://docs.celeryproject.org
- SendGrid: https://sendgrid.com/docs
- PostgreSQL: https://www.postgresql.org/docs
- Docker: https://docs.docker.com

---

**Last Updated:** February 21, 2026
**Version:** 1.0.0
**Status:** Production Ready ✅

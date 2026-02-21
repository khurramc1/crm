# CRM with Email Automation

A comprehensive Django-based CRM system with email automation, similar to HubSpot/Mailchimp. Built with Django REST Framework, Celery, Redis, PostgreSQL, and Tailwind CSS.

## 📋 Features

### Contact Management
- CRUD operations for contacts and companies
- Contact status tracking (Lead, Prospect, Customer, Archived)
- Tagging and segmentation
- Activity timeline (notes, emails, calls, meetings)
- CSV import functionality
- Contact assignment to sales reps

### Deal Pipeline
- Kanban-style deal board with drag-and-drop stages
- Deal value, close date, and status tracking
- Pipeline customization with configurable stages
- Deal-to-contact relationships

### Email Campaigns  
- HTML email template editor with merge tags
- Campaign scheduling and bulk sending
- Contact segmentation for targeted campaigns
- Campaign performance tracking (open rate, click rate)

### Email Automation / Drip Sequences
- Workflow automation with multiple trigger types
  - Contact Created
  - Deal Stage Changed
  - Manual Trigger
  - Tag Added
  - Contact Updated
- Multi-step sequences with delays
- Automatic email sending, tagging, and status changes
- Workflow execution tracking

### Email Tracking
- Open tracking via 1x1 pixel
- Link click tracking with redirects
- Detailed email logs with status tracking
- Campaign analytics

### Dashboard
- Real-time statistics (contacts, deals, campaigns)
- Recent activity feed
- Campaign performance overview
- Quick action buttons

## 🚀 Quick Start

### Prerequisites
- Python 3.12+
- Docker & Docker Compose (for containerized setup)
- PostgreSQL (for production)
- Redis (for Celery)

### Local Development Setup

#### 1. Clone and Setup
```bash
cd /home/khurram/Documents/vs_code_projects/crm
source .venv/bin/activate
pip install -r requirements.txt
```

#### 2. Database Setup
```bash
python manage.py migrate
python manage.py populate_sample_data
```

This creates:
- Admin user: `admin` / `admin123`
- 3 sample companies
- 3 sample contacts
- 1 email template
- 1 sales pipeline with 5 stages
- 3 sample deals
- 1 workflow

#### 3. Run Locally (without Docker)

In separate terminals:

```bash
# Terminal 1: Django development server
python manage.py runserver

# Terminal 2: Celery worker
celery -A crm_project worker -l info

# Terminal 3: Celery Beat (for scheduled tasks)
celery -A crm_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler
```

Access the application at: http://localhost:8000

Login with: `admin` / `admin123`

### Docker Setup

#### Build and Run
```bash
docker-compose up --build
```

This starts:
- Django app on http://localhost:8000
- PostgreSQL database
- Redis message broker
- Celery worker
- Celery Beat scheduler

#### Initialize Database (in Docker)
```bash
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py populate_sample_data
```

## 📚 Project Structure

```
crm/
├── crm_project/          # Project configuration
│   ├── settings.py      # Django settings
│   ├── celery.py        # Celery configuration
│   └── urls.py          # URL routing
├── contacts/            # Contact & company management
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── deals/              # Deal pipeline
│   ├── models.py
│   └── views.py
├── emails/             # Email campaigns & templates
│   ├── models.py
│   ├── views.py
│   ├── tasks.py        # Celery tasks for email sending
│   └── tracking_views.py
├── automations/        # Workflow automation
│   ├── models.py
│   ├── views.py
│   └── tasks.py        # Celery tasks for workflows
├── dashboard/          # Dashboard & analytics
│   ├── models.py
│   └── views.py
└── templates/          # HTML templates
```

## 🔧 Core Models

### Contact
```python
- first_name, last_name
- email (unique)
- phone
- company (FK)
- status: lead, prospect, customer, archived
- tags: comma-separated
- assigned_to: User
- created_at, updated_at
```

### Company
```python
- name
- domain (unique)
- industry
- size: 1-10, 11-50, 51-200, 201-500, 501-1000, 1000+
```

### Deal
```python
- title
- value (decimal)
- contact (FK), company (FK)
- pipeline (FK), stage (FK)
- status: open, won, lost
- assigned_to: User
- close_date
```

### EmailTemplate
```python
- name
- subject (with merge tags: {{first_name}}, {{company_name}}, etc)
- html_body, plain_body
- from_email, from_name
- created_by: User
```

### Campaign
```python
- name, description
- template (FK)
- segment_filter: JSON ({status, tags, company_id})
- status: draft, scheduled, sending, sent, paused, cancelled
- scheduled_at
- sent_count, opened_count, clicked_count, failed_count
```

### EmailLog
```python
- contact (FK), campaign (FK), template (FK)
- status: pending, sent, delivered, failed, bounced
- sent_at, opened_at, clicked_at
- open_count, click_count
- rendered_subject, rendered_html
- error_message
```

### Workflow
```python
- name, description
- trigger_event: contact_created, deal_stage_changed, manual, tag_added, contact_updated
- trigger_data: JSON for trigger conditions
- is_active: Boolean
```

### WorkflowStep
```python
- workflow (FK)
- order
- action: send_email, add_tag, change_status, assign_to, wait
- delay_days
- email_template (FK) - for send_email action
- action_data: JSON for action parameters
```

## 🔌 Environment Variables

Create a `.env` file with:

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=sqlite:///db.sqlite3
# For PostgreSQL: postgresql://user:password@localhost:5432/crm_db

# Redis & Celery
REDIS_URL=redis://localhost:6379/0

# Email
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
SENDGRID_API_KEY=your-sendgrid-api-key
DEFAULT_FROM_EMAIL=noreply@crm.example.com

ENVIRONMENT=development
```

## 📧 Email Sending

### Console Backend (Development)
Emails print to console instead of sending.

### SendGrid (Production)
1. Get API key from SendGrid
2. Set `SENDGRID_API_KEY` in `.env`
3. Set `DEFAULT_FROM_EMAIL` to your SendGrid verified sender

### Django SMTP
Configure standard Django email settings:
```env
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 🧪 Testing Features Locally

### Test 1: Contact CRUD
1. Go to http://localhost:8000/contacts/
2. Click "New Contact"
3. Fill in: John Test, john.test@example.com
4. Save and view the contact detail page
5. Edit and delete to test all operations

### Test 2: Email Template Creation
1. Go to http://localhost:8000/emails/templates/
2. Click "Create Template"
3. Enter:
   - Name: Test Email
   - Subject: Hello {{first_name}}!
   - Body: `<html><body>Hi {{first_name}} from {{company_name}}</body></html>`
4. Save and view template

### Test 3: Campaign Creation & Sending
1. Create an email template (see Test 2)
2. Go to http://localhost:8000/emails/campaigns/
3. Click "New Campaign"
4. Fill in:
   - Name: Welcome Campaign
   - Select the template
   - Status: draft
5. Save, then click "Send"
6. Check console or SendGrid dashboard for emails

**To test without SendGrid:**
- Leave `SENDGRID_API_KEY` empty
- Use `EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend`
- Emails will print to console

### Test 4: Email Tracking
1. Receive an email from a campaign
2. The email contains:
   - `<img src="/track/open/{log_id}/">` for open tracking
   - All links replaced with `/track/click/{log_id}/` redirects
3. Open the email or click a link
4. Check EmailLog in admin or database - status will update

### Test 5: Workflow Automation
1. Go to http://localhost:8000/automations/
2. Click "New Workflow"
3. Fill in:
   - Name: Welcome Sequence
   - Trigger: Contact Created
4. Save
5. Add workflow steps by clicking "Add Step"
   - Step 1: Send Email (immediate)
   - Step 2: Add Tag (after 3 days)
6. Create a new contact - workflow should trigger automatically
7. Check WorkflowExecution to see status

### Test 6: Deal Pipeline
1. Go to http://localhost:8000/deals/
2. View sample deals or create new ones
3. Click "Kanban View" to see drag-and-drop board
4. Drag deals between stages to move them
5. Deals triggering stage change workflow automatically

### Test 7: Dashboard
1. Go to http://localhost:8000/
2. See stats: total contacts, active deals, emails sent
3. View recent activity
4. Access all apps from sidebar

## 🗄️ Database Models Reference

### Relationships
```
Contact → Company (FK)
Contact → User (assigned_to)
Deal → Contact, Company, Pipeline, Stage, User
EmailTemplate → User (created_by)
Campaign → EmailTemplate, User (created_by)
EmailLog → Contact, Campaign, EmailTemplate
Workflow → User (created_by)
WorkflowStep → Workflow, EmailTemplate
WorkflowExecution → Workflow, Contact
WorkflowStepExecution → WorkflowExecution, WorkflowStep
```

## 🚀 Deployment

### Using Docker Compose
```bash
docker-compose up -d --build
```

### To Scale Celery Workers
```bash
docker-compose up -d --scale celery_worker=3
```

### Database Migrations
```bash
docker-compose exec web python manage.py migrate
```

### Collect Static Files
```bash
docker-compose exec web python manage.py collectstatic --noinput
```

## 🔐 Security Checklist

- [ ] Change `SECRET_KEY` in production
- [ ] Set `DEBUG=False` in production
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure ALLOWED_HOSTS properly
- [ ] Use HTTPS in production
- [ ] Set up proper logging
- [ ] Configure CSRF and CORS properly
- [ ] Use environment variables for sensitive data
- [ ] Set up periodic backups for PostgreSQL
- [ ] Monitor Celery tasks and Redis

## 📊 API Endpoints (REST Framework)

The project includes Django REST Framework configuration for:
- List/Create contacts: `/api/contacts/`
- Detail view: `/api/contacts/{id}/`
- Similar patterns for other models

## 🐛 Troubleshooting

### Celery Tasks Not Running
- Check Redis is running: `redis-cli ping`
- Check Celery worker logs
- Verify REDIS_URL is correct in settings

### Emails Not Sending
- Check EMAIL_BACKEND setting
- If using SendGrid, verify API key is set
- Check email_log status in database
- Look for error_message in EmailLog

### Migrations Failed
- Clear migration state: `rm */migrations/0*.py`
- Recreate migrations: `python manage.py makemigrations`
- Apply: `python manage.py migrate`

### Port Already in Use
- Change port: `python manage.py runserver 8001`
- Or kill process using port 8000: `lsof -ti:8000 | xargs kill -9`

## 📝 Creating Custom Workflows

### Example: Send email then add tag after 1 day
```python
workflow = Workflow.objects.create(
    name='Post Email Tag',
    trigger_event='contact_created',
    is_active=True,
    created_by=user
)

# Step 1: Send email immediately
WorkflowStep.objects.create(
    workflow=workflow,
    order=1,
    action='send_email',
    delay_days=0,
    email_template=template
)

# Step 2: Add tag after 1 day
WorkflowStep.objects.create(
    workflow=workflow,
    order=2,
    action='add_tag',
    delay_days=1,
    action_data='{"tag": "emailed"}'
)
```

## 📞 Support

For issues or questions:
1. Check Django documentation: https://docs.djangoproject.com
2. Check Celery documentation: https://docs.celeryproject.org
3. Review code comments in models.py and tasks.py
4. Check logs in `/logs/crm.log`

## 📄 License

MIT License - feel free to modify and use for your projects.

---

**Happy CRM-ing! 🚀**

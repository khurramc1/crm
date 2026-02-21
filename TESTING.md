# Testing Guide for CRM System

## Running the Complete System

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up

# In another terminal, initialize database
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py populate_sample_data

# Access at http://localhost:8000
```

### Option 2: Local Development (All Services)

```bash
# Setup
source .venv/bin/activate
python manage.py migrate
python manage.py populate_sample_data

# Terminal 1: Django
cd /home/khurram/Documents/vs_code_projects/crm
python manage.py runserver

# Terminal 2: Celery Worker  
cd /home/khurram/Documents/vs_code_projects/crm
celery -A crm_project worker -l info

# Terminal 3: Celery Beat
cd /home/khurram/Documents/vs_code_projects/crm
celery -A crm_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler

# Terminal 4: Redis (if not running)
redis-server
```

## Test Scenarios

### Test 1: Basic Contact Management
**Goal:** Verify contact CRUD operations work

Steps:
1. Login at http://localhost:8000 (admin / admin123)
2. Click "Contacts" from sidebar
3. Click "New Contact" 
4. Fill form:
   - First Name: John
   - Last Name: Smith
   - Email: john.smith@example.com
   - Phone: 555-1234
   - Company: Select "Acme Corp"
   - Status: lead
   - Tags: important, sales
5. Click Save
6. Verify contact appears in list
7. Click contact name to view detail page
8. Click Edit to modify details
9. Click Delete to remove (then confirm)

**Expected Result:** All operations complete without errors

---

### Test 2: Email Template Creation
**Goal:** Create and manage email templates with merge tags

Steps:
1. Go to http://localhost:8000/emails/templates/
2. Click "New Template"
3. Fill form:
   - Name: Monthly Newsletter
   - Subject: {{first_name}}, here's your update from {{company_name}}
   - From Name: CRM Team
   - From Email: noreply@crm.example.com
   - HTML Body:
     ```html
     <html>
     <body>
       <h1>Hi {{first_name}},</h1>
       <p>Welcome to this month's update from {{company_name}}.</p>
       <p>Email: {{email}}</p>
       <p>Best regards,<br>The CRM Team</p>
     </body>
     </html>
     ```
4. Click Save
5. View template detail
6. Click Edit to modify

**Expected Result:** Template renders correctly with merge tags shown

---

### Test 3: Campaign Creation and Sending
**Goal:** Test campaign creation, segmentation, and email sending

Steps:
1. Ensure you have an email template (see Test 2)
2. Go to http://localhost:8000/emails/campaigns/
3. Click "New Campaign"
4. Fill form:
   - Name: Q1 Outreach
   - Description: Reaching out to all leads
   - Template: Select "Monthly Newsletter" or created template
   - Segment Filter (optional): 
     ```json
     {"status": "lead", "tags": "sales"}
     ```
   - Status: draft
5. Click Save
6. Click campaign name to view detail
7. Click "Send" button
8. Observe console or SendGrid dashboard

**Check Email Sending:**
- If using `EMAIL_BACKEND=console`: Check Django terminal for email output
- If using SendGrid: Check SendGrid dashboard > Email Activity
- Database: Check `emails_emaillog` table - status should be "sent"

**Expected Result:** 
- Campaign shows sent_count > 0
- Email logs created for each contact
- Emails visible in console or SendGrid

---

### Test 4: Email Open Tracking
**Goal:** Verify open tracking via pixel

Steps:
1. Send a campaign (see Test 3)
2. Look at email output - should contain:
   ```html
   <img src="/track/open/{log_id}/" width="1" height="1" alt="">
   ```
3. Click the tracking link in console output
4. Check database - `EmailLog.opened_at` should be set
5. Campaign stats should show opened_count > 0

**Expected Result:** 
- Tracking pixel is added to emails
- Opens are recorded in database
- Campaign shows open rate

---

### Test 5: Email Click Tracking
**Goal:** Verify click tracking via redirect URLs

Steps:
1. Send a campaign with template containing links
2. Email should contain:
   ```html
   <a href="/track/click/{log_id}/?url=https://example.com">Link</a>
   ```
3. Click the tracked link in email
4. Should redirect to original URL
5. Check database - `EmailLog.clicked_at` should be set

**Expected Result:**
- Links are converted to tracking URLs
- Clicking link redirects to original URL
- Clicks recorded in database

---

### Test 6: Deal Pipeline
**Goal:** Test deal management and Kanban board

Steps:
1. Go to http://localhost:8000/deals/
2. View list of existing deals
3. Click "Kanban View" to see board
4. Drag deals between stages
5. Create new deal:
   - Click "New Deal"
   - Fill: Title, Value, Contact, Pipeline, Stage, Close Date
   - Save
6. Visit deal detail to see information

**Expected Result:**
- Deals display correctly
- Kanban board shows all stages
- Drag-and-drop works
- Deal totals update

---

### Test 7: Workflow Automation
**Goal:** Create and test automated workflows

Steps:
1. Go to http://localhost:8000/automations/
2. Click "New Workflow"
3. Fill form:
   - Name: Welcome Sequence
   - Description: Automated welcome emails for new contacts
   - Trigger Event: Contact Created
   - Is Active: Yes
4. Save
5. Add workflow steps:
   - Click "Add Step" (or go to workflow detail)
   - Step 1:
     - Order: 1
     - Action: send_email
     - Delay Days: 0
     - Template: Select an email template
   - Step 2:
     - Order: 2
     - Action: add_tag
     - Delay Days: 1
     - Action Data: `{"tag": "welcome_sent"}`
6. Save steps
7. Create a new contact
8. Check `WorkflowExecution` to see automation ran

**Expected Result:**
- Workflow executes when trigger occurs
- Email sent immediately
- Tag added after 1 day delay

---

### Test 8: Dashboard Analytics
**Goal:** Verify dashboard displays correct statistics

Steps:
1. Click dashboard icon or go to http://localhost:8000/
2. Expected stats visible:
   - Total Contacts: Should match count
   - Active Deals: Count of open deals
   - Deal Value: Sum of open deal values
   - Emails This Month: Count of sent emails
3. Click cards to drill down

**Expected Result:**
- All stats show correct values
- Recent activity displays
- Quick action buttons work

---

### Test 9: CSV Import
**Goal:** Test bulk contact import

Steps:
1. Create CSV file (sample.csv):
   ```
   first_name,last_name,email,phone,status,tags
   Alice,Johnson,alice@company.com,555-0001,prospect,"interested,tech"
   Bob,Williams,bob@company.com,555-0002,prospect,"interested,sales"
   ```
2. Go to http://localhost:8000/contacts/
3. Click "Import CSV"
4. Select file and upload
5. See import results

**Expected Result:**
- Contacts imported successfully
- Duplicates handled (by email)
- Tags preserved

---

### Test 10: Complete Email-to-Automation Flow
**Goal:** Test end-to-end workflow with email and tracking

Steps:
1. Create Email Template with HTML body:
   ```html
   <html><body>
   <p>Hi {{first_name}},</p>
   <p>Check out our <a href="https://example.com/offer">special offer</a>.</p>
   </body></html>
   ```
2. Create Campaign using template
3. Send to segment
4. Observe emails in console with:
   - Merge tags rendered
   - Open tracking pixel
   - Click tracking redirects
5. "Click" tracking link
6. View Campaign detail
   - sent_count, opened_count, clicked_count updated
7. View EmailLog records
   - status: sent
   - opened_at, clicked_at populated
   - clicked_links: JSON array of clicks

**Expected Result:**
- Complete tracking pipeline works
- All metrics updated correctly
- Data integrity maintained

---

## Monitoring & Debugging

### Check Celery Tasks
```python
# Django shell
python manage.py shell

from emails.tasks import process_campaign
from emails.models import Campaign

campaign = Campaign.objects.first()
process_campaign.delay(campaign.id)  # Queue task

# Check Celery worker terminal for task execution
```

### Check Email Logs
```python
python manage.py shell

from emails.models import EmailLog

# View all logs
for log in EmailLog.objects.all():
    print(f"{log.contact.email} - {log.status} - Opens: {log.open_count}")

# Find failed emails
EmailLog.objects.filter(status='failed')
```

### View Workflows
```python
python manage.py shell

from automations.models import Workflow, WorkflowExecution

workflow = Workflow.objects.first()
print(f"Workflow: {workflow.name}")
print(f"Trigger: {workflow.trigger_event}")
print(f"Steps: {workflow.steps.count()}")

# Check executions
for execution in workflow.executions.all():
    print(f"Contact: {execution.contact} - Status: {execution.status}")
```

### Monitor Celery
```bash
# Watch Celery tasks
celery -A crm_project events

# Or use Flower (web UI for Celery)
pip install flower
celery -A crm_project -B flower
# Access at http://localhost:5555
```

## Troubleshooting Tests

### Issue: "Celery task not executing"
- Verify Redis is running: `redis-cli ping`
- Check Celery worker logs for errors
- Verify `REDIS_URL` in .env

### Issue: "Emails not sending"
- Check `EMAIL_BACKEND` setting
- For console backend: watch Django terminal
- For SendGrid: verify API key and check dashboard
- Check EmailLog.error_message for details

### Issue: "Tracking not working"
- Verify tracking URLs in email HTML
- Test tracking URL directly: `GET /track/open/1/`
- Check EmailLog opened_at/clicked_at timestamps

### Issue: "Workflow not triggering"
- Verify workflow is_active = True
- Check trigger_event matches action
- View WorkflowExecution table for execution records
- Check Celery worker logs

---

## Performance Testing

### Load Test: Send 1000 Emails
```python
python manage.py shell

from contacts.models import Contact
from emails.models import Campaign, EmailTemplate

template = EmailTemplate.objects.first()
campaign = Campaign.objects.create(
    name="Load Test",
    template=template,
    status="draft"
)

# Note: In real world, create via UI
from emails.tasks import process_campaign
process_campaign.delay(campaign.id)

# Monitor in Celery
# Should see 1000 tasks queued and executed
```

### Monitor Performance
```bash
# Check Redis memory usage
redis-cli info memory

# Check database connections
python manage.py shell
from django.db import connection
print(f"Connections: {len(connection.queries)}")
```

---

## Success Checklist

- [ ] All CRUD operations work (contacts, deals, campaigns)
- [ ] Email templates render with merge tags
- [ ] Campaigns send successfully
- [ ] Open tracking pixel added to emails
- [ ] Click tracking redirects work
- [ ] Campaign statistics update correctly
- [ ] Workflows trigger automatically
- [ ] Workflow steps execute in sequence
- [ ] Dashboard displays correct statistics
- [ ] CSV import works
- [ ] Celery tasks execute without errors
- [ ] Database is populated with sample data

When all checks pass, your CRM system is ready for use! 🎉

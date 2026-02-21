#!/bin/bash

# CRM System Health Check & Testing Script

set -e

echo "=========================================="
echo "CRM System Health Check"
echo "=========================================="
echo ""

# Check Python
echo "✓ Checking Python..."
python --version

# Check if virtual environment is active
if [ -z "$VIRTUAL_ENV" ]; then
    echo "⚠ Virtual environment not active. Activate it:"
    echo "  source .venv/bin/activate"
    exit 1
fi

echo "✓ Virtual environment active: $VIRTUAL_ENV"
echo ""

# Check Django
echo "✓ Checking Django..."
python -c "import django; print('  Django ' + django.__version__)"

# Check critical packages
echo "✓ Checking critical packages..."
python -c "import celery; print('  Celery ' + celery.__version__)"
python -c "import redis; print('  Redis client installed')"
python -c "import sendgrid; print('  SendGrid installed')"

echo ""
echo "=========================================="
echo "Database Check"
echo "=========================================="
echo ""

# Check if migrations are applied
python manage.py migrate --check 2>/dev/null && echo "✓ Migrations up to date" || echo "⚠ Pending migrations detected"

# Count records
echo ""
echo "Database Records:"
python -c "
from django.core.management import call_command
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crm_project.settings')
import django
django.setup()
from contacts.models import Contact, Company
from deals.models import Deal, Pipeline
from emails.models import EmailTemplate, Campaign
from automations.models import Workflow

print(f'  Contacts: {Contact.objects.count()}')
print(f'  Companies: {Company.objects.count()}')
print(f'  Deals: {Deal.objects.count()}')
print(f'  Pipelines: {Pipeline.objects.count()}')
print(f'  Email Templates: {EmailTemplate.objects.count()}')
print(f'  Campaigns: {Campaign.objects.count()}')
print(f'  Workflows: {Workflow.objects.count()}')
"

echo ""
echo "=========================================="
echo "Services Check"
echo "=========================================="
echo ""

# Check Redis
echo -n "Checking Redis... "
if redis-cli ping > /dev/null 2>&1; then
    echo "✓ Connected"
    REDIS_INFO=$(redis-cli info server | grep redis_version | cut -d: -f2)
    echo "  Redis version: $REDIS_INFO"
else
    echo "✗ Not running (optional for development)"
    echo "  Start Redis: redis-server"
fi

echo ""
echo "=========================================="
echo "Quick Start Commands"
echo "=========================================="
echo ""
echo "To start the application:"
echo ""
echo "Terminal 1 - Django Dev Server:"
echo "  python manage.py runserver"
echo ""
echo "Terminal 2 - Celery Worker:"
echo "  celery -A crm_project worker -l info"
echo ""
echo "Terminal 3 - Celery Beat (optional):"
echo "  celery -A crm_project beat -l info --scheduler django_celery_beat.schedulers:DatabaseScheduler"
echo ""
echo "Then access: http://localhost:8000"
echo "Admin user: admin / admin123"
echo ""

echo "=========================================="
echo "Health Check Complete ✓"
echo "=========================================="

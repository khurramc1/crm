from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.shortcuts import redirect
from PIL import Image
from io import BytesIO
import json

from .models import EmailLog


def get_transparent_pixel():
    """Create a 1x1 transparent GIF"""
    img = Image.new('RGB', (1, 1), color=(255, 255, 255))
    img_io = BytesIO()
    img.save(img_io, format='GIF')
    img_io.seek(0)
    return img_io.getvalue()


@require_http_methods(["GET"])
def track_email_open(request, log_id):
    """
    Track email open via 1x1 pixel
    """
    try:
        email_log = EmailLog.objects.get(id=log_id)
        
        # Only count first open or count each open
        if email_log.opened_at is None:
            email_log.opened_at = timezone.now()
        
        email_log.open_count += 1
        email_log.save()
        
        # Return 1x1 transparent GIF
        response = HttpResponse(get_transparent_pixel(), content_type='image/gif')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        response['Pragma'] = 'no-cache'
        response['Expires'] = '0'
        return response
        
    except EmailLog.DoesNotExist:
        # Return 1x1 transparent GIF even if log doesn't exist
        response = HttpResponse(get_transparent_pixel(), content_type='image/gif')
        response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
        return response


@require_http_methods(["GET"])
def track_email_click(request, log_id):
    """
    Track email link click and redirect to original URL
    """
    try:
        email_log = EmailLog.objects.get(id=log_id)
        
        original_url = request.GET.get('url', '/')
        
        # Track click
        if email_log.clicked_at is None:
            email_log.clicked_at = timezone.now()
        
        email_log.click_count += 1
        
        # Store clicked links
        clicked_links = []
        if email_log.clicked_links:
            try:
                clicked_links = json.loads(email_log.clicked_links)
            except json.JSONDecodeError:
                clicked_links = []
        
        clicked_links.append({
            'url': original_url,
            'clicked_at': timezone.now().isoformat()
        })
        
        email_log.clicked_links = json.dumps(clicked_links)
        email_log.save()
        
        return redirect(original_url)
        
    except EmailLog.DoesNotExist:
        return redirect(request.GET.get('url', '/'))

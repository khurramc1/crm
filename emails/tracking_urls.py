from django.urls import path
from . import tracking_views

urlpatterns = [
    path('open/<int:log_id>/', tracking_views.track_email_open, name='track_open'),
    path('click/<int:log_id>/', tracking_views.track_email_click, name='track_click'),
]


# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Main endpoints
    path('api/jobs/start/', views.StartRenameJobView.as_view(), name='start-job'),
    path('api/jobs/', views.LocalJobsListView.as_view(), name='list-jobs'),
    path('api/jobs/<uuid:job_id>/', views.JobStatusView.as_view(), name='job-status'),
    path('api/jobs/<uuid:job_id>/status/', views.JobStatusView.as_view(), name='job-status-alt'),
    
    # YouTube operations
    path('api/youtube/', views.YouTubeAPIView.as_view(), name='youtube-api'),
    
    # Preview & Analysis
    path('api/analyze/', views.FileAnalysisView.as_view(), name='analyze-files'),
    path('api/preview/', views.QuickPreviewView.as_view(), name='quick-preview'),
    
    # Utilities
    path('api/health/', views.HealthCheckView.as_view(), name='health-check'),
    path('api/clear-cache/', views.ClearCacheView.as_view(), name='clear-cache'),
    
    # Web interface (optional)
    path('', views.HealthCheckView.as_view(), name='home'),
]
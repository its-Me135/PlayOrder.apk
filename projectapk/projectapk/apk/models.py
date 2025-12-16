from django.db import models
import uuid


class RenameJob(models.Model):
    STATUS_CHOICES = [
        ('pending', 'pending'),
        ('processing', 'processing'),
        ('completed', 'completed'),
        ('failed', 'failed'),
    ]

    job_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    playlist_url = models.TextField()
    selected_files = models.JSONField(default=list)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True)
    matches = models.JSONField(default=list)
    rename_commands = models.JSONField(default=list)
    statistics = models.JSONField(default=dict)
    playlist_title = models.CharField(max_length=255, blank=True)
    video_titles = models.JSONField(default=list)

    def __str__(self):
        return f"Job {self.id} - {self.status}"

    class Meta:
        ordering = ['-created_at']


class YouTubeCache(models.Model):
    playlist_id = models.CharField(max_length=100, unique=True)
    video_data = models.JSONField()
    fetched_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()

    def is_vaild(self):
        from django.utils import timezone
        return timezone.now() < self.expires_at


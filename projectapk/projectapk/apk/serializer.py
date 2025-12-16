from rest_framework import serializers
from .models import RenameJob

class RenameJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = RenameJob
        fields = [
            'job_id',
            'playlist_url',
            'selected_files',
            'status',
            'created_at',
            'completed_at',
            'matches',
            'rename_commands',
            'statistics',
            'playlist_title',
            'video_titles'
        ]
        read_only_fields = [
            'job_id',
            'status',
            'created_at',
            'completed_at',
            'matches',
            'rename_commands',
            'statistics'
        ]
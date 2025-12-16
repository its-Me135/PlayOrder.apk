
import json
import threading
from pathlib import Path
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.conf import settings
from django.core.cache import cache
from .mixins import LocalRenameMixin

from .models import RenameJob, YouTubeCache

class StartRenameJobView(LocalRenameMixin, APIView):
    """Start a rename job - main endpoint"""
    
    def post(self, request):
        # Get data from Flutter
        playlist_url = request.data.get('playlist_url')
        selected_files = request.data.get('selected_files', [])  # From file picker
        api_key = request.data.get('youtube_api_key')  # Flutter sends this
        
        if not playlist_url:
            return Response(
                {'error': 'Playlist URL is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not selected_files:
            return Response(
                {'error': 'No files selected'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Use provided API key or try to get from config
        if not api_key:
            api_key = self.get_youtube_api_key()
        
        if not api_key:
            return Response(
                {'error': 'YouTube API key required. Please provide one.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create job record
        job = RenameJob.objects.create(
            playlist_url=playlist_url,
            selected_files=selected_files,
            status='pending'
        )
        
        # Process in background thread (but still local)
        threading.Thread(
            target=self._process_job_background,
            args=(job.id, api_key),
            daemon=True
        ).start()
        
        return Response({
            'success': True,
            'job_id': str(job.job_id),
            'message': 'Job started processing',
            'status_endpoint': f'/api/jobs/{job.job_id}/status/'
        })

    def _process_job_background(self, job_id, api_key):
        """Process job in background thread"""
        try:
            job = RenameJob.objects.get(id=job_id)
            job.status = 'processing'
            job.save()
            
            # Get playlist videos
            videos = self.get_playlist_videos_local(api_key, job.playlist_url)
            
            # Match files to videos
            matches = self.process_local_files(job.selected_files, videos)
            
            # Prepare rename commands for Flutter
            rename_commands = []
            for match in matches:
                rename_commands.append({
                    'original_path': match['file_path'],
                    'new_name': match['suggested_name'],
                    'video_title': match['video_title'],
                    'confidence': match['score']
                })
            
            # Update job
            job.status = 'completed'
            job.video_titles = videos
            job.matches = matches
            job.rename_commands = rename_commands
            job.statistics = {
                'total_files': len(job.selected_files),
                'total_videos': len(videos),
                'matches_found': len(matches),
                'success_rate': len(matches) / len(job.selected_files) if job.selected_files else 0
            }
            job.save()
            
        except Exception as e:
            job = RenameJob.objects.get(id=job_id)
            job.status = 'failed'
            job.statistics = {'error': str(e)}
            job.save()


class JobStatusView(APIView):
    """Check job status"""
    
    def get(self, request, job_id):
        job = get_object_or_404(RenameJob, job_id=job_id)
        
        response_data = {
            'job_id': str(job.job_id),
            'status': job.status,
            'created_at': job.created_at,
            'completed_at': job.completed_at,
            'statistics': job.statistics,
            'playlist_url': job.playlist_url
        }
        
        if job.status == 'completed':
            response_data['rename_commands'] = job.rename_commands
            response_data['matches'] = job.matches[:10]  # First 10 matches
            response_data['total_matches'] = len(job.matches)
        
        return Response(response_data)


class YouTubeAPIView(LocalRenameMixin, APIView):
    """Direct YouTube API operations"""
    
    def post(self, request):
        action = request.data.get('action')
        api_key = request.data.get('api_key') or self.get_youtube_api_key()
        
        if not api_key:
            return Response(
                {'error': 'YouTube API key required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if action == 'fetch_playlist':
            playlist_url = request.data.get('playlist_url')
            if not playlist_url:
                return Response(
                    {'error': 'Playlist URL required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            try:
                videos = self.get_playlist_videos_local(api_key, playlist_url)
                return Response({
                    'success': True,
                    'total_videos': len(videos),
                    'videos': videos[:20],  # Preview first 20
                    'playlist_url': playlist_url
                })
            except Exception as e:
                return Response(
                    {'error': str(e)},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        elif action == 'save_api_key':
            # Save API key locally
            api_key = request.data.get('api_key')
            if not api_key:
                return Response({'error': 'No API key provided'})
            
            # Save to config file
            config_dir = Path.home() / '.youtube_renamer'
            config_dir.mkdir(exist_ok=True)
            
            config_file = config_dir / 'config.json'
            config = {'youtube_api_key': api_key}
            
            with open(config_file, 'w') as f:
                json.dump(config, f)
            
            return Response({'success': True, 'message': 'API key saved locally'})
        
        return Response({'error': 'Invalid action'})


class FileAnalysisView(LocalRenameMixin, APIView):
    """Analyze files before processing"""
    
    def post(self, request):
        selected_files = request.data.get('files', [])
        
        if not selected_files:
            return Response({'error': 'No files provided'})
        
        analysis = {
            'total_files': len(selected_files),
            'by_extension': {},
            'suggestions': [],
            'estimated_time': f"{len(selected_files) * 0.2} seconds"
        }
        
        # Analyze file extensions
        extensions = {}
        for file_info in selected_files:
            filename = file_info.get('name', '')
            if '.' in filename:
                ext = filename.split('.')[-1].lower()
                extensions[ext] = extensions.get(ext, 0) + 1
        
        analysis['by_extension'] = extensions
        
        # Generate suggestions
        if len(selected_files) > 50:
            analysis['suggestions'].append({
                'type': 'warning',
                'message': 'Large number of files selected. Processing may take time.'
            })
        
        if 'mp3' in extensions or 'm4a' in extensions:
            analysis['suggestions'].append({
                'type': 'info',
                'message': 'Audio files detected. Consider music playlists.'
            })
        
        return Response(analysis)


class QuickPreviewView(LocalRenameMixin, APIView):
    """Quick preview without creating job"""
    
    def post(self, request):
        playlist_url = request.data.get('playlist_url')
        selected_files = request.data.get('files', [])
        api_key = request.data.get('api_key')
        
        if not api_key:
            api_key = self.get_youtube_api_key()
        
        if not all([playlist_url, selected_files, api_key]):
            return Response(
                {'error': 'Missing required parameters'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get videos
            videos = self.get_playlist_videos_local(api_key, playlist_url, use_cache=True)
            
            # Find matches for preview
            preview_matches = []
            for i, video_title in enumerate(videos[:5]):  # First 5 videos
                for file_info in selected_files[:10]:  # First 10 files
                    filename = file_info.get('name', '')
                    score, _ = self.calculate_similarity_score(video_title, filename)
                    
                    if score > 0.5:
                        preview_matches.append({
                            'video': video_title,
                            'file': filename,
                            'score': score,
                            'suggested_name': f"{i+1:03d} - {video_title[:30]}"
                        })
                        break  # One match per video for preview
            
            return Response({
                'preview': True,
                'total_videos': len(videos),
                'total_files': len(selected_files),
                'sample_matches': preview_matches[:5],
                'confidence': 'high' if preview_matches else 'low'
            })
            
        except Exception as e:
            return Response(
                {'error': str(e), 'preview': False},
                status=status.HTTP_400_BAD_REQUEST
            )


class LocalJobsListView(generics.ListAPIView):
    """List all local jobs"""
    from .models import RenameJob
    from .serializer import RenameJobSerializer
    
    queryset = RenameJob.objects.all().order_by('-created_at')
    serializer_class = RenameJobSerializer


# ============================================================================
# UTILITY ENDPOINTS
# ============================================================================

class HealthCheckView(APIView):
    """Check if local server is running"""
    
    def get(self, request):
        return Response({
            'status': 'running',
            'service': 'YouTube Renamer Local API',
            'version': '1.0.0',
            'database': 'connected' if RenameJob.objects.exists() else 'empty'
        })


class ClearCacheView(APIView):
    """Clear local cache"""
    
    def post(self, request):
        # Clear YouTube cache
        YouTubeCache.objects.all().delete()
        
        # Clear Django cache
        cache.clear()
        
        return Response({
            'success': True,
            'message': 'Local cache cleared',
            'cleared': {
                'youtube_cache': True,
                'django_cache': True
            }
        })
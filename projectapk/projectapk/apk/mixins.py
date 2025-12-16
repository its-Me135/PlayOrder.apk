# mixins.py
import os
import re
import json
from pathlib import Path
from difflib import SequenceMatcher
from googleapiclient.discovery import build
from .models import YouTubeCache

class LocalRenameMixin:
    """
    Mixin containing all renaming helper methods.
    Can be inherited by any view that needs renaming functionality.
    """
    
    def get_youtube_api_key(self):
        config_path = Path.home()/ '.youtube_renamer' / 'config.json'
        if config_path.exists():
            with open(config_path, 'r') as f:
                config = json.load(f)
                return config.get('youtube_api_key')
            
        return os.environ.get('YOUTUBE_API_KEY')

    def clean_titles(self, title):
        tags_to_remove = [
            r'\[[^\]]*\]', r'\([^\)]*\)',
            r'1080p', r'720p', r'480p', r'HD', r'FULL HD', r'4K', r'60FPS',
            r'official', r'official video', r'official audio',
            r'video', r'audio', r'lyrics', r'lyric video',
            r'MP3', r'MP4', r'M4A', r'WEBRip', r'x264',
            r'download', r'free download', r'stream',
            r'\(?ft\.?[^\)]*\)?', r'\(?feat\.?[^\)]*\)?',
        ]
        
        cleaned = title.lower()
        for tag in tags_to_remove:
            cleaned = re.sub(tag, '', cleaned, flags=re.IGNORECASE)
        
        cleaned = re.sub(r'[^\w\s]', ' ', cleaned)
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        
        return cleaned
        pass
    
    def extract_possible_numbers(self, text):
        patterns = [
            r'\b(\d+\.\d+)\b',
            r'\b(\d+)\s*-\s*\d+',
            r'#\s*(\d+)',
            r'episode\s*(\d+)',
            r'part\s*(\d+)',
            r'\b(\d+)\s*:\s*',
            r'^(\d+)\.\s+',
            r'\b(\d+)\b',
        ]
        
        numbers = []
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            numbers.extend(matches)
        
        return numbers
        pass
    
    def calculate_similarity_score(self, playlist_title, filename):
        clean_playlist = self.clean_titles(playlist_title)
        clean_filename = self.clean_titles(filename)
        
        similarity = SequenceMatcher(None, clean_playlist, clean_filename).ratio()
        
        playlist_words = set(clean_playlist.split())
        filename_words = set(clean_filename.split())
        
        if playlist_words and filename_words:
            common_words = playlist_words.intersection(filename_words)
            word_overlap = len(common_words) / len(playlist_words.union(filename_words))
        else:
            word_overlap = 0
        
        playlist_numbers = self.extract_possible_numbers(playlist_title)
        filename_numbers = self.extract_possible_numbers(filename)
        number_match = 1.0 if (playlist_numbers and filename_numbers and 
                              any(pn in filename_numbers for pn in playlist_numbers)) else 0
        
        substring_match = 1 if (clean_playlist in clean_filename or 
                               clean_filename in clean_playlist) else 0
        
        combined_score = (
            similarity * 0.4 +
            word_overlap * 0.3 +
            number_match * 0.2 +
            substring_match * 0.1
        )
        
        return combined_score, {
            'similarity': similarity,
            'word_overlap': word_overlap,
            'number_match': number_match,
            'substring_match': substring_match
        }
        pass
    
    def get_playlist_videos_local(self, api_key, playlist_url, use_cache=True):
        youtube = build('youtube', 'v3', developerKey=api_key)
        
        if 'list=' in playlist_url:
            playlist_id = playlist_url.split('list=')[-1].split('&')[0]
        else:
            playlist_id = playlist_url
        
        if use_cache:
            cache_entry = YouTubeCache.objects.filter(playlist_id=playlist_id).first()
            if cache_entry and cache_entry.is_valid():
                return cache_entry.video_data
            
        
        youtube = build('youtube', 'v3', developerKey=api_key)
        videos = []
        nextPageToken = None
        
        try:
            while True:
                pl_request = youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=nextPageToken
                )
                pl_response = pl_request.execute()
                
                for item in pl_response['items']:
                    video_title = item['snippet']['title']
                    videos.append(video_title)
                
                nextPageToken = pl_response.get('nextPageToken')
                if not nextPageToken:
                    break

            from django.utils import timezone
            from datetime import timedelta

            YouTubeCache.objects.update_or_create(
                playlist_id=playlist_id,
                defaults={
                    'video_data': videos,
                    'expires_at': timezone.now() + timedelta(hours=24)
                }
            )
            
            return videos
        except Exception as e:
            cache_entry = YouTubeCache.objects.filter(playlist_id=playlist_id).first()
            if cache_entry:
                return cache_entry.video_data
            raise e
    
    def process_local_files(self, selected_files, playlist_videos):
        """Match local files to playlist videos"""
        matches = []
        
        for video_index, video_title in enumerate(playlist_videos):
            best_match = None
            best_score = 0
            
            for file_info in selected_files:
                filename = file_info.get('name', '')
                if not filename:
                    continue
                
                score, details = self.calculate_similarity_score(video_title, filename)
                
                if score > best_score and score > 0.3:  # Threshold
                    best_score = score
                    best_match = {
                        'video_index': video_index,
                        'video_title': video_title,
                        'original_name': filename,
                        'file_path': file_info.get('path', ''),
                        'score': score,
                        'details': details,
                        'suggested_name': f"{video_index+1:03d} - {video_title[:50]}"
                    }
            
            if best_match:
                matches.append(best_match)
        
        return matches

    
    #def _process_job_async(self, job_id):
       # def process():
           # apps.populate(settings.INSTALLED_APPS)
           # from .models import RenameJob
            
           # job = RenameJob.objects.get(id=job_id)
           # job.status = 'processing'
           # job.save()
            
           # try:
              #  result = self._rename_playlist(job.folder_path, job.playlist_url)
             #   job.status = 'completed'
            #    job.result_summary = result
            #    job.save()
           # except Exception as e:
          #      job.status = 'failed'
         #       job.result_summary = {'error': str(e)}
        #        job.save()
        
        #thread = threading.Thread(target=process)
        #thread.daemon = True
       # thread.start() 


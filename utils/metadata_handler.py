"""File metadata handler"""
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
from rich.console import Console

console = Console()


class MetadataHandler:
    """Handles file metadata operations"""
    
    @staticmethod
    def set_video_metadata(file_path: str, metadata: Dict):
        """
        Set video file metadata
        
        Args:
            file_path: Path to video file
            metadata: Dictionary containing metadata fields
        """
        try:
            from mutagen.mp4 import MP4, MP4Cover
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, COMM
            from mutagen.mp3 import MP3
            
            file_ext = Path(file_path).suffix.lower()
            
            if file_ext in ['.mp4', '.m4a', '.m4v']:
                MetadataHandler._set_mp4_metadata(file_path, metadata)
            elif file_ext == '.mp3':
                MetadataHandler._set_mp3_metadata(file_path, metadata)
            else:
                console.print(f"[yellow]Metadata not supported for {file_ext} files[/yellow]")
                
        except ImportError:
            console.print("[yellow]mutagen not installed. Install with: pip install mutagen[/yellow]")
        except Exception as e:
            console.print(f"[yellow]Could not set metadata: {e}[/yellow]")
    
    @staticmethod
    def _set_mp4_metadata(file_path: str, metadata: Dict):
        """Set MP4/M4A metadata"""
        try:
            from mutagen.mp4 import MP4, MP4Cover
            
            video = MP4(file_path)
            
            # Title
            if 'title' in metadata:
                video['\xa9nam'] = metadata['title']
            
            # Artist/Uploader
            if 'artist' in metadata:
                video['\xa9ART'] = metadata['artist']
            
            # Album/Playlist
            if 'album' in metadata:
                video['\xa9alb'] = metadata['album']
            
            # Year
            if 'year' in metadata:
                video['\xa9day'] = metadata['year']
            
            # Description
            if 'description' in metadata:
                video['\xa9cmt'] = metadata['description']
            
            # URL
            if 'url' in metadata:
                video['purl'] = metadata['url']
            
            # Track number
            if 'track' in metadata:
                video['trkn'] = [(metadata['track'], 0)]
            
            video.save()
            console.print(f"[dim]✓ Set MP4 metadata for {Path(file_path).name}[/dim]")
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not set MP4 metadata: {e}[/yellow]")
    
    @staticmethod
    def _set_mp3_metadata(file_path: str, metadata: Dict):
        """Set MP3 metadata"""
        try:
            from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, COMM, TRCK, WXXX
            from mutagen.mp3 import MP3
            
            # Create ID3 tag if it doesn't exist
            try:
                audio = ID3(file_path)
            except:
                audio = MP3(file_path)
                audio.add_tags()
                audio = ID3(file_path)
            
            # Title
            if 'title' in metadata:
                audio['TIT2'] = TIT2(encoding=3, text=metadata['title'])
            
            # Artist/Uploader
            if 'artist' in metadata:
                audio['TPE1'] = TPE1(encoding=3, text=metadata['artist'])
            
            # Album/Playlist
            if 'album' in metadata:
                audio['TALB'] = TALB(encoding=3, text=metadata['album'])
            
            # Year
            if 'year' in metadata:
                audio['TDRC'] = TDRC(encoding=3, text=metadata['year'])
            
            # Description
            if 'description' in metadata:
                audio['COMM'] = COMM(encoding=3, lang='eng', desc='', text=metadata['description'])
            
            # Track number
            if 'track' in metadata:
                audio['TRCK'] = TRCK(encoding=3, text=str(metadata['track']))
            
            # URL
            if 'url' in metadata:
                audio['WXXX'] = WXXX(encoding=3, desc='Source', url=metadata['url'])
            
            audio.save()
            console.print(f"[dim]✓ Set MP3 metadata for {Path(file_path).name}[/dim]")
            
        except Exception as e:
            console.print(f"[yellow]Warning: Could not set MP3 metadata: {e}[/yellow]")
    
    @staticmethod
    def extract_metadata(video_info: Dict, index: int = 0, playlist_title: str = "") -> Dict:
        """
        Extract metadata from video info
        
        Args:
            video_info: Video information dictionary
            index: Position in playlist
            playlist_title: Playlist name
            
        Returns:
            Dictionary of metadata fields
        """
        metadata = {}
        
        # Title
        if 'title' in video_info:
            metadata['title'] = video_info['title']
        
        # Artist/Uploader
        if 'uploader' in video_info:
            metadata['artist'] = video_info['uploader']
        elif 'channel' in video_info:
            metadata['artist'] = video_info['channel']
        
        # Album/Playlist
        if playlist_title:
            metadata['album'] = playlist_title
        elif 'playlist' in video_info:
            metadata['album'] = video_info['playlist']
        
        # Year
        if 'upload_date' in video_info and video_info['upload_date']:
            try:
                date_str = video_info['upload_date']
                year = date_str[:4]
                metadata['year'] = year
            except:
                pass
        
        # Description
        if 'description' in video_info and video_info['description']:
            # Limit description length
            desc = video_info['description'][:500]
            metadata['description'] = desc
        
        # URL
        if 'webpage_url' in video_info:
            metadata['url'] = video_info['webpage_url']
        
        # Track number
        if index > 0:
            metadata['track'] = index
        
        return metadata

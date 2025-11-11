"""File renaming utilities"""
import re
import unicodedata


class FileRenamer:
    """Handles file renaming with template system"""

    @staticmethod
    def normalize_title(title: str, sentence_case: bool = True) -> str:
        """
        Normalize video title to clean format
        
        Args:
            title: Original title
            sentence_case: Convert to sentence case (True) or keep original case (False)
        """
        # Remove emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        title = emoji_pattern.sub('', title)
        
        # Normalize unicode characters (convert accented chars to normal)
        title = unicodedata.normalize('NFKD', title)
        title = title.encode('ascii', 'ignore').decode('ascii')
        
        # Remove special characters but keep letters, numbers, spaces, and basic punctuation
        # Keep: letters, numbers, spaces, hyphens, apostrophes
        title = re.sub(r"[^\w\s\-']", ' ', title)
        
        # Remove extra whitespace
        title = ' '.join(title.split())
        
        # Convert to sentence case if requested
        if sentence_case:
            # Split into words
            words = title.split()
            if words:
                # Capitalize first word
                words[0] = words[0].capitalize()
                
                # Lowercase remaining words except for acronyms (all caps words)
                for i in range(1, len(words)):
                    # Keep acronyms uppercase (words with 2+ chars all uppercase)
                    if len(words[i]) > 1 and words[i].isupper():
                        continue
                    # Keep words with mixed case (likely proper nouns)
                    elif any(c.isupper() for c in words[i][1:]):
                        continue
                    else:
                        words[i] = words[i].lower()
                
                title = ' '.join(words)
        
        # Remove leading/trailing hyphens and spaces
        title = title.strip('- ')
        
        return title

    @staticmethod
    def sanitize_filename(filename: str, normalize: bool = True) -> str:
        """
        Remove invalid characters and normalize filename
        
        Args:
            filename: Original filename
            normalize: Apply title normalization (sentence case, etc.)
        """
        if normalize:
            filename = FileRenamer.normalize_title(filename)
        else:
            # Just remove emojis without normalization
            emoji_pattern = re.compile("["
                u"\U0001F600-\U0001F64F"
                u"\U0001F300-\U0001F5FF"
                u"\U0001F680-\U0001F6FF"
                u"\U0001F1E0-\U0001F1FF"
                u"\U00002702-\U000027B0"
                u"\U000024C2-\U0001F251"
                "]+", flags=re.UNICODE)
            filename = emoji_pattern.sub('', filename)
        
        # Remove or replace invalid characters for filesystems
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')
        
        # Remove extra whitespace
        filename = ' '.join(filename.split())
        
        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')
        
        # Limit length (leave room for extension and index)
        max_length = 200
        if len(filename) > max_length:
            filename = filename[:max_length].strip()
        
        return filename

    @staticmethod
    def apply_template(template: str, title: str, uploader: str = "Unknown",
                      upload_date: str = "Unknown", index: int = 0,
                      playlist_title: str = "", video_id: str = "unknown",
                      normalize: bool = True) -> str:
        """
        Apply filename template with placeholders
        
        Args:
            template: Filename template with placeholders
            title: Video title
            uploader: Channel/uploader name
            upload_date: Upload date
            index: Position in playlist
            playlist_title: Playlist name
            video_id: YouTube video ID
            normalize: Apply title normalization
        """
        placeholders = {
            'title': FileRenamer.sanitize_filename(title, normalize),
            'uploader': FileRenamer.sanitize_filename(uploader, normalize),
            'date': upload_date,
            'index': index,
            'playlist': FileRenamer.sanitize_filename(playlist_title, normalize),
            'video_id': video_id,
        }

        # Apply template
        filename = template
        for key, value in placeholders.items():
            pattern = f"{{{key}}}"
            if pattern in filename:
                filename = filename.replace(pattern, str(value))

            # Handle format specifiers like {index:03d}
            format_pattern = re.compile(r'\{' + key + r':([^}]+)\}')
            match = format_pattern.search(filename)
            if match:
                format_spec = match.group(1)
                if key == 'index':
                    formatted_value = f"{value:{format_spec}}"
                else:
                    formatted_value = str(value)
                filename = format_pattern.sub(formatted_value, filename)

        return FileRenamer.sanitize_filename(filename, normalize=False)

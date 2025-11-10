"""File renaming utilities"""
import re


class FileRenamer:
    """Handles file renaming with template system"""

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Remove invalid characters and normalise filename"""
        # Remove emojis
        emoji_pattern = re.compile("["
            u"\U0001F600-\U0001F64F"  # emoticons
            u"\U0001F300-\U0001F5FF"  # symbols & pictographs
            u"\U0001F680-\U0001F6FF"  # transport & map symbols
            u"\U0001F1E0-\U0001F1FF"  # flags
            u"\U00002702-\U000027B0"
            u"\U000024C2-\U0001F251"
            "]+", flags=re.UNICODE)
        filename = emoji_pattern.sub('', filename)

        # Remove or replace invalid characters
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '')

        # Remove extra whitespace
        filename = ' '.join(filename.split())

        # Remove leading/trailing dots and spaces
        filename = filename.strip('. ')

        # Normalise punctuation
        filename = re.sub(r'[!]+', '!', filename)
        filename = re.sub(r'[?]+', '?', filename)
        filename = re.sub(r'\.{2,}', '.', filename)

        return filename

    @staticmethod
    def apply_template(template: str, title: str, uploader: str = "Unknown",
                      upload_date: str = "Unknown", index: int = 0,
                      playlist_title: str = "", video_id: str = "unknown") -> str:
        """Apply filename template with placeholders"""
        placeholders = {
            'title': FileRenamer.sanitize_filename(title),
            'uploader': FileRenamer.sanitize_filename(uploader),
            'date': upload_date,
            'index': index,
            'playlist': FileRenamer.sanitize_filename(playlist_title),
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

        return FileRenamer.sanitize_filename(filename)

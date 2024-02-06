import json
import os
import sys
import logging
import shutil
import schedule
import time
from pytube import YouTube, Playlist, Channel
from tqdm import tqdm
from PyInquirer import prompt, Separator
from colorama import Fore, Style, init

# Initialize colorama for colored console output
init(autoreset=True)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class YouTubeDownloader:
    def __init__(self, config_file: str = 'config.json') -> None:
        self.config_file = config_file
        self.config = self.load_config(config_file)
        self.menu()

    def load_config(self, config_file: str) -> dict:
        try:
            if not os.path.exists(config_file):
                logging.info("No config file found, creating a new one.")
                return {}
            with open(config_file, 'r') as file:
                return json.load(file)
        except Exception as e:
            logging.error(f"Failed to load config: {e}")
            return {}

    def save_config(self) -> None:
        try:
            with open(self.config_file, 'w') as file:
                json.dump(self.config, file, indent=4)
            print(Fore.GREEN + "Configuration saved.")
        except Exception as e:
            print(Fore.RED + f"Failed to save config: {e}")
            logging.error(f"Failed to save config: {e}")

    def get_config_value(self, key: str, prompt_msg: str) -> str:
        if key in self.config:
            return self.config[key]
        else:
            value = input(prompt_msg)
            self.config[key] = value
            return value

    def check_disk_space(self, required_space: int, download_path: str) -> bool:
        try:
            free_space = shutil.disk_usage(download_path).free
            if free_space < required_space:
                print(Fore.RED + "Insufficient disk space for download.")
                return False
            return True
        except Exception as e:
            print(Fore.RED + f"Failed to check disk space: {e}")
            logging.error(f"Failed to check disk space: {e}")
            return False

    def download_video(self, video_url: str, quality: str, download_path: str) -> None:
        yt = YouTube(video_url)
        stream = self.get_best_stream(yt, quality)
        if stream:
            if self.check_disk_space(stream.filesize, download_path):
                self.download_stream(stream, yt.title, download_path)
            else:
                print(Fore.RED + "Download aborted due to insufficient disk space.")
        else:
            print(Fore.RED + "No suitable stream found for the requested quality.")

    def download_playlist(self, playlist_url: str, quality: str, download_path: str) -> None:
        playlist = Playlist(playlist_url)
        total_size = sum(self.get_best_stream(YouTube(url), quality).filesize for url in playlist.video_urls if self.get_best_stream(YouTube(url), quality))
        if self.check_disk_space(total_size, download_path):
            for video_url in tqdm(playlist.video_urls, desc="Downloading Playlist"):
                self.download_video(video_url, quality, download_path)
        else:
            print(Fore.RED + "Download aborted due to insufficient disk space.")

    def get_best_stream(self, yt: YouTube, quality: str):
        stream = yt.streams.filter(res=quality, file_extension='mp4').first()
        if not stream:
            stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
        return stream

    def download_stream(self, stream, title: str, download_path: str) -> None:
        with tqdm(desc=f"Downloading {title}", total=stream.filesize, unit='B', unit_scale=True, unit_divisor=1024) as pbar:
            stream.download(output_path=download_path, filename=title, on_progress_callback=lambda chunk, _, total: pbar.update(len(chunk)))
        print(Fore.GREEN + f"'{title}' downloaded successfully.")

    def handle_channel(self, channel_url: str, quality: str, download_path: str) -> None:
        channel = Channel(channel_url)
        playlists = list(channel.playlists)
        playlist_choices = [{'name': pl.title, 'value': pl.playlist_url} for pl in playlists]

        questions = [
            {
                'type': 'checkbox',
                'qmark': '>',
                'message': 'Select playlists to download:',
                'name': 'selected_playlists',
                'choices': playlist_choices,
                'validate': lambda answer: 'You must choose at least one playlist.' if len(answer) == 0 else True
            }
        ]

        selected_playlists = prompt(questions)['selected_playlists']
        for playlist_url in selected_playlists:
            self.download_playlist(playlist_url, quality, os.path.join(download_path, channel.channel_name))

    def auto_download_task(self):
        for item in self.config.get('auto_download', []):
            if "playlist" in item:
                self.download_playlist(item, self.config.get('quality', '1080p'), self.config.get('download_path', './downloads'))
            elif "channel" in item:
                self.handle_channel(item, self.config.get('quality', '1080p'), self.config.get('download_path', './downloads'))
            else:
                logging.warning(f"Unsupported URL in auto_download: {item}")

    def schedule_downloads(self, interval=1):
        schedule.every(interval).hours.do(self.auto_download_task)
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def menu(self) -> None:
        print("\nWelcome to YouTubeDownloader")
        action_question = [
            {
                'type': 'list',
                'name': 'action',
                'message': 'What do you want to do?',
                'choices': ['Download a single video', 'Download a playlist', 'Download from a channel']
            }
        ]
        action_answer = prompt(action_question)

        url_question = [{'type': 'input', 'name': 'url', 'message': 'Enter the URL:'}]
        url_answer = prompt(url_question)['url']

        quality = self.get_config_value('quality', 'Enter preferred video quality (e.g., 720p, 1080p): ')
        download_path = self.get_config_value('download_path', 'Enter download path (./downloads): ')

        if action_answer['action'] == 'Download a single video':
            self.download_video(url_answer, quality, download_path)
        elif action_answer['action'] == 'Download a playlist':
            self.download_playlist(url_answer, quality, download_path)
        elif action_answer['action'] == 'Download from a channel':
            self.handle_channel(url_answer, quality, download_path)

        if input("Update config with these settings? (y/n): ").lower() == 'y':
            self.save_config()

if __name__ == '__main__':
    downloader = YouTubeDownloader()

    # This will block; consider running in a separate thread
    downloader.schedule_downloads()

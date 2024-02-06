import json
import os
import sys
import logging
from pytube import YouTube, Playlist, Channel
from tqdm import tqdm
import inquirer

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

class YouTubeDownloader:
    def __init__(self, config_file: str = 'config.json') -> None:
        self.config_file = config_file
        self.config = self.load_config(config_file)
        self.menu()

    def load_config(self, config_file: str) -> dict:
        if not os.path.exists(config_file):
            logging.info("No config file found, creating a new one.")
            return {}
        with open(config_file, 'r') as file:
            return json.load(file)

    def save_config(self) -> None:
        with open(self.config_file, 'w') as file:
            json.dump(self.config, file, indent=4)
        logging.info("Configuration saved.")

    def check_disk_space(self, required_space: int, download_path: str) -> bool:
        free_space = shutil.disk_usage(download_path).free
        if free_space < required_space:
            logging.warning("Insufficient disk space for download.")
            return False
        return True

    def download_video(self, video_url: str, quality: str, download_path: str) -> None:
        yt = YouTube(video_url)
        stream = self.get_best_stream(yt, quality)
        if stream:
            if self.check_disk_space(stream.filesize, download_path):
                self.download_stream(stream, title=yt.title, download_path=download_path)
            else:
                logging.error("Download aborted due to insufficient disk space.")
        else:
            logging.error("No suitable stream found.")

    def get_playlist_size(self, playlist_url: str, quality: str) -> int:
        playlist = Playlist(playlist_url)
        total_size = 0
        for video_url in playlist.video_urls:
            yt = YouTube(video_url)
            stream = self.get_best_stream(yt, quality)
            if stream:
                total_size += stream.filesize
        return total_size

    def download_playlist(self, playlist_url: str, quality: str, download_path: str) -> None:
        playlist = Playlist(playlist_url)
        total_size = self.get_playlist_size(playlist_url, quality)
        if self.check_disk_space(total_size, download_path):
            for video_url in tqdm(playlist.video_urls, desc="Downloading Playlist"):
                self.download_video(video_url, quality, download_path)
        else:
            logging.error("Download aborted due to insufficient disk space.")

    def handle_channel(self, channel_url: str, quality: str) -> None:
        channel = Channel(channel_url)
        playlists = channel.playlists
        playlist_choices = [{'name': pl.title, 'value': pl.playlist_url} for pl in playlists]

        questions = [
            inquirer.Checkbox('playlists',
            message="Select playlists to download",
            choices=playlist_choices,
            carousel=True)
        ]

        selected_playlists = inquirer.prompt(questions)['playlists']

        for playlist_url in selected_playlists:
            self.download_playlist(playlist_url, quality, os.path.join(self.config['download_path'], channel.channel_name))

    def menu(self) -> None:
        print("Welcome to YouTubeDownloader")
        print("1. Download a single video")
        print("2. Download a playlist")
        print("3. Download from a channel")
        choice = input("Enter your choice (1-3): ")

        if choice not in ['1', '2', '3']:
            logging.error("Invalid choice. Exiting.")
            return

        url = input("Enter the URL: ")
        quality = self.get_config_value('quality', 'Enter preferred video quality (e.g., 720p, 1080p): ')
        download_path = self.get_config_value('download_path', 'Enter download path (./downloads): ')

        if choice == '1':
            self.download_video(url, quality, download_path)
        elif choice == '2':
            self.download_playlist(url, quality, download_path)
        elif choice == '3':
            self.handle_channel(url, quality)

        if input("Update config with these settings? (y/n): ").lower() == 'y':
            self.save_config()

# Usage
YouTubeDownloader()

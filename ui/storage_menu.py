"""Storage menu"""
from pathlib import Path
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

console = Console()


class StorageMenu:
    """Storage provider management menu"""
    
    def __init__(self):
        from managers.config_manager import ConfigManager
        from utils.storage_providers import StorageManager
        
        self.config_manager = ConfigManager()
        self.storage_manager = StorageManager()
    
    def show(self):
        """Display storage management menu"""
        console.print("\n")
        
        # Current default storage
        default_storage = self.config_manager.config.default_storage
        
        status_panel = Panel(
            f"[bold]Default Storage:[/bold] {default_storage}\n"
            f"[cyan]Configured Providers:[/cyan] {len(self.config_manager.config.storage_providers)}",
            title="[bold]Storage Configuration[/bold]",
            border_style="cyan"
        )
        console.print(status_panel)
        
        # List storage providers
        if self.config_manager.config.storage_providers:
            storage_table = Table(title="Storage Providers", show_header=True)
            storage_table.add_column("Name", style="cyan")
            storage_table.add_column("Type", style="yellow")
            storage_table.add_column("Status", style="green")
            storage_table.add_column("Video Quality", style="magenta")
            storage_table.add_column("Audio Quality", style="blue")
            
            for name, config_dict in self.config_manager.config.storage_providers.items():
                from managers.config_manager import StorageConfig
                storage_config = StorageConfig.from_dict(config_dict)
                
                provider_type = storage_config.provider_type.upper()
                status = "Enabled" if storage_config.enabled else "Disabled"
                video_q = storage_config.video_quality or "Default"
                audio_q = storage_config.audio_quality or "Default"
                
                storage_table.add_row(name, provider_type, status, video_q, audio_q)
            
            console.print("\n")
            console.print(storage_table)
        
        options = [
            ("1", "Add FTP storage"),
            ("2", "Add SFTP storage"),
            ("3", "Add Google Drive storage"),
            ("4", "Add Dropbox storage"),
            ("5", "Add OneDrive storage"),
            ("6", "Configure storage provider"),
            ("7", "Remove storage provider"),
            ("8", "Set default storage"),
            ("9", "Test storage connections"),
            ("0", "Back to main menu")
        ]
        
        option_text = "\n".join([f"  {num}. {desc}" for num, desc in options])
        console.print(f"\n{option_text}\n")
        
        choice = Prompt.ask(
            "[bold cyan]Select an option[/bold cyan]",
            choices=[num for num, _ in options],
            default="0"
        )
        
        return choice
    
    @staticmethod
    def add_ftp_storage(config_manager):
        """Add FTP storage provider"""
        from managers.config_manager import StorageConfig
        
        console.print("\n[cyan]Add FTP Storage[/cyan]")
        
        name = Prompt.ask("Storage name", default="ftp_server")
        host = Prompt.ask("FTP host")
        port = IntPrompt.ask("FTP port", default=21)
        username = Prompt.ask("Username", default="")
        password = Prompt.ask("Password (leave blank for anonymous)", default="", password=True)
        base_path = Prompt.ask("Base path", default="/")
        
        # Quality settings
        console.print("\n[yellow]Quality Settings (leave blank to use defaults)[/yellow]")
        video_quality = Prompt.ask(
            "Video quality override (best/1080p/720p/480p/360p)",
            default=""
        )
        audio_quality = Prompt.ask(
            "Audio quality override (320/192/128)",
            default=""
        )
        
        storage_config = StorageConfig(
            enabled=True,
            provider_type="ftp",
            host=host,
            port=port,
            username=username,
            password=password,
            base_path=base_path,
            video_quality=video_quality if video_quality else None,
            audio_quality=audio_quality if audio_quality else None
        )
        
        config_manager.add_storage_provider(name, storage_config)
        console.print(f"[green]✓ Added FTP storage: {name}[/green]")
    
    @staticmethod
    def add_sftp_storage(config_manager):
        """Add SFTP storage provider"""
        from managers.config_manager import StorageConfig
        
        console.print("\n[cyan]Add SFTP Storage[/cyan]")
        
        name = Prompt.ask("Storage name", default="sftp_server")
        host = Prompt.ask("SFTP host")
        port = IntPrompt.ask("SFTP port", default=22)
        username = Prompt.ask("Username")
        
        use_key = Confirm.ask("Use SSH key authentication?", default=False)
        
        if use_key:
            key_filename = Prompt.ask("Path to private key file")
            password = ""
        else:
            key_filename = None
            password = Prompt.ask("Password", password=True)
        
        base_path = Prompt.ask("Base path", default="/")
        
        # Quality settings
        console.print("\n[yellow]Quality Settings (leave blank to use defaults)[/yellow]")
        video_quality = Prompt.ask(
            "Video quality override (best/1080p/720p/480p/360p)",
            default=""
        )
        audio_quality = Prompt.ask(
            "Audio quality override (320/192/128)",
            default=""
        )
        
        storage_config = StorageConfig(
            enabled=True,
            provider_type="sftp",
            host=host,
            port=port,
            username=username,
            password=password,
            key_filename=key_filename,
            base_path=base_path,
            video_quality=video_quality if video_quality else None,
            audio_quality=audio_quality if audio_quality else None
        )
        
        config_manager.add_storage_provider(name, storage_config)
        console.print(f"[green]✓ Added SFTP storage: {name}[/green]")
    
    @staticmethod
    def add_google_drive_storage(config_manager):
        """Add Google Drive storage provider"""
        from managers.config_manager import StorageConfig
        
        console.print("\n[cyan]Add Google Drive Storage[/cyan]")
        console.print("\nYou'll need Google Cloud credentials:")
        console.print("  1. Go to https://console.cloud.google.com")
        console.print("  2. Create a project and enable Google Drive API")
        console.print("  3. Create OAuth 2.0 credentials")
        console.print("  4. Download credentials JSON file\n")
        
        name = Prompt.ask("Storage name", default="google_drive")
        credentials_file = Prompt.ask("Path to credentials JSON file")
        
        if not Path(credentials_file).exists():
            console.print("[red]Credentials file not found[/red]")
            return
        
        folder_id = Prompt.ask("Folder ID (leave blank for root)", default="")
        
        # Quality settings
        console.print("\n[yellow]Quality Settings (leave blank to use defaults)[/yellow]")
        video_quality = Prompt.ask(
            "Video quality override (best/1080p/720p/480p/360p)",
            default=""
        )
        audio_quality = Prompt.ask(
            "Audio quality override (320/192/128)",
            default=""
        )
        
        storage_config = StorageConfig(
            enabled=True,
            provider_type="gdrive",
            credentials_file=credentials_file,
            folder_id=folder_id if folder_id else None,
            video_quality=video_quality if video_quality else None,
            audio_quality=audio_quality if audio_quality else None
        )
        
        config_manager.add_storage_provider(name, storage_config)
        console.print(f"[green]✓ Added Google Drive storage: {name}[/green]")
    
    @staticmethod
    def add_dropbox_storage(config_manager):
        """Add Dropbox storage provider"""
        from managers.config_manager import StorageConfig
        
        console.print("\n[cyan]Add Dropbox Storage[/cyan]")
        console.print("\nYou'll need a Dropbox access token:")
        console.print("  1. Go to https://www.dropbox.com/developers/apps")
        console.print("  2. Create an app")
        console.print("  3. Generate an access token\n")
        
        name = Prompt.ask("Storage name", default="dropbox")
        access_token = Prompt.ask("Dropbox access token", password=True)
        base_path = Prompt.ask("Base path", default="/")
        
        # Quality settings
        console.print("\n[yellow]Quality Settings (leave blank to use defaults)[/yellow]")
        console.print("[dim]Tip: Consider 480p for Dropbox to save space[/dim]")
        video_quality = Prompt.ask(
            "Video quality override (best/1080p/720p/480p/360p)",
            default="480p"
        )
        audio_quality = Prompt.ask(
            "Audio quality override (320/192/128)",
            default=""
        )
        
        storage_config = StorageConfig(
            enabled=True,
            provider_type="dropbox",
            access_token=access_token,
            base_path=base_path,
            video_quality=video_quality if video_quality else None,
            audio_quality=audio_quality if audio_quality else None
        )
        
        config_manager.add_storage_provider(name, storage_config)
        console.print(f"[green]✓ Added Dropbox storage: {name}[/green]")
    
    @staticmethod
    def add_onedrive_storage(config_manager):
        """Add OneDrive storage provider"""
        from managers.config_manager import StorageConfig
        
        console.print("\n[cyan]Add OneDrive Storage[/cyan]")
        console.print("\nYou'll need OneDrive app credentials:")
        console.print("  1. Go to https://portal.azure.com")
        console.print("  2. Register an application")
        console.print("  3. Get client ID and secret\n")
        
        name = Prompt.ask("Storage name", default="onedrive")
        client_id = Prompt.ask("Client ID")
        client_secret = Prompt.ask("Client secret", password=True)
        folder_path = Prompt.ask("Folder path", default="/")
        
        # Quality settings
        console.print("\n[yellow]Quality Settings (leave blank to use defaults)[/yellow]")
        video_quality = Prompt.ask(
            "Video quality override (best/1080p/720p/480p/360p)",
            default=""
        )
        audio_quality = Prompt.ask(
            "Audio quality override (320/192/128)",
            default=""
        )
        
        storage_config = StorageConfig(
            enabled=True,
            provider_type="onedrive",
            client_id=client_id,
            client_secret=client_secret,
            base_path=folder_path,
            video_quality=video_quality if video_quality else None,
            audio_quality=audio_quality if audio_quality else None
        )
        
        config_manager.add_storage_provider(name, storage_config)
        console.print(f"[green]✓ Added OneDrive storage: {name}[/green]")
    
    @staticmethod
    def configure_storage_provider(config_manager):
        """Configure existing storage provider"""
        providers = config_manager.list_storage_providers()
        
        if not providers:
            console.print("\n[yellow]No storage providers configured[/yellow]")
            return
        
        console.print("\n[cyan]Select provider to configure:[/cyan]")
        for idx, name in enumerate(providers, 1):
            console.print(f"  {idx}. {name}")
        
        selection = IntPrompt.ask(
            "Provider number (0 to cancel)",
            default=0
        )
        
        if selection > 0 and selection <= len(providers):
            provider_name = providers[selection - 1]
            storage_config = config_manager.get_storage_provider(provider_name)
            
            console.print(f"\n[cyan]Configuring: {provider_name}[/cyan]")
            
            # Toggle enabled
            storage_config.enabled = Confirm.ask(
                "Enable this storage?",
                default=storage_config.enabled
            )
            
            # Update quality settings
            console.print("\n[yellow]Quality Settings (leave blank to keep current)[/yellow]")
            
            current_video = storage_config.video_quality or "Default"
            video_quality = Prompt.ask(
                f"Video quality (current: {current_video})",
                default=""
            )
            if video_quality:
                storage_config.video_quality = video_quality
            
            current_audio = storage_config.audio_quality or "Default"
            audio_quality = Prompt.ask(
                f"Audio quality (current: {current_audio})",
                default=""
            )
            if audio_quality:
                storage_config.audio_quality = audio_quality
            
            config_manager.add_storage_provider(provider_name, storage_config)
            console.print(f"[green]✓ Updated {provider_name}[/green]")

    @staticmethod
    def remove_storage_provider(config_manager):
        """Remove storage provider"""
        providers = config_manager.list_storage_providers()
        
        if not providers:
            console.print("\n[yellow]No storage providers configured[/yellow]")
            return
        
        console.print("\n[cyan]Select provider to remove:[/cyan]")
        for idx, name in enumerate(providers, 1):
            console.print(f"  {idx}. {name}")
        
        selection = IntPrompt.ask(
            "Provider number (0 to cancel)",
            default=0
        )
        
        if selection > 0 and selection <= len(providers):
            provider_name = providers[selection - 1]
            
            if Confirm.ask(f"Remove {provider_name}?", default=False):
                config_manager.remove_storage_provider(provider_name)
                console.print(f"[green]✓ Removed {provider_name}[/green]")
    
    @staticmethod
    def set_default_storage(config_manager):
        """Set default storage provider"""
        providers = ["local"] + config_manager.list_storage_providers()
        
        console.print("\n[cyan]Select default storage:[/cyan]")
        for idx, name in enumerate(providers, 1):
            is_default = " (current)" if name == config_manager.config.default_storage else ""
            console.print(f"  {idx}. {name}{is_default}")
        
        selection = IntPrompt.ask(
            "Storage number",
            default=1
        )
        
        if selection > 0 and selection <= len(providers):
            storage_name = providers[selection - 1]
            config_manager.set_default_storage(storage_name)
            console.print(f"[green]✓ Default storage set to: {storage_name}[/green]")
    
    @staticmethod
    def test_storage_connections(config_manager, storage_manager):
        """Test all storage provider connections"""
        from utils.storage_providers import (
            FTPStorage, SFTPStorage, GoogleDriveStorage,
            DropboxStorage, OneDriveStorage
        )
        
        console.print("\n[cyan]Testing Storage Connections...[/cyan]\n")
        
        if not config_manager.config.storage_providers:
            console.print("[yellow]No storage providers configured[/yellow]")
            return
        
        results_table = Table(title="Connection Test Results", show_header=True)
        results_table.add_column("Provider", style="cyan")
        results_table.add_column("Type", style="yellow")
        results_table.add_column("Status", style="white")
        
        for name, config_dict in config_manager.config.storage_providers.items():
            from managers.config_manager import StorageConfig
            storage_config = StorageConfig.from_dict(config_dict)
            
            if not storage_config.enabled:
                results_table.add_row(name, storage_config.provider_type.upper(), "[dim]Disabled[/dim]")
                continue
            
            # Create provider instance
            provider = None
            
            try:
                if storage_config.provider_type == "ftp":
                    provider = FTPStorage(
                        storage_config.host,
                        storage_config.port,
                        storage_config.username,
                        storage_config.password,
                        storage_config.base_path
                    )
                elif storage_config.provider_type == "sftp":
                    provider = SFTPStorage(
                        storage_config.host,
                        storage_config.port,
                        storage_config.username,
                        storage_config.password,
                        storage_config.key_filename,
                        storage_config.base_path
                    )
                elif storage_config.provider_type == "gdrive":
                    provider = GoogleDriveStorage(
                        storage_config.credentials_file,
                        storage_config.folder_id
                    )
                elif storage_config.provider_type == "dropbox":
                    provider = DropboxStorage(
                        storage_config.access_token,
                        storage_config.base_path
                    )
                elif storage_config.provider_type == "onedrive":
                    provider = OneDriveStorage(
                        storage_config.client_id,
                        storage_config.client_secret,
                        storage_config.base_path
                    )
                
                if provider:
                    if provider.connect():
                        results_table.add_row(
                            name,
                            storage_config.provider_type.upper(),
                            "[green]Connected[/green]"
                        )
                        provider.disconnect()
                    else:
                        results_table.add_row(
                            name,
                            storage_config.provider_type.upper(),
                            "[red]Failed[/red]"
                        )
                else:
                    results_table.add_row(
                        name,
                        storage_config.provider_type.upper(),
                        "[red]Unknown Type[/red]"
                    )
            
            except Exception as e:
                results_table.add_row(
                    name,
                    storage_config.provider_type.upper(),
                    f"[red]Error: {str(e)[:30]}[/red]"
                )
        
        console.print("\n")
        console.print(results_table)  

"""Remote storage provider integrations"""
import os
from pathlib import Path
from typing import Optional, Dict
from abc import ABC, abstractmethod
from rich.console import Console

console = Console()


class StorageProvider(ABC):
    """Abstract base class for storage providers"""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to storage provider"""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from storage provider"""
        pass
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to remote storage"""
        pass
    
    @abstractmethod
    def create_directory(self, remote_path: str) -> bool:
        """Create directory on remote storage"""
        pass
    
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected"""
        pass


class FTPStorage(StorageProvider):
    """FTP storage provider"""
    
    def __init__(self, host: str, port: int = 21, username: str = "", 
                 password: str = "", base_path: str = "/"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.base_path = base_path
        self.ftp = None
        
    def connect(self) -> bool:
        """Connect to FTP server"""
        try:
            from ftplib import FTP
            
            self.ftp = FTP()
            self.ftp.connect(self.host, self.port, timeout=30)
            
            if self.username:
                self.ftp.login(self.username, self.password)
            else:
                self.ftp.login()
            
            # Change to base path
            if self.base_path and self.base_path != "/":
                self.ftp.cwd(self.base_path)
            
            console.print(f"[green]✓ Connected to FTP: {self.host}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]FTP connection failed: {e}[/red]")
            return False
    
    def disconnect(self):
        """Disconnect from FTP server"""
        if self.ftp:
            try:
                self.ftp.quit()
            except:
                pass
            self.ftp = None
    
    def create_directory(self, remote_path: str) -> bool:
        """Create directory on FTP server"""
        if not self.ftp:
            return False
        
        try:
            # Create nested directories
            parts = remote_path.strip('/').split('/')
            current = ''
            
            for part in parts:
                current = f"{current}/{part}" if current else part
                try:
                    self.ftp.mkd(current)
                except:
                    pass  # Directory might already exist
            
            return True
        except Exception as e:
            console.print(f"[yellow]Warning: Could not create directory {remote_path}: {e}[/yellow]")
            return False
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to FTP server"""
        if not self.ftp:
            console.print("[red]Not connected to FTP[/red]")
            return False
        
        try:
            # Ensure remote directory exists
            remote_dir = str(Path(remote_path).parent)
            if remote_dir != '.':
                self.create_directory(remote_dir)
            
            # Upload file
            with open(local_path, 'rb') as f:
                self.ftp.storbinary(f'STOR {remote_path}', f)
            
            console.print(f"[green]✓ Uploaded to FTP: {remote_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]FTP upload failed: {e}[/red]")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected"""
        if not self.ftp:
            return False
        
        try:
            self.ftp.voidcmd("NOOP")
            return True
        except:
            return False


class SFTPStorage(StorageProvider):
    """SFTP storage provider"""
    
    def __init__(self, host: str, port: int = 22, username: str = "", 
                 password: str = "", key_filename: Optional[str] = None,
                 base_path: str = "/"):
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.key_filename = key_filename
        self.base_path = base_path
        self.sftp = None
        self.transport = None
        
    def connect(self) -> bool:
        """Connect to SFTP server"""
        try:
            import paramiko
            
            # Create transport
            self.transport = paramiko.Transport((self.host, self.port))
            
            # Authenticate
            if self.key_filename and Path(self.key_filename).exists():
                key = paramiko.RSAKey.from_private_key_file(self.key_filename)
                self.transport.connect(username=self.username, pkey=key)
            else:
                self.transport.connect(username=self.username, password=self.password)
            
            # Create SFTP client
            self.sftp = paramiko.SFTPClient.from_transport(self.transport)
            
            # Change to base path
            if self.base_path and self.base_path != "/":
                try:
                    self.sftp.chdir(self.base_path)
                except:
                    pass  # Directory might not exist yet
            
            console.print(f"[green]✓ Connected to SFTP: {self.host}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]SFTP connection failed: {e}[/red]")
            return False
    
    def disconnect(self):
        """Disconnect from SFTP server"""
        if self.sftp:
            try:
                self.sftp.close()
            except:
                pass
            self.sftp = None
        
        if self.transport:
            try:
                self.transport.close()
            except:
                pass
            self.transport = None
    
    def create_directory(self, remote_path: str) -> bool:
        """Create directory on SFTP server"""
        if not self.sftp:
            return False
        
        try:
            # Create nested directories
            parts = remote_path.strip('/').split('/')
            current = ''
            
            for part in parts:
                current = f"{current}/{part}" if current else part
                try:
                    self.sftp.mkdir(current)
                except:
                    pass  # Directory might already exist
            
            return True
        except Exception as e:
            console.print(f"[yellow]Warning: Could not create directory {remote_path}: {e}[/yellow]")
            return False
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to SFTP server"""
        if not self.sftp:
            console.print("[red]Not connected to SFTP[/red]")
            return False
        
        try:
            # Ensure remote directory exists
            remote_dir = str(Path(remote_path).parent)
            if remote_dir != '.':
                self.create_directory(remote_dir)
            
            # Upload file
            self.sftp.put(local_path, remote_path)
            
            console.print(f"[green]✓ Uploaded to SFTP: {remote_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]SFTP upload failed: {e}[/red]")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected"""
        if not self.transport:
            return False
        return self.transport.is_active()


class GoogleDriveStorage(StorageProvider):
    """Google Drive storage provider"""
    
    def __init__(self, credentials_file: str, folder_id: Optional[str] = None):
        self.credentials_file = credentials_file
        self.folder_id = folder_id
        self.service = None
        
    def connect(self) -> bool:
        """Connect to Google Drive"""
        try:
            from google.oauth2.credentials import Credentials
            from google_auth_oauthlib.flow import InstalledAppFlow
            from google.auth.transport.requests import Request
            from googleapiclient.discovery import build
            import pickle
            
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            
            creds = None
            token_file = 'token_drive.pickle'
            
            # Load existing token
            if Path(token_file).exists():
                with open(token_file, 'rb') as token:
                    creds = pickle.load(token)
            
            # Refresh or get new token
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    creds.refresh(Request())
                else:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Save token
                with open(token_file, 'wb') as token:
                    pickle.dump(creds, token)
            
            self.service = build('drive', 'v3', credentials=creds)
            console.print("[green]✓ Connected to Google Drive[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Google Drive connection failed: {e}[/red]")
            console.print("[yellow]Install: pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client[/yellow]")
            return False
    
    def disconnect(self):
        """Disconnect from Google Drive"""
        self.service = None
    
    def create_directory(self, remote_path: str) -> bool:
        """Create directory in Google Drive"""
        if not self.service:
            return False
        
        try:
            file_metadata = {
                'name': remote_path,
                'mimeType': 'application/vnd.google-apps.folder',
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            folder = self.service.files().create(
                body=file_metadata,
                fields='id'
            ).execute()
            
            return True
        except Exception as e:
            console.print(f"[yellow]Warning: Could not create folder: {e}[/yellow]")
            return False
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to Google Drive"""
        if not self.service:
            console.print("[red]Not connected to Google Drive[/red]")
            return False
        
        try:
            from googleapiclient.http import MediaFileUpload
            
            file_metadata = {
                'name': Path(remote_path).name,
                'parents': [self.folder_id] if self.folder_id else []
            }
            
            media = MediaFileUpload(local_path, resumable=True)
            
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id'
            ).execute()
            
            console.print(f"[green]✓ Uploaded to Google Drive: {remote_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Google Drive upload failed: {e}[/red]")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.service is not None


class DropboxStorage(StorageProvider):
    """Dropbox storage provider"""
    
    def __init__(self, access_token: str, base_path: str = "/"):
        self.access_token = access_token
        self.base_path = base_path
        self.dbx = None
        
    def connect(self) -> bool:
        """Connect to Dropbox"""
        try:
            import dropbox
            
            self.dbx = dropbox.Dropbox(self.access_token)
            
            # Test connection
            self.dbx.users_get_current_account()
            
            console.print("[green]✓ Connected to Dropbox[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Dropbox connection failed: {e}[/red]")
            console.print("[yellow]Install: pip install dropbox[/yellow]")
            return False
    
    def disconnect(self):
        """Disconnect from Dropbox"""
        self.dbx = None
    
    def create_directory(self, remote_path: str) -> bool:
        """Create directory in Dropbox"""
        if not self.dbx:
            return False
        
        try:
            full_path = f"{self.base_path}/{remote_path}".replace('//', '/')
            self.dbx.files_create_folder_v2(full_path)
            return True
        except:
            return False  # Folder might already exist
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to Dropbox"""
        if not self.dbx:
            console.print("[red]Not connected to Dropbox[/red]")
            return False
        
        try:
            full_path = f"{self.base_path}/{remote_path}".replace('//', '/')
            
            # Read file and upload
            with open(local_path, 'rb') as f:
                self.dbx.files_upload(
                    f.read(),
                    full_path,
                    mode=dropbox.files.WriteMode.overwrite
                )
            
            console.print(f"[green]✓ Uploaded to Dropbox: {remote_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]Dropbox upload failed: {e}[/red]")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.dbx is not None


class OneDriveStorage(StorageProvider):
    """OneDrive storage provider"""
    
    def __init__(self, client_id: str, client_secret: str, folder_path: str = "/"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.folder_path = folder_path
        self.session = None
        
    def connect(self) -> bool:
        """Connect to OneDrive"""
        try:
            from onedrivesdk import get_default_client
            from onedrivesdk.helpers import GetAuthCodeServer
            
            redirect_uri = 'http://localhost:8080/'
            scopes = ['wl.signin', 'wl.offline_access', 'onedrive.readwrite']
            
            client = get_default_client(
                client_id=self.client_id,
                scopes=scopes
            )
            
            auth_url = client.auth_provider.get_auth_url(redirect_uri)
            
            code = GetAuthCodeServer.get_auth_code(auth_url, redirect_uri)
            client.auth_provider.authenticate(code, redirect_uri, self.client_secret)
            
            self.session = client
            
            console.print("[green]✓ Connected to OneDrive[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]OneDrive connection failed: {e}[/red]")
            console.print("[yellow]Install: pip install onedrivesdk[/yellow]")
            return False
    
    def disconnect(self):
        """Disconnect from OneDrive"""
        self.session = None
    
    def create_directory(self, remote_path: str) -> bool:
        """Create directory in OneDrive"""
        if not self.session:
            return False
        
        try:
            folder = self.session.item(path=self.folder_path).children[remote_path].request().create()
            return True
        except:
            return False
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file to OneDrive"""
        if not self.session:
            console.print("[red]Not connected to OneDrive[/red]")
            return False
        
        try:
            full_path = f"{self.folder_path}/{remote_path}".replace('//', '/')
            
            self.session.item(path=full_path).upload(local_path)
            
            console.print(f"[green]✓ Uploaded to OneDrive: {remote_path}[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]OneDrive upload failed: {e}[/red]")
            return False
    
    def is_connected(self) -> bool:
        """Check if connected"""
        return self.session is not None


class StorageManager:
    """Manages storage providers"""
    
    def __init__(self):
        self.providers: Dict[str, StorageProvider] = {}
        self.active_provider: Optional[str] = None
    
    def add_provider(self, name: str, provider: StorageProvider):
        """Add a storage provider"""
        self.providers[name] = provider
    
    def set_active_provider(self, name: str) -> bool:
        """Set active storage provider"""
        if name in self.providers:
            self.active_provider = name
            return True
        return False
    
    def get_active_provider(self) -> Optional[StorageProvider]:
        """Get active storage provider"""
        if self.active_provider and self.active_provider in self.providers:
            return self.providers[self.active_provider]
        return None
    
    def upload_file(self, local_path: str, remote_path: str) -> bool:
        """Upload file using active provider"""
        provider = self.get_active_provider()
        if not provider:
            return False
        
        if not provider.is_connected():
            if not provider.connect():
                return False
        
        return provider.upload_file(local_path, remote_path)

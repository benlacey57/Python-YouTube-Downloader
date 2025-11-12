"""Proxy manager"""
from typing import List, Optional
import random
from rich.console import Console
from managers.config_manager import ConfigManager

console = Console()


class ProxyManager:
    """Manages proxy rotation"""
    
    def __init__(self):
        # Get config internally
        config_manager = ConfigManager()
        self.proxies: List[str] = config_manager.config.proxies.copy()
        self.current_index = 0
    
    def get_next_proxy(self) -> Optional[str]:
        """Get next proxy in rotation"""
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def get_random_proxy(self) -> Optional[str]:
        """Get random proxy"""
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def add_proxy(self, proxy: str):
        """Add proxy to list"""
        if proxy not in self.proxies:
            self.proxies.append(proxy)
            console.print(f"[green]✓ Added proxy: {proxy}[/green]")
    
    def remove_proxy(self, proxy: str):
        """Remove proxy from list"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            console.print(f"[yellow]Removed proxy: {proxy}[/yellow]")
    
    def get_all_proxies(self) -> List[str]:
        """Get all proxies"""
        return self.proxies.copy()
    
    def clear_proxies(self):
        """Clear all proxies"""
        self.proxies = []
        self.current_index = 0
        console.print("[yellow]Cleared all proxies[/yellow]")
    
    def has_proxies(self) -> bool:
        """Check if any proxies configured"""
        return len(self.proxies) > 0
    
    def reload_from_config(self):
        """Reload proxies from config"""
        config_manager = ConfigManager()
        self.proxies = config_manager.config.proxies.copy()
        self.current_index = 0
        console.print(f"[green]✓ Reloaded {len(self.proxies)} proxies from config[/green]")

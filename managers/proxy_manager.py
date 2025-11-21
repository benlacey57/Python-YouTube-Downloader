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
        self.config = config_manager.config # Store config for rotation logic
        self.proxies: List[str] = self.config.proxies.copy()
        self.current_index = 0
        self.download_counter = 0 # NEW: Counter for rotation frequency
        
        if self.has_proxies() and self.config.proxy_rotation_enabled:
            console.print(f"[cyan]Proxy rotation enabled. Current proxy: {self.proxies[self.current_index]}. Frequency: {self.config.proxy_rotation_frequency} downloads.[/cyan]")
        elif self.has_proxies():
            console.print(f"[yellow]Proxies loaded ({len(self.proxies)}). Rotation is disabled. Using fixed proxy: {self.proxies[0]}.[/yellow]")
    
    def get_next_proxy(self) -> Optional[str]:
        """Get the current or next proxy in rotation, depending on frequency."""
        if not self.proxies:
            return None
        
        # Check if rotation is enabled
        if not self.config.proxy_rotation_enabled:
            # If disabled, always use the first proxy
            proxy = self.proxies[0]
            console.print(f"[blue]Using fixed proxy: {proxy}[/blue]")
            return proxy

        # Check if it's time to rotate
        if self.download_counter > 0 and self.download_counter % self.config.proxy_rotation_frequency == 0:
            # Time to rotate: increment index
            self.current_index = (self.current_index + 1) % len(self.proxies)
            proxy = self.proxies[self.current_index]
            
            # Print a change notification
            console.print(f"[yellow]--- Proxy Rotated! (Download #{self.download_counter} reached rotation frequency) ---[/yellow]")
            console.print(f"[blue]Using new proxy: {proxy}[/blue]")
        else:
            # Not time to rotate: use current index
            proxy = self.proxies[self.current_index]
            # Print the current proxy being used
            if self.download_counter == 0:
                # Print status on first call only if not rotated
                console.print(f"[blue]Using initial proxy: {proxy}[/blue]")
            elif self.config.proxy_rotation_frequency == 1:
                # This case is already covered by the rotation logic above, but for clarity
                pass 
            else:
                console.print(f"[blue]Using proxy: {proxy} (Rotation in {self.config.proxy_rotation_frequency - (self.download_counter % self.config.proxy_rotation_frequency)} downloads)[/blue]")

        # Increment counter for next check
        self.download_counter += 1
        
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
        self.download_counter = 0
        console.print("[yellow]Cleared all proxies[/yellow]")
    
    def has_proxies(self) -> bool:
        """Check if any proxies configured"""
        return len(self.proxies) > 0
    
    def reload_from_config(self):
        """Reload proxies from config"""
        config_manager = ConfigManager()
        self.config = config_manager.config
        self.proxies = self.config.proxies.copy()
        self.current_index = 0
        self.download_counter = 0
        console.print(f"[green]✓ Reloaded {len(self.proxies)} proxies from config[/green]")
        

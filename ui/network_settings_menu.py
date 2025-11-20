"""Network and proxy settings submenu"""
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from rich.table import Table

from managers.config_manager import ConfigManager

console = Console()


class NetworkSettingsMenu:
    """Network & proxy configuration submenu"""
    
    def __init__(self):
        self.config_manager = ConfigManager()
    
    def show(self):
        """Show network settings menu"""
        while True:
            console.clear()
            
            header = Panel(
                "[bold cyan]Network & Proxy Settings[/bold cyan]",
                border_style="cyan"
            )
            console.print(header)
            
            # Show current proxy status
            self._show_proxy_status()
            
            console.print("\n1. Add proxy")
            console.print("2. Remove proxy")
            console.print("3. List all proxies")
            console.print("4. Test proxies")
            console.print("5. Enable/disable proxy rotation")
            console.print("6. Configure rotation frequency")
            console.print("7. Rate limiting settings")
            console.print("8. Bandwidth limit")
            console.print("0. Back")
            
            choice = Prompt.ask(
                "\nSelect option",
                choices=["1", "2", "3", "4", "5", "6", "7", "8", "0"],
                default="0"
            )
            
            if choice == "1":
                self._add_proxy()
            elif choice == "2":
                self._remove_proxy()
            elif choice == "3":
                self._list_proxies()
            elif choice == "4":
                self._test_proxies()
            elif choice == "5":
                self._toggle_rotation()
            elif choice == "6":
                self._configure_rotation()
            elif choice == "7":
                self.config_manager.configure_rate_limiting()
            elif choice == "8":
                self.config_manager.configure_bandwidth_limit()
            elif choice == "0":
                break
    
    def _show_proxy_status(self):
        """Show current proxy configuration"""
        config = self.config_manager.config
        proxies = config.proxies or []
        
        table = Table(show_header=False, box=None)
        table.add_column("Label", style="cyan")
        table.add_column("Value", style="green")
        
        table.add_row("Proxies configured:", str(len(proxies)))
        table.add_row("Rotation enabled:", "Yes" if config.proxy_rotation_enabled else "No")
        if config.proxy_rotation_enabled:
            table.add_row("Rotate every:", f"{config.proxy_rotation_frequency} downloads")
        
        console.print(table)
    
    def _add_proxy(self):
        """Add a new proxy"""
        console.print("\n[cyan]Add Proxy[/cyan]")
        console.print("Format: http://host:port or http://user:pass@host:port")
        
        proxy_url = Prompt.ask("Proxy URL")
        
        if not proxy_url:
            console.print("[yellow]Cancelled[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        # Add proxy to config
        config = self.config_manager.config
        if not config.proxies:
            config.proxies = []
        
        if proxy_url not in config.proxies:
            config.proxies.append(proxy_url)
            self.config_manager.save_config()
            console.print(f"[green]✓ Proxy added: {proxy_url}[/green]")
        else:
            console.print("[yellow]Proxy already exists[/yellow]")
        
        input("\nPress Enter to continue...")
    
    def _remove_proxy(self):
        """Remove a proxy"""
        config = self.config_manager.config
        if not config.proxies:
            console.print("[yellow]No proxies configured[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        console.print("\n[cyan]Remove Proxy[/cyan]")
        for idx, proxy in enumerate(config.proxies, 1):
            console.print(f"  {idx}. {proxy}")
        
        try:
            choice = IntPrompt.ask("Select proxy to remove", default=0)
            if choice > 0 and choice <= len(config.proxies):
                removed = config.proxies.pop(choice - 1)
                self.config_manager.save_config()
                console.print(f"[green]✓ Removed: {removed}[/green]")
            else:
                console.print("[yellow]Cancelled[/yellow]")
        except:
            console.print("[yellow]Cancelled[/yellow]")
        
        input("\nPress Enter to continue...")
    
    def _list_proxies(self):
        """List all proxies"""
        config = self.config_manager.config
        
        console.print("\n[cyan]Configured Proxies[/cyan]")
        if not config.proxies:
            console.print("[dim]No proxies configured[/dim]")
        else:
            for idx, proxy in enumerate(config.proxies, 1):
                console.print(f"  {idx}. {proxy}")
        
        input("\nPress Enter to continue...")
    
    def _test_proxies(self):
        """Test all proxies"""
        config = self.config_manager.config
        
        if not config.proxies:
            console.print("[yellow]No proxies to test[/yellow]")
            input("\nPress Enter to continue...")
            return
        
        console.print("\n[cyan]Testing Proxies...[/cyan]")
        
        import requests
        test_url = "https://www.google.com"
        
        for idx, proxy in enumerate(config.proxies, 1):
            try:
                response = requests.get(
                    test_url,
                    proxies={"http": proxy, "https": proxy},
                    timeout=10
                )
                if response.status_code == 200:
                    console.print(f"  {idx}. {proxy} [green]✓ Working[/green]")
                else:
                    console.print(f"  {idx}. {proxy} [red]✗ Failed (Status: {response.status_code})[/red]")
            except Exception as e:
                console.print(f"  {idx}. {proxy} [red]✗ Error: {str(e)[:50]}[/red]")
        
        input("\nPress Enter to continue...")
    
    def _toggle_rotation(self):
        """Enable/disable proxy rotation"""
        config = self.config_manager.config
        
        current = config.proxy_rotation_enabled if hasattr(config, 'proxy_rotation_enabled') else False
        config.proxy_rotation_enabled = not current
        
        self.config_manager.save_config()
        
        status = "enabled" if config.proxy_rotation_enabled else "disabled"
        console.print(f"[green]✓ Proxy rotation {status}[/green]")
        input("\nPress Enter to continue...")
    
    def _configure_rotation(self):
        """Configure rotation frequency"""
        console.print("\n[cyan]Proxy Rotation Frequency[/cyan]")
        console.print("How many downloads before switching proxy?")
        
        frequency = IntPrompt.ask("Rotation frequency", default=10)
        
        config = self.config_manager.config
        config.proxy_rotation_frequency = frequency
        self.config_manager.save_config()
        
        console.print(f"[green]✓ Will rotate proxy every {frequency} downloads[/green]")
        input("\nPress Enter to continue...")

#!/usr/bin/env python3
"""Load proxies from proxies.txt into configuration"""
import json
from pathlib import Path
from rich.console import Console

console = Console()

def main():
    config_file = Path('downloader_config.json')
    proxies_file = Path('proxies.txt')
    
    # Check if proxies.txt exists
    if not proxies_file.exists():
        console.print("[red]✗ proxies.txt not found[/red]")
        console.print("[dim]Create a proxies.txt file with one proxy per line[/dim]")
        return False
    
    # Load proxies from file
    try:
        with open(proxies_file, 'r') as f:
            proxies = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        
        if not proxies:
            console.print("[yellow]⚠ proxies.txt is empty[/yellow]")
            return False
        
        console.print(f"[cyan]Found {len(proxies)} proxies in proxies.txt[/cyan]")
        
    except Exception as e:
        console.print(f"[red]✗ Error reading proxies.txt: {e}[/red]")
        return False
    
    # Load existing config or create new one
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            console.print("[dim]Loaded existing configuration[/dim]")
        except Exception as e:
            console.print(f"[yellow]⚠ Error loading config, creating new: {e}[/yellow]")
            config = {}
    else:
        console.print("[dim]Creating new configuration[/dim]")
        config = {}
    
    # Update proxy settings
    config['proxies'] = proxies
    config['proxy_rotation_enabled'] = True
    config['proxy_rotation_frequency'] = config.get('proxy_rotation_frequency', 5)
    
    # Save config
    try:
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        console.print(f"[green]✓ Loaded {len(proxies)} proxies into configuration[/green]")
        console.print(f"[green]✓ Proxy rotation enabled (every {config['proxy_rotation_frequency']} downloads)[/green]")
        console.print("\n[cyan]Sample proxies loaded:[/cyan]")
        for i, proxy in enumerate(proxies[:3], 1):
            console.print(f"  {i}. {proxy}")
        if len(proxies) > 3:
            console.print(f"  ... and {len(proxies) - 3} more")
        
        return True
        
    except Exception as e:
        console.print(f"[red]✗ Error saving configuration: {e}[/red]")
        return False


if __name__ == "__main__":
    console.print("\n[bold cyan]Proxy Loader[/bold cyan]\n")
    success = main()
    console.print()
    exit(0 if success else 1)

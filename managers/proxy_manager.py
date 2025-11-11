"""Proxy management and validation"""
import csv
import random
import requests
from pathlib import Path
from typing import List, Optional, Dict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
from concurrent.futures import ThreadPoolExecutor, as_completed

console = Console()


class ProxyManager:
    """Manages proxy rotation and validation"""

    def __init__(self, proxies: List[str] = None):
        self.proxies = proxies if proxies else []
        self.current_index = 0
        self.working_proxies: List[str] = []
        self.failed_proxies: List[str] = []

    def load_proxies_from_file(self) -> bool:
        """Load proxies from proxies.txt or proxies.csv"""
        proxies = []

        # Try proxies.txt first
        if Path("proxies.txt").exists():
            try:
                with open("proxies.txt", 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            proxies.append(line)
                console.print(f"[green]✓ Loaded {len(proxies)} proxies from proxies.txt[/green]")
                self.proxies = proxies
                return True
            except Exception as e:
                console.print(f"[red]Error reading proxies.txt: {e}[/red]")
                return False

        # Try proxies.csv
        elif Path("proxies.csv").exists():
            try:
                with open("proxies.csv", 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    # Check if this is the expected format
                    if reader.fieldnames and 'ip' in reader.fieldnames and 'port' in reader.fieldnames:
                        # Format: ip,port,country,https,scraped_from,status,speed,location,last_checked
                        for row in reader:
                            try:
                                ip = row.get('ip', '').strip()
                                port = row.get('port', '').strip()
                                https = row.get('https', 'False').strip()
                                
                                # Skip empty rows or header-like rows
                                if not ip or not port or ip == 'ip':
                                    continue
                                
                                # Skip commented rows
                                if ip.startswith('#'):
                                    continue
                                
                                # Determine scheme
                                if https.lower() in ('true', '1', 'yes'):
                                    scheme = 'https'
                                else:
                                    scheme = 'http'
                                
                                # Construct proxy URL
                                proxy_url = f"{scheme}://{ip}:{port}"
                                proxies.append(proxy_url)
                                
                            except Exception as e:
                                console.print(f"[yellow]Warning: Skipping invalid row: {e}[/yellow]")
                                continue
                    else:
                        # Fallback: Try reading just the first column as simple proxy URLs
                        f.seek(0)  # Reset file pointer
                        reader = csv.reader(f)
                        for row in reader:
                            if not row or len(row) < 1:
                                continue
                            proxy = row[0].strip()
                            if proxy and not proxy.startswith('#') and proxy != 'ip':
                                # If it doesn't have a scheme, add http://
                                if not proxy.startswith(('http://', 'https://', 'socks4://', 'socks5://')):
                                    proxy = f"http://{proxy}"
                                proxies.append(proxy)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_proxies = []
                for proxy in proxies:
                    if proxy not in seen:
                        seen.add(proxy)
                        unique_proxies.append(proxy)
                
                proxies = unique_proxies
                
                console.print(f"[green]✓ Loaded {len(proxies)} proxies from proxies.csv[/green]")
                self.proxies = proxies
                return True
                
            except csv.Error as e:
                console.print(f"[red]Error parsing proxies.csv: {e}[/red]")
                console.print("[yellow]Make sure the file is a valid CSV format[/yellow]")
                return False
            except Exception as e:
                console.print(f"[red]Error reading proxies.csv: {e}[/red]")
                return False

        console.print("[yellow]No proxy file found (proxies.txt or proxies.csv)[/yellow]")
        return False

    def validate_proxy(self, proxy: str, timeout: int = 10) -> bool:
        """Validate a single proxy"""
        try:
            test_url = "https://www.google.com"
            proxies = {
                'http': proxy,
                'https': proxy
            }
            response = requests.get(
                test_url,
                proxies=proxies,
                timeout=timeout,
                verify=False  # Disable SSL verification for proxy testing
            )
            return response.status_code == 200
        except requests.exceptions.ProxyError:
            return False
        except requests.exceptions.ConnectTimeout:
            return False
        except requests.exceptions.ReadTimeout:
            return False
        except requests.exceptions.Timeout:
            return False
        except requests.exceptions.ConnectionError:
            return False
        except Exception:
            return False

    def validate_all_proxies(self, timeout: int = 10, max_workers: int = 5, auto_remove: bool = True):
        """
        Validate all proxies and optionally remove non-working ones
        
        Args:
            timeout: Timeout in seconds per proxy
            max_workers: Number of concurrent validation threads
            auto_remove: Automatically remove failed proxies after validation
        """
        if not self.proxies:
            console.print("[yellow]No proxies to validate[/yellow]")
            return

        console.print(f"\n[cyan]Validating {len(self.proxies)} proxies...[/cyan]")
        console.print(f"[yellow]Timeout: {timeout} seconds per proxy[/yellow]")
        console.print(f"[yellow]Using {max_workers} concurrent workers[/yellow]\n")

        self.working_proxies = []
        self.failed_proxies = []

        # Disable SSL warnings for proxy testing
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task(
                "Validating proxies...",
                total=len(self.proxies)
            )

            with ThreadPoolExecutor(max_workers=max_workers) as executor:
                future_to_proxy = {
                    executor.submit(self.validate_proxy, proxy, timeout): proxy
                    for proxy in self.proxies
                }

                for future in as_completed(future_to_proxy):
                    proxy = future_to_proxy[future]
                    try:
                        is_valid = future.result()
                        if is_valid:
                            self.working_proxies.append(proxy)
                            progress.console.print(f"[green]✓[/green] {proxy}")
                        else:
                            self.failed_proxies.append(proxy)
                            progress.console.print(f"[red]✗[/red] {proxy}")
                    except Exception as e:
                        self.failed_proxies.append(proxy)
                        progress.console.print(f"[red]✗[/red] {proxy}: {e}")

                    progress.update(task, advance=1)

        # Show summary
        self._show_validation_summary()
        
        # Auto-remove failed proxies if requested
        if auto_remove and self.failed_proxies:
            if Confirm.ask(f"\n[yellow]Remove {len(self.failed_proxies)} failed proxies?[/yellow]", default=True):
                self.remove_dead_proxies()

    def _show_validation_summary(self):
        """Show validation summary"""
        from rich.table import Table
        from rich.panel import Panel

        total = len(self.proxies)
        working = len(self.working_proxies)
        failed = len(self.failed_proxies)
        success_rate = (working / total * 100) if total > 0 else 0

        summary = (
            f"[green]Working proxies:[/green] {working}\n"
            f"[red]Failed proxies:[/red] {failed}\n"
            f"[cyan]Success rate:[/cyan] {success_rate:.1f}%"
        )

        panel = Panel(
            summary,
            title="[bold]Validation Summary[/bold]",
            border_style="cyan"
        )

        console.print("\n")
        console.print(panel)

        # Show sample of working proxies
        if self.working_proxies:
            console.print("\n[green]Sample of working proxies:[/green]")
            for proxy in self.working_proxies[:5]:
                console.print(f"  • {proxy}")
            if len(self.working_proxies) > 5:
                console.print(f"  ... and {len(self.working_proxies) - 5} more")

    def remove_dead_proxies(self):
        """Remove non-working proxies and update proxy list"""
        if not self.failed_proxies:
            console.print("[yellow]No failed proxies to remove[/yellow]")
            return

        self.proxies = self.working_proxies.copy()
        removed_count = len(self.failed_proxies)

        console.print(f"\n[green]✓ Removed {removed_count} non-working proxies[/green]")
        console.print(f"[cyan]Active proxies: {len(self.proxies)}[/cyan]")

        # Save updated proxy list
        self._save_proxies_to_file()

    def _save_proxies_to_file(self):
        """Save working proxies back to file"""
        if not self.proxies:
            return

        # Determine which file to save to
        if Path("proxies.txt").exists():
            try:
                with open("proxies.txt", 'w', encoding='utf-8') as f:
                    for proxy in self.proxies:
                        f.write(f"{proxy}\n")
                console.print("[green]✓ Updated proxies.txt[/green]")
            except Exception as e:
                console.print(f"[red]Error saving proxies.txt: {e}[/red]")

        elif Path("proxies.csv").exists():
            try:
                # Try to parse existing proxies back into CSV format
                with open("proxies.csv", 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    
                    # Write header
                    writer.writerow(['ip', 'port', 'country', 'https', 'scraped_from', 'status', 'speed', 'location', 'last_checked'])
                    
                    # Write proxy data
                    for proxy in self.proxies:
                        # Parse proxy URL
                        if proxy.startswith('https://'):
                            https = 'True'
                            proxy_clean = proxy.replace('https://', '')
                        elif proxy.startswith('http://'):
                            https = 'False'
                            proxy_clean = proxy.replace('http://', '')
                        else:
                            https = 'False'
                            proxy_clean = proxy
                        
                        # Split IP and port
                        if ':' in proxy_clean:
                            ip, port = proxy_clean.split(':', 1)
                        else:
                            ip = proxy_clean
                            port = '80'
                        
                        writer.writerow([ip, port, '', https, 'Validated', 'Working', '', '', ''])
                
                console.print("[green]✓ Updated proxies.csv[/green]")
            except Exception as e:
                console.print(f"[red]Error saving proxies.csv: {e}[/red]")

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

    def get_summary(self) -> Dict:
        """Get proxy statistics"""
        return {
            'total_proxies': len(self.proxies),
            'working_proxies': len(self.working_proxies),
            'failed_proxies': len(self.failed_proxies),
            'success_rate': (len(self.working_proxies) / len(self.proxies) * 100) if self.proxies else 0
        }

    def display_proxy_list(self, max_display: int = 20):
        """Display current proxy list"""
        from rich.table import Table
        
        if not self.proxies:
            console.print("[yellow]No proxies loaded[/yellow]")
            return
        
        table = Table(title=f"Loaded Proxies ({len(self.proxies)} total)", show_header=True)
        table.add_column("#", style="cyan", width=6)
        table.add_column("Proxy", style="white")
        table.add_column("Scheme", style="yellow", width=8)
        
        for idx, proxy in enumerate(self.proxies[:max_display], 1):
            scheme = proxy.split('://')[0] if '://' in proxy else 'http'
            table.add_row(str(idx), proxy, scheme)
        
        if len(self.proxies) > max_display:
            table.add_row("...", f"and {len(self.proxies) - max_display} more", "...")
        
        console.print("\n")
        console.print(table)

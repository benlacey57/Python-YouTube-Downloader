"""Proxy management and validation"""
import csv
import random
import requests
from pathlib import Path
from typing import List, Optional, Dict
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
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
            except Exception as e:
                console.print(f"[red]Error reading proxies.txt: {e}[/red]")
                return False

        # Try proxies.csv
        elif Path("proxies.csv").exists():
            try:
                with open("proxies.csv", 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for row in reader:
                        if not row:
                            continue
                        if len(row) < 1:
                            continue
                        proxy = row[0].strip()
                        if proxy and not proxy.startswith('#'):
                            proxies.append(proxy)
                console.print(f"[green]✓ Loaded {len(proxies)} proxies from proxies.csv[/green]")
            except csv.Error as e:
                console.print(f"[red]Error parsing proxies.csv: {e}[/red]")
                return False
            except Exception as e:
                console.print(f"[red]Error reading proxies.csv: {e}[/red]")
                return False

        if proxies:
            self.proxies = proxies
            return True

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
                timeout=timeout
            )
            return response.status_code == 200
        except Exception:
            return False

    def validate_all_proxies(self, timeout: int = 10, max_workers: int = 5):
        """Validate all proxies and remove non-working ones"""
        if not self.proxies:
            console.print("[yellow]No proxies to validate[/yellow]")
            return

        console.print(f"\n[cyan]Validating {len(self.proxies)} proxies...[/cyan]")
        console.print(f"[yellow]Timeout: {timeout} seconds per proxy[/yellow]\n")

        self.working_proxies = []
        self.failed_proxies = []

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

    def _show_validation_summary(self):
        """Show validation summary"""
        from rich.table import Table
        from rich.panel import Panel

        summary = (
            f"[green]Working proxies:[/green] {len(self.working_proxies)}\n"
            f"[red]Failed proxies:[/red] {len(self.failed_proxies)}\n"
            f"[cyan]Success rate:[/cyan] {(len(self.working_proxies) / len(self.proxies) * 100):.1f}%"
        )

        panel = Panel(
            summary,
            title="[bold]Validation Summary[/bold]",
            border_style="cyan"
        )

        console.print("\n")
        console.print(panel)

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
                with open("proxies.csv", 'w', encoding='utf-8', newline='') as f:
                    writer = csv.writer(f)
                    for proxy in self.proxies:
                        writer.writerow([proxy])
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

"""Database seeding utilities"""
import re
from pathlib import Path
from typing import List, Dict, Callable
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class DatabaseSeeder:
    """Handles database seeding from text files"""
    
    def __init__(self, seeds_dir: str = "seeds"):
        self.seeds_dir = Path(seeds_dir)
        self.seeds_dir.mkdir(exist_ok=True)
    
    def parse_seed_file(self, file_path: str) -> List[Dict]:
        """
        Parse a seed file with entries separated by ---
        
        Format:
        Name
        Description
        URL
        [optional_field: value]
        ---
        """
        records = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by separator
            entries = content.split('---')
            
            for entry in entries:
                entry = entry.strip()
                if not entry:
                    continue
                
                lines = [line.strip() for line in entry.split('\n') if line.strip()]
                
                if len(lines) < 3:
                    console.print(f"[yellow]Skipping invalid entry: {lines}[/yellow]")
                    continue
                
                record = {
                    'name': lines[0],
                    'description': lines[1],
                    'url': lines[2]
                }
                
                # Parse optional fields (key: value format)
                for line in lines[3:]:
                    if ':' in line:
                        key, value = line.split(':', 1)
                        record[key.strip().lower().replace(' ', '_')] = value.strip()
                
                records.append(record)
            
            console.print(f"[green]✓ Parsed {len(records)} records from {Path(file_path).name}[/green]")
            return records
        
        except Exception as e:
            console.print(f"[red]Error parsing {file_path}: {e}[/red]")
            return []
    
    def seed(self, seed_name: str, insert_callback: Callable):
        """
        Seed a database table
        
        Args:
            seed_name: Name of the seed file (without .txt extension)
            insert_callback: Function to call for each record
        """
        seed_file = self.seeds_dir / f"{seed_name}.txt"
        
        if not seed_file.exists():
            console.print(f"[yellow]Seed file not found: {seed_file}[/yellow]")
            return
        
        console.print(f"\n[cyan]Seeding from {seed_file}...[/cyan]")
        
        records = self.parse_seed_file(str(seed_file))
        
        if not records:
            console.print("[yellow]No records to seed[/yellow]")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task(f"Seeding {seed_name}...", total=len(records))
            
            success_count = 0
            error_count = 0
            
            for record in records:
                try:
                    insert_callback(record)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    progress.console.print(f"[red]✗ Failed to seed {record.get('name', 'Unknown')}: {e}[/red]")
                
                progress.update(task, advance=1)
        
        console.print(f"\n[green]✓ Seeded {success_count} records[/green]")
        if error_count > 0:
            console.print(f"[red]✗ Failed {error_count} records[/red]")
    
    def seed_all(self, seed_configs: Dict[str, Callable]):
        """
        Seed all tables from multiple files
        
        Args:
            seed_configs: Dict mapping seed names to insert callbacks
        """
        console.print("\n[bold cyan]Starting Database Seeding[/bold cyan]\n")
        
        for seed_name, callback in seed_configs.items():
            self.seed(seed_name, callback)
        
        console.print("\n[bold green]✓ All seeding completed![/bold green]")
    
    def create_seed_file_template(self, file_name: str, sample_data: List[Dict] = None):
        """Create a template seed file"""
        seed_file = self.seeds_dir / f"{file_name}.txt"
        
        if seed_file.exists():
            console.print(f"[yellow]Seed file already exists: {seed_file}[/yellow]")
            return
        
        template = "# Seed file for {}\n# Format: Name, Description, URL, [optional fields]\n\n".format(file_name)
        
        if sample_data:
            for record in sample_data:
                template += f"{record.get('name', 'Name')}\n"
                template += f"{record.get('description', 'Description')}\n"
                template += f"{record.get('url', 'https://example.com')}\n"
                
                # Add optional fields
                for key, value in record.items():
                    if key not in ['name', 'description', 'url']:
                        template += f"{key}: {value}\n"
                
                template += "---\n\n"
        else:
            template += "Example Entry\n"
            template += "This is a description\n"
            template += "https://example.com\n"
            template += "optional_field: value\n"
            template += "---\n"
        
        with open(seed_file, 'w', encoding='utf-8') as f:
            f.write(template)
        
        console.print(f"[green]✓ Created seed file template: {seed_file}[/green]")

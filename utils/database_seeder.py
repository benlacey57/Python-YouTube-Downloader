"""Database seeding utilities"""
import json
from pathlib import Path
from typing import List, Dict, Callable
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

console = Console()


class DatabaseSeeder:
    """Handles database seeding from JSON files"""
    
    def __init__(self, seeds_dir: str = "seeds"):
        self.seeds_dir = Path(seeds_dir)
        self.seeds_dir.mkdir(exist_ok=True)
    
    def load_json_seed(self, file_path: str) -> Dict[str, List[Dict]]:
        """
        Load seed data from JSON file
        
        Args:
            file_path: Path to JSON seed file
            
        Returns:
            Dictionary with table names as keys and lists of records as values
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            console.print(f"[green]✓ Loaded seed file: {Path(file_path).name}[/green]")
            return data
        
        except json.JSONDecodeError as e:
            console.print(f"[red]JSON parsing error in {file_path}: {e}[/red]")
            return {}
        except Exception as e:
            console.print(f"[red]Error loading {file_path}: {e}[/red]")
            return {}
    
    def seed_table(self, table_name: str, records: List[Dict], 
                   insert_callback: Callable, skip_existing: bool = True):
        """
        Seed a database table
        
        Args:
            table_name: Name of the table being seeded
            records: List of record dictionaries
            insert_callback: Function to call for each record
            skip_existing: Whether to skip existing records
        """
        if not records:
            console.print(f"[yellow]No records to seed for {table_name}[/yellow]")
            return
        
        console.print(f"\n[cyan]Seeding {table_name}...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task(f"Seeding {table_name}...", total=len(records))
            
            success_count = 0
            skip_count = 0
            error_count = 0
            
            for record in records:
                try:
                    result = insert_callback(record)
                    
                    if result == "skipped":
                        skip_count += 1
                        name = record.get('title', record.get('name', 'Unknown'))
                        progress.console.print(f"[yellow]⊘ Skipped (exists): {name}[/yellow]")
                    else:
                        success_count += 1
                        name = record.get('title', record.get('name', 'Unknown'))
                        progress.console.print(f"[green]✓ Seeded: {name}[/green]")
                
                except Exception as e:
                    error_count += 1
                    name = record.get('title', record.get('name', 'Unknown'))
                    progress.console.print(f"[red]✗ Failed: {name}: {e}[/red]")
                
                progress.update(task, advance=1)
        
        # Summary
        summary_table = Table(title=f"{table_name} Seeding Summary", show_header=True)
        summary_table.add_column("Status", style="cyan")
        summary_table.add_column("Count", justify="right")
        
        summary_table.add_row("[green]Seeded[/green]", str(success_count))
        summary_table.add_row("[yellow]Skipped[/yellow]", str(skip_count))
        summary_table.add_row("[red]Failed[/red]", str(error_count))
        summary_table.add_row("[bold]Total[/bold]", str(len(records)))
        
        console.print("\n")
        console.print(summary_table)
    
    def seed_from_json(self, json_file: str, seed_configs: Dict[str, Callable]):
        """
        Seed multiple tables from a JSON file
        
        Args:
            json_file: Name of JSON file (without extension)
            seed_configs: Dict mapping table names to insert callbacks
        """
        seed_path = self.seeds_dir / f"{json_file}.json"
        
        if not seed_path.exists():
            console.print(f"[red]Seed file not found: {seed_path}[/red]")
            console.print(f"[yellow]Create the file at: {seed_path.absolute()}[/yellow]")
            return
        
        data = self.load_json_seed(str(seed_path))
        
        if not data:
            console.print("[yellow]No data to seed[/yellow]")
            return
        
        for table_name, callback in seed_configs.items():
            if table_name in data:
                self.seed_table(table_name, data[table_name], callback)
            else:
                console.print(f"[yellow]No data for table '{table_name}' in seed file[/yellow]")
    
    def validate_seed_file(self, json_file: str, required_fields: Dict[str, List[str]]) -> bool:
        """
        Validate a seed file structure
        
        Args:
            json_file: Name of JSON file (without extension)
            required_fields: Dict mapping table names to lists of required field names
            
        Returns:
            bool: True if valid, False otherwise
        """
        seed_path = self.seeds_dir / f"{json_file}.json"
        
        if not seed_path.exists():
            console.print(f"[red]✗ File not found: {seed_path}[/red]")
            return False
        
        data = self.load_json_seed(str(seed_path))
        
        if not data:
            return False
        
        valid = True
        errors = []
        
        for table_name, fields in required_fields.items():
            if table_name not in data:
                errors.append(f"Missing table: {table_name}")
                valid = False
                continue
            
            records = data[table_name]
            
            if not isinstance(records, list):
                errors.append(f"Table '{table_name}' must be a list")
                valid = False
                continue
            
            for idx, record in enumerate(records):
                if not isinstance(record, dict):
                    errors.append(f"Record {idx + 1} in '{table_name}' must be a dictionary")
                    valid = False
                    continue
                
                missing_fields = [f for f in fields if f not in record]
                
                if missing_fields:
                    record_name = record.get('title', record.get('name', f'Record {idx + 1}'))
                    errors.append(f"{record_name}: missing fields: {', '.join(missing_fields)}")
                    valid = False
        
        if errors:
            console.print(f"\n[red]Validation failed with {len(errors)} error(s):[/red]")
            for error in errors[:10]:  # Show first 10 errors
                console.print(f"  [red]✗[/red] {error}")
            if len(errors) > 10:
                console.print(f"  [dim]... and {len(errors) - 10} more errors[/dim]")
        else:
            console.print("[green]✓ Seed file is valid[/green]")
        
        return valid
    
    def get_seed_statistics(self, json_file: str) -> Dict:
        """
        Get statistics about a seed file
        
        Args:
            json_file: Name of JSON file (without extension)
            
        Returns:
            Dictionary with statistics
        """
        seed_path = self.seeds_dir / f"{json_file}.json"
        
        if not seed_path.exists():
            return {
                'exists': False,
                'error': 'File not found'
            }
        
        try:
            data = self.load_json_seed(str(seed_path))
            
            stats = {
                'exists': True,
                'file_size_kb': seed_path.stat().st_size / 1024,
                'tables': {},
                'total_records': 0
            }
            
            for table_name, records in data.items():
                record_count = len(records) if isinstance(records, list) else 0
                stats['tables'][table_name] = record_count
                stats['total_records'] += record_count
            
            return stats
        
        except Exception as e:
            return {
                'exists': True,
                'error': str(e)
            }
    
    def list_seed_files(self) -> List[Dict]:
        """
        List all available seed files with statistics
        
        Returns:
            List of dictionaries with file information
        """
        if not self.seeds_dir.exists():
            return []
        
        json_files = list(self.seeds_dir.glob("*.json"))
        
        files_info = []
        
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                total_records = sum(
                    len(records) for records in data.values() 
                    if isinstance(records, list)
                )
                
                files_info.append({
                    'name': json_file.name,
                    'path': str(json_file),
                    'size_kb': json_file.stat().st_size / 1024,
                    'tables': list(data.keys()),
                    'total_records': total_records,
                    'valid': True
                })
            
            except Exception as e:
                files_info.append({
                    'name': json_file.name,
                    'path': str(json_file),
                    'error': str(e),
                    'valid': False
                })
        
        return files_info
    
    def display_seed_files_table(self):
        """Display a table of all available seed files"""
        files_info = self.list_seed_files()
        
        if not files_info:
            console.print("[yellow]No seed files found in seeds/ directory[/yellow]")
            return
        
        table = Table(title="Available Seed Files", show_header=True)
        table.add_column("File", style="cyan")
        table.add_column("Size", style="green", justify="right")
        table.add_column("Tables", style="yellow")
        table.add_column("Records", style="magenta", justify="right")
        table.add_column("Status", style="white")
        
        for file_info in files_info:
            if file_info.get('valid', False):
                table.add_row(
                    file_info['name'],
                    f"{file_info['size_kb']:.1f} KB",
                    ', '.join(file_info['tables']),
                    str(file_info['total_records']),
                    "[green]✓ Valid[/green]"
                )
            else:
                table.add_row(
                    file_info['name'],
                    "N/A",
                    "N/A",
                    "N/A",
                    f"[red]✗ Error[/red]"
                )
        
        console.print("\n")
        console.print(table)
    
    def create_seed_template(self, table_name: str, fields: List[str], 
                           sample_records: int = 2):
        """
        Create a template seed file
        
        Args:
            table_name: Name of the table
            fields: List of field names
            sample_records: Number of sample records to create
        """
        template_data = {
            table_name: []
        }
        
        for i in range(sample_records):
            record = {}
            for field in fields:
                if field == 'id':
                    record[field] = None
                elif field in ['is_monitored', 'enabled']:
                    record[field] = True
                elif 'minutes' in field or 'interval' in field:
                    record[field] = 60
                elif field == 'url':
                    record[field] = f"https://example.com/channel{i+1}"
                elif field == 'title' or field == 'name':
                    record[field] = f"Example {table_name.title()} {i+1}"
                elif field == 'description':
                    record[field] = f"This is a sample description for {table_name} {i+1}"
                elif field == 'quality':
                    record[field] = "720p"
                elif field == 'format_type':
                    record[field] = "video"
                elif 'dir' in field or 'path' in field:
                    record[field] = f"downloads/{table_name}/{i+1}"
                elif 'template' in field:
                    record[field] = "{index:03d} - {title}"
                elif 'order' in field:
                    record[field] = "newest_first"
                else:
                    record[field] = f"sample_{field}"
            
            template_data[table_name].append(record)
        
        output_file = self.seeds_dir / f"{table_name}_template.json"
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(template_data, f, indent=2, ensure_ascii=False)
            
            console.print(f"[green]✓ Created template: {output_file}[/green]")
            console.print(f"[dim]Edit this file and rename it to {table_name}.json[/dim]")
        
        except Exception as e:
            console.print(f"[red]Failed to create template: {e}[/red]")
    
    def backup_seed_file(self, json_file: str):
        """
        Create a backup of a seed file
        
        Args:
            json_file: Name of JSON file (without extension)
        """
        from datetime import datetime
        
        seed_path = self.seeds_dir / f"{json_file}.json"
        
        if not seed_path.exists():
            console.print(f"[red]File not found: {seed_path}[/red]")
            return
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = self.seeds_dir / f"{json_file}_backup_{timestamp}.json"
        
        try:
            import shutil
            shutil.copy2(seed_path, backup_path)
            console.print(f"[green]✓ Backup created: {backup_path.name}[/green]")
        
        except Exception as e:
            console.print(f"[red]Backup failed: {e}[/red]")

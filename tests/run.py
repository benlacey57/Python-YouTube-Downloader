import subprocess
import sys
import os
import shutil
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

# Initialize rich console
console = Console()

# --- Configuration ---
LOG_DIR = Path("logs/tests")
LIVE_TEST_PROXY = "http://localhost:8080" # Placeholder for live proxy/server address

# --- Setup Functions ---

def setup_environment():
    """Ensure log directory exists."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    if not Path("pytest.ini").exists():
        console.print("[yellow]Warning: 'pytest.ini' not found. Using default pytest configuration.[/yellow]")

def get_log_filepath():
    """Generates a timestamped log file path."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return LOG_DIR / f"{timestamp}.log"

def run_pytest(command: list, log_file: Path):
    """Executes pytest and streams output to console and log file."""
    
    full_command = [sys.executable, '-m', 'pytest'] + command
    
    # Run the test command, capturing stdout/stderr
    with open(log_file, "w") as log:
        console.print(f"[dim]Running command: {' '.join(full_command)}[/dim]")
        
        # We use Popen to stream output in real-time while also capturing it
        process = subprocess.Popen(
            full_command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
        )
        
        # Stream output to both console and log
        for line in process.stdout:
            console.print(line.strip(), highlight=True)
            log.write(line)
        
        process.wait()
        
    return process.returncode

# --- Menu Logic ---

def display_menu():
    """Display the test runner menu and get user choice."""
    console.print("\n")

    title = Panel.fit(
        "[bold magenta]Playlist Downloader Testing Suite[/bold magenta]",
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(title)

    options = [
        ("1", "Run All Unit Tests (Fast, Mocked)"),
        ("2", "Run Full Coverage Report"),
        ("3", "Run Live Tests (External Network)"),
        ("4", "Test Managers/Core Logic"),
        ("5", "Test UI/Display Components"),
        ("6", "Test Models/Data Structures"),
        ("7", "Exit")
    ]

    option_text = "\n".join([f"  {num}. {desc}" for num, desc in options])

    menu_panel = Panel(
        option_text,
        title="[bold]Test Options[/bold]",
        border_style="yellow",
        padding=(1, 2)
    )
    console.print(menu_panel)

    choice = Prompt.ask(
        "\n[bold magenta]Select an option[/bold magenta]",
        choices=[num for num, _ in options],
        default="1"
    )

    return choice

def handle_choice(choice: str, log_file: Path):
    """Maps menu choice to pytest command arguments."""
    
    # Base command args
    args = []
    
    if choice == "1":
        # Run all tests (excluding 'live')
        args = ['-m', 'not live']
        title = "ALL UNIT TESTS"
    
    elif choice == "2":
        # Run all tests (excluding 'live') with coverage report
        args = ['-m', 'not live', '--cov=.', '--cov-report', 'term-missing']
        title = "FULL COVERAGE REPORT"
        
    elif choice == "3":
        # Run only 'live' tests (requires configuration/network)
        args = ['-m', 'live', '--config-file=config_test.json']
        title = "LIVE NETWORK TESTS"
        
        console.print(f"\n[yellow]Note: Live tests require 'config_test.json' and network access.[/yellow]")
        
    elif choice == "4":
        # Test managers and core logic (e.g., config_manager, monitor_manager)
        args = ['-m', 'managers and not live']
        title = "MANAGER/CORE TESTS"
        
    elif choice == "5":
        # Test UI components (e.g., settings_menu, setup_wizard)
        args = ['-m', 'ui and not live']
        title = "UI/DISPLAY TESTS"
        
    elif choice == "6":
        # Test data models (e.g., channel, queue)
        args = ['-m', 'models and not live']
        title = "MODEL/DATA STRUCTURE TESTS"

    else:
        return
    
    console.print(f"\n[bold cyan]--- Running {title} ---[/bold cyan]")
    
    return_code = run_pytest(args, log_file)
    
    if return_code == 0:
        console.print(f"\n[green]✓ {title} COMPLETED SUCCESSFULLY[/green]")
    else:
        console.print(f"\n[red]✗ {title} FAILED (Exit Code {return_code})[/red]")
    
    console.print(f"[dim]Full output saved to: {log_file.resolve()}[/dim]")
    input("Press Enter to continue...")


def main():
    """Main execution loop for the test runner."""
    setup_environment()
    
    while True:
        log_file = get_log_filepath()
        choice = display_menu()
        
        if choice == "7":
            console.print("\n[bold magenta]Exiting Test Runner. Goodbye![/bold magenta]")
            break
        
        handle_choice(choice, log_file)

if __name__ == "__main__":
    main()

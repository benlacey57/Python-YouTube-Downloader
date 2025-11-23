#!/usr/bin/env python3
"""
Installation script: Handles environment setup (venv, dependencies, run script, directories).
Does NOT handle configuration; run setup.py for configuration.
"""
import sys
import subprocess
import os
from pathlib import Path
import time

# Import Rich libraries
from rich.console import Console
from rich.panel import Panel

console = Console()

# --- CONSTANTS ---
APP_BANNER_TITLE = "The Download Manager"
APP_BANNER_SUBTITLE = "Advanced download management system"
CORE_DEPENDENCIES = ["yt-dlp", "rich"]
# Development dependencies needed by linters/formatters in the dev container
DEV_DEPENDENCIES = ["black", "flake8", "mypy", "safety", "isort", "pytest"]
# Assuming these modules are placeholders for the new config process
REQUIRED_MANAGERS = ["managers.config_manager", "managers.queue_manager"]


# --- UTILS ---

def print_banner():
    """Print application banner"""
    BANNER = f"""
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║              [bold yellow]{APP_BANNER_TITLE.center(65)}[/bold yellow]             ║
║                                                                           ║
║              [dim]{APP_BANNER_SUBTITLE.center(65)}[/dim]                         ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
    """
    console.print(Panel(BANNER.strip(), border_style="bold blue"))
    console.print()


def print_section(title):
    """Print a section header"""
    console.print(f"\n[bold yellow]{'═' * 75}[/bold yellow]")
    console.print(f"  [bold cyan]{title}[/bold cyan]")
    console.print(f"[bold yellow]{'═' * 75}\n")


def check_python_version():
    """Check if Python version is adequate"""
    if sys.version_info < (3, 8):
        console.print("❌ [bold red]Python 3.8 or higher is required![/bold red]")
        console.print(f"   [dim]Current version: {sys.version}[/dim]")
        sys.exit(1)
    console.print(f"✓ [green]Python version: {sys.version.split()[0]}[/green]")


def create_virtual_environment():
    """Create Python virtual environment"""
    print_section("Creating Virtual Environment")
    venv_dir = "venv"
    if os.path.exists(venv_dir):
        console.print(f"⊙ [yellow]Virtual environment '{venv_dir}/' already exists.[/yellow] Skipping creation.")
        return
        
    try:
        console.print(f"Creating environment at ./{venv_dir}/...")
        subprocess.run(
            [sys.executable, "-m", "venv", venv_dir],
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE
        )
        console.print("✓ [green]Virtual environment created successfully.[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"❌ [bold red]Failed to create virtual environment:[/bold red] {e.stderr.decode().strip()}")
        sys.exit(1)


def install_dependencies():
    """Install all Python dependencies (core and dev) into venv"""
    print_section("Installing Python Dependencies")
    venv_pip = os.path.join("venv", "bin", "pip")
    
    if not os.path.exists(venv_pip):
        console.print("❌ [bold red]Virtual environment setup failed.[/bold red] Could not find pip.")
        sys.exit(1)

    all_dependencies = CORE_DEPENDENCIES + DEV_DEPENDENCIES
    
    console.print(f"Installing {

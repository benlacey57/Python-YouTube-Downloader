"""Main menu display"""
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()


class Menu:
    """Main menu display and handling"""

    @staticmethod
    def display_main_menu() -> str:
        """Display main menu with enhanced UI"""
        console.print("\n")

        title = Panel.fit(
            "[bold cyan]Playlist Downloader Pro[/bold cyan]\n"
            "Advanced video/audio playlist management",
            border_style="cyan",
            padding=(1, 2)
        )
        console.print(title)

        options = [
            ("1", "Download new playlist"),
            ("2", "Resume incomplete download"),
            ("3", "Search channel for playlists"),
            ("4", "View queue status"),
            ("5", "View statistics"),
            ("6", "Monitoring"),
            ("7", "Settings"),
            ("8", "Exit")
        ]

        option_text = "\n".join([f"  {num}. {desc}" for num, desc in options])

        menu_panel = Panel(
            option_text,
            title="[bold]Main Menu[/bold]",
            border_style="blue",
            padding=(1, 2)
        )
        console.print(menu_panel)

        choice = Prompt.ask(
            "\n[bold cyan]Select an option[/bold cyan]",
            choices=[num for num, _ in options],
            default="1"
        )

        return choice

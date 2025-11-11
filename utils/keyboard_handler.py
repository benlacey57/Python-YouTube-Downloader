"""Keyboard handler for mobile-friendly shortcuts"""
import sys
import threading
import signal
import time
from typing import Callable, Optional, Dict
from rich.console import Console

console = Console()


class KeyboardHandler:
    """Handles keyboard shortcuts including mobile-friendly single key presses"""
    
    def __init__(self):
        self.cancel_requested = False
        self.pause_requested = False
        self.skip_requested = False
        self.listener_thread: Optional[threading.Thread] = None
        self.running = False
        self.callbacks: Dict[str, Callable] = {}
        self._last_key_time = 0
        self._debounce_delay = 0.3  # Prevent accidental double presses
        
    def register_callback(self, key: str, callback: Callable):
        """Register a callback for a specific key"""
        self.callbacks[key.lower()] = callback
    
    def start_listening(self):
        """Start listening for keyboard input"""
        if self.running:
            return
        
        self.running = True
        self.cancel_requested = False
        self.pause_requested = False
        self.skip_requested = False
        
        self.listener_thread = threading.Thread(target=self._listen_loop, daemon=True)
        self.listener_thread.start()
        
        console.print("\n[dim]────────────────────────────────────────[/dim]")
        console.print("[bold cyan]Keyboard Shortcuts:[/bold cyan]")
        console.print("  [yellow]c[/yellow] - Cancel (finish current, stop queue)")
        console.print("  [yellow]p[/yellow] - Pause (finish current, wait)")
        console.print("  [yellow]r[/yellow] - Resume downloads")
        console.print("  [yellow]s[/yellow] - Skip current download")
        console.print("  [yellow]q[/yellow] - Quit immediately")
        console.print("[dim]────────────────────────────────────────[/dim]\n")
    
    def stop_listening(self):
        """Stop listening for keyboard input"""
        self.running = False
        if self.listener_thread:
            self.listener_thread.join(timeout=1)
    
    def _listen_loop(self):
        """Main listening loop - works on Unix and Windows"""
        try:
            if sys.platform == 'win32':
                self._listen_windows()
            else:
                self._listen_unix()
        except Exception as e:
            console.print(f"[dim][yellow]Keyboard handler error: {e}[/yellow][/dim]")
    
    def _listen_windows(self):
        """Listen for keys on Windows"""
        try:
            import msvcrt
            
            while self.running:
                if msvcrt.kbhit():
                    try:
                        key = msvcrt.getch().decode('utf-8', errors='ignore').lower()
                        self._handle_key(key)
                    except:
                        pass
                time.sleep(0.05)  # Small delay to prevent CPU spinning
        except ImportError:
            console.print("[yellow]msvcrt not available on this platform[/yellow]")
    
    def _listen_unix(self):
        """Listen for keys on Unix/Linux/Mac"""
        try:
            import termios
            import tty
            import select
            
            # Save terminal settings
            stdin_fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(stdin_fd)
            
            try:
                # Set terminal to raw mode for single character input
                tty.setcbreak(stdin_fd)
                
                while self.running:
                    # Check if input is available (non-blocking)
                    if select.select([sys.stdin], [], [], 0.1)[0]:
                        try:
                            key = sys.stdin.read(1).lower()
                            self._handle_key(key)
                        except:
                            pass
            finally:
                # Restore terminal settings
                termios.tcsetattr(stdin_fd, termios.TCSADRAIN, old_settings)
        
        except Exception as e:
            console.print(f"[yellow]Unix keyboard handler error: {e}[/yellow]")
    
    def _handle_key(self, key: str):
        """Handle a key press with debouncing"""
        current_time = time.time()
        
        # Debounce - ignore keys pressed too quickly
        if current_time - self._last_key_time < self._debounce_delay:
            return
        
        self._last_key_time = current_time
        
        # Handle specific keys
        if key == 'c':
            self.cancel_requested = True
            console.print("\n[yellow]⏹  Cancel requested - finishing current download...[/yellow]")
            console.print("[dim]Press 'q' to quit immediately[/dim]\n")
        
        elif key == 'p':
            if not self.pause_requested:
                self.pause_requested = True
                console.print("\n[yellow]⏸  Pause requested - finishing current download...[/yellow]")
                console.print("[dim]Press 'r' to resume[/dim]\n")
            else:
                console.print("\n[dim]Already paused. Press 'r' to resume.[/dim]\n")
        
        elif key == 'r':
            if self.pause_requested:
                self.pause_requested = False
                console.print("\n[green]▶️  Resuming downloads...[/green]\n")
            else:
                console.print("\n[dim]Downloads are not paused.[/dim]\n")
        
        elif key == 's':
            self.skip_requested = True
            console.print("\n[cyan]⏭  Skip requested - moving to next download...[/cyan]\n")
        
        elif key == 'q':
            console.print("\n[red]🛑 Quit requested - stopping immediately...[/red]\n")
            self.cancel_requested = True
            self.running = False
            
            # Send interrupt signal to cleanly exit
            import os
            os.kill(os.getpid(), signal.SIGINT)
        
        elif key == 'h' or key == '?':
            self._show_help()
        
        # Call registered callback if exists
        if key in self.callbacks:
            try:
                self.callbacks[key]()
            except Exception as e:
                console.print(f"[red]Callback error: {e}[/red]")
    
    def _show_help(self):
        """Show keyboard shortcuts help"""
        console.print("\n[cyan]═══════════════════════════════════════[/cyan]")
        console.print("[bold cyan]Keyboard Shortcuts Help:[/bold cyan]")
        console.print("[cyan]═══════════════════════════════════════[/cyan]")
        console.print("  [yellow]c[/yellow] - [white]Cancel queue (finishes current download)[/white]")
        console.print("  [yellow]p[/yellow] - [white]Pause downloads (after current finishes)[/white]")
        console.print("  [yellow]r[/yellow] - [white]Resume downloads[/white]")
        console.print("  [yellow]s[/yellow] - [white]Skip current download[/white]")
        console.print("  [yellow]q[/yellow] - [white]Quit immediately (no cleanup)[/white]")
        console.print("  [yellow]h[/yellow] or [yellow]?[/yellow] - [white]Show this help[/white]")
        console.print("[cyan]═══════════════════════════════════════[/cyan]\n")
    
    def is_cancelled(self) -> bool:
        """Check if cancellation was requested"""
        return self.cancel_requested
    
    def is_paused(self) -> bool:
        """Check if pause was requested"""
        return self.pause_requested
    
    def is_skip_requested(self) -> bool:
        """Check if skip was requested"""
        skip = self.skip_requested
        if skip:
            self.skip_requested = False  # Reset after checking
        return skip
    
    def reset(self):
        """Reset all flags"""
        self.cancel_requested = False
        self.pause_requested = False
        self.skip_requested = False
    
    def get_status(self) -> str:
        """Get current status as string"""
        if self.cancel_requested:
            return "Cancelled"
        elif self.pause_requested:
            return "Paused"
        else:
            return "Running"


# Global keyboard handler instance
keyboard_handler = KeyboardHandler()


# Example usage function
def demo_keyboard_handler():
    """Demo of keyboard handler usage"""
    from rich.progress import Progress, SpinnerColumn, TextColumn
    import time
    
    console.print("[cyan]Starting demo - try pressing keys![/cyan]")
    
    keyboard_handler.start_listening()
    
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            task = progress.add_task("Downloading...", total=100)
            
            for i in range(100):
                # Check for cancellation
                if keyboard_handler.is_cancelled():
                    console.print("[yellow]Download cancelled![/yellow]")
                    break
                
                # Check for pause
                while keyboard_handler.is_paused() and not keyboard_handler.is_cancelled():
                    time.sleep(0.5)
                
                # Check for skip
                if keyboard_handler.is_skip_requested():
                    console.print("[cyan]Skipping to next...[/cyan]")
                    break
                
                # Simulate work
                time.sleep(0.1)
                progress.update(task, advance=1)
        
        console.print(f"[green]Demo completed! Status: {keyboard_handler.get_status()}[/green]")
    
    finally:
        keyboard_handler.stop_listening()
        keyboard_handler.reset()


if __name__ == "__main__":
    demo_keyboard_handler()

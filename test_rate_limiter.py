#!/usr/bin/env python3
"""Test rate limiter"""
from utils.rate_limiter import RateLimiter
from rich.console import Console
import time

console = Console()


def test_rate_limiter():
    """Test rate limiter functionality"""
    console.print("[cyan]Testing Rate Limiter...[/cyan]\n")
    
    # Create rate limiter with low limits for testing
    rate_limiter = RateLimiter(
        max_downloads_per_hour=5,
        min_delay_seconds=0.5,
        max_delay_seconds=1.0
    )
    
    console.print("[yellow]Testing 10 downloads with 5/hour limit...[/yellow]\n")
    
    for i in range(10):
        console.print(f"[cyan]Download {i+1}...[/cyan]")
        
        # Show stats before
        stats = rate_limiter.get_stats()
        console.print(f"  Before: {stats['downloads_this_hour']}/{stats['max_per_hour']} "
                     f"({stats['remaining']} remaining)")
        
        # Wait if needed
        start_time = time.time()
        rate_limiter.wait_if_needed()
        elapsed = time.time() - start_time
        
        if elapsed > 1:
            console.print(f"  [yellow]Waited {elapsed:.1f}s for rate limit[/yellow]")
        else:
            console.print(f"  [green]Proceeded after {elapsed:.1f}s delay[/green]")
        
        # Simulate download
        time.sleep(0.1)
    
    console.print("\n[green]✓ Rate limiter test completed![/green]")
    
    # Final stats
    stats = rate_limiter.get_stats()
    console.print(f"\nFinal stats: {stats['downloads_this_hour']}/{stats['max_per_hour']} used")
    console.print(f"Percentage: {stats['percentage_used']:.1f}%")


def test_rate_limiter_stats():
    """Test rate limiter statistics"""
    console.print("\n[cyan]Testing Rate Limiter Stats...[/cyan]\n")
    
    rate_limiter = RateLimiter(
        max_downloads_per_hour=50,
        min_delay_seconds=2.0,
        max_delay_seconds=5.0
    )
    
    # Simulate some downloads
    for i in range(10):
        rate_limiter.wait_if_needed()
    
    stats = rate_limiter.get_stats()
    
    console.print("[cyan]Statistics:[/cyan]")
    console.print(f"  Downloads this hour: {stats['downloads_this_hour']}")
    console.print(f"  Max per hour: {stats['max_per_hour']}")
    console.print(f"  Remaining: {stats['remaining']}")
    console.print(f"  Usage: {stats['percentage_used']:.1f}%")
    
    console.print("\n[green]✓ Stats test completed![/green]")


if __name__ == "__main__":
    try:
        test_rate_limiter()
        test_rate_limiter_stats()
    except KeyboardInterrupt:
        console.print("\n[yellow]Test interrupted[/yellow]")

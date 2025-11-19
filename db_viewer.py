#!/usr/bin/env python3
"""SQLite Database Viewer for YouTube Playlist Downloader"""
import sqlite3
import sys
from pathlib import Path
from typing import List, Tuple
import os

# Banner
BANNER = """
╔═══════════════════════════════════════════════════════════════════════════╗
║                                                                           ║
║                    SQLite Database Viewer                                ║
║              YouTube Playlist Downloader Database Inspector              ║
║                                                                           ║
╚═══════════════════════════════════════════════════════════════════════════╝
"""


def print_banner():
    """Print viewer banner"""
    print(BANNER)
    print()


def print_section(title):
    """Print a section header"""
    print(f"\n{'═' * 75}")
    print(f"  {title}")
    print(f"{'═' * 75}\n")


def get_database_size(db_path: Path) -> str:
    """Get database file size"""
    if not db_path.exists():
        return "N/A"
    
    size_bytes = db_path.stat().st_size
    
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_table_info(cursor: sqlite3.Cursor, table_name: str) -> Tuple[int, List[str]]:
    """Get row count and column names for a table"""
    # Get row count
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    row_count = cursor.fetchone()[0]
    
    # Get column names
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [row[1] for row in cursor.fetchall()]
    
    return row_count, columns


def format_value(value, max_length: int = 50) -> str:
    """Format a value for display"""
    if value is None:
        return "NULL"
    
    str_value = str(value)
    if len(str_value) > max_length:
        return str_value[:max_length - 3] + "..."
    return str_value


def display_table_summary(cursor: sqlite3.Cursor, tables: List[str]):
    """Display summary of all tables"""
    print("TABLE SUMMARY")
    print("─" * 75)
    print(f"{'Table Name':<30} {'Row Count':>15} {'Columns':>10}")
    print("─" * 75)
    
    for table_name in tables:
        row_count, columns = get_table_info(cursor, table_name)
        print(f"{table_name:<30} {row_count:>15,} {len(columns):>10}")
    
    print("─" * 75)


def display_table_data(cursor: sqlite3.Cursor, table_name: str, limit: int = 10):
    """Display last N rows of a table"""
    print_section(f"Table: {table_name}")
    
    # Get table info
    row_count, columns = get_table_info(cursor, table_name)
    
    print(f"Total rows: {row_count:,}")
    print(f"Columns: {', '.join(columns)}\n")
    
    if row_count == 0:
        print("⊙ Table is empty\n")
        return
    
    # Get last N rows
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid DESC LIMIT {limit}")
    rows = cursor.fetchall()
    
    if not rows:
        print("⊙ No data to display\n")
        return
    
    # Display rows
    print(f"Showing last {len(rows)} entries:\n")
    
    for i, row in enumerate(reversed(rows), 1):
        print(f"Entry #{i}")
        print("─" * 60)
        for col_name, value in zip(columns, row):
            formatted_value = format_value(value)
            print(f"  {col_name:<25}: {formatted_value}")
        print()


def view_database(db_path: str):
    """Main database viewing function"""
    db_file = Path(db_path)
    
    if not db_file.exists():
        print(f"❌ Database file not found: {db_path}")
        sys.exit(1)
    
    print_banner()
    
    print(f"📂 Database: {db_path}")
    print(f"💾 File Size: {get_database_size(db_file)}")
    
    try:
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        if not tables:
            print("\n⊙ Database has no tables")
            conn.close()
            return
        
        print(f"📊 Tables: {len(tables)}\n")
        
        # Display summary
        print_section("Database Overview")
        display_table_summary(cursor, tables)
        
        # Display each table
        for table_name in tables:
            display_table_data(cursor, table_name)
            
            # Prompt to continue
            if table_name != tables[-1]:  # Not the last table
                response = input("Press Enter to view next table (or 'q' to quit): ").strip().lower()
                if response == 'q':
                    break
        
        conn.close()
        print_section("End of Database")
        
    except sqlite3.Error as e:
        print(f"\n❌ Database error: {e}")
        sys.exit(1)


def list_databases():
    """List available database files"""
    print_banner()
    print_section("Available Databases")
    
    db_files = [
        "downloads.db",
        "stats.db"
    ]
    
    found_dbs = []
    for db_file in db_files:
        path = Path(db_file)
        if path.exists():
            size = get_database_size(path)
            print(f"✓ {db_file:<20} ({size})")
            found_dbs.append(db_file)
        else:
            print(f"⊙ {db_file:<20} (not found)")
    
    print()
    
    if not found_dbs:
        print("No database files found.")
        sys.exit(0)
    
    return found_dbs


def main():
    """Main entry point"""
    try:
        # Check arguments
        if len(sys.argv) > 1:
            db_path = sys.argv[1]
            view_database(db_path)
        else:
            # Interactive mode
            found_dbs = list_databases()
            
            if len(found_dbs) == 1:
                print(f"Viewing: {found_dbs[0]}\n")
                input("Press Enter to continue...")
                view_database(found_dbs[0])
            else:
                print("Select a database to view:")
                for i, db in enumerate(found_dbs, 1):
                    print(f"  {i}. {db}")
                print(f"  0. Exit")
                
                choice = input("\nEnter selection: ").strip()
                
                if choice == "0":
                    print("Exiting...")
                    sys.exit(0)
                
                try:
                    idx = int(choice) - 1
                    if 0 <= idx < len(found_dbs):
                        view_database(found_dbs[idx])
                    else:
                        print("Invalid selection")
                        sys.exit(1)
                except ValueError:
                    print("Invalid input")
                    sys.exit(1)
        
    except KeyboardInterrupt:
        print("\n\n⊙ Viewer closed")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

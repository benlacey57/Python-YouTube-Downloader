"""Database migration system"""
import sqlite3
from pathlib import Path
from typing import List, Callable
from datetime import datetime


class Migration:
    """Represents a single database migration"""
    
    def __init__(self, version: int, description: str, up: Callable, down: Callable = None):
        self.version = version
        self.description = description
        self.up = up
        self.down = down
    
    def apply(self, conn: sqlite3.Connection):
        """Apply the migration"""
        self.up(conn)
    
    def rollback(self, conn: sqlite3.Connection):
        """Rollback the migration"""
        if self.down:
            self.down(conn)


class MigrationManager:
    """Manages database migrations"""
    
    def __init__(self, db_path: str = "downloads.db"):
        self.db_path = Path(db_path)
        self.migrations: List[Migration] = []
        self._register_migrations()
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _ensure_migrations_table(self, conn: sqlite3.Connection):
        """Ensure the migrations tracking table exists"""
        conn.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version INTEGER PRIMARY KEY,
                description TEXT NOT NULL,
                applied_at TEXT NOT NULL
            )
        """)
        conn.commit()
    
    def _get_current_version(self, conn: sqlite3.Connection) -> int:
        """Get the current schema version"""
        try:
            cursor = conn.execute("SELECT MAX(version) FROM schema_migrations")
            result = cursor.fetchone()[0]
            return result if result is not None else 0
        except sqlite3.OperationalError:
            return 0
    
    def _register_migrations(self):
        """Register all migrations in order"""
        
        # Migration 1: Add status column to queues table if missing
        def migration_1_up(conn):
            """Add status column to queues if it doesn't exist"""
            cursor = conn.cursor()
            
            # Check if status column exists
            cursor.execute("PRAGMA table_info(queues)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'status' not in columns:
                cursor.execute("ALTER TABLE queues ADD COLUMN status TEXT DEFAULT 'pending'")
                print("  ✓ Added status column to queues table")
            else:
                print("  ⊙ Status column already exists in queues table")
            
            conn.commit()
        
        self.migrations.append(Migration(
            version=1,
            description="Add status column to queues table",
            up=migration_1_up
        ))
        
        # Migration 2: Add filename_template to queues if missing
        def migration_2_up(conn):
            """Add filename_template column to queues if it doesn't exist"""
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(queues)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'filename_template' not in columns:
                cursor.execute("ALTER TABLE queues ADD COLUMN filename_template TEXT")
                print("  ✓ Added filename_template column to queues table")
            else:
                print("  ⊙ Filename_template column already exists")
            
            conn.commit()
        
        self.migrations.append(Migration(
            version=2,
            description="Add filename_template column to queues table",
            up=migration_2_up
        ))
        
        # Migration 3: Add storage fields to queues if missing
        def migration_3_up(conn):
            """Add storage-related columns to queues if they don't exist"""
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(queues)")
            columns = [row[1] for row in cursor.fetchall()]
            
            if 'storage_provider' not in columns:
                cursor.execute("ALTER TABLE queues ADD COLUMN storage_provider TEXT DEFAULT 'local'")
                print("  ✓ Added storage_provider column to queues table")
            
            if 'storage_video_quality' not in columns:
                cursor.execute("ALTER TABLE queues ADD COLUMN storage_video_quality TEXT")
                print("  ✓ Added storage_video_quality column to queues table")
            
            if 'storage_audio_quality' not in columns:
                cursor.execute("ALTER TABLE queues ADD COLUMN storage_audio_quality TEXT")
                print("  ✓ Added storage_audio_quality column to queues table")
            
            conn.commit()
        
        self.migrations.append(Migration(
            version=3,
            description="Add storage-related columns to queues table",
            up=migration_3_up
        ))
        
        # Migration 4: Ensure all required indexes exist
        def migration_4_up(conn):
            """Create indexes if they don't exist"""
            cursor = conn.cursor()
            
            # Check existing indexes
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index'")
            existing_indexes = {row[0] for row in cursor.fetchall()}
            
            indexes = [
                ("idx_queues_status", "CREATE INDEX IF NOT EXISTS idx_queues_status ON queues(status)"),
                ("idx_items_queue", "CREATE INDEX IF NOT EXISTS idx_items_queue ON download_items(queue_id)"),
                ("idx_items_status", "CREATE INDEX IF NOT EXISTS idx_items_status ON download_items(status)"),
                ("idx_stats_date", "CREATE INDEX IF NOT EXISTS idx_stats_date ON statistics(date)"),
                ("idx_channels_monitored", "CREATE INDEX IF NOT EXISTS idx_channels_monitored ON channels(is_monitored, enabled)"),
            ]
            
            for idx_name, idx_sql in indexes:
                if idx_name not in existing_indexes:
                    cursor.execute(idx_sql)
                    print(f"  ✓ Created index: {idx_name}")
            
            conn.commit()
        
        self.migrations.append(Migration(
            version=4,
            description="Ensure all required indexes exist",
            up=migration_4_up
        ))
    
    def migrate(self) -> bool:
        """Run all pending migrations"""
        conn = self._get_connection()
        
        try:
            self._ensure_migrations_table(conn)
            current_version = self._get_current_version(conn)
            
            print(f"Current schema version: {current_version}")
            
            # Find pending migrations
            pending = [m for m in self.migrations if m.version > current_version]
            
            if not pending:
                print("✓ Database schema is up to date")
                return True
            
            print(f"Found {len(pending)} pending migration(s)")
            
            # Apply each migration
            for migration in pending:
                print(f"\nApplying migration {migration.version}: {migration.description}")
                
                try:
                    migration.apply(conn)
                    
                    # Record the migration
                    conn.execute(
                        "INSERT INTO schema_migrations (version, description, applied_at) VALUES (?, ?, ?)",
                        (migration.version, migration.description, datetime.now().isoformat())
                    )
                    conn.commit()
                    
                    print(f"✓ Migration {migration.version} applied successfully")
                    
                except Exception as e:
                    print(f"✗ Migration {migration.version} failed: {e}")
                    conn.rollback()
                    raise
            
            print(f"\n✓ All migrations completed. Current version: {self._get_current_version(conn)}")
            return True
            
        except Exception as e:
            print(f"✗ Migration failed: {e}")
            return False
            
        finally:
            conn.close()
    
    def get_migration_status(self) -> dict:
        """Get the current migration status"""
        conn = self._get_connection()
        
        try:
            self._ensure_migrations_table(conn)
            current_version = self._get_current_version(conn)
            
            applied = []
            cursor = conn.execute("SELECT version, description, applied_at FROM schema_migrations ORDER BY version")
            for row in cursor.fetchall():
                applied.append({
                    'version': row[0],
                    'description': row[1],
                    'applied_at': row[2]
                })
            
            pending = [
                {'version': m.version, 'description': m.description}
                for m in self.migrations if m.version > current_version
            ]
            
            return {
                'current_version': current_version,
                'total_migrations': len(self.migrations),
                'applied': applied,
                'pending': pending
            }
            
        finally:
            conn.close()


def run_migrations(db_path: str = "downloads.db") -> bool:
    """Convenience function to run all migrations"""
    manager = MigrationManager(db_path)
    return manager.migrate()


if __name__ == "__main__":
    # Run migrations when executed directly
    print("=" * 70)
    print("  Database Migration Tool")
    print("=" * 70)
    print()
    
    success = run_migrations()
    
    if success:
        print("\n✓ Database migrations completed successfully")
    else:
        print("\n✗ Database migrations failed")
        exit(1)

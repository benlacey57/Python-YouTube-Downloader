# Changelog - November 2025 Updates

## Major Improvements

### 1. Simplified Menu Structure ✅
**Problem:** Settings menu had 21 options making it overwhelming and hard to navigate.

**Solution:** Reorganized into 5 logical submenus:
- **Download Settings** - Quality, timeout, parallel downloads, filename options
- **Network & Proxy Settings** - Proxies, authentication, rate limiting, bandwidth
- **Notifications** - Slack, email, alerts, preferences
- **Storage Management** - Storage providers configuration
- **Advanced Settings** - Live streams, system status, database, config management

**Files Changed:**
- `ui/settings_menu.py` - Simplified from 21 options to 5 submenus
- `ui/download_settings_submenu.py` - New submenu (5 options)
- `ui/notifications_submenu.py` - New submenu (5 options)
- `ui/advanced_settings_submenu.py` - New submenu (5 options)

### 2. Enhanced Installation Script ✅
**Problems:** 
- Missing `check_system_dependencies()` function causing install failures
- No fresh install option to clean existing data

**Solutions:**
- Added `check_system_dependencies()` function that verifies:
  - ffmpeg installation (recommended for best quality)
  - git installation (optional)
  - Provides installation instructions for missing dependencies
- Implemented `--fresh` flag to remove existing data before install
  - Removes: data/, logs/, *.db files, config files
  - Prompts for confirmation before deletion

**Usage:**
```bash
python3 install.py           # Normal install
python3 install.py --fresh   # Fresh install (removes existing data)
```

### 3. Improved Proxy Management ✅
**Problems:**
- Proxy testing showed raw exceptions
- No detection when proxies.txt exists
- No removal of failed proxies

**Solutions:**
- **Better Error Display:** Categorized errors with clean formatting
  - Connection timeout
  - Proxy errors  
  - HTTP status codes
  - Connection errors
- **Summary Display:** Shows working vs failed proxy counts
- **Auto-removal:** Prompts to remove failed proxies after testing
- **Load from File:** New option to load proxies from `proxies.txt`
  - Detects existing file properly
  - Options to replace or add to existing proxies
  - Shows current directory if file not found

**Files Changed:**
- `ui/network_settings_menu.py` - Enhanced proxy testing and added file loading

### 4. Enhanced Download Display ✅
**Problem:** Proxy selection not clearly shown during downloads.

**Solution:**
- Shows selected proxy for each download item with arrows (► and ↪)
- Displays proxy in both rotation and fixed modes
- Clear visual indicators for:
  - Item number and title
  - Selected proxy
  - Download status

**Example Output:**
```
► [1/10] Song Title Here
↪ Proxy: 103.26.176.31:8080
✓ Downloaded successfully
```

### 5. Download All Option ✅
**Problem:** No way to redownload all items ignoring past download logs.

**Solution:**
- Added prompt when downloading queue: "Download all items (ignoring past download logs)?"
- If yes: Resets all items to PENDING status and downloads everything
- If no: Downloads only pending items (default behavior)
- Shows mode in download header

**Files Changed:**
- `ui/menu.py` - Added download all prompt
- `downloaders/playlist.py` - Added `download_all` parameter

### 6. Comprehensive Makefile ✅
**Problem:** No simple way to run common operations.

**Solution:** Created Makefile with targets:
- `make install` - Install application and dependencies
- `make install-fresh` - Fresh install removing existing data
- `make run` - Run the application
- `make test` - Run tests
- `make lint` - Run linters (ruff if available)
- `make format` - Format code (ruff or black)
- `make check-deps` - Check system dependencies
- `make clean` - Clean cache and temporary files
- `make uninstall` - Uninstall application data
- `make db-viewer` - Start database viewer
- `make seed` - Seed database
- `make help` - Show all available targets

**Usage:**
```bash
make help          # See all commands
make install       # Install everything
make run           # Start application
make clean         # Clean up cache
```

## Summary of Files Modified

### New Files Created
- `ui/download_settings_submenu.py`
- `ui/notifications_submenu.py`
- `ui/advanced_settings_submenu.py`
- `Makefile`
- `CHANGELOG_2025.md`

### Files Modified
- `ui/settings_menu.py` - Simplified to 5 submenu options
- `ui/menu.py` - Added download all option
- `ui/network_settings_menu.py` - Enhanced proxy testing and file loading
- `install.py` - Added system dependency checks and --fresh flag
- `downloaders/playlist.py` - Enhanced proxy display and download all mode

## Testing Checklist

- [x] Settings menu navigation works
- [x] All submenu options accessible
- [x] Proxy loading from file works
- [x] Proxy testing shows formatted errors
- [x] Failed proxies can be removed
- [x] Download all option prompts correctly
- [x] Makefile targets execute properly
- [x] Fresh install flag removes data
- [x] System dependency check works
- [x] Python syntax validates

## Next Steps for User

1. **Test the new menu structure:**
   ```bash
   python3 main.py
   # Navigate to Settings → Download Settings/Network/etc.
   ```

2. **Load proxies from file:**
   ```bash
   # In menu: Settings → Network & Proxy Settings → Load proxies from file
   # Enter: proxies.txt (default)
   ```

3. **Test proxies:**
   ```bash
   # In menu: Settings → Network & Proxy Settings → Test proxies
   # Review results and remove failed ones
   ```

4. **Try fresh install:**
   ```bash
   make install-fresh
   # or
   python3 install.py --fresh
   ```

5. **Use Makefile for operations:**
   ```bash
   make help          # See all commands
   make check-deps    # Verify dependencies
   make clean         # Clean cache
   ```

## Notes

- **Parallel Downloads:** The current implementation uses sequential downloads with a progress bar. True parallel downloads with multiple simultaneous progress bars would require significant refactoring of the download architecture.
  
- **Metadata Downloads:** The system downloads actual video/audio data, not just metadata. Metadata is extracted during download and embedded into files.

- **Progress Display:** Each item shows progress during download. For better per-item progress bars with parallel downloads, consider using `rich.progress.Progress` with multiple tasks.

## Test Suite Organization ✅

### Improvements Made
1. **Removed misplaced files**: Deleted non-test file from tests directory
2. **Created comprehensive fixtures**: `tests/conftest.py` with shared fixtures for:
   - Configuration, models, managers, file operations, network mocking
3. **Created new tests**: Tests for all new submenu components
4. **Organized test structure**: Clear directory structure with unit tests by category
5. **Documentation**: Added `tests/README.md` and `tests/TEST_STATUS.md`

### Running Tests
```bash
# Run all tests
make test

# Run with coverage
python3 -m pytest tests/ --cov=. --cov-report=term-missing

# Run specific tests
python3 -m pytest tests/unit/ui/ -v

# Interactive test runner
python3 tests/run.py
```

### Test Coverage
- **Target**: 80% code coverage
- **New tests created**: 3 test files for new UI submenus
- **Shared fixtures**: Centralized in conftest.py for consistency
- **Test markers**: `live`, `managers`, `models`, `ui`, `utils` for selective running

### Files Created
- `tests/conftest.py` - Shared test fixtures and configuration
- `tests/README.md` - Test suite documentation
- `tests/TEST_STATUS.md` - Test coverage status and roadmap
- `tests/unit/ui/test_download_settings_submenu.py` - Tests for download settings
- `tests/unit/ui/test_notifications_submenu.py` - Tests for notifications
- `tests/unit/ui/test_advanced_settings_submenu.py` - Tests for advanced settings

### Next Steps
See `tests/TEST_STATUS.md` for:
- Current test coverage status
- Tests that need import fixes
- Tests still needed (downloaders, managers, utils)
- Testing best practices

## Download Experience Improvements ✅

### Problem
- Verbose yt-dlp output cluttering the screen (warnings, API calls)
- No way to resume interrupted downloads
- Missing ffmpeg warnings on every download

### Solution
**Quiet Mode for Downloads**
- Enabled `quiet` and `no_warnings` in yt-dlp options
- Suppressed YouTube API extraction messages
- Kept only the essential progress bar
- Cleaner, more professional download experience

**Resume Queue Feature**
- Added "Resume queue" option to main menu
- Automatically tracks interrupted downloads
- Shows pending item count for each resumable queue
- Continues from where you left off

**Files Changed:**
- `downloaders/base.py` - Enabled quiet mode, suppressed warnings
- `ui/menu.py` - Added resume queue menu option (#4)
- `managers/queue_manager.py` - Already has resume tracking functionality

**Usage:**
```
Main Menu:
  1. Add new download queue
  2. View queues
  3. Download queue
  4. Resume queue          ← NEW!
  5. View statistics
  6. Channel monitoring
  7. Storage management
  8. Settings
  9. Exit
```

## Database Migration System ✅

### Problem
- Installation failing with "no such column: status" error
- No way to handle schema changes between versions
- Old databases incompatible with new code

### Solution
**Created Proper Migration System**
- New file: `database/migrations.py`
- Tracks schema version in `schema_migrations` table
- Four initial migrations to fix existing databases
- Idempotent - safe to run multiple times

**Migrations:**
1. Add `status` column to queues table
2. Add `filename_template` column
3. Add storage-related columns
4. Create all required indexes

**Updated Installation:**
- Creates virtual environment automatically
- Runs migrations during install (no data loss)
- Fixed "externally-managed-environment" error

**Usage:**
```bash
make migrate          # Run migrations manually
make install          # Includes migrations
python3 -m database.migrations  # Direct execution
```

## Compatibility

- Python 3.8+ required
- Ubuntu/Debian tested
- Should work on macOS and other Linux distros
- Windows: Makefile may need adaptation (consider using `make` alternatives)

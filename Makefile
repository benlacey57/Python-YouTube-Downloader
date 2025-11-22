.PHONY: help install install-fresh run test clean uninstall lint format check-deps setup

# Default target
help:
	@echo "YouTube Playlist Downloader - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make setup          - Quick setup (install + migrate)"
	@echo "  make install        - Install the application and dependencies"
	@echo "  make install-fresh  - Fresh install (removes existing data)"
	@echo "  make run            - Run the application"
	@echo "  make test           - Run tests"
	@echo "  make test-coverage  - Run tests with coverage report"
	@echo "  make test-file      - Run specific test file (FILE=path/to/test.py)"
	@echo "  make migrate        - Run database migrations"
	@echo "  make load-proxies   - Load proxies from proxies.txt"
	@echo "  make backup         - Backup configuration and database"
	@echo "  make restore        - Restore from backup"
	@echo "  make status         - Show application status"
	@echo "  make lint           - Run linters (if available)"
	@echo "  make format         - Format code (if available)"
	@echo "  make check-deps     - Check system dependencies"
	@echo "  make clean          - Clean cache and temporary files"
	@echo "  make uninstall      - Uninstall application data"
	@echo "  make help           - Show this help message"
	@echo ""
	@echo "Quick Start:"
	@echo "  1. make setup       - First time setup"
	@echo "  2. make run         - Start the application"

# Quick setup (first time use)
setup: install migrate
	@echo ""
	@echo "✓ Setup complete! Run 'make run' to start the application."

# Install the application
install:
	@echo "Installing YouTube Playlist Downloader..."
	python3 install.py

# Fresh install (removes existing data)
install-fresh:
	@echo "Fresh installing YouTube Playlist Downloader..."
	python3 install.py --fresh

# Run the application
run:
	@if [ ! -f "venv/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Starting YouTube Playlist Downloader..."
	./run.sh

# Run tests
test:
	@if [ ! -f "venv/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Running tests..."
	. venv/bin/activate && pytest tests/ -v

# Run tests with coverage report
test-coverage:
	@if [ ! -f "venv/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Running tests with coverage..."
	. venv/bin/activate && pytest tests/ -v --cov=. --cov-report=html --cov-report=term-missing
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Run specific test file
test-file:
	@if [ ! -f "venv/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@if [ -z "$(FILE)" ]; then \
		echo "Usage: make test-file FILE=tests/unit/managers/test_queue_manager.py"; \
		exit 1; \
	fi
	@echo "Running test file: $(FILE)"
	. venv/bin/activate && pytest $(FILE) -v

# Lint code
lint:
	@if [ ! -f "venv/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Running linters..."
	@if command -v ruff > /dev/null; then \
		. venv/bin/activate && ruff check .; \
	else \
		echo "Ruff not installed. Skipping lint."; \
	fi

# Format code
format:
	@if [ ! -f "venv/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Formatting code..."
	@if command -v ruff > /dev/null; then \
		. venv/bin/activate && ruff format .; \
	elif command -v black > /dev/null; then \
		. venv/bin/activate && black .; \
	else \
		echo "No formatter installed. Install ruff or black."; \
	fi

# Check system dependencies
check-deps:
	@echo "Checking system dependencies..."
	@echo ""
	@echo "Python version:"
	@python3 --version
	@echo ""
	@echo "ffmpeg:"
	@if command -v ffmpeg > /dev/null; then \
		ffmpeg -version | head -n 1; \
	else \
		echo "  Not installed (recommended)"; \
	fi
	@echo ""
	@echo "git:"
	@if command -v git > /dev/null; then \
		git --version; \
	else \
		echo "  Not installed (optional)"; \
	fi

# Clean cache and temporary files
clean:
	@echo "Cleaning cache and temporary files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	@echo "Clean complete!"

# Uninstall application data
uninstall:
	@echo "Uninstalling YouTube Playlist Downloader..."
	python3 uninstall.py

# Database viewer
db-viewer:
	@if [ ! -f "venv/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Starting database viewer..."
	. venv/bin/activate && python3 db_viewer.py

# Seed database
seed:
	@if [ ! -f "venv/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Seeding database..."
	. venv/bin/activate && python3 seed_database.py

# Run database migrations
migrate:
	@if [ ! -f "venv/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@echo "Running database migrations..."
	. venv/bin/activate && python3 -m database.migrations

# Load proxies from proxies.txt
load-proxies:
	@if [ ! -f "venv/bin/activate" ]; then \
		echo "Virtual environment not found. Run 'make install' first."; \
		exit 1; \
	fi
	@if [ ! -f "proxies.txt" ]; then \
		echo "proxies.txt not found. Create it with one proxy per line."; \
		exit 1; \
	fi
	@echo "Loading proxies from proxies.txt..."
	. venv/bin/activate && python3 load_proxies.py

# Backup configuration and database
backup:
	@echo "Creating backup..."
	@mkdir -p backups
	@BACKUP_NAME="backup-$$(date +%Y%m%d-%H%M%S)"; \
	echo "Backup name: $$BACKUP_NAME"; \
	mkdir -p "backups/$$BACKUP_NAME"; \
	if [ -f "downloader_config.json" ]; then \
		cp downloader_config.json "backups/$$BACKUP_NAME/"; \
		echo "✓ Backed up configuration"; \
	fi; \
	if [ -d "data" ]; then \
		cp -r data "backups/$$BACKUP_NAME/"; \
		echo "✓ Backed up database"; \
	fi; \
	if [ -f "proxies.txt" ]; then \
		cp proxies.txt "backups/$$BACKUP_NAME/"; \
		echo "✓ Backed up proxies"; \
	fi; \
	echo "✓ Backup complete: backups/$$BACKUP_NAME"

# Restore from backup
restore:
	@if [ ! -d "backups" ] || [ -z "$$(ls -A backups)" ]; then \
		echo "No backups found in backups/ directory"; \
		exit 1; \
	fi
	@echo "Available backups:"
	@ls -1 backups/ | nl
	@echo ""
	@read -p "Enter backup number to restore (or 'q' to cancel): " num; \
	if [ "$$num" = "q" ]; then \
		echo "Cancelled."; \
		exit 0; \
	fi; \
	BACKUP=$$(ls -1 backups/ | sed -n "$${num}p"); \
	if [ -z "$$BACKUP" ]; then \
		echo "Invalid selection."; \
		exit 1; \
	fi; \
	echo "Restoring from: $$BACKUP"; \
	if [ -f "backups/$$BACKUP/downloader_config.json" ]; then \
		cp "backups/$$BACKUP/downloader_config.json" .; \
		echo "✓ Restored configuration"; \
	fi; \
	if [ -d "backups/$$BACKUP/data" ]; then \
		cp -r "backups/$$BACKUP/data" .; \
		echo "✓ Restored database"; \
	fi; \
	if [ -f "backups/$$BACKUP/proxies.txt" ]; then \
		cp "backups/$$BACKUP/proxies.txt" .; \
		echo "✓ Restored proxies"; \
	fi; \
	echo "✓ Restore complete"

# Show application status
status:
	@echo "YouTube Playlist Downloader - Status"
	@echo ""
	@echo "Environment:"
	@if [ -d "venv" ]; then \
		echo "  ✓ Virtual environment: Installed"; \
	else \
		echo "  ✗ Virtual environment: Not found"; \
	fi
	@echo ""
	@echo "Configuration:"
	@if [ -f "downloader_config.json" ]; then \
		echo "  ✓ Config file: Found"; \
		PROXY_COUNT=$$(grep -o '"proxies"' downloader_config.json 2>/dev/null | wc -l); \
		if [ $$PROXY_COUNT -gt 0 ]; then \
			echo "  ✓ Proxies: Configured"; \
		else \
			echo "  ⚠ Proxies: Not configured"; \
		fi; \
	else \
		echo "  ✗ Config file: Not found"; \
	fi
	@echo ""
	@echo "Database:"
	@if [ -f "data/downloader.db" ]; then \
		DB_SIZE=$$(du -h data/downloader.db | cut -f1); \
		echo "  ✓ Database: Found ($$DB_SIZE)"; \
	else \
		echo "  ✗ Database: Not found"; \
	fi
	@echo ""
	@echo "Backups:"
	@if [ -d "backups" ] && [ -n "$$(ls -A backups 2>/dev/null)" ]; then \
		BACKUP_COUNT=$$(ls -1 backups | wc -l); \
		echo "  ✓ Backups: $$BACKUP_COUNT available"; \
	else \
		echo "  ⚠ Backups: None found"; \
	fi

.PHONY: help install install-fresh run test clean uninstall lint format check-deps

# Default target
help:
	@echo "YouTube Playlist Downloader - Makefile"
	@echo ""
	@echo "Available targets:"
	@echo "  make install        - Install the application and dependencies"
	@echo "  make install-fresh  - Fresh install (removes existing data)"
	@echo "  make run            - Run the application"
	@echo "  make test           - Run tests"
	@echo "  make migrate        - Run database migrations"
	@echo "  make load-proxies   - Load proxies from proxies.txt"
	@echo "  make lint           - Run linters (if available)"
	@echo "  make format         - Format code (if available)"
	@echo "  make check-deps     - Check system dependencies"
	@echo "  make clean          - Clean cache and temporary files"
	@echo "  make uninstall      - Uninstall application data"
	@echo "  make help           - Show this help message"

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
	@echo "Running database migrations..."
	python3 -m database.migrations

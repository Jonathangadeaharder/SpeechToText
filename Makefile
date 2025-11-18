.PHONY: help lint format test structure clean all

# Default target
help:
	@echo "Available targets:"
	@echo "  make lint       - Run all linters (flake8, pylint, black check)"
	@echo "  make format     - Auto-format code with black"
	@echo "  make test       - Run pytest tests"
	@echo "  make structure  - Check project structure with structurelint"
	@echo "  make all        - Run all checks (format, lint, structure, test)"
	@echo "  make clean      - Remove cache files and build artifacts"

# Install structurelint (one-time setup)
install-structurelint:
	@echo "Installing structurelint..."
	@if ! command -v structurelint > /dev/null 2>&1; then \
		if ! command -v go > /dev/null 2>&1; then \
			echo "Error: Go is not installed. Please install Go first."; \
			exit 1; \
		fi; \
		git clone https://github.com/Jonathangadeaharder/structurelint.git /tmp/structurelint && \
		cd /tmp/structurelint && \
		go build -o $${HOME}/go/bin/structurelint ./cmd/structurelint && \
		echo "structurelint installed to $${HOME}/go/bin/structurelint"; \
	else \
		echo "structurelint is already installed"; \
	fi

# Format code with black
format:
	@echo "Formatting code with black..."
	black .

# Run all linters
lint:
	@echo "Running flake8..."
	@flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics || true
	@flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics || true
	@echo ""
	@echo "Running pylint..."
	@find . -name "*.py" -type f -not -path "./venv/*" -not -path "./.venv/*" -exec pylint {} + --exit-zero || true
	@echo ""
	@echo "Checking code formatting with black..."
	@black --check --diff . || true

# Run tests
test:
	@echo "Running tests with pytest..."
	pytest --verbose --cov=. --cov-report=term

# Check project structure
structure:
	@echo "Checking project structure with structurelint..."
	@if command -v structurelint > /dev/null 2>&1; then \
		structurelint .; \
	elif [ -f $${HOME}/go/bin/structurelint ]; then \
		$${HOME}/go/bin/structurelint .; \
	else \
		echo "Error: structurelint not found. Run 'make install-structurelint' first."; \
		exit 1; \
	fi

# Run all checks
all: format lint structure test
	@echo ""
	@echo "✅ All checks completed!"

# Clean cache files
clean:
	@echo "Cleaning cache files..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✨ Clean complete!"

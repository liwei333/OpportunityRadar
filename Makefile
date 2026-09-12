.PHONY: install install-api install-web dev-api dev-web dev test lint clean help

# Default target
help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

# Installation
install: install-api install-web ## Install all dependencies

install-api: ## Install backend dependencies
	cd services/agent && uv sync --extra dev

install-web: ## Install frontend dependencies
	cd apps/web && pnpm install

# Development
dev-api: ## Start backend development server
	cd services/agent && export PATH="$HOME/.local/bin:$$PATH" && \
		uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-web: ## Start frontend development server
	cd apps/web && export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && nvm use 22 && pnpm dev

dev: ## Start both API and web (parallel)
	@echo "Starting backend..."
	@$(MAKE) dev-api & \
	echo "Starting frontend..." && \
	$(MAKE) dev-web

# Testing
test: ## Run all backend tests
	cd services/agent && export PATH="$HOME/.local/bin:$$PATH" && \
		uv run pytest tests/ -v

test-unit: ## Run unit tests only
	cd services/agent && export PATH="$HOME/.local/bin:$$PATH" && \
		uv run pytest tests/unit/ -v

test-api: ## Run API integration tests only
	cd services/agent && export PATH="$HOME/.local/bin:$$PATH" && \
		uv run pytest tests/integration/ -v

# Linting
lint: ## Run ruff linter
	cd services/agent && export PATH="$HOME/.local/bin:$$PATH" && \
		uv run ruff check .

lint-fix: ## Run ruff linter with auto-fix
	cd services/agent && export PATH="$HOME/.local/bin:$$PATH" && \
		uv run ruff check . --fix --unsafe-fixes

# Building
build-web: ## Build frontend for production
	cd apps/web && export NVM_DIR="$$HOME/.nvm" && [ -s "$$NVM_DIR/nvm.sh" ] && \. "$$NVM_DIR/nvm.sh" && nvm use 22 && pnpm build

# Cleanup
clean: ## Clean generated files
	rm -rf services/agent/.venv
	rm -rf services/agent/__pycache__
	rm -rf services/agent/app/**/__pycache__
	rm -rf services/agent/tests/**/__pycache__
	rm -rf apps/web/node_modules
	rm -rf apps/web/dist
	rm -f data/*.db

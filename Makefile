SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c
.DEFAULT_GOAL := help

UV   ?= uv
PNPM ?= pnpm
WEB  := web

# WSL1 (kernel 4.4 "Microsoft") fails uv's parallel/reflink installs with ENOMEM;
# copy + serial is slower but works everywhere.
export UV_LINK_MODE ?= copy
export UV_CONCURRENT_INSTALLS ?= 1

.PHONY: help setup data export dev check check-py check-web

help: ## list targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-10s %s\n", $$1, $$2}'

setup: ## install python + web deps, pre-commit hook
	$(UV) sync
	cd $(WEB) && $(PNPM) install
	@if [ -d .git ]; then $(UV) run pre-commit install; fi

data: ## run the data pipeline (stubs for now)
	$(UV) run python -m pipeline all

export: ## run engine -> web/public/data (falls back to mock fields / synthetic weather)
	$(UV) run python -m engine.export

dev: ## web dev server
	cd $(WEB) && $(PNPM) dev

check: check-py check-web ## everything that must pass before a commit
	@echo "make check: all OK"

check-py:
	$(UV) run ruff check .
	$(UV) run ruff format --check .
	$(UV) run pytest
	$(UV) run python -m engine.validate

check-web:
	cd $(WEB) && $(PNPM) run format:check
	cd $(WEB) && $(PNPM) run typecheck
	cd $(WEB) && $(PNPM) run check:data
	cd $(WEB) && $(PNPM) run build

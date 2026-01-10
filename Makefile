# ============================================================================
# Vex - Valgrind Error eXplorer
# Docker-based build system for memory leak analysis
# ============================================================================

.PHONY: all run rebuild shell clean logs help build install uninstall

# ============================================================================
# Configuration
# ============================================================================

# Auto-detect architecture (ARM64 -> linux/amd64 for Valgrind compatibility)
UNAME_M := $(shell uname -m)
ifeq ($(UNAME_M),arm64)
    PLATFORM := --platform linux/amd64
else
    PLATFORM :=
endif

# ANSI color codes
LIGHT_PINK := \033[38;5;225m
PINK := \033[38;5;219m
YELLOW := \033[38;5;214m
GREEN  := \033[38;5;49m
RED    := \033[38;5;196m
BLUE   := \033[38;5;31m
RESET  := \033[0m

# Build log file
LOG_FILE := /tmp/vex_build.log

# ============================================================================
# Public Commands
# ============================================================================

# Default rule: display help
all: help

# Display available commands
help:
	@echo ""
	@echo "$(GREEN)Vex - Valgrind Error eXplorer$(RESET)"
	@echo ""
	@echo "Available commands:"
	@echo "  $(BLUE)make run$(RESET)        - Compile and run Vex (builds image if needed)"
	@echo "  $(BLUE)make install$(RESET)    - Install Vex globally (requires sudo)"
	@echo "  $(BLUE)make uninstall$(RESET)  - Remove Vex installation (requires sudo)"
	@echo "  $(BLUE)make rebuild$(RESET)    - Force rebuild Docker image"
	@echo "  $(BLUE)make shell$(RESET)      - Open interactive shell in container"
	@echo "  $(BLUE)make logs$(RESET)       - Display last build logs"
	@echo "  $(BLUE)make clean$(RESET)      - Remove Docker image"
	@echo ""

# Compile test project and run Vex
run:
	@docker image inspect vex > /dev/null 2>&1 || $(MAKE) build --no-print-directory
	@printf "\n"
	@printf "\033[?25l"
	@printf "$(YELLOW)- $(RESET)Starting Docker container"
	@docker run $(PLATFORM) --rm \
		-v $(PWD):/app \
		-w /app/test_cases \
		vex /bin/bash -c "echo 'CONTAINER_READY'" > /dev/null 2>&1
	@printf "\r$(GREEN)✓ $(RESET)Starting Docker container\n"
	@printf "$(YELLOW)- $(RESET)Compiling test project"
	@docker run $(PLATFORM) --rm \
		-v $(PWD):/app \
		-w /app/test_cases \
		vex /bin/bash -c "make re > /tmp/build.log 2>&1 && echo 'BUILD_SUCCESS' || cat /tmp/build.log" > $(LOG_FILE) 2>&1; \
	if grep -q "BUILD_SUCCESS" $(LOG_FILE); then \
		printf "\r$(GREEN)✓ $(RESET)Compiling test project\n"; \
		printf "\033[?25h"; \
		docker run $(PLATFORM) -it --rm -v $(PWD):/app -w /app/test_cases vex ../srcs/vex.py ./leaky; \
	else \
		printf "\r$(RED)⨯ $(RESET)Compilation failed:\n"; \
		cat $(LOG_FILE); \
		printf "\033[?25h"; \
		exit 1; \
	fi

# Force complete rebuild
rebuild: clean build

# Open interactive shell in container
shell:
	@docker image inspect vex > /dev/null 2>&1 || $(MAKE) build --no-print-directory
	@docker run $(PLATFORM) -it --rm -v $(PWD):/app vex /bin/bash

# Display last build logs
logs:
	@if [ -f $(LOG_FILE) ]; then \
		echo "$(GREEN)Last build logs:$(RESET)"; \
		echo ""; \
		cat $(LOG_FILE); \
	else \
		echo "$(RED)No build logs found$(RESET)"; \
		echo "Run 'make run' first to generate logs"; \
	fi

# Remove Docker image
clean:
	@docker rmi vex 2>/dev/null || true

# ============================================================================
# Internal Commands
# ============================================================================

# Build Docker image (auto-triggered by run/shell if needed)
build:
	@printf "$(YELLOW)- $(RESET)Building Docker image\n"
	@docker build $(PLATFORM) -t vex .
	@printf "$(GREEN)✓ $(RESET)Docker image ready\n"

# Install Vex globally
install: build
	@echo ""
	@printf "$(YELLOW)- $(RESET)Installing Vex globally\n"
	@chmod +x vex_cli
	@echo "$(YELLOW)- $(RESET)Installing to /usr/local/bin/vex"
	@sudo cp vex_cli /usr/local/bin/vex
	@printf "$(GREEN)✓ $(RESET)Vex installed successfully!\n"
	@echo ""
	@echo "$(PINK)1. Configure your API key$(RESET)"
	@echo "$(LIGHT_PINK)vex configure$(RESET)"
	@echo ""
	@echo "$(PINK)2. Run Vex from anywhere:$(RESET)"
	@echo "$(LIGHT_PINK)vex ./my_program$(RESET)"
	@echo ""

# Uninstall Vex
uninstall:
	@printf "$(YELLOW)- $(RESET)Removing Vex installation\n"
	@sudo rm -f /usr/local/bin/vex
	@printf "$(GREEN)✓ $(RESET)Vex uninstalled\n"
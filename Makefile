# ============================================================================
# Vex - Valgrind Error eXplorer
# Makefile for installation and development
# ============================================================================

.PHONY: all help install uninstall shell clean

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
YELLOW := \033[38;5;214m
LIGHT_YELLOW := \033[38;5;230m
GREEN  := \033[38;5;49m
BLUE   := \033[38;5;211m
RESET  := \033[0m

# ============================================================================
# Public Commands
# ============================================================================

# Default rule: display help
all: help

# Display available commands
help:
	@echo "Available commands:"
	@echo "  $(BLUE)make install$(RESET)    - Install Vex globally (requires sudo)"
	@echo "  $(BLUE)make uninstall$(RESET)  - Remove Vex installation (requires sudo)"
	@echo "  $(BLUE)make shell$(RESET)      - Open interactive shell in Docker container"
	@echo "  $(BLUE)make clean$(RESET)      - Remove Docker image and Python cache"
	@echo ""

# Install Vex globally
install: build
	@sudo -v
	@printf "$(YELLOW)- $(RESET)Installing Vex to /usr/local/bin"
	@chmod +x vex_cli > /dev/null 2>&1
	@sudo cp vex_cli /usr/local/bin/vex > /dev/null 2>&1
	@printf "\r$(GREEN)✓ $(RESET)Installing Vex to /usr/local/bin\n"
	@echo "$(GREEN)✓$(RESET) Installation complete!"
	@echo ""
	@echo "$(YELLOW)-$(RESET) Run $(LIGHT_YELLOW)vex configure$(RESET) to set up your Mistral API key$(RESET)"
	@echo ""

# Uninstall Vex
uninstall:
	@echo ""
	@sudo -v  # Demande le password ici
	@printf "$(YELLOW)- $(RESET)Removing Vex installation"
	@sudo rm -f /usr/local/bin/vex > /dev/null 2>&1
	@printf "\r$(GREEN)✓ $(RESET)Removing Vex installation\n"
	@echo ""

# Open interactive shell in container
shell:
	@docker image inspect vex > /dev/null 2>&1 || $(MAKE) build --no-print-directory
	@docker run $(PLATFORM) -it --rm --cap-add=SYS_PTRACE --security-opt seccomp=unconfined -v $(PWD):/app vex /bin/bash

# Remove Docker image and Python cache
clean:
	@echo ""
	@printf "$(YELLOW)- $(RESET)Removing Docker image"
	@docker rmi vex > /dev/null 2>&1 || true
	@printf "\r$(GREEN)✓ $(RESET)Removing Docker image\n"
	@printf "$(YELLOW)- $(RESET)Cleaning Python cache"
	@find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@printf "\r$(GREEN)✓ $(RESET)Cleaning Python cache\n"
	@echo ""

# ============================================================================
# Internal Commands
# ============================================================================

# Build Docker image (auto-triggered by install/shell if needed)
build:
	@echo ""
	@printf "\033[?25l"; \
	YELLOW='\033[38;5;214m'; \
	GREEN='\033[38;5;49m'; \
	WHITE='\033[97m'; \
	DARK_GRAY='\033[38;5;238m'; \
	RESET='\033[0m'; \
	(pos=0; seconds=0; iterations=0; while true; do \
		printf "\r$${YELLOW}- $${RESET}$${WHITE}Building Docker image $${RESET}"; \
		for i in 0 1 2 3; do \
			if [ $$i -eq $$pos ]; then \
				printf "$${GREEN}--$${RESET}"; \
			else \
				printf "$${WHITE}--$${RESET}"; \
			fi; \
		done; \
		printf " $${DARK_GRAY}$${seconds}s$${RESET}"; \
		pos=$$((pos + 1)); \
		if [ $$pos -ge 4 ]; then pos=0; fi; \
		iterations=$$((iterations + 1)); \
		if [ $$((iterations % 10)) -eq 0 ]; then seconds=$$((seconds + 1)); fi; \
		sleep 0.1; \
	done) & \
	SPINNER_PID=$$!; \
	docker build $(PLATFORM) -t vex . > /dev/null 2>&1; \
	BUILD_STATUS=$$?; \
	kill $$SPINNER_PID 2>/dev/null; wait $$SPINNER_PID 2>/dev/null; \
	printf "\r\033[K"; \
	printf "\033[?25h"; \
	GREEN='\033[38;5;49m'; \
	RESET='\033[0m'; \
	RED='\033[38;5;196m'; \
	if [ $$BUILD_STATUS -eq 0 ]; then \
		printf "$${GREEN}✓ $${RESET}Building Docker image\n"; \
	else \
		printf "$${RED}✗ $${RESET}Building Docker image failed\n"; \
		exit 1; \
	fi
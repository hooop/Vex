![Vex Logo](./assets/logo.svg)

# VEX - Valgrind Error eXplorer

VEX is a CLI tool that combines deterministic memory leak analysis with Mistral AI to provide intelligent, guided debugging assistance for C programs.

## Why VEX?

Memory leak analysis is a domain where LLMs perform poorly when used naively. They don't simulate memory, propagate early mistakes, and often fail on non-trivial cases involving aliasing, embedded allocations, or container lifetimes.

**VEX takes a different approach:** Instead of asking an LLM to find the root cause, it separates the problem into two phases:

1. **Deterministic root cause identification** - A Python algorithm tracks memory paths through your code, following Valgrind's execution trace line by line
2. **LLM-assisted explanation** - Mistral AI (mistral-small-latest) explains the leak, justifies the root cause, and suggests a minimal fix

The LLM never guesses ownership or simulates memory. It only explains what the deterministic analysis has already proven.

<video src="https://github.com/user-attachments/assets/a5e54af0-27f8-45a6-8c25-920ca0973407" controls></video>

## Installation

1. **Clone the repository**
```bash
   git clone <repository-url>
   cd vex
```

2. **Install VEX**
```bash
   make install
```
   You'll be prompted for your sudo password to install the tool system-wide.

3. **Configure your API key**
```bash
   vex configure
```
   Enter your Mistral AI API key when prompted.

## Usage

### Basic Command
```bash
vex <executable> [arguments]
```

VEX will:
1. Run your program through Valgrind
2. Analyze memory paths deterministically
3. Provide AI-powered explanations and fix suggestions

### Try the Examples
```bash
cd examples/Type_1
make
vex ./leaky
```

The `examples` directory contains three types of memory leak scenarios to help you understand how VEX works.

## How It Works

### Deterministic Analysis

Given a Valgrind report, VEX tracks one allocation at a time through your code:

- Maintains **roots** (variables that can reach the allocation)
- Tracks **access paths** (e.g., `node->data`)
- Updates paths when encountering aliases, reassignments, frees, or scope exits

When no valid path remains and the allocation wasn't freed, the root cause is identified.

### Leak Classification

VEX categorizes leaks into three concrete types:

1. **Missing free** - Allocation never freed before paths disappear
2. **Path loss by reassignment** - Last access path overwritten or set to NULL
3. **Container freed first** - Structure freed while owning embedded allocations

Each points to the precise line of code responsible.

### LLM Role

After deterministic analysis, Mistral AI receives:
- The Valgrind report
- Relevant source code
- The identified root cause
- The leak classification

It then explains the leak step-by-step and proposes a correct fix.

## Design Philosophy

**What VEX avoids:**
- Global program analysis
- Heuristics or "smart" guessing
- Overfitting to simple examples

**What VEX focuses on:**
- Constrained reasoning
- Explicit assumptions
- Trustworthy results within supported scope

**Current limitations:**
- No loop handling
- Single execution path only
- One allocation tracked at a time
- Conditions not handled
- External free functions not tracked

These features are on the TODO list.

## Why This Matters

This project explores how deterministic analysis and LLMs can complement each other by assigning each tool a role aligned with its strengths:

- **Deterministic analysis**: Root cause identification with zero false positives
- **LLMs**: Explanation, pedagogy, and fix suggestions

The goal isn't to replace Valgrind, but to make its output actionable for developers learning C.

## Requirements

- Docker
- Mistral AI API key
- Python 3.x
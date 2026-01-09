#!/usr/bin/env python3

"""
Vex - Valgrind Error eXplorer.

Command-line tool for analyzing memory leaks in C programs.
Integrates Valgrind execution, source code extraction, memory tracking
analysis, and AI-powered explanations.

Usage: ./vex.py <executable> [args...]
"""

import sys
import time
from typing import Optional

from builder import rebuild_project
from code_extractor import extract_call_stack
from colors import RESET, DARK_GREEN, RED
from display import display_analysis, display_leak_menu
from memory_tracker import find_root_cause, convert_extracted_code
from mistral_analyzer import analyze_with_mistral, MistralAPIError
from type_defs import ParsedValgrindReport, ValgrindError, BuildResult
from valgrind_parser import parse_valgrind_report
from valgrind_runner import run_valgrind, ExecutableNotFoundError, ValgrindError as ValgrindRunnerError
from welcome import (
    clear_screen,
    display_logo,
    start_spinner,
    stop_spinner,
    start_block_spinner,
    stop_block_spinner,
    display_summary
)

# Return codes
SUCCESS = 0
ERROR = 1

def print_error(message: str) -> None:
    """
    Display a formatted error message.
    
    Args:
        message: Error message to display.
    """

    print(f"\nError : {message}\n", file=sys.stderr)


def _run_valgrind_analysis(executable: str, program_args: list[str]) -> ParsedValgrindReport:
    """
    Execute Valgrind and parse the report.

    Args:
        executable: Path to the executable.
        program_args: Program arguments.

    Returns:
        Dictionary containing has_leaks, summary, and leaks.
    """

    # Build complete command
    full_command = executable
    if program_args:
        full_command += " " + " ".join(program_args)

    # Execute Valgrind
    t = start_spinner("Running Valgrind")
    valgrind_output = run_valgrind(full_command)
    stop_spinner(t, "Running Valgrind")

    # Parse report
    t = start_spinner("Parsing report")
    parsed_data = parse_valgrind_report(valgrind_output)
    stop_spinner(t, "Parsing report")

    return parsed_data


def _reanalyze_after_compilation(full_command: str, initial_leak_count: int) -> Optional[tuple[list[ValgrindError], int]]:
    """
    Re-run Valgrind after compilation and display delta.

    Args:
        full_command: Complete command (executable + args).
        initial_leak_count: Number of leaks before fix.

    Returns:
        None if all leaks resolved.
        (parsed_errors, new_leak_count) otherwise.
    """

    clear_screen()
    display_logo()

    # Re-run Valgrind
    t = start_spinner("Running Valgrind")
    valgrind_output = run_valgrind(full_command)
    stop_spinner(t, "Running Valgrind")

    # Re-parse
    t = start_spinner("Parsing report")
    parsed_data = parse_valgrind_report(valgrind_output)
    stop_spinner(t, "Parsing report")

    # Check if leaks remain
    new_leak_count = len(parsed_data.get('leaks', []))

    if new_leak_count == 0:
        print(f"\n{RED}All leaks resolved !{RESET}\n")
        return None

    # Display delta
    resolved_count = initial_leak_count - new_leak_count
    leak_word = "leak" if new_leak_count == 1 else "leaks"
    resolved_word = "leak resolved" if resolved_count == 1 else "leaks resolved"
    detected_word = "leak detected" if new_leak_count == 1 else "leaks detected"

    if new_leak_count < initial_leak_count:
        print(f"\n{RED}{resolved_count} {resolved_word}{RESET}")
    else:
        print(f"\n{RED}Still {new_leak_count} {detected_word}{RESET}")

    # Update data
    parsed_errors = parsed_data.get('leaks', [])

    # Display Valgrind summary
    display_summary(parsed_data)

    # Pause before continuing
    input("[Press Enter to continue...]")

    # Re-extract code
    _extract_source_code(parsed_errors)

    return (parsed_errors, new_leak_count)


def _extract_source_code(parsed_errors: list[ValgrindError]) -> None:
    """
    Extract source code for each leak if not already done.
    
    Args:
        parsed_errors: List of parsed Valgrind errors.
    """

    if not parsed_errors[0].get('extracted_code'):
        clear_screen()
        t = start_spinner("Extracting source code")

        for error in parsed_errors:
            if 'backtrace' in error and error['backtrace']:
                error['extracted_code'] = extract_call_stack(error['backtrace'])
            else:
                error['extracted_code'] = []

        stop_spinner(t, "Extracting source code")


def _find_root_causes(parsed_errors: list[ValgrindError]) -> None:
    """
    Find root cause for each leak using memory tracking algorithm.

    Args:
        parsed_errors: List of parsed Valgrind errors with extracted code.
    """

    t = start_spinner("Analyzing memory paths")

    for error in parsed_errors:
        if error.get('extracted_code'):
            try:
                converted = convert_extracted_code(error['extracted_code'])
                root_cause = find_root_cause(converted)
                if root_cause:
                    error['root_cause'] = {
                        'type': root_cause["leak_type"],
                        'line': root_cause["line"],
                        'function': root_cause["function"],
                        'file': root_cause["file"],
                        'steps': root_cause["steps"]
                    }
            except Exception as e:
                # If analysis fails, continue without root cause
                error['root_cause'] = None

    stop_spinner(t, "Analyzing memory paths")


def _process_all_leaks(parsed_errors: list[ValgrindError], executable: str) -> str:
    """
    Process all leaks one by one.

    Args:
        parsed_errors: List of leaks to process.
        executable: Path to executable (for recompilation).

    Returns:
        "completed" if all processed, "need_recompile" if [v] chosen, "quit" if [q] chosen.
    """

    # Hide real cursor
    print("\033[?25l", end="", flush=True)

    t = start_block_spinner("Calling Mistral AI")

    for i, error in enumerate(parsed_errors, 1):
        try:

            # Hide cursor before spinner
            print("\033[?25l", end="", flush=True)

            # Start spinner for this leak
            t = start_block_spinner("Calling Mistral AI")
            time.sleep(0.1)
            
            # Analyze error
            analysis = analyze_with_mistral(error)
            
            # Stop spinner after analysis
            stop_block_spinner(t, "Calling Mistral AI")

            # Show real cursor
            print("\033[?25h", end="", flush=True)

            display_analysis(error, analysis, error_number=i, total_errors=len(parsed_errors))

            # Menu after each leak
            choice = display_leak_menu()

            if choice == "verify":
                # Recompile
                result = rebuild_project(executable)
                if not result['success']:
                    print(result['output'])
                    input("\n[Press Enter to continue...]]")
                    continue

                return "need_recompile"

            elif choice == "skip":
                # Skip to next
                if i < len(parsed_errors):
                    continue
                else:
                    # Was the last leak
                    return "completed"

            elif choice == "quit":
                return "quit"

        except MistralAPIError as e:
            if i == 1:
                stop_block_spinner(t, "Calling Mistral AI")
            print_error(f"Error analyzing leak #{i}: {e}")
            continue

    # If we reach here, all leaks processed
    return "completed"

def _parse_command_line() -> tuple[str, list[str], str]:
    """
    Parse command line arguments.

    Returns:
        Tuple: (executable, program_args, full_command).
    """

    executable = sys.argv[1]
    program_args = sys.argv[2:]

    # Build complete command
    full_command = executable
    if program_args:
        full_command += " " + " ".join(program_args)

    return (executable, program_args, full_command)

def main() -> int:
    """
    Main entry point for Vex.

    Returns:
        0 if success, 1 if error.
    """

    # Check arguments
    if len(sys.argv) < 2:
        return ERROR

    # Unpack returned tuple
    executable, program_args, full_command = _parse_command_line()

    try:
        clear_screen()

        # Hide real cursor
        print("\033[?25l", end="", flush=True)
        time.sleep(1)
        display_logo()

        # Valgrind analysis, returns dictionary with all leaks
        parsed_data = _run_valgrind_analysis(executable, program_args)

        # If leak list is empty, exit
        parsed_errors = parsed_data.get('leaks', [])
        if not parsed_errors:
            print("\nNo memory leaks detected !\n")
            return SUCCESS

        # Display Valgrind summary
        display_summary(parsed_data)

        # Réafficher le vrai curseur
        print("\033[?25h", end="", flush=True)

        # Show real cursor
        while True:
            choice = input(DARK_GREEN + "Start leak analysis ? [Y/n] " + RESET).strip().lower()

            if choice == "" or choice == "y":
                break
            elif choice == "n":
                print()
                print()
                return SUCCESS
            else:
                # Display error message below
                print(RED + "Invalid choice. Press ENTER or type 'n'." + RESET)
                # Move up two lines
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[F")
                # Return to line start and clear
                sys.stdout.write("\r" + " " * 80 + "\r")
                sys.stdout.flush()

        # ========================================
        # START ANALYSIS LOOP
        # ========================================

        # Store initial leak count (list size)
        initial_leak_count = len(parsed_errors)

        # Variable to track if we need to re-analyze
        need_reanalysis = False

        while True:

            # If need to re-analyze (after [v])
            if need_reanalysis:
                result = _reanalyze_after_compilation(full_command, initial_leak_count)
                if result is None:
                    return SUCCESS

                parsed_errors, initial_leak_count = result
                need_reanalysis = False

            # Extract source code
            _extract_source_code(parsed_errors)

            # Find root causes
            _find_root_causes(parsed_errors)

            # Process all leaks
            status = _process_all_leaks(parsed_errors, executable)

            if status == "need_recompile":
                need_reanalysis = True
            elif status == "completed":
                print("\nAnalysis complete !\n")
                return SUCCESS
            elif status == "quit":
                print("Goodbye !\n")
                return SUCCESS

    except ExecutableNotFoundError as e:
        print_error(str(e))
        return ERROR

    except ValgrindError as e:
        print_error(f"Issue with Valgrind :\n{e}")
        return ERROR

    except MistralAPIError as e:
        print_error(f"Issue with Mistra API :\n{e}")
        return ERROR

    except KeyboardInterrupt:
        print("\n\nAnalysis interrupted by user.\n")
        return ERROR

    except Exception as e:
        print_error(f"Unexpected error : {e}")
        import traceback
        traceback.print_exc()
        return ERROR


if __name__ == "__main__":
    sys.exit(main())
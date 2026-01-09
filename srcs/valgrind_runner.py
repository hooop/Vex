"""
Valgrind execution module.

Executes Valgrind on a program and captures its complete report.

Features:
- Verify executable existence and permissions
- Check Valgrind installation
- Execute Valgrind with appropriate flags
- Capture complete output (stdout + stderr)
- Handle common errors
"""

import os
import subprocess

class ValgrindError(Exception):
    """Raised when Valgrind execution fails."""

    pass


class ExecutableNotFoundError(Exception):
    """Raised when executable does not exist or is not executable."""

    pass


def check_valgrind_installed() -> bool:
	"""
    Check if Valgrind is installed on the system.

    Returns:
        True if Valgrind is installed, False otherwise.
    """
      
	try:
		# Try to execute valgrind --version
		result = subprocess.run(
			["valgrind", "--version"],
			capture_output=True,
			text=True,
			timeout=5
		)
		return result.returncode == 0
	except FileNotFoundError:
		return False
	except subprocess.TimeoutExpired:
		return False


def check_executable_exists(executable_path: str) -> bool:
	"""
    Check if executable exists and is a valid file.

    Args:
        executable_path: Path to the executable to analyze.

    Returns:
        True if file exists and is executable, False otherwise.
    """
      
	if not os.path.exists(executable_path):
		return False

	if not os.path.isfile(executable_path):
		return False

	# Check if file has execution permissions
	if not os.access(executable_path, os.X_OK):
		return False

	return True


def run_valgrind(executable_path: str) -> str:
    """
    Run Valgrind on specified executable and capture complete report.

    Executes Valgrind with the following flags:
    - --leak-check=full: complete memory leak detection
    - --track-origins=yes: trace origin of uninitialized values
    - --show-leak-kinds=all: display all leak types

    Args:
        executable_path: Path to executable to analyze (can include arguments).
                        Example: "./my_prog" or "./my_prog arg1 arg2"

    Returns:
        Complete Valgrind report (stderr output).

    Raises:
        ExecutableNotFoundError: If executable doesn't exist or isn't executable.
        ValgrindError: If Valgrind is not installed or execution fails.
    """

    # Check 1: Is Valgrind installed ?
    if not check_valgrind_installed():
        raise ValgrindError(
            "Valgrind is not installed on this system.\n"
            "Install with: sudo apt-get install valgrind"
        )

    # Split to separate executable from arguments
    command_parts = executable_path.split()
    actual_executable = command_parts[0]  # First argument is the executable

    # Check 2: Does executable exist ?
    if not check_executable_exists(actual_executable):
        if not os.path.exists(actual_executable):
            raise ExecutableNotFoundError(
                f"Executable '{actual_executable}' does not exist."
            )
        elif not os.path.isfile(actual_executable):
            raise ExecutableNotFoundError(
                f"'{actual_executable}' is not a file."
            )
        else:
            raise ExecutableNotFoundError(
                f"'{actual_executable}' does not have execution permissions.\n"
                f"Try: chmod +x {actual_executable}"
            )

    # Build Valgrind command
    command = [
        "valgrind",
        "--leak-check=full",            # Complete leak detection
        "--track-origins=yes",          # Trace origin of uninitialized values
        "--show-leak-kinds=all",        # Display all leak types
        "--verbose",                    # Verbose mode for more details
    ] + command_parts                   # Add executable and its arguments

    try:
        # Execute Valgrind
        # Note: Valgrind writes its report to stderr not stdout
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30  # 30 second timeout to avoid hanging
        )

        # Valgrind writes its report to stderr
        valgrind_output = result.stderr

        # Even if analyzed program has non-zero exit code,
        # Valgrind still generates a valid report
        if not valgrind_output:
            raise ValgrindError(
                "Valgrind produced no output. "
                "Program may have crashed before Valgrind could analyze it."
            )

        return valgrind_output

    except subprocess.TimeoutExpired:
        raise ValgrindError(
            f"Analysis of '{actual_executable}' exceeded 30 second timeout.\n"
            "Analyzed program may be stuck in an infinite loop."
        )

    except Exception as e:
        raise ValgrindError(
            f"Valgrind execution failed: {str(e)}"
        )
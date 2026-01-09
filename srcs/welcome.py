"""
welcome.py

Module responsible for displaying the welcome screen with logo,
progress spinners, and summary before starting leak analysis.
"""

import os
import random
import sys
import threading
import time

from colors import (
    RESET, GREEN, DARK_GREEN, LIGHT_YELLOW, DARK_YELLOW,
    LIGHT_PINK
)
from type_defs import ParsedValgrindReport

# Global flags for spinner control
_spinner_active = False
_block_spinner_active = False


def clear_screen() -> None:
    """Clear the terminal screen."""

    os.system('clear')


def display_logo() -> None:
    """Display the Vex ASCII logo with pixel-by-pixel animation."""

    logo_lines = [
        "██  ██  ██████  ██  ██",
        "██  ██  ████      ██",
        "  ██    ██████  ██  ██"
    ]

    # Step 1 : Parse pixels
    pixels = []
    for line_idx, line in enumerate(logo_lines):
        col = 0
        while col < len(line):
            if col < len(line) and line[col] == '█':
                pixels.append((line_idx, col))
                col += 2  # Skip second block character
            else:
                col += 1

    # Step 2 : Shuffle
    random.shuffle(pixels)

    # Step 3 : Display pixel by pixel
    for line_idx, col in pixels:
        
        # Display pink cursor effect
        print(f"\033[{line_idx + 2};{col + 1}H{LIGHT_PINK}██{RESET}", end="", flush=True)
        time.sleep(0.035)

        # Display final green pixel
        print(f"\033[{line_idx + 2};{col + 1}H{DARK_GREEN}██{RESET}", end="", flush=True)
        time.sleep(0.001)

    # Position cursor after logo
    print(f"\033[{len(logo_lines) + 2};1H")

    print("Valgrind Error Explorer")
    print(GREEN + "Mistral AI internship project" + RESET)
    print()


def _spinner_animation(message: str) -> None:
    """Thread function that displays the animated spinner."""

    spinner = ['◐', '◓', '◑', '◒']
    colors = [LIGHT_PINK, DARK_GREEN]
    i = 0
    while _spinner_active:
        color = colors[i % len(colors)]
        symbol = spinner[i % len(spinner)]
        sys.stdout.write(f"\r{color}{symbol}{RESET} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1

def start_spinner(message: str) -> threading.Thread:
    """
    Start an animated spinner with a message.

    Args:
        message: The message to display next to the spinner

    Returns:
        threading.Thread: The spinner thread
    """

    global _spinner_active
    _spinner_active = True
    thread = threading.Thread(target=_spinner_animation, args=(message,))
    thread.daemon = True
    thread.start()
    return thread


def stop_spinner(thread: threading.Thread, message: str) -> None:
    """
    Stop the spinner and display a success checkmark.

    Args:
        thread: The spinner thread to stop
        message: The success message to display
    """

    global _spinner_active
    _spinner_active = False
    thread.join()
    sys.stdout.write(f"\r{GREEN}✓{RESET} {message}\n")
    sys.stdout.flush()



def _block_spinner_animation(message: str) -> None:
    """
    Thread function that reveals/hides text with block animation.

    Args:
        message: The message to animate.
    """

    colors = [LIGHT_PINK, DARK_GREEN]

    length = len(message)

    pos_counter = 0
    color_counter = 0

    pos_speed = 0.25   # Larger = slower scrolling
    color_speed = 3    # Larger = slower blinking

    tick = 0

    while _block_spinner_active:
        phase = (pos_counter // length) % 2
        pos = pos_counter % length
        color = colors[color_counter % 2]

        if phase == 0:
            text = f"  {message[:pos + 1]}{color}{'▉' * (length - pos - 1)}{RESET}"
        else:
            text = f"  {color}{'▉' * (pos + 1)}{RESET}{message[pos + 1:]}"

        sys.stdout.write(f"\r{text}")
        sys.stdout.flush()

        tick += 1
        if tick % color_speed == 0:
            color_counter += 1
        if tick % pos_speed == 0:
            pos_counter += 1

        time.sleep(0.02)


def start_block_spinner(message: str) -> threading.Thread:
    """
    Start an animated block spinner with a message.

    Args:
        message: The message to display with the animation.

    Returns:
        The spinner thread.
    """

    global _block_spinner_active
    _block_spinner_active = True
    thread = threading.Thread(target=_block_spinner_animation, args=(message,))
    thread.daemon = True
    thread.start()
    return thread


def stop_block_spinner(thread: threading.Thread, message: str) -> None:
    """
    Stop the block spinner and display a success checkmark.

    Args:
        thread: The spinner thread to stop.
        message: The success message to display.
    """

    global _block_spinner_active
    _block_spinner_active = False
    thread.join()
    sys.stdout.write(f"\r{GREEN}✓{RESET} {message}\n")
    sys.stdout.flush()


def display_summary(parsed_data: ParsedValgrindReport) -> None:
    """
    Display the Valgrind report summary.

    Args:
        parsed_data: Parsed Valgrind report with summary and leaks.
    """

    print()
    print(GREEN + "• Valgrind Report Summary :" + RESET)
    print()

    summary = parsed_data.get('summary', {})
    num_leaks = len(parsed_data.get('leaks', []))

    # Larger = slower blinking
    leak_word = "memory leak detected" if num_leaks == 1 else "memory leaks detected"

    # Values for alignment
    def_bytes = f"{summary.get('definitely_lost', 0)} bytes"
    ind_bytes = f"{summary.get('indirectly_lost', 0)} bytes"
    total_bytes = f"{summary.get('total_leaked', 0)} bytes"

    # Max length of byte values
    max_bytes_len = max(len(def_bytes), len(ind_bytes), len(total_bytes))

    # Build lines
    line1 = f"{num_leaks} {leak_word}"
    line2 = f"   Definitely lost : {def_bytes:>{max_bytes_len}}"
    line3 = f"   Indirectly lost : {ind_bytes:>{max_bytes_len}}"
    line4 = f" ‣ Total : {total_bytes:>{max_bytes_len}}"

    lines = [line1, line2, line3, line4]

    # Find max length
    max_length = max(len(line) for line in lines)
    separator = "-" * max_length

    # Display
    print(LIGHT_YELLOW + separator + RESET)
    print(DARK_YELLOW + lines[0] + RESET)
    print(LIGHT_YELLOW + separator + RESET)
    print(LIGHT_YELLOW + lines[1] + RESET)
    print(LIGHT_YELLOW + separator + RESET)
    print(LIGHT_YELLOW + lines[2] + RESET)
    print(LIGHT_YELLOW + separator + RESET)
    print(DARK_YELLOW + lines[3] + RESET)
    print()
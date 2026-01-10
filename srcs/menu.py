#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
menu.py
Interactive menu system with arrow key navigation.
"""
import sys
import tty
import termios
import time
import select

# ANSI Color codes
RESET = "\033[0m"
LIGHT_PINK = "\033[38;5;225m"
DARK_GREEN = "\033[38;5;49m"


def read_key():
    """
    Read a single keypress (arrow or ENTER).
    Returns:
        "up", "down", "enter", or None
    """
    # Save terminal settings
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    
    try:
        # Switch to raw mode
        tty.setraw(fd)
        
        # Read first byte
        char = sys.stdin.read(1)
        
        # ENTER key
        if char == '\r' or char == '\n':
            return "enter"
        
        # ESC sequence (arrows)
        if char == '\x1b':
            # Read next 2 bytes
            bracket = sys.stdin.read(1)  # '['
            arrow = sys.stdin.read(1)    # 'A' or 'B'
            
            if arrow == 'A':
                return "up"
            elif arrow == 'B':
                return "down"
        
        return None
        
    finally:
        # Restore terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        
        # DON'T drain buffer - let animation check for keys


def display_menu(options, selected_index):
    """
    Display menu with selected option highlighted.
    
    Args:
        options: List of menu options (strings)
        selected_index: Index of currently selected option
    """
    # Clear from cursor down
    print("\033[J", end="")
    
    # Display all options
    for i, option in enumerate(options):
        if i == selected_index:
            print(f" {DARK_GREEN}‣{RESET} {option}")
        else:
            print(f"   {option}")
    
    sys.stdout.flush()


def animate_block_reveal(text, delay=0.015):
    """
    Block animation: blocks eat text from left, then text reappears from left.
    Blocks alternate between pink and green colors.
    Can be interrupted by key press.
    
    Args:
        text: Text to animate
        delay: Delay between frames
    
    Returns:
        bool: True if animation completed, False if interrupted
    """
    colors = [LIGHT_PINK, DARK_GREEN]
    length = len(text)
    color_counter = 0
    color_speed = 3
    
    def interruptible_sleep(duration):
        """Sleep but check for key press frequently."""
        sleep_interval = 0.005  # Check every 5ms
        elapsed = 0
        while elapsed < duration:
            if select.select([sys.stdin], [], [], 0)[0]:
                return True  # Key detected
            time.sleep(sleep_interval)
            elapsed += sleep_interval
        return False  # No key
    
    # Phase 1: Blocks eat text from left
    for i in range(length + 1):
        color = colors[(color_counter // color_speed) % 2]
        blocks = '▉' * i
        remaining_text = text[i:]
        
        sys.stdout.write(f"\r\033[K {DARK_GREEN}‣{RESET} {color}{blocks}{RESET}{remaining_text}")
        sys.stdout.flush()
        
        if interruptible_sleep(delay):
            # Key pressed! Stop and display final
            sys.stdout.write(f"\r\033[K {DARK_GREEN}‣{RESET} {text}")
            sys.stdout.flush()
            return False
        
        color_counter += 1
    
    # Phase 2: Text reappears from left
    for i in range(length + 1):
        color = colors[(color_counter // color_speed) % 2]
        revealed_text = text[:i]
        blocks = '▉' * (length - i)
        
        sys.stdout.write(f"\r\033[K {DARK_GREEN}‣{RESET} {revealed_text}{color}{blocks}{RESET}")
        sys.stdout.flush()
        
        if interruptible_sleep(delay):
            # Key pressed! Stop and display final
            sys.stdout.write(f"\r\033[K {DARK_GREEN}‣{RESET} {text}")
            sys.stdout.flush()
            return False
        
        color_counter += 1
    
    # Final: clean text
    sys.stdout.write(f"\r\033[K {DARK_GREEN}‣{RESET} {text}")
    sys.stdout.flush()
    return True


def interactive_menu(options):
    """
    Display interactive menu and return user choice.
    
    Args:
        options: List of menu options (strings)
    
    Returns:
        int: Index of selected option (0-based)
    """
    selected = 0
    menu_lines = len(options)
    
    # Hide cursor
    print("\033[?25l", end="", flush=True)
    print()
    
    try:
        # Display initial menu (no animation)
        display_menu(options, selected)
        
        while True:
            key = read_key()
            
            if key == "up":
                selected = (selected - 1) % len(options)
                print(f"\033[{menu_lines}A", end="")
                display_menu(options, selected)
                lines_to_move_up = menu_lines - selected
                print(f"\033[{lines_to_move_up}A\033[1G", end="")
                animate_block_reveal(options[selected])
                print("\033[1G", end="")
                print(f"\033[{lines_to_move_up}B", end="")
                
            elif key == "down":
                selected = (selected + 1) % len(options)
                print(f"\033[{menu_lines}A", end="")
                display_menu(options, selected)
                lines_to_move_up = menu_lines - selected
                print(f"\033[{lines_to_move_up}A\033[1G", end="")
                animate_block_reveal(options[selected])
                print("\033[1G", end="")
                print(f"\033[{lines_to_move_up}B", end="")
                
            elif key == "enter":
                return selected
    
    finally:
        print("\033[?25h", end="", flush=True)


if __name__ == "__main__":
    options = ["Start analysis", "Quit Vex"]
    choice_index = interactive_menu(options)
    print(f"\n\nChoix validé : {options[choice_index]}\n")
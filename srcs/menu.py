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
    Block animation that can be interrupted by key press.
    
    Returns:
        str or None: The key that interrupted ("up"/"down"/"enter"), or None if completed
    """
    colors = [LIGHT_PINK, DARK_GREEN]
    length = len(text)
    color_counter = 0
    color_speed = 3
    
    # Save terminal settings and switch to raw mode
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    tty.setraw(fd)
    
    try:
        # Phase 1: Blocks eat text from left
        for i in range(length + 1):
            # Check for interrupt
            if select.select([sys.stdin], [], [], 0)[0]:
                # Read the complete key sequence
                char = sys.stdin.read(1)
                key = None
                
                if char == '\x1b':
                    bracket = sys.stdin.read(1)
                    arrow = sys.stdin.read(1)
                    if arrow == 'A':
                        key = "up"
                    elif arrow == 'B':
                        key = "down"
                elif char == '\r' or char == '\n':
                    key = "enter"
                
                # Restore terminal
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                sys.stdout.write(f"\r\033[K {DARK_GREEN}‣{RESET} {text}")
                sys.stdout.flush()
                return key
            
            color = colors[(color_counter // color_speed) % 2]
            blocks = '▉' * i
            remaining_text = text[i:]
            
            sys.stdout.write(f"\r\033[K {DARK_GREEN}‣{RESET} {color}{blocks}{RESET}{remaining_text}")
            sys.stdout.flush()
            time.sleep(delay)
            color_counter += 1
        
        # Phase 2: Text reappears from left
        for i in range(length + 1):
            # Check for interrupt
            if select.select([sys.stdin], [], [], 0)[0]:
                # Read the complete key sequence
                char = sys.stdin.read(1)
                key = None
                
                if char == '\x1b':
                    bracket = sys.stdin.read(1)
                    arrow = sys.stdin.read(1)
                    if arrow == 'A':
                        key = "up"
                    elif arrow == 'B':
                        key = "down"
                elif char == '\r' or char == '\n':
                    key = "enter"
                
                # Restore terminal
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                sys.stdout.write(f"\r\033[K {DARK_GREEN}‣{RESET} {text}")
                sys.stdout.flush()
                return key
            
            color = colors[(color_counter // color_speed) % 2]
            revealed_text = text[:i]
            blocks = '▉' * (length - i)
            
            sys.stdout.write(f"\r\033[K {DARK_GREEN}‣{RESET} {revealed_text}{color}{blocks}{RESET}")
            sys.stdout.flush()
            time.sleep(delay)
            color_counter += 1
        
        # Final: clean text
        sys.stdout.write(f"\r\033[K {DARK_GREEN}‣{RESET} {text}")
        sys.stdout.flush()
        return None
    
    finally:
        # Always restore terminal settings
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def interactive_menu(options):
    """
    Display interactive menu and return user choice.
    """
    selected = 0
    menu_lines = len(options)
    
    print("\033[?25l", end="", flush=True)
    print()
    
    try:
        display_menu(options, selected)
        
        while True:
            key = read_key()
            
            # Process key and update selection
            if key == "up":
                selected = (selected - 1) % len(options)
            elif key == "down":
                selected = (selected + 1) % len(options)
            elif key == "enter":
                return selected
            else:
                continue
            
            # Animation loop: continue until no interruption
            while True:
                # Redraw menu
                print(f"\033[{menu_lines}A", end="")
                display_menu(options, selected)
                
                # Move to selected line and animate
                lines_to_move_up = menu_lines - selected
                print(f"\033[{lines_to_move_up}A\033[1G", end="")
                
                interrupted_key = animate_block_reveal(options[selected])
                
                # Return cursor below menu
                print(f"\033[1G\033[{lines_to_move_up}B", end="")
                
                # If interrupted, update selection and continue animation loop
                if interrupted_key == "up":
                    selected = (selected - 1) % len(options)
                elif interrupted_key == "down":
                    selected = (selected + 1) % len(options)
                elif interrupted_key == "enter":
                    return selected
                else:
                    # Animation completed, exit animation loop
                    break
    
    finally:
        print("\033[?25h", end="", flush=True)
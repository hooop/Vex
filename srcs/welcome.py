#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
welcome.py

Module responsible for displaying the welcome screen with logo,
progress spinners, and summary before starting leak analysis.
"""

import os
import threading
import time
import sys
import random


# ANSI Color codes
RESET = "\033[0m"
GREEN = "\033[38;5;158m"
DARK_GREEN = "\033[38;5;49m"
LIGHT_YELLOW = "\033[38;5;230m"
DARK_YELLOW = "\033[38;5;228m"
MAGENTA = "\033[38;5;219m"
RED = "\033[38;5;174m"


def clear_screen():
    """Clear the terminal screen."""
    os.system('clear')

import random

def display_logo():
    """Display the Vex ASCII logo with pixel-by-pixel animation."""
    logo_lines = [
        "██  ██  ██████  ██  ██",
        "██  ██  ██████    ██",
        "  ██    ██████  ██  ██"
    ]
    
    # Étape 1 : Parser les pixels
    pixels = []
    for line_idx, line in enumerate(logo_lines):
        col = 0
        while col < len(line):
            if col < len(line) and line[col] == '█':
                pixels.append((line_idx, col))
                col += 2  # skip le deuxième █
            else:
                col += 1
    
    # Étape 2 : Mélanger
    random.shuffle(pixels)
    # Étape 3 : Afficher pixel par pixel
    for line_idx, col in pixels:
        # Positionner le curseur (attention : ANSI commence à 1, pas 0)
        print(f"\033[{line_idx + 2};{col + 1}H{DARK_GREEN}██{RESET}", end="", flush=True)
        time.sleep(0.06)  # ajuste la vitesse ici
    
    # Positionner le curseur après le logo
    print(f"\033[{len(logo_lines) + 2};1H")
    
    print("Valgrind Error Explorer")
    print(GREEN + "Mistral AI internship project" + RESET)
    print()


# Global flag for spinner control
_spinner_active = False


def _spinner_animation(message):
    """Thread function that displays the animated spinner."""
    spinner = ['✦', '✪', '✺', '✻', '✿', '✭', '❈']
    i = 0
    while _spinner_active:
        sys.stdout.write(f"\r{spinner[i % len(spinner)]} {message}")
        sys.stdout.flush()
        time.sleep(0.1)
        i += 1


def start_spinner(message):
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


def stop_spinner(thread, message):
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


def display_summary(parsed_data):
    """
    Display the Valgrind report summary.
    
    Args:
        parsed_data: Dict returned by parse_valgrind_report()
    """
    print()
    print(GREEN + "• Résumé du rapport Valgrind :" + RESET)
    print()
    
    summary = parsed_data.get('summary', {})
    num_leaks = len(parsed_data.get('leaks', []))
    
    print(LIGHT_YELLOW + "------------------------------" + RESET)
    print(DARK_YELLOW + str(num_leaks) + RESET + LIGHT_YELLOW + " fuites de mémoires détéctées" + RESET)
    print(LIGHT_YELLOW + "------------------------------" + RESET)
    print(LIGHT_YELLOW + f"    Definitely lost : {summary.get('definitely_lost', 0)} bytes" + RESET)
    print(LIGHT_YELLOW + "------------------------------" + RESET)
    print(LIGHT_YELLOW + f"    Indirectly lost : {summary.get('indirectly_lost', 0)} bytes" + RESET)
    print(LIGHT_YELLOW + "------------------------------" + RESET)
    print(DARK_YELLOW + f"‣ Total : {summary.get('total_leaked', 0)} bytes" + RESET)
    print()


def display_menu():
    """
    Display the menu and wait for user choice.
    
    Returns:
        str: "start" to begin resolution, "quit" to exit
    """
    print()
    print(MAGENTA + "[ENTRÉE]" + RESET + " Commencer la résolution")
    print(MAGENTA + "[Q]     " + RESET + " Quitter")
    print()
    
    while True:
        choice = input(DARK_GREEN + "vex > " + RESET).strip().lower()
        
        if choice == "":  # ENTRÉE
            clear_screen()
            return "start"
        elif choice == "q":
            clear_screen()
            return "quit"
        else:
            # Afficher le message d'erreur en dessous
            print(RED + "Choix invalide. Appuyez sur ENTRÉE ou tapez [Q].")
            # Remonter d'une ligne
            sys.stdout.write("\033[F")
            sys.stdout.write("\033[F")
            # Revenir au début de la ligne et effacer
            sys.stdout.write("\r" + " " * 80 + "\r")
            sys.stdout.flush()
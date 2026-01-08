#!/usr/bin/env python3
"""
Vex - Valgrind Error eXplorer
Command-line tool for analyzing memory leaks in C programs.

Usage: vex <executable> [args...]
"""

import sys
import os
import time
import threading
from typing import Dict, List, Tuple, Optional
from memory_tracker import find_root_cause, convert_extracted_code

# Import des modules Vex
from valgrind_runner import run_valgrind, ExecutableNotFoundError, ValgrindError
from valgrind_parser import parse_valgrind_report
from code_extractor import extract_call_stack
from mistral_analyzer import analyze_with_mistral, MistralAPIError
from display import display_analysis, display_leak_menu
from welcome import clear_screen, display_logo, start_spinner, stop_spinner, start_block_spinner, stop_block_spinner, display_summary, display_menu
from builder import rebuild_project

# Return codes
SUCCESS = 0
ERROR = 1

RESET = "\033[0m"
GREEN = "\033[38;5;158m"
DARK_GREEN = "\033[38;5;49m"
RED = "\033[38;5;174m"

def print_error(message: str) -> None:
    """Affiche un message d'erreur formaté."""
    print(f"\nError : {message}\n", file=sys.stderr)


def _run_valgrind_analysis(executable: str, program_args: List[str]) -> Dict:
    """
    Exécute Valgrind et parse le rapport.

    Args:
        executable: Chemin vers l'exécutable
        program_args: Arguments du programme

    Returns:
        Dict contenant has_leaks, summary, leaks
    """
    # Construction de la commande complète
    full_command = executable
    if program_args:
        full_command += " " + " ".join(program_args)

    # Exécution de Valgrind
    t = start_spinner("Running Valgrind")
    valgrind_output = run_valgrind(full_command)
    stop_spinner(t, "Running Valgrind")

    # Parsing du rapport
    t = start_spinner("Parsing report")
    parsed_data = parse_valgrind_report(valgrind_output)
    stop_spinner(t, "Parsing report")

    return parsed_data


def _reanalyze_after_compilation(full_command: str, initial_leak_count: int) -> Optional[Tuple[List[Dict], int]]:
    """
    Re-lance Valgrind après compilation et affiche le delta.

    Args:
        full_command: Commande complète (executable + args)
        initial_leak_count: Nombre de leaks avant la correction

    Returns:
        None si tous les leaks sont résolus
        (parsed_errors, new_leak_count) sinon
    """
    clear_screen()
    display_logo()

    RED = "\033[38;5;174m"
    RESET = "\033[0m"

    # Re-lancer Valgrind
    t = start_spinner("Running Valgrind")
    valgrind_output = run_valgrind(full_command)
    stop_spinner(t, "Running Valgrind")

    # Re-parser
    t = start_spinner("Parsing report")
    parsed_data = parse_valgrind_report(valgrind_output)
    stop_spinner(t, "Parsing report")

    # Vérifier s'il reste des leaks
    new_leak_count = len(parsed_data.get('leaks', []))

    if new_leak_count == 0:
        print(f"\n{RED}All leaks resolved !{RESET}\n")
        return None

    # Afficher le delta
    resolved_count = initial_leak_count - new_leak_count
    leak_word = "leak" if new_leak_count == 1 else "leaks"
    resolved_word = "leak resolved" if resolved_count == 1 else "leaks resolved"
    detected_word = "leak detected" if new_leak_count == 1 else "leaks detected"

    if new_leak_count < initial_leak_count:
        print(f"\n{RED}{resolved_count} {resolved_word}{RESET}")
    else:
        print(f"\n{RED}Still {new_leak_count} {detected_word}{RESET}")

    # Mettre à jour les données
    parsed_errors = parsed_data.get('leaks', [])

    # Affichage du résumé Valgrind
    display_summary(parsed_data)

    # Pause avant de continuer
    input("[Press Enter to continue...]")

    # Re-extraire le code
    _extract_source_code(parsed_errors)

    return (parsed_errors, new_leak_count)

def _extract_source_code(parsed_errors: List[Dict]) -> None:
    """
    Extrait le code source pour chaque leak si pas déjà fait.
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


def _find_root_causes(parsed_errors: List[Dict]) -> None:
    """
    Find root cause for each leak using memory tracking algorithm.
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


def _process_all_leaks(parsed_errors: List[Dict], executable: str) -> str:
    """
    Traite tous les leaks un par un.

    Args:
        parsed_errors: Liste des leaks à traiter
        executable: Chemin vers l'exécutable (pour recompilation)

    Returns:
        str: "completed" si tous traités, "need_recompile" si [v] choisi, "quit" si [q] choisi
    """
    # Masquer le vrai curseur
    print("\033[?25l", end="", flush=True)

    t = start_block_spinner("Calling Mistral AI")

    for i, error in enumerate(parsed_errors, 1):
        try:

            # Masquer le curseur avant le spinner
            print("\033[?25l", end="", flush=True)

            # Démarrer le spinner pour ce leak
            t = start_block_spinner("Calling Mistral AI")
            time.sleep(0.1)  # ← AJOUTER cette ligne (laisse le thread démarrer)
            
            # Analyse de l'erreur
            analysis = analyze_with_mistral(error)
            
            # Arrêter le spinner après l'analyse
            stop_block_spinner(t, "Calling Mistral AI")

            # Affichage
                # Réafficher le vrai curseur
            print("\033[?25h", end="", flush=True)

            display_analysis(error, analysis, error_number=i, total_errors=len(parsed_errors))

            # Menu après chaque leak
            choice = display_leak_menu()

            if choice == "verify":
                # Recompiler
                result = rebuild_project(executable)
                if not result['success']:
                    print(result['output'])
                    input("\n[Press Enter to continue...]]")
                    continue

                return "need_recompile"

            elif choice == "skip":
                # Passer au suivant
                if i < len(parsed_errors):
                    continue
                else:
                    # C'était le dernier leak
                    return "completed"

            elif choice == "quit":
                return "quit"

        except MistralAPIError as e:
            if i == 1:
                stop_block_spinner(t, "Calling Mistral AI")
            print_error(f"Error analyzing leak #{i}: {e}")
            continue

    # Si on arrive ici, tous les leaks ont été traités
    return "completed"

def _parse_command_line() -> Tuple[str, List[str], str]:
    """
    Parse les arguments de la ligne de commande.

    Returns:
        Tuple: (executable, program_args, full_command)
    """
    executable = sys.argv[1]
    program_args = sys.argv[2:]

    # Construction de la commande complète
    full_command = executable
    if program_args:
        full_command += " " + " ".join(program_args)

    return (executable, program_args, full_command)

def main() -> int:
    """
    Point d'entrée principal de Vex.

    Returns:
        0 si succès, 1 si erreur
    """
    # Vérification des arguments
    if len(sys.argv) < 2:
        return ERROR

    # unpacking du tuple qui est retourné
    executable, program_args, full_command = _parse_command_line()

    try:
        # Affichage du logo et démarrage
        clear_screen()
        # Masquer le vrai curseur
        print("\033[?25l", end="", flush=True)
        time.sleep(1)
        display_logo()

        # Analyse Valgrind, renvoie un dictionnaire avec tous les leaks
        parsed_data = _run_valgrind_analysis(executable, program_args)

        # Si la liste des leaks est vide on termnine
        parsed_errors = parsed_data.get('leaks', [])
        if not parsed_errors:
            print("\nNo memory leaks detected !\n")
            return SUCCESS

        # Affichage du résumé Valgrind
        display_summary(parsed_data)

        # Menu : commencer ou quitter
        # choice = display_menu()

        # if choice == "quit":
        #     print("Au revoir :)\n")
        #     return SUCCESS

        # Réafficher le vrai curseur
        print("\033[?25h", end="", flush=True)

        # Menu : commencer ou quitter
        while True:
            choice = input(DARK_GREEN + "Start leak analysis ? [Y/n] " + RESET).strip().lower()

            if choice == "" or choice == "y":
                break
            elif choice == "n":
                print()
                print()
                return SUCCESS
            else:
                # Afficher le message d'erreur en dessous
                print(RED + "Invalid choice. Press ENTER or type 'n'." + RESET)
                # Remonter de deux lignes
                sys.stdout.write("\033[F")
                sys.stdout.write("\033[F")
                # Revenir au début de la ligne et effacer
                sys.stdout.write("\r" + " " * 80 + "\r")
                sys.stdout.flush()

        # ========================================
        # DÉBUT DE LA BOUCLE D'ANALYSE
        # ========================================

        # Stockage du nombre initial de leaks (taille de la liste)
        initial_leak_count = len(parsed_errors)

        # Variable pour savoir si on doit tout re-analyser
        need_reanalysis = False

        while True:

            # Si besoin de re-analyser (après [v])
            if need_reanalysis:
                result = _reanalyze_after_compilation(full_command, initial_leak_count)
                if result is None:
                    return SUCCESS

                parsed_errors, initial_leak_count = result
                need_reanalysis = False

            # Extraire le code source
            _extract_source_code(parsed_errors)

            # Trouver les root causes
            _find_root_causes(parsed_errors)

            # Traiter tous les leaks
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

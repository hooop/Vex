#!/usr/bin/env python3
"""
Vex - Valgrind Error eXplorer
Command-line tool for analyzing memory leaks in C programs.

Usage: vex <executable> [args...]
"""

import sys
import os
from typing import Dict, List, Tuple, Optional

# Import des modules Vex
from valgrind_runner import run_valgrind, ExecutableNotFoundError, ValgrindError
from valgrind_parser import parse_valgrind_report
from code_extractor import extract_call_stack
from mistral_analyzer import analyze_with_mistral, MistralAPIError
from display import display_analysis, display_leak_menu
from welcome import clear_screen, display_logo, start_spinner, stop_spinner, display_summary, display_menu
from builder import rebuild_project

# Return codes
SUCCESS = 0
ERROR = 1

def print_error(message: str) -> None:
    """Affiche un message d'erreur formaté."""
    print(f"\nErreur: {message}\n", file=sys.stderr)


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
    t = start_spinner("Lancement de Valgrind")
    valgrind_output = run_valgrind(full_command)
    stop_spinner(t, "Lancement de Valgrind")
    
    # Parsing du rapport
    t = start_spinner("Parsing du rapport")
    parsed_data = parse_valgrind_report(valgrind_output)
    stop_spinner(t, "Parsing du rapport")
    
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
    t = start_spinner("Lancement de Valgrind")
    valgrind_output = run_valgrind(full_command)
    stop_spinner(t, "Lancement de Valgrind")
    
    # Re-parser
    t = start_spinner("Parsing du rapport")
    parsed_data = parse_valgrind_report(valgrind_output)
    stop_spinner(t, "Parsing du rapport")
    
    # Vérifier s'il reste des leaks
    new_leak_count = len(parsed_data.get('leaks', []))
    
    if new_leak_count == 0:
        print(f"\n{RED}Tous les leaks sont résolus !{RESET}\n")
        return None
    
    # Afficher le delta
    resolved_count = initial_leak_count - new_leak_count
    leak_word = "leak" if new_leak_count == 1 else "leaks"
    resolved_word = "leak résolu" if resolved_count == 1 else "leaks résolus"
    detected_word = "leak détecté" if new_leak_count == 1 else "leaks détectés"
    
    if new_leak_count < initial_leak_count:
        print(f"\n{RED}{resolved_count} {resolved_word}{RESET}")
    else:
        print(f"\n{RED}Toujours {new_leak_count} {detected_word}{RESET}")
    
    # Mettre à jour les données
    parsed_errors = parsed_data.get('leaks', [])
    
    # Affichage du résumé Valgrind
    display_summary(parsed_data)
    
    # Pause avant de continuer
    input("[Appuyez sur Entrée pour continuer...]")
    
    # Re-extraire le code
    _extract_source_code(parsed_errors)
    
    return (parsed_errors, new_leak_count)

def _extract_source_code(parsed_errors: List[Dict]) -> None:
    """
    Extrait le code source pour chaque leak si pas déjà fait.
    """
    if not parsed_errors[0].get('extracted_code'):
        clear_screen()
        t = start_spinner("Extraction du code source")
        
        for error in parsed_errors:
            if 'backtrace' in error and error['backtrace']:
                error['extracted_code'] = extract_call_stack(error['backtrace'])
            else:
                error['extracted_code'] = []
        
        stop_spinner(t, "Extraction du code source")


def _process_all_leaks(parsed_errors: List[Dict], executable: str) -> str:
    """
    Traite tous les leaks un par un.
    
    Args:
        parsed_errors: Liste des leaks à traiter
        executable: Chemin vers l'exécutable (pour recompilation)
        
    Returns:
        str: "completed" si tous traités, "need_recompile" si [v] choisi, "quit" si [q] choisi
    """
    t = start_spinner("Interrogation de Mistral AI")
    
    for i, error in enumerate(parsed_errors, 1):
        try:
            # Analyse de l'erreur
            analysis = analyze_with_mistral(error)
            
            # Arrêter le spinner avant le premier affichage
            if i == 1:
                stop_spinner(t, "Interrogation de Mistral AI")
            
            # Affichage
            display_analysis(error, analysis, error_number=i, total_errors=len(parsed_errors))
            
            # Menu après chaque leak
            choice = display_leak_menu()
            
            if choice == "verify":
                # Recompiler
                result = rebuild_project(executable)
                if not result['success']:
                    print(result['output'])
                    input("\n[Appuyez sur Entrée pour continuer...]")
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
                stop_spinner(t, "Interrogation de Mistral AI")
            print_error(f"Erreur lors de l'analyse de l'erreur #{i}: {e}")
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
        display_logo()

        # Analyse Valgrind, renvoie un dictionnaire avec tous les leaks
        parsed_data = _run_valgrind_analysis(executable, program_args)

        # Si la liste des leaks est vide on termnine
        parsed_errors = parsed_data.get('leaks', [])
        if not parsed_errors:
            print("\nAucune erreur mémoire détectée !\n")
            return SUCCESS

        # Affichage du résumé Valgrind
        display_summary(parsed_data)

        # Menu : commencer ou quitter
        choice = display_menu()
        
        if choice == "quit":
            print("Au revoir :)\n")
            return SUCCESS

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
            
            # Traiter tous les leaks
            status = _process_all_leaks(parsed_errors, executable)
            
            if status == "need_recompile":
                need_reanalysis = True
            elif status == "completed":
                print("\nAnalyse terminée !\n")
                return SUCCESS
            elif status == "quit":
                print("Au revoir !\n")
                return SUCCESS

    except ExecutableNotFoundError as e:
        print_error(str(e))
        return ERROR

    except ValgrindError as e:
        print_error(f"Problème avec Valgrind :\n{e}")
        return ERROR

    except MistralAPIError as e:
        print_error(f"Problème avec l'API Mistral :\n{e}")
        return ERROR

    except KeyboardInterrupt:
        print("\n\nAnalyse interrompue par l'utilisateur.\n")
        return ERROR

    except Exception as e:
        print_error(f"Erreur inattendue : {e}")
        import traceback
        traceback.print_exc()
        return ERROR


if __name__ == "__main__":
    sys.exit(main())
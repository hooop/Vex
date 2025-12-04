#!/usr/bin/env python3
"""
Vex - Valgrind Error eXplorer
Command-line tool for analyzing memory leaks in C programs.

Usage: vex <executable> [args...]
"""

import sys
import os
from typing import Dict, List

# Import des modules Vex
from valgrind_runner import run_valgrind, ExecutableNotFoundError, ValgrindError
from valgrind_parser import parse_valgrind_report
from code_extractor import extract_call_stack
from mistral_analyzer import analyze_with_mistral, MistralAPIError
from display import display_analysis, display_leak_menu  # ← AJOUT display_leak_menu
from welcome import clear_screen, display_logo, start_spinner, stop_spinner, display_summary, display_menu
from builder import rebuild_project  # ← AJOUT builder


def print_error(message: str) -> None:
    """Affiche un message d'erreur formaté."""
    print(f"\n❌ Erreur: {message}\n", file=sys.stderr)


def print_usage() -> None:
    """Affiche l'aide d'utilisation."""
    print("""
╔════════════════════════════════════════╗
║              VEX v1.0                  ║
║   Valgrind Error eXplorer.             ║
╚════════════════════════════════════════╝

Usage: vex <executable> [args...]

Exemples:
  vex ./my_program
  vex ./push_swap 3 2 1
  vex ./a.out

Vex analyse automatiquement votre programme avec
Valgrind, explique et propose une solution aux erreurs mémoire détectées.
""")


def main() -> int:
    """
    Point d'entrée principal de Vex.

    Returns:
        0 si succès, 1 si erreur
    """
    # Vérification des arguments
    if len(sys.argv) < 2:
        print_usage()
        return 1

    executable = sys.argv[1]
    program_args = sys.argv[2:]  # Tous les arguments après l'exécutable

    # Vérification de l'aide
    if executable in ["-h", "--help", "help"]:
        print_usage()
        return 0

    try:
        # Affichage du logo et démarrage
        clear_screen()
        display_logo()

        # Étape 1: Exécution de Valgrind avec spinner
        full_command = executable
        if program_args:
            full_command += " " + " ".join(program_args)

        t = start_spinner("Lancement de Valgrind")
        valgrind_output = run_valgrind(full_command)
        stop_spinner(t, "Lancement de Valgrind")
        
        # Étape 2: Parsing du rapport avec spinner
        t = start_spinner("Parsing du rapport")
        parsed_data = parse_valgrind_report(valgrind_output)
        stop_spinner(t, "Parsing du rapport")

        # Vérification : y a-t-il des leaks ?
        if not parsed_data.get('has_leaks', False):
            print("\n✅ Aucune erreur mémoire détectée ! Votre code est clean.\n")
            return 0

        parsed_errors = parsed_data.get('leaks', [])
        if not parsed_errors:
            print("\n✅ Aucune erreur mémoire détectée ! Votre code est clean.\n")
            return 0

        # Affichage du résumé
        display_summary(parsed_data)

        # Menu : commencer ou quitter
        choice = display_menu()
        
        if choice == "quit":
            print("\n👋 Au revoir !\n")
            return 0

        # ========================================
        # DÉBUT DE LA BOUCLE D'ANALYSE
        # ========================================
        
        # Stockage du nombre initial de leaks
        initial_leak_count = len(parsed_errors)
        
        # Variable pour savoir si on doit tout re-analyser
        need_reanalysis = False
        
        while True:
            # Si besoin de re-analyser (après [v])
            if need_reanalysis:
                clear_screen()
                display_logo()
                
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
                    print(f"\n🎉 Tous les leaks sont résolus ! ({initial_leak_count} → 0)\n")
                    return 0
                
                # Afficher le delta
                if new_leak_count < initial_leak_count:
                    print(f"\n✅ {initial_leak_count - new_leak_count} leak(s) résolu(s) !")
                    print(f"Il reste {new_leak_count} leak(s)\n")
                else:
                    print(f"\n⚠️  Toujours {new_leak_count} leak(s) détecté(s)\n")
                
                # Mettre à jour les données
                parsed_errors = parsed_data.get('leaks', [])
                initial_leak_count = new_leak_count
                
                # Re-extraire le code
                for error in parsed_errors:
                    if 'backtrace' in error and error['backtrace']:
                        error['extracted_code'] = extract_call_stack(error['backtrace'])
                    else:
                        error['extracted_code'] = []
                
                need_reanalysis = False
                
                # Pause avant de continuer
                input("[Appuyez sur Entrée pour continuer...]")
            
            # Si première analyse, extraire le code
            if not need_reanalysis and not parsed_errors[0].get('extracted_code'):
                clear_screen()
                t = start_spinner("Extraction du code source")
                for error in parsed_errors:
                    if 'backtrace' in error and error['backtrace']:
                        error['extracted_code'] = extract_call_stack(error['backtrace'])
                    else:
                        error['extracted_code'] = []
                stop_spinner(t, "Extraction du code source")
            
            # Analyser chaque leak
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
                    
                    # DEBUG
                    # print(f"\nDEBUG error['file']: {error.get('file')}")
                    # print(f"DEBUG cause file: {analysis.get('cause_reelle', {}).get('file')}")

                    # Menu après chaque leak
                    choice = display_leak_menu()
                    
                    if choice == "verify":
                        # Recompiler
                        result = rebuild_project(executable)
                        if not result['success']:
                            print(result['output'])
                            input("\n[Appuyez sur Entrée pour continuer...]")
                            continue
                        
                        # Déclencher re-analyse
                        need_reanalysis = True
                        break  # Sortir de la boucle for
                    
                    elif choice == "skip":
                        # Passer au suivant
                        if i < len(parsed_errors):
                            continue
                        else:
                            # C'était le dernier leak
                            print("\n✨ Analyse terminée !\n")
                            return 0
                    
                    elif choice == "quit":
                        print("\n👋 Au revoir !\n")
                        return 0
                
                except MistralAPIError as e:
                    if i == 1:
                        stop_spinner(t, "Interrogation de Mistral AI")
                    print_error(f"Erreur lors de l'analyse de l'erreur #{i}: {e}")
                    continue
            
            # Si on a fini tous les leaks sans [v]
            if not need_reanalysis:
                print("\n✨ Analyse terminée !\n")
                return 0

    except ExecutableNotFoundError as e:
        print_error(str(e))
        return 1

    except ValgrindError as e:
        print_error(f"Problème avec Valgrind:\n{e}")
        return 1

    except MistralAPIError as e:
        print_error(f"Problème avec l'API Mistral:\n{e}")
        return 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Analyse interrompue par l'utilisateur.\n")
        return 1

    except Exception as e:
        print_error(f"Erreur inattendue: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
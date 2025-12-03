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
from display import display_analysis


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
        # Étape 1: Exécution de Valgrind
        print(f"🔍 Analyse de {executable} avec Valgrind...")
        full_command = executable

        if program_args:
            full_command += " " + " ".join(program_args)

        valgrind_output = run_valgrind(full_command)

        # Étape 2: Parsing du rapport
        print("📝 Parsing du rapport Valgrind...")
        parsed_data = parse_valgrind_report(valgrind_output)

        # Le parser retourne un dict avec 'has_leaks', 'summary', et 'leaks'
        if not parsed_data.get('has_leaks', False):
            print("\n✅ Aucune erreur mémoire détectée ! Votre code est clean.\n")
            return 0

        # Extraire la liste des leaks
        parsed_errors = parsed_data.get('leaks', [])

        if not parsed_errors:
            print("\n✅ Aucune erreur mémoire détectée ! Votre code est clean.\n")
            return 0

        print(f"⚠️  {len(parsed_errors)} erreur(s) détectée(s)\n")

        # Étape 3: Extraction du code pour chaque erreur
        print("🔎 Extraction du contexte du code...")

        for error in parsed_errors:
            if 'backtrace' in error and error['backtrace']:
                error['extracted_code'] = extract_call_stack(error['backtrace'])
            else:
                error['extracted_code'] = []

        # Étape 4: Analyse avec Mistral AI
        print("🤖 Analyse avec Mistral AI...\n")
        print("="*60)

        for i, error in enumerate(parsed_errors, 1):
            try:
                # Analyse de l'erreur
                analysis = analyze_with_mistral(error)

                # Affichage
                display_analysis(error, analysis, error_number=i, total_errors=len(parsed_errors))

                # Si ce n'est pas le dernier leak, attendre l'utilisateur
                if i < len(parsed_errors):
                    input("\n[Appuyez sur Entrée pour voir le leak suivant...]")
                    print("\n" + "="*60 + "\n")

            except MistralAPIError as e:
                print_error(f"Erreur lors de l'analyse de l'erreur #{i}: {e}")
                continue

        print("="*60)
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
        traceback.print_exc()  # Pour voir l'erreur complète pendant le debug
        return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
valgrind_runner.py

Module responsable de l'exÃ©cution de Valgrind sur un programme
et de la capture de son rapport complet.

FonctionnalitÃ©s :
- VÃ©rification de l'existence de l'exÃ©cutable
- VÃ©rification de la prÃ©sence de Valgrind sur le systÃ¨me
- ExÃ©cution de Valgrind avec les flags appropriÃ©s
- Capture de la sortie complÃ¨te (stdout + stderr)
- Gestion des erreurs courantes
"""

import subprocess
import os
import sys
from typing import Optional


class ValgrindError(Exception):
	"""Exception personnalisÃ©e pour les erreurs liÃ©es Ã  Valgrind"""
	pass


class ExecutableNotFoundError(Exception):
	"""Exception levÃ©e quand l'exÃ©cutable n'existe pas"""
	pass


def check_valgrind_installed() -> bool:
	"""
	VÃ©rifie si Valgrind est installÃ© sur le systÃ¨me.

	Returns:
		bool: True si Valgrind est installÃ©, False sinon
	"""
	try:
		# Tente d'exÃ©cuter valgrind --version
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
	VÃ©rifie si l'exÃ©cutable existe et est bien un fichier.

	Args:
		executable_path: Chemin vers l'exÃ©cutable Ã  analyser

	Returns:
		bool: True si le fichier existe et est exÃ©cutable, False sinon
	"""
	if not os.path.exists(executable_path):
		return False

	if not os.path.isfile(executable_path):
		return False

	# VÃ©rifie que le fichier a les droits d'exÃ©cution
	if not os.access(executable_path, os.X_OK):
		return False

	return True


def run_valgrind(executable_path: str) -> str:
    """
    Lance Valgrind sur l'exÃ©cutable spÃ©cifiÃ© et capture son rapport complet.

    Cette fonction exÃ©cute Valgrind avec les flags suivants :
    - --leak-check=full : dÃ©tection complÃ¨te des fuites mÃ©moire
    - --track-origins=yes : trace l'origine des valeurs non initialisÃ©es
    - --show-leak-kinds=all : affiche tous les types de fuites

    Args:
        executable_path: Chemin vers l'exÃ©cutable Ã  analyser (peut inclure des arguments)
                        Exemple: "./mon_prog" ou "./mon_prog arg1 arg2"

    Returns:
        str: Le rapport complet de Valgrind (sortie stderr)

    Raises:
        ExecutableNotFoundError: Si l'exÃ©cutable n'existe pas ou n'est pas exÃ©cutable
        ValgrindError: Si Valgrind n'est pas installÃ© ou si l'exÃ©cution Ã©choue
    """

    # VÃ©rification 1 : Valgrind est-il installÃ© ?
    if not check_valgrind_installed():
        raise ValgrindError(
            "Valgrind n'est pas installÃ© sur ce systÃ¨me.\n"
            "Installation : sudo apt-get install valgrind"
        )

    # Split pour sÃ©parer l'exÃ©cutable des arguments
    command_parts = executable_path.split()
    actual_executable = command_parts[0]  # Le premier Ã©lÃ©ment est l'exÃ©cutable

    # VÃ©rification 2 : L'exÃ©cutable existe-t-il ?
    if not check_executable_exists(actual_executable):
        if not os.path.exists(actual_executable):
            raise ExecutableNotFoundError(
                f"L'exÃ©cutable '{actual_executable}' n'existe pas."
            )
        elif not os.path.isfile(actual_executable):
            raise ExecutableNotFoundError(
                f"'{actual_executable}' n'est pas un fichier."
            )
        else:
            raise ExecutableNotFoundError(
                f"'{actual_executable}' n'a pas les droits d'exÃ©cution.\n"
                f"Essayez : chmod +x {actual_executable}"
            )

    # Construction de la commande Valgrind
    command = [
        "valgrind",
        "--leak-check=full",           # DÃ©tection complÃ¨te des leaks
        "--track-origins=yes",          # Trace l'origine des valeurs non initialisÃ©es
        "--show-leak-kinds=all",        # Affiche tous les types de fuites
        "--verbose",                    # Mode verbeux pour plus de dÃ©tails
    ] + command_parts  # Ajoute l'exÃ©cutable ET ses arguments

    try:
        # ExÃ©cution de Valgrind
        # Note : Valgrind Ã©crit son rapport sur stderr, pas stdout
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30  # Timeout de 30 secondes pour Ã©viter les blocages
        )

        # Valgrind Ã©crit son rapport sur stderr
        valgrind_output = result.stderr

        # MÃªme si le programme analysÃ© a un code de retour non nul,
        # Valgrind gÃ©nÃ¨re quand mÃªme un rapport valide
        if not valgrind_output:
            raise ValgrindError(
                "Valgrind n'a produit aucune sortie. "
                "Le programme a peut-Ãªtre plantÃ© avant que Valgrind puisse l'analyser."
            )

        return valgrind_output

    except subprocess.TimeoutExpired:
        raise ValgrindError(
            f"L'analyse de '{actual_executable}' a dÃ©passÃ© le timeout de 30 secondes.\n"
            "Le programme analysÃ© est peut-Ãªtre bloquÃ© dans une boucle infinie."
        )

    except Exception as e:
        raise ValgrindError(
            f"Erreur lors de l'exÃ©cution de Valgrind : {str(e)}"
        )


def main():
    """
    Fonction principale pour tester le module en standalone.
    Usage : python3 valgrind_runner.py <executable>
    """
    if len(sys.argv) != 2:
        print("Usage: python3 valgrind_runner.py <executable>")
        sys.exit(1)

    executable = sys.argv[1]

    try:
        print(f"Lancement de Valgrind sur {executable}...")
        report = run_valgrind(executable)
        print("\n" + "="*60)
        print("RAPPORT VALGRIND")
        print("="*60 + "\n")
        print(report)

    except (ExecutableNotFoundError, ValgrindError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()

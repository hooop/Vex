#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
valgrind_runner.py

Module responsable de l'exÃ©cution de Valgrind sur un programme
et de la capture de son rapport complet.

FonctionnalitÃ©s :
- Vérification de l'existence de l'exÃ©cutable
- Vérification de la présence de Valgrind sur le système
- Exécution de Valgrind avec les flags appropriés
- Capture de la sortie complète (stdout + stderr)
- Gestion des erreurs courantes
"""

import subprocess
import os
import sys
from typing import Optional


class ValgrindError(Exception):
	"""Exception personnalisée pour les erreurs liées Ã  Valgrind"""
	pass


class ExecutableNotFoundError(Exception):
	"""Exception levée quand l'exécutable n'existe pas"""
	pass


def check_valgrind_installed() -> bool:
	"""
	Vérifie si Valgrind est installé sur le système.

	Returns:
		bool: True si Valgrind est installé, False sinon
	"""
	try:
		# Tente d'exécuter valgrind --version
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
	Vérifie si l'exécutable existe et est bien un fichier.

	Args:
		executable_path: Chemin vers l'exécutable Ã  analyser

	Returns:
		bool: True si le fichier existe et est exécutable, False sinon
	"""
	if not os.path.exists(executable_path):
		return False

	if not os.path.isfile(executable_path):
		return False

	# Vérifie que le fichier a les droits d'exécution
	if not os.access(executable_path, os.X_OK):
		return False

	return True


def run_valgrind(executable_path: str) -> str:
    """
    Lance Valgrind sur l'exécutable spécifié et capture son rapport complet.

    Cette fonction exÃ©cute Valgrind avec les flags suivants :
    - --leak-check=full : détection complète des fuites mémoire
    - --track-origins=yes : trace l'origine des valeurs non initialisées
    - --show-leak-kinds=all : affiche tous les types de fuites

    Args:
        executable_path: Chemin vers l'exécutable à analyser (peut inclure des arguments)
                        Exemple: "./mon_prog" ou "./mon_prog arg1 arg2"

    Returns:
        str: Le rapport complet de Valgrind (sortie stderr)

    Raises:
        ExecutableNotFoundError: Si l'exécutable n'existe pas ou n'est pas exécutable
        ValgrindError: Si Valgrind n'est pas installé ou si l'exécution échoue
    """

    # Vérification 1 : Valgrind est-il installé ?
    if not check_valgrind_installed():
        raise ValgrindError(
            "Valgrind n'est pas installé sur ce système.\n"
            "Installation : sudo apt-get install valgrind"
        )

    # Split pour séparer l'exécutable des arguments
    command_parts = executable_path.split()
    actual_executable = command_parts[0]  # Le premier argument est l'exécutable

    # Vérification 2 : L'exécutable existe-t-il ?
    if not check_executable_exists(actual_executable):
        if not os.path.exists(actual_executable):
            raise ExecutableNotFoundError(
                f"L'exécutable '{actual_executable}' n'existe pas."
            )
        elif not os.path.isfile(actual_executable):
            raise ExecutableNotFoundError(
                f"'{actual_executable}' n'est pas un fichier."
            )
        else:
            raise ExecutableNotFoundError(
                f"'{actual_executable}' n'a pas les droits d'exécution.\n"
                f"Essayez : chmod +x {actual_executable}"
            )

    # Construction de la commande Valgrind
    command = [
        "valgrind",
        "--leak-check=full",            # Détection complète des leaks
        "--track-origins=yes",          # Trace l'origine des valeurs non initialisées
        "--show-leak-kinds=all",        # Affiche tous les types de fuites
        "--verbose",                    # Mode verbeux pour plus de détails
    ] + command_parts                   # Ajoute l'exécutable et ses arguments

    try:
        # Exécution de Valgrind
        # Note : Valgrind écrit son rapport sur stderr pas stdout
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30  # Timeout de 30 secondes pour éviter les blocages
        )

        # Valgrind écrit son rapport sur stderr
        valgrind_output = result.stderr

        # Même si le programme analysé a un code de retour non nul,
        # Valgrind génère quand même un rapport valide
        if not valgrind_output:
            raise ValgrindError(
                "Valgrind n'a produit aucune sortie. "
                "Le programme a peut-être planté avant que Valgrind puisse l'analyser."
            )

        return valgrind_output

    except subprocess.TimeoutExpired:
        raise ValgrindError(
            f"L'analyse de '{actual_executable}' a dépassé le timeout de 30 secondes.\n"
            "Le programme analysé est peut-être bloqué dans une boucle infinie."
        )

    except Exception as e:
        raise ValgrindError(
            f"Erreur lors de l'exécution de Valgrind : {str(e)}"
        )
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
builder.py

Module responsible for recompiling the user's C project.
Used when the user wants to verify their corrections with [v].
"""

import subprocess
import os
from typing import Dict


def rebuild_project(executable_path):
    """
    Recompile le projet de l'utilisateur.
    
    Args:
        executable_path: Chemin vers l'exécutable (ex: "./test_mistral/leaky")
    
    Returns:
        dict: {'success': bool, 'output': str}
    """
    import os
    import subprocess
    
    # Extraire le dossier de l'exécutable
    project_dir = os.path.dirname(executable_path)
    
    # Si pas de dossier (ex: "./leaky"), utiliser le répertoire courant
    if not project_dir:
        project_dir = "."
    
    # Chercher le Makefile dans ce dossier
    makefile_path = os.path.join(project_dir, "Makefile")
    
    if not os.path.exists(makefile_path):
        return {
            'success': False,
            'output': (
                "⚠️  Makefile requis pour la vérification automatique\n\n"
                f"Créez un Makefile dans {project_dir}, puis relancez [v]\n"
                "(ou utilisez [s] pour passer au leak suivant)"
            )
        }
    
    try:
        # Exécuter make depuis le dossier du projet
        result = subprocess.run(
            ['make'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_dir  # ← Exécuter depuis ce dossier
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'output': '✅ Compilation réussie'
            }
        else:
            return {
                'success': False,
                'output': (
                    "❌ Erreur de compilation\n\n"
                    f"{result.stderr if result.stderr else result.stdout}"
                )
            }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': (
                "❌ La compilation a dépassé le timeout de 30 secondes\n"
                "Vérifiez votre Makefile"
            )
        }
    
    except Exception as e:
        return {
            'success': False,
            'output': f"❌ Erreur lors de la compilation : {str(e)}"
        }


def main():
    """
    Test function for standalone execution.
    """
    print("🔨 Test du module builder...\n")
    result = rebuild_project()
    
    print(f"Success: {result['success']}")
    print(f"Output:\n{result['output']}")


if __name__ == "__main__":
    main()
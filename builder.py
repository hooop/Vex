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


def rebuild_project() -> Dict[str, any]:
    """
    Recompile the user's project by running 'make'.

    Looks for a Makefile in the current directory and executes it.
    Captures compilation output to display errors if any.

    Returns:
        dict: {
            'success': bool - True if compilation succeeded
            'output': str - Compilation output (for error display)
        }
    """
    # Check if Makefile exists
    if not os.path.exists('Makefile'):
        return {
            'success': False,
            'output': (
                "⚠️  Makefile requis pour la vérification automatique\n\n"
                "Créez un Makefile dans votre projet, puis relancez [v]\n"
                "(ou utilisez [s] pour passer au leak suivant)"
            )
        }

    try:
        # Execute make
        result = subprocess.run(
            ['make'],
            capture_output=True,
            text=True,
            timeout=30
        )

        # Check return code
        if result.returncode == 0:
            return {
                'success': True,
                'output': '✅ Compilation réussie'
            }
        else:
            # Compilation failed
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
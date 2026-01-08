"""
builder.py

Module responsible for recompiling the user's C project.
Used when the user wants to verify their corrections with [v].
"""

import os
import subprocess
from typing import TypedDict

class BuildResult(TypedDict):
    """Result of a project rebuild attempt."""
    success: bool
    output: str

def rebuild_project(executable_path: str) -> BuildResult:
    """
    Recompile the user's project using make.
    
    Args:
        executable_path: Path to the executable (e.g., "./test_mistral/leaky")
    
    Returns:
        dict: Dictionary with keys:
            - 'success' (bool): Whether compilation succeeded
            - 'output' (str): Compilation output or error message
    """
     
    # Extract the project directory from executable path
    project_dir = os.path.dirname(executable_path)
    
    # If no directory (e.g., "./leaky"), use current directory
    if not project_dir:
        project_dir = "."
    
    # Look for Makefile in this directory
    makefile_path = os.path.join(project_dir, "Makefile")
    
    if not os.path.exists(makefile_path):
        return {
            'success': False,
            'output': (
                "Makefile required for automatic verification\n\n"
                f"Create a Makefile in {project_dir}, then retry [v]\n"
                "(or use [n] to skip to next leak)"
            )
        }
    
    try:
        # Run make from the project directory
        result = subprocess.run(
            ['make'],
            capture_output=True,
            text=True,
            timeout=30,
            cwd=project_dir
        )
        
        if result.returncode == 0:
            return {
                'success': True,
                'output': 'Compilation successful'
            }
        else:
            return {
                'success': False,
                'output': (
                    "Compilation error\n\n"
                    f"{result.stderr if result.stderr else result.stdout}"
                )
            }
    
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'output': (
                "Compilation exceeded 30 second timeout\n"
                "Check your Makefile"
            )
        }
    
    except Exception as e:
        return {
            'success': False,
            'output': f"Error during compilation: {str(e)}"
        }
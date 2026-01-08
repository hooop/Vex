"""
Mistral Analyzer - Wrapper pour l'analyse avec Mistral AI

Adapte mistral_api.py pour l'intégration avec vex.py
"""

from mistral_api import analyze_memory_leak


class MistralAPIError(Exception):
    """Exception levée en cas d'erreur avec l'API Mistral."""
    pass


def analyze_with_mistral(error_data):
    """
    Analyse une erreur mémoire avec Mistral AI.

    Args:
        error_data: Dict avec 'type', 'bytes', 'file', 'line', 'function',
                   'backtrace', 'extracted_code', et 'root_cause'

    Returns:
        dict: Analyse de Mistral

    Raises:
        MistralAPIError: En cas d'erreur API
    """
    try:
        # Formater le code extrait
        code_context = _format_extracted_code(error_data.get('extracted_code', []))

        # Récupérer la root cause (calculée par memory_tracker)
        root_cause = error_data.get('root_cause', None)

        # Appel à l'API Mistral via mistral_api.py
        analysis = analyze_memory_leak(error_data, code_context, root_cause)

        return analysis

    except Exception as e:
        raise MistralAPIError(f"Erreur lors de l'analyse : {str(e)}")


def _format_extracted_code(extracted_code):
    if not extracted_code:
        return "=== Aucun code source disponible ===\n"

    formatted = "=== CALL STACK WITH SOURCE CODE ===\n\n"

    for i, frame in enumerate(extracted_code, 1):
        code_lines = frame['code'].strip().split('\n')
        last_line_num = code_lines[-1].split(':')[0] if code_lines else '?'

        formatted += f"{'='*50}\n"
        formatted += f"FONCTION {i}: {frame['function']}\n"
        formatted += f"Fichier: {frame['file']}\n"
        formatted += f"Commence à la ligne: {frame['line']}\n"
        formatted += f"Fin fonction: ligne {last_line_num}\n"
        formatted += f"{'='*50}\n"
        formatted += frame['code']
        formatted += "\n\n"

    return formatted

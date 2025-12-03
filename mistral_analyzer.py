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
                   'backtrace', et 'extracted_code'

    Returns:
        str: Analyse de Mistral

    Raises:
        MistralAPIError: En cas d'erreur API
    """
    try:
        # Formater le code extrait
        code_context = _format_extracted_code(error_data.get('extracted_code', []))

        # Appel à l'API Mistral via mistral_api.py
        analysis = analyze_memory_leak(error_data, code_context)

        return analysis

    except Exception as e:
        raise MistralAPIError(f"Erreur lors de l'analyse : {str(e)}")


def _format_extracted_code(extracted_code):
    """
    Formate le code extrait pour l'envoi à Mistral.

    Args:
        extracted_code: Liste de dicts avec 'file', 'function', 'line', 'code'

    Returns:
        str: Code formaté
    """
    if not extracted_code:
        return "=== Aucun code source disponible ===\n"

    formatted = "=== CALL STACK WITH SOURCE CODE ===\n\n"

    for i, frame in enumerate(extracted_code, 1):
        formatted += f"--- Function {i}: {frame['function']} ---\n"
        formatted += f"File: {frame['file']}\n"
        formatted += f"Line: {frame['line']}\n\n"
        formatted += frame['code']
        formatted += "\n\n"

    return formatted

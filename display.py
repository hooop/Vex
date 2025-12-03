"""
Display Module for Vex

Formats and displays analysis results in the terminal.
"""
import os

def _build_header(error_number, total_errors):
    """
    Construit le header avec les lignes horizontales et le séparateur aligné.
    
    Args:
        error_number: Numéro du leak actuel
        total_errors: Nombre total de leaks
    
    Returns:
        str: Header formaté avec couleurs ANSI
    """
    DARK_GREEN = "\033[38;5;49m"
    RESET = "\033[0m"
    
    # Construction du texte central
    text = f"‣ Leak {error_number} / {total_errors} | Valgrind Error eXplorer"
    
    # Trouve la position du '|' dans le texte
    separator_pos = text.index('|')
    
    # Calcule la longueur totale
    total_length = len(text)
    
    # Construction des lignes avec le '+' aligné sur le '|'
    top_line = "―" * separator_pos + "+" + "―" * (total_length - separator_pos - 1)
    bottom_line = top_line  # Identique
    
    # Assemblage final avec couleurs
    header = f"{DARK_GREEN}{top_line}\n{text}\n{bottom_line}{RESET}\n"
    
    return header

def _build_valgrind_section(error):
    """
    Construit la section Extrait Valgrind avec les bonnes couleurs.
    
    Args:
        error: Dict de l'erreur (type, bytes, blocks, backtrace, etc.)
    
    Returns:
        str: Section formatée avec couleurs ANSI
    """
    GREEN = "\033[38;5;158m"
    LIGHT_YELLOW = "\033[38;5;230m"
    RESET = "\033[0m"
    
    # Titre
    output = f"{GREEN}• Extrait Valgrind{RESET}\n\n"
    
    # Première ligne avec infos complètes
    bytes_info = f"{error.get('bytes', '?')} bytes"
    if error.get('blocks'):
        bytes_info += f" in {error['blocks']} blocks"
    bytes_info += f" are {error.get('type', 'unknown')}"
    
    output += f"{LIGHT_YELLOW}{bytes_info}\n"
    
    # Ligne malloc (système)
    output += "    at 0x[...]: malloc (in /usr/libexec/valgrind/vgpreload_memcheck-amd64-linux.so)\n"
    
    # Backtrace dans l'ordre Valgrind (allocation → main)
    if error.get('backtrace'):
        backtrace_reversed = list(reversed(error['backtrace']))
        for frame in backtrace_reversed:
            output += f"    by {frame.get('function', '?')} ({frame.get('file', '?')}:{frame.get('line', '?')})\n"
    
    output += f"{RESET}\n"
    
    return output

def _build_analysis_section(analysis):
    """
    Construit la section Analyse Vex avec type de leak et diagnostic.
    
    Args:
        analysis: Dict retourné par Mistral
    
    Returns:
        str: Section formatée avec couleurs ANSI
    """
    GREEN = "\033[38;5;158m"
    DARK_YELLOW = "\033[38;5;228m"
    LIGHT_YELLOW = "\033[38;5;230m"
    RESET = "\033[0m"
    
    type_leak_labels = {
        1: "La mémoire n'a jamais été libérée",
        2: "Le pointeur a été perdu avant de libérer la mémoire",
        3: "Plus aucun pointeur ne permet d'accéder à cette mémoire"
    }
    
    # Titre
    output = f"{GREEN}• Analyse Vex{RESET}\n\n"
    
    # Type de leak
    type_leak = analysis.get('type_leak', 0)
    if type_leak in type_leak_labels:
        output += f"{DARK_YELLOW}→ {type_leak_labels[type_leak]}{RESET}\n\n"
    
    # Diagnostic
    diagnostic = analysis.get('diagnostic', 'Aucun diagnostic disponible')
    output += f"{LIGHT_YELLOW}{diagnostic}{RESET}\n\n"
    
    return output


def _build_code_section(error, analysis):
    """
    Construit la section Code concerné avec le code source et la root cause.
    
    Args:
        error: Dict de l'erreur
        analysis: Dict retourné par Mistral
    
    Returns:
        str: Section formatée avec couleurs ANSI
    """
    GREEN = "\033[38;5;158m"
    LIGHT_YELLOW = "\033[38;5;230m"
    DARK_PINK = "\033[38;5;205m"
    GRAY = "\033[38;5;236m"
    RESET = "\033[0m"
    
    cause = analysis.get('cause_reelle')
    if not cause:
        return ""
    
    type_leak = analysis.get('type_leak', 0)
    
    # Titre
    output = f"{GREEN}• Code concerné{RESET}\n\n"
    
    # Fichier et fonction
    if type_leak == 1:
        display_file = error.get('file', 'unknown')
        display_line = error.get('line', '?')
        display_function = error.get('function', 'unknown')
    else:
        display_file = cause.get('file', error.get('file', 'unknown'))
        display_line = cause.get('line', error.get('line', '?'))
        display_function = cause.get('function', error.get('function', 'unknown'))
    
    output += f"{LIGHT_YELLOW}Fichier  : {display_file}:{display_line}\n"
    output += f"Fonction : {display_function}(){RESET}\n\n"
    
    # Récupération du numéro de ligne de la root cause
    root_line_number = int(display_line) if str(display_line).isdigit() else None
    
    # context_before
    if not cause.get('contributing_lines') and cause.get('context_before'):
        line_num = root_line_number - 1 if root_line_number else "?"
        output += f"   {line_num} | {cause['context_before']}\n"
    
    # contributing_lines
    if cause.get('contributing_lines'):
        # Trier par numéro de ligne croissant
        sorted_contribs = sorted(cause['contributing_lines'], key=lambda x: x.get('line', 0))
        for contrib in sorted_contribs:
            line_num = contrib.get('line', '?')
            # output += f"   {line_num} | {contrib['code']}  {GRAY}// {contrib['comment']}{RESET}\n"
            output += f"   {line_num} | {contrib['code']}\n"
   
    # root_cause_line
    root_cause = cause['root_cause_line']
    root_comment = cause.get('root_cause_comment', '')
    output += f"{DARK_PINK}‣  {root_line_number if root_line_number else '?'} | {root_cause}{RESET}  {GRAY}// {root_comment}{RESET}\n"
    
    # context_after
    if cause.get('context_after'):
        line_num = root_line_number + 1 if root_line_number else "?"
        output += f"   {line_num} | {cause['context_after']}\n"
    
    output += "\n"
    
    return output


def _build_solution_section(analysis):
    """
    Construit la section Solution avec le principe et le code.
    
    Args:
        analysis: Dict retourné par Mistral
    
    Returns:
        str: Section formatée avec couleurs ANSI
    """
    GREEN = "\033[38;5;158m"
    LIGHT_YELLOW = "\033[38;5;230m"
    RESET = "\033[0m"
    
    # Titre
    output = f"{GREEN}• Solution{RESET}\n\n"
    
    # Principe de résolution
    resolution = analysis.get('resolution_principe', 'Aucune résolution proposée')
    output += f"{LIGHT_YELLOW}{resolution}{RESET}\n\n"
    
    # Code de résolution
    if analysis.get('resolution_code'):
        output += f"{analysis['resolution_code']}\n\n"
    
    return output

def _build_explications_section(analysis):
    """
    Construit la section Explications.
    
    Args:
        analysis: Dict retourné par Mistral
    
    Returns:
        str: Section formatée avec couleurs ANSI
    """
    GREEN = "\033[38;5;158m"
    LIGHT_YELLOW = "\033[38;5;230m"
    RESET = "\033[0m"
    
    # Titre
    output = f"{GREEN}• Explications{RESET}\n\n"
    
    # Contenu des explications
    explications = analysis.get('explications', 'Aucune explication disponible')
    output += f"{LIGHT_YELLOW}{explications}{RESET}\n\n"
    
    return output

def display_analysis(error, analysis, error_number=1, total_errors=1):
    """
    Affiche une analyse de façon formatée dans le terminal.

    Args:
        error: Dict de l'erreur (type, bytes, file, line, etc.)
        analysis: Dict retourné par Mistral (JSON parsé) ou dict avec 'error'
        error_number: Numéro de l'erreur actuelle
        total_errors: Nombre total d'erreurs
    """
    # Header

    # Clear screen
    # os.system('clear')

    print(_build_header(error_number, total_errors))

    # DEBUG: affiche le JSON brut
    import json
    print("DEBUG JSON:")
    print(json.dumps(analysis.get('cause_reelle'), indent=2, ensure_ascii=False))
    print()

    print(_build_valgrind_section(error))

    # Si erreur dans l'analyse Mistral
    if 'error' in analysis:
        print(f"❌ Erreur Mistral : {analysis['error']}")
        if 'raw' in analysis:
            print(f"\nRéponse brute :\n{analysis['raw']}")
        return

    print(_build_analysis_section(analysis))

    print(_build_code_section(error, analysis))

    print(_build_solution_section(analysis))

    print(_build_explications_section(analysis))
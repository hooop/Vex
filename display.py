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
    
    # Ligne malloc (système) - utilise celle capturée ou fallback
    allocation = error.get('allocation_line', 
        "    at 0x[...]: malloc (in /usr/libexec/valgrind/vgpreload_memcheck-amd64-linux.so)")
    output += f"{allocation}\n"
    
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

def _find_line_number(filepath, code_to_find):
    """
    Cherche le numéro de ligne d'un code dans un fichier source.
    
    Args:
        filepath: Chemin du fichier source
        code_to_find: Code à chercher (sans numéro de ligne)
    
    Returns:
        int: Numéro de ligne (1-indexed) ou None si pas trouvé
    """
    import os
    
    # Si le fichier n'existe pas, essayer de le trouver
    if not os.path.exists(filepath):
        # Essayer juste le nom du fichier dans le répertoire courant
        basename = os.path.basename(filepath)
        if os.path.exists(basename):
            filepath = basename
        else:
            return None
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except (IOError, UnicodeDecodeError):
        return None
    
    # Nettoyer le code à chercher (enlever espaces superflus)
    code_clean = code_to_find.strip()
    
    # Chercher dans toutes les lignes
    for i, line in enumerate(lines, start=1):
        # Enlever les espaces et comparer
        if line.strip() == code_clean:
            return i
    
    return None


def _clean_and_sort_code_lines(source_file, cause):
    """
    Nettoie et trie les lignes de code selon leur position réelle dans le fichier.
    Supprime les doublons et les lignes dans le mauvais ordre.
    
    Args:
        source_file: Chemin du fichier source
        cause: Dict cause_reelle de Mistral
    
    Returns:
        dict: Lignes nettoyées avec numéros de ligne
    """
    # 1. Trouver le numéro de la root_cause
    root_code = cause.get('root_cause_code', '')
    root_line = _find_line_number(source_file, root_code)
    
    if not root_line:
        return None
    
    # 2. Traiter les contributing_codes
    contributing = []
    seen_codes = set()  # Pour éviter les doublons
    
    for contrib in cause.get('contributing_codes', []):
        code = contrib.get('code', '').strip()
        
        # Ignorer si doublon
        if code in seen_codes:
            continue
        
        # Ignorer si égal à root_cause
        if code == root_code.strip():
            continue
        
        line_num = _find_line_number(source_file, code)
        
        # Ignorer si pas trouvé ou après root_cause
        if not line_num or line_num >= root_line:
            continue
        
        seen_codes.add(code)
        contributing.append({
            'line': line_num,
            'code': code,
            'comment': contrib.get('comment')
        })
    
    # Trier par numéro de ligne croissant
    contributing.sort(key=lambda x: x['line'])
    
    # 3. Traiter context_before
    context_before = None
    context_before_code = cause.get('context_before_code', '').strip()
    
    if context_before_code:
        # Ignorer si déjà dans contributing ou égal à root
        if context_before_code not in seen_codes and context_before_code != root_code.strip():
            ctx_line = _find_line_number(source_file, context_before_code)
            # Doit être avant root_cause
            if ctx_line and ctx_line < root_line:
                context_before = {
                    'line': ctx_line,
                    'code': context_before_code
                }
    
    # 4. Traiter context_after
    context_after = None
    context_after_code = cause.get('context_after_code', '').strip()
    
    if context_after_code:
        # Ignorer si déjà vu ou égal à root
        if context_after_code not in seen_codes and context_after_code != root_code.strip():
            ctx_line = _find_line_number(source_file, context_after_code)
            # Doit être après root_cause
            if ctx_line and ctx_line > root_line:
                context_after = {
                    'line': ctx_line,
                    'code': context_after_code
                }
    
    return {
        'root_line': root_line,
        'root_code': root_code,
        'root_comment': cause.get('root_cause_comment', ''),
        'contributing': contributing,
        'context_before': context_before,
        'context_after': context_after
    }


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
    
    # Récupérer le fichier source
    source_file = cause.get('file', error.get('file', 'unknown'))
    
    # Nettoyer et trier les lignes
    cleaned = _clean_and_sort_code_lines(source_file, cause)
    
    if not cleaned:
        output += f"{LIGHT_YELLOW}Impossible de localiser le code source.{RESET}\n\n"
        return output
    
    # Fichier et fonction
    display_function = cause.get('function', error.get('function', 'unknown'))
    
    output += f"{LIGHT_YELLOW}Fichier  : {source_file}:{cleaned['root_line']}\n"
    output += f"Fonction : {display_function}(){RESET}\n\n"
    
    # Construire la liste ordonnée de toutes les lignes à afficher
    lines_to_display = []

    # 1. context_before (si pas de contributing)
    if not cleaned['contributing'] and cleaned['context_before']:
        lines_to_display.append({
            'line': cleaned['context_before']['line'],
            'code': cleaned['context_before']['code'],
            'comment': None,
            'is_root': False
        })

    # 2. contributing (déjà triés)
    for contrib in cleaned['contributing']:
        lines_to_display.append({
            'line': contrib['line'],
            'code': contrib['code'],
            'comment': contrib['comment'],
            'is_root': False
        })

    # 3. root_cause
    lines_to_display.append({
        'line': cleaned['root_line'],
        'code': cleaned['root_code'],
        'comment': cleaned['root_comment'],
        'is_root': True
    })

    # 4. context_after
    if cleaned['context_after']:
        lines_to_display.append({
            'line': cleaned['context_after']['line'],
            'code': cleaned['context_after']['code'],
            'comment': None,
            'is_root': False
        })

    # Affichage avec détection des sauts
    for i, item in enumerate(lines_to_display):
        # Afficher "..." si saut détecté
        if i > 0:
            prev_line = lines_to_display[i-1]['line']
            curr_line = item['line']
            if curr_line - prev_line > 1:
                output += f"   {GRAY}···{RESET}\n"
        
        # Afficher la ligne
        if item['is_root']:
            # Root cause en rose
            output += f"{DARK_PINK}‣  {item['line']} | {item['code']}{RESET}"
            if item['comment']:
                output += f"  {GRAY}// {item['comment']}{RESET}"
            output += "\n"
        else:
            # Ligne normale
            output += f"   {item['line']} | {item['code']}"
            if item['comment']:
                output += f"  {GRAY}// {item['comment']}{RESET}"
            output += "\n"

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
    # import json
    # print("DEBUG JSON:")
    # print(json.dumps(analysis, indent=2, ensure_ascii=False))
    # print()

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
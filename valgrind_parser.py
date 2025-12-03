#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
valgrind_parser.py

Module responsable du parsing des rapports Valgrind pour en extraire
les informations structurées sur les fuites mémoire.

Fonctionnalités :
- Détection de la présence de leaks
- Extraction du résumé global (LEAK SUMMARY)
- Extraction détaillée de chaque leak individuel (bytes, fichier, ligne)
- Gestion du cas "no leaks"
"""

import re
from typing import Dict, List, Optional


def parse_valgrind_report(report: str) -> Dict:
    """
    Parse un rapport Valgrind et extrait les informations sur les fuites mémoire.

    Args:
        report: Le texte complet du rapport Valgrind (retourné par valgrind_runner)

    Returns:
        dict: Dictionnaire structuré contenant :
            - has_leaks (bool): True si des leaks sont détectés
            - summary (dict): Résumé des leaks (bytes par type)
            - leaks (list): Liste détaillée de chaque leak

    Example:
        >>> report = "==123== 24 bytes in 1 blocks are definitely lost..."
        >>> result = parse_valgrind_report(report)
        >>> print(result["has_leaks"])
        True
    """

    # Structure de base du résultat
    result = {
        "has_leaks": False,
        "summary": {
            "definitely_lost": 0,
            "indirectly_lost": 0,
            "possibly_lost": 0,
            "still_reachable": 0,
            "total_leaked": 0
        },
        "leaks": []
    }

    # Vérification rapide : y a-t-il des leaks ?
    if "All heap blocks were freed -- no leaks are possible" in report:
        return result

    # Extraction du résumé global
    summary = _extract_leak_summary(report)
    if summary:
        result["summary"] = summary
        # Si definitely_lost ou indirectly_lost > 0, on a des leaks
        if summary["definitely_lost"] > 0 or summary["indirectly_lost"] > 0:
            result["has_leaks"] = True

    # Extraction des leaks individuels
    leaks = _extract_individual_leaks(report)
    if leaks:
        result["leaks"] = leaks

    return result


def _extract_leak_summary(report: str) -> Optional[Dict]:
    """
    Extrait le résumé global des leaks depuis la section LEAK SUMMARY.

    Cherche la section :
    ==PID== LEAK SUMMARY:
    ==PID==    definitely lost: X bytes in Y blocks
    ==PID==    indirectly lost: X bytes in Y blocks
    ...

    Args:
        report: Le rapport Valgrind complet

    Returns:
        dict ou None: Dictionnaire avec les bytes par type de leak
    """

    # Pattern pour trouver la section LEAK SUMMARY
    summary_pattern = r"LEAK SUMMARY:"

    if not re.search(summary_pattern, report):
        return None

    summary = {
        "definitely_lost": 0,
        "indirectly_lost": 0,
        "possibly_lost": 0,
        "still_reachable": 0,
        "total_leaked": 0
    }

    # Pattern pour extraire chaque ligne du summary
    # Exemple: "==28==    definitely lost: 74 bytes in 2 blocks"
    line_pattern = r"==\d+==\s+(definitely lost|indirectly lost|possibly lost|still reachable):\s+(\d+)\s+bytes"

    matches = re.finditer(line_pattern, report)

    for match in matches:
        leak_type = match.group(1).replace(" ", "_")  # "definitely lost" -> "definitely_lost"
        bytes_leaked = int(match.group(2))

        if leak_type in summary:
            summary[leak_type] = bytes_leaked

    # Calcul du total leaked (definitely + indirectly)
    summary["total_leaked"] = summary["definitely_lost"] + summary["indirectly_lost"]

    return summary


def _extract_individual_leaks(report: str) -> List[Dict]:
    """
    Extrait chaque leak individuel avec ses détails (bytes, fichier, ligne).

    Cherche les blocs de la forme :
    ==PID== 24 bytes in 1 blocks are definitely lost in loss record 1 of 2
    ==PID==    at 0x4846828: malloc (...)
    ==PID==    by 0x109270: main (test_multiple_errors.c:37)

    Args:
        report: Le rapport Valgrind complet

    Returns:
        list: Liste de dictionnaires, un par leak détecté
    """

    leaks = []


    # Pattern pour détecter le début d'un leak
    # Exemple: "==28== 24 bytes in 1 blocks are definitely lost in loss record 1 of 2"
    leak_header_pattern = r"==\d+==\s+(\d+)(?:\s+\([^)]+\))?\s+bytes in\s+(\d+)\s+blocks? (?:is |are )(definitely|possibly) lost"

    # Trouve tous les headers de leak
    header_matches = list(re.finditer(leak_header_pattern, report))

    for header_match in header_matches:
        bytes_leaked = int(header_match.group(1))
        blocks_count = int(header_match.group(2))
        leak_type = header_match.group(3) + " lost"

        # Position dans le texte où commence ce leak
        start_pos = header_match.end()

        # On cherche la location (fichier:ligne) dans les lignes suivantes
        # Pattern: "by 0xADDRESS: function_name (file.c:123)"
        location_info = _parse_leak_location(report, start_pos)

        leak_entry = {
            "type": leak_type,
            "bytes": bytes_leaked,
            "blocks": blocks_count,
            "file": location_info.get("file", "unknown"),
            "line": location_info.get("line", 0),
            "function": location_info.get("function", "unknown"),
            "backtrace": location_info.get("backtrace", [])
        }

        leaks.append(leak_entry)

    return leaks


def _parse_leak_location(report: str, start_pos: int) -> Dict:
    """
    Parse la location complète d'un leak avec toute la backtrace.

    Extrait TOUTES les fonctions de la pile d'appels, de l'allocation
    jusqu'au point d'entrée (main), pour avoir le contexte complet.

    Args:
        report: Le rapport Valgrind complet
        start_pos: Position dans le rapport où commencer la recherche

    Returns:
        dict: Contient 'file', 'line', 'function' pour la première entrée,
              et 'backtrace' avec la pile complète
    """

    # Fonctions système à ignorer
    SYSTEM_FUNCTIONS = {'malloc', 'calloc', 'realloc', 'free', 'strdup',
                        'memcpy', 'memmove', 'memset'}

    # On prend un extrait
    excerpt = report[start_pos:start_pos + 1000]

    # IMPORTANT: S'arrêter à la première ligne vide après le début
    # Les blocs Valgrind sont séparés par des lignes vides
    lines = excerpt.split('\n')
    relevant_lines = []
    started = False

    for line in lines:
        # Si on trouve "at" ou "by", on commence à capturer
        if re.search(r'(?:at|by)\s+0x[0-9A-Fa-f]+:', line):
            relevant_lines.append(line)
            started = True
        # Si ligne vide et qu'on a déjà commencé, on s'arrête
        elif started and (line.strip() == '' or re.match(r'==\d+==\s*$', line)):
            break
        # Sinon on continue si démarré
        elif started:
            relevant_lines.append(line)

    # Reconstruire l'extrait pertinent
    excerpt = '\n'.join(relevant_lines)

    # Pattern pour capturer "at" ET "by"
    location_pattern = r"(?:at|by)\s+0x[0-9A-Fa-f]+:\s+(\w+)\s+\(([^:)]+):(\d+)\)"

    # Trouver toutes les correspondances
    matches = re.finditer(location_pattern, excerpt)

    backtrace = []
    for match in matches:
        function = match.group(1)
        file = match.group(2)
        line = int(match.group(3))

        # Filtrer les fonctions système ET les fichiers système
        if function in SYSTEM_FUNCTIONS:
            continue
        if file.startswith("/usr/") or file.startswith("vg_"):
            continue

        backtrace.append({
            "function": function,
            "file": file,
            "line": line
        })

    # Inverser la backtrace pour avoir l'ordre logique (main -> ... -> fonction_leak)
    backtrace.reverse()

    # Si on a trouvé au moins une entrée
    if backtrace:
        # Maintenant la DERNIÈRE entrée est celle où le malloc a été fait
        last = backtrace[-1]
        return {
            "function": last["function"],
            "file": last["file"],
            "line": last["line"],
            "backtrace": backtrace
        }

    # Si on ne trouve rien, retour de valeurs par défaut
    return {
        "function": "unknown",
        "file": "unknown",
        "line": 0,
        "backtrace": []
    }

    # Inverser la backtrace pour avoir l'ordre logique (main -> ... -> fonction_leak)
    backtrace.reverse()

    # Si on a trouvé au moins une entrée
    if backtrace:
        # Maintenant la DERNIÈRE entrée est celle où le malloc a été fait
        last = backtrace[-1]
        return {
            "function": last["function"],
            "file": last["file"],
            "line": last["line"],
            "backtrace": backtrace
        }

    # Si on ne trouve rien, retour de valeurs par défaut
    return {
        "function": "unknown",
        "file": "unknown",
        "line": 0,
        "backtrace": []
    }


def main():
    """
    Fonction de test standalone pour valider le parser.
    """
    import sys

    if len(sys.argv) != 2:
        print("Usage: python3 valgrind_parser.py <valgrind_report.txt>")
        sys.exit(1)

    report_file = sys.argv[1]

    try:
        with open(report_file, 'r') as f:
            report = f.read()

        result = parse_valgrind_report(report)

        # Affichage du résultat de parsing
        print("\n" + "="*60)
        print("RÉSULTAT DU PARSING")
        print("="*60 + "\n")

        print(f"📊 Leaks détectés : {'OUI' if result['has_leaks'] else 'NON'}")
        print()

        if result["has_leaks"]:
            print("📈 RÉSUMÉ :")
            summary = result["summary"]
            print(f"  • Definitely lost : {summary['definitely_lost']} bytes")
            print(f"  • Indirectly lost : {summary['indirectly_lost']} bytes")
            print(f"  • Possibly lost   : {summary['possibly_lost']} bytes")
            print(f"  • TOTAL           : {summary['total_leaked']} bytes")
            print()

            print(f"🔍 DÉTAILS ({len(result['leaks'])} leaks) :")
            for i, leak in enumerate(result["leaks"], 1):
                print(f"\n  Leak #{i}:")
                print(f"    Type     : {leak['type']}")
                print(f"    Taille   : {leak['bytes']} bytes ({leak['blocks']} block(s))")
                print(f"    Location : {leak['file']}:{leak['line']}")
                print(f"    Fonction : {leak['function']}")

                # Affichage de la backtrace si disponible
                if leak.get('backtrace') and len(leak['backtrace']) > 1:
                    print(f"\n    📚 Call stack ({len(leak['backtrace'])} niveaux) :")
                    for j, frame in enumerate(leak['backtrace'], 1):
                        indent = "      "
                        # Dernier élément = où se fait l'allocation (le problème)
                        arrow = "└→" if j == len(leak['backtrace']) else "├→"
                        print(f"{indent}{arrow} {frame['function']} ({frame['file']}:{frame['line']})")
        else:
            print("✅ Aucune fuite mémoire détectée !")

        print("\n" + "="*60 + "\n")

    except FileNotFoundError:
        print(f"❌ Erreur : le fichier '{report_file}' n'existe pas.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lors du parsing : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

"""
Test du pipeline complet de Vex avec affichage amélioré
"""

from valgrind_runner import run_valgrind
from valgrind_parser import parse_valgrind_report
from code_extractor import extract_call_stack, format_for_ai
from mistral_api import analyze_memory_leak

# Import de rich pour un bel affichage
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

# Création de la console rich
console = Console()


def print_header(text):
    """Affiche un header stylisé"""
    console.print(f"\n[bold cyan]{text}[/bold cyan]")


def print_section(title, content):
    """Affiche une section avec un titre"""
    console.print(f"\n[bold yellow]{title}:[/bold yellow] {content}")


def display_mistral_response(analysis):
    """
    Affiche la réponse de Mistral de façon élégante avec rich

    Args:
        analysis: La réponse texte de Mistral (en Markdown)
    """
    # Crée un panel avec le markdown rendu
    md = Markdown(analysis)
    panel = Panel(
        md,
        title="[bold magenta]🤖 Analyse Mistral AI[/bold magenta]",
        border_style="magenta",
        padding=(1, 2)
    )
    console.print(panel)


def main():
    # 1. Lance Valgrind sur ton programme
    print_header("🔧 Exécution de Valgrind...")

    executable_cmd = "./leaky"
    console.print(f"Commande : '{executable_cmd}'", style="dim")

    try:
        valgrind_output = run_valgrind(executable_cmd)
    except Exception as e:
        console.print(f"[bold red]❌ Erreur : {e}[/bold red]")
        import traceback
        traceback.print_exc()
        return

    # 2. Parse le rapport
    print_header("📊 Parsing du rapport...")
    result = parse_valgrind_report(valgrind_output)

    # DEBUG: Affiche la structure complète du résultat
    console.print(f"  has_leaks: {result['has_leaks']}", style="dim")
    console.print(f"  nombre de leaks: {len(result['leaks'])}", style="dim")
    console.print(f"  summary: {result['summary']}", style="dim")

    errors = result["leaks"]

    if not errors:
        console.print("\n[bold green]🎉 Aucun memory leak détecté ![/bold green]")
        console.print("\n📄 Extrait du rapport Valgrind (premiers caractères) :", style="dim")
        console.print(valgrind_output[:1000], style="dim")
        return

    console.print(f"\n[bold green]✅ {len(errors)} leak(s) détecté(s)[/bold green]\n")

    # 3. Pour chaque erreur
    for i, error in enumerate(errors, 1):
        console.rule(f"[bold]LEAK #{i}[/bold]", style="cyan")

        # Affiche les infos brutes
        print_section("Type", error['type'])
        print_section("Taille", f"{error['bytes']} bytes ({error['blocks']} blocks)")
        print_section("Fonction", f"{error['function']}() [{error['file']}:{error['line']}]")
        print_section("Backtrace", f"{len(error['backtrace'])} fonctions")

        # 4. Extrait le code
        console.print("\n[cyan]🔎 Extraction du code source...[/cyan]")
        extracted_functions = extract_call_stack(error['backtrace'])

        if not extracted_functions:
            console.print("[yellow]⚠️  Impossible d'extraire le code source[/yellow]")
            continue

        code_formatted = format_for_ai(extracted_functions)

        # Affiche le code extrait de façon condensée
        console.print(f"{code_formatted[:200]}...", style="dim")

        # 5. Analyse avec Mistral
        console.print("\n[magenta]🤖 Analyse avec Mistral AI...[/magenta]\n")

        # Adapter le format pour mistral_api
        error_for_mistral = {
            'type': error['type'],
            'size': f"{error['bytes']} bytes",
            'address': 'N/A',
            'function': error['function'],
            'file': error['file'],
            'line': error['line']
        }

        analysis = analyze_memory_leak(error_for_mistral, code_formatted)

        # AFFICHAGE AMÉLIORÉ avec rich
        display_mistral_response(analysis)

        console.print("\n")


if __name__ == "__main__":
    main()

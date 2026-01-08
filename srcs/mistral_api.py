"""
Mistral API Module for Vex

Sends memory leak analysis requests to Mistral AI and returns pedagogical explanations.
"""

import os
import json
from dotenv import load_dotenv
from mistralai import Mistral


# Charge les variables d'environnement
load_dotenv()

# Initialise le client Mistral
API_KEY = os.environ.get("MISTRAL_API_KEY")
if not API_KEY:
    raise ValueError(
        "MISTRAL_API_KEY n'est pas définie.\n"
        "Créez un fichier .env avec : MISTRAL_API_KEY=votre_clé"
    )

client = Mistral(api_key=API_KEY)


def _clean_json_response(response):
    """Nettoie la réponse pour extraire le JSON pur."""
    response = response.strip()

    if "```" in response:
        start = response.find('{')
        end = response.rfind('}')
        if start != -1 and end != -1:
            response = response[start:end+1]

    return response.strip()


def analyze_memory_leak(error_data, code_context, root_cause=None):
    """
    Analyse un memory leak avec Mistral AI.

    Args:
        error_data: Dict avec infos Valgrind
        code_context: Code source formaté
        root_cause: Dict avec 'type', 'line', 'function', 'file', 'steps' (from memory_tracker)

    Returns:
        dict: Analyse structurée ou dict avec 'error' en cas de problème
    """
    try:
        prompt = _build_prompt(error_data, code_context, root_cause)
        response = _call_mistral_api(prompt)

        # Nettoie la réponse
        cleaned = _clean_json_response(response)

        # Parse le JSON
        analysis = json.loads(cleaned)

        # Validation basique
        required_keys = ["type_leak", "diagnostic", "raisonnement",
                        "resolution_principe", "resolution_code", "explications"]

        for key in required_keys:
            if key not in analysis:
                raise ValueError(f"Clé manquante : {key}")

        # Injecter les données de root_cause dans la réponse
        if root_cause:
            analysis["type_leak"] = root_cause["type"]
            if "cause_reelle" not in analysis:
                analysis["cause_reelle"] = {}
            analysis["cause_reelle"]["file"] = root_cause.get("file", "unknown")
            analysis["cause_reelle"]["function"] = root_cause["function"]
            analysis["cause_reelle"]["root_cause_code"] = root_cause["line"].strip()

        return analysis

    except json.JSONDecodeError as e:
        return {"error": f"JSON invalide : {str(e)}", "raw": response if 'response' in locals() else 'N/A'}
    except Exception as e:
        return {"error": str(e)}


def _format_steps(steps):
    """Formate les steps pour le prompt."""
    if not steps:
        return "Aucune étape disponible"

    formatted = ""
    for i, step in enumerate(steps, 1):
        formatted += f"  {i}. {step}\n"
    return formatted


def _build_prompt(error_data, code_context, root_cause=None):
    """Construit le prompt pour Mistral."""

    # Type de leak en texte
    type_labels = {
        1: "Type 1 : La mémoire n'a jamais été libérée",
        2: "Type 2 : Le pointeur a été perdu avant de libérer la mémoire",
        3: "Type 3 : Le conteneur a été libéré avant son contenu"
    }

    # Infos root cause
    if root_cause:
        root_cause_section = f"""
====================================================
ROOT CAUSE (identifiée par analyse statique)
====================================================

{type_labels.get(root_cause['type'], 'Type inconnu')}

Fichier   : {root_cause.get('file', 'unknown')}
Fonction  : {root_cause['function']}()
Ligne     : {root_cause['line'].strip()}

Chemin de la mémoire :
{_format_steps(root_cause.get('steps', []))}
"""
    else:
        root_cause_section = """
====================================================
ROOT CAUSE
====================================================

Non identifiée (analyse manuelle requise)
"""

    prompt = f"""Tu es un expert en C et en gestion mémoire. Tu dois expliquer un memory leak de façon pédagogique.

====================================================
RAPPORT VALGRIND
====================================================

{error_data.get('bytes', '?')} bytes in {error_data.get('blocks', '?')} blocks are {error_data.get('type', 'definitely lost')}
Fonction d'allocation : {error_data.get('function', 'unknown')}()
Fichier : {error_data.get('file', 'unknown')}
Ligne : {error_data.get('line', '?')}

====================================================
CODE SOURCE
====================================================

{code_context}
{root_cause_section}
====================================================
TA MISSION
====================================================

1. Explique le diagnostic en 2-3 phrases claires
2. Fournis un raisonnement pédagogique étape par étape (basé sur le chemin mémoire ci-dessus)
3. Identifie les lignes de code importantes (contributing_codes)
4. Propose une solution avec le code correctif

====================================================
FORMAT JSON (uniquement, aucun texte autour)
====================================================

{{
  "type_leak": {root_cause['type'] if root_cause else 1},
  "diagnostic": "<explication claire du problème en 2-3 phrases>",
  "raisonnement": [
    "<étape : explication pédagogique>",
    "<étape : que devient la mémoire>",
    "<étape : pourquoi c'est un problème>",
    "<ajoute autant d'étapes que nécessaire>"
  ],
  "cause_reelle": {{
    "file": "{root_cause.get('file', 'unknown') if root_cause else 'unknown'}",
    "function": "{root_cause['function'] if root_cause else 'unknown'}",
    "owner": "<variable qui aurait dû libérer la mémoire>",
    "root_cause_code": "{root_cause['line'].strip() if root_cause else ''}",
    "root_cause_comment": "<pourquoi cette ligne cause le leak>",
    "contributing_codes": [
      {{"code": "<ligne importante>", "comment": "<son rôle dans le leak>"}},
      {{"code": "<autre ligne>", "comment": "<son rôle>"}}
    ],
    "context_before_code": "<ligne juste avant la root cause ou vide>",
    "context_after_code": "<ligne juste après la root cause ou vide>"
  }},
  "resolution_principe": "Dans <fonction>(), <action à faire> avant/après <ligne existante du code>",
  "resolution_code": "<code C exact à insérer>",
  "explications": "<explication pédagogique de pourquoi cette solution fonctionne> + <règle de bonne pratique>"
}}

RÈGLES IMPORTANTES :
- Utilise un français simple et pédagogique
- Le raisonnement doit guider l'utilisateur pas à pas
- Dans "raisonnement" : pas de numérotation, maximum 15 mots par étape
- Ne copie pas les steps bruts, reformule-les de façon compréhensible
- contributing_codes : uniquement les lignes AVANT root_cause_code
- root_cause_comment : maximum 10 mots
- resolution_principe : mentionner la fonction, l'action, et la ligne de référence
- JSON uniquement, aucun texte autour
"""

    return prompt


def _call_mistral_api(prompt):
    """Effectue l'appel à l'API Mistral."""
    try:
        response = client.chat.complete(
            model="mistral-small-latest",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ]
        )
        return response.choices[0].message.content

    except Exception as e:
        raise Exception(f"Erreur lors de l'appel API Mistral : {str(e)}")


def main():
    """Fonction de test standalone."""
    print("Test du module Mistral API...")
    print("Utilisez vex.py pour tester l'intégration complète.")


if __name__ == "__main__":
    main()

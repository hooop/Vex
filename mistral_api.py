"""
Mistral API Module for Vex

Sends memory leak analysis requests to Mistral AI and returns pedagogical explanations.
"""

import os
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


import json

def _clean_json_response(response):
    """Nettoie la réponse pour extraire le JSON pur."""

    response = response.strip()
    
    # Retire les backticks markdown si présents
    if response.startswith("```"):
        # Retire la première ligne (```json ou ```)
        lines = response.split('\n')
        lines = lines[1:]  # Skip première ligne
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Skip dernière ligne
        response = '\n'.join(lines)
    
    return response.strip()

def analyze_memory_leak(error_data, extracted_code_formatted):
    """
    Analyse un memory leak avec Mistral AI.
    Returns:
        dict: Analyse structurée ou dict avec 'error' en cas de problème
    """
    try:
        prompt = _build_prompt(error_data, extracted_code_formatted)
        response = _call_mistral_api(prompt)
        
        # Nettoie la réponse
        cleaned = _clean_json_response(response)
        
        # Parse le JSON
        analysis = json.loads(cleaned)
        
        # Validation basique
        required_keys = ["type_leak", "diagnostic", "resolution_principe", 
                        "resolution_code", "explications"]
        
        for key in required_keys:
            if key not in analysis:
                raise ValueError(f"Clé manquante : {key}")
        
        if analysis["type_leak"] not in [1, 2, 3]:
            raise ValueError(f"type_leak invalide : {analysis['type_leak']}")
        
        # cause_reelle TOUJOURS obligatoire maintenant
        if not analysis.get("cause_reelle") or not analysis["cause_reelle"].get("root_cause_code"):
            raise ValueError("cause_reelle manquante")
        
        # Validation file/function pour Type 2/3
        if analysis["type_leak"] in [2, 3]:
            cause = analysis.get("cause_reelle", {})
            if not cause.get("file") or not cause.get("function"):
                raise ValueError("cause_reelle incomplète (manque file/function)")
        
        # Validation owner pour Type 3
        if analysis["type_leak"] == 3:
            cause = analysis.get("cause_reelle", {})
            owner = cause.get("owner", "")
            # resolution_code = analysis.get("resolution_code", "")
            
            if not owner:
                raise ValueError("Type 3 : owner manquant dans cause_reelle")
            
            # if f"free({owner})" not in resolution_code:
            #     raise ValueError(f"Type 3 : resolution_code doit contenir free({owner})")
        
        return analysis
          
    except json.JSONDecodeError as e:
        # print(f"DEBUG: JSONDecodeError - {e}")
        # print(f"DEBUG: response existe? {response if 'response' in locals() else 'NON'}")
        return {"error": f"JSON invalide : {str(e)}", "raw": response if 'response' in locals() else 'N/A'}
    except Exception as e:
        # print(f"DEBUG: Exception - {e}")
        return {"error": str(e)}


def _build_prompt(error_data, code_context):

    # DEBUG affichage call trace
    # print("="*60)
    # print("CODE_CONTEXT REÇU :")
    # print(code_context)
    # print("="*60)
    
    prompt = f"""Tu es un expert en C et en gestion mémoire. Tu analyses un memory leak détecté par Valgrind.

====================================================
DONNÉES VALGRIND
====================================================

RAPPORT :
- Taille : {error_data.get('bytes', error_data.get('size', 'unknown'))} bytes
- Fonction d'allocation : {error_data.get('function', 'unknown')}()
- Fichier : {error_data.get('file', 'unknown')}
- Ligne : {error_data.get('line', '?')}

CALL STACK :
{code_context}

====================================================
SYSTÈME D'ANALYSE PAR LABELS
====================================================

Tu traces la RESPONSABILITÉ de libération, pas juste les variables.

LABELS :
- OWNER : variable simple qui reçoit malloc, responsable de free
- EMBEDDED : mémoire stockée dans un conteneur (via -> ou [])
- TRANSFERRED : responsabilité transférée via return
- FREED : mémoire libérée
- LEAK : état final non libéré

DÉTECTION SYNTAXIQUE :
- ptr = malloc(...) → ptr est OWNER
- x->field = malloc(...) → mémoire EMBEDDED dans x
- x[i] = malloc(...) → mémoire EMBEDDED dans x
- return ptr → ptr devient TRANSFERRED
- free(ptr) → ptr devient FREED

====================================================
PROCÉDURE D'ANALYSE
====================================================

ÉTAPE 1 — IDENTIFIER L'ALLOCATION (CRITIQUE)

La call stack Valgrind te donne des numéros de ligne PRÉCIS.
Pour chaque fonction de la call stack :
1. Lis le numéro de ligne indiqué
2. Trouve cette ligne EXACTE dans le code fourni
3. Lis ce que cette ligne contient

Exemple : si Valgrind dit "ma_fonction (mon_fichier.c:77)", va à la ligne 77 dans le code et lis-la. Cette ligne te dit QUEL appel précis parmi plusieurs.

Une fois la ligne trouvée :
- Quelle variable ou champ reçoit le malloc ?
- Label initial : OWNER ou EMBEDDED ?

ÉTAPE 2 — REMONTER LA CALL STACK

Pour chaque return, suis où le pointeur est stocké dans la fonction appelante.
Construis le chemin complet jusqu'au propriétaire final.

ÉTAPE 3 — CHERCHER LE FREE

Cherche un free() sur le propriétaire final ou un alias équivalent.

Si le free passe par une fonction intermédiaire :
1. Analyse ce que fait cette fonction
2. Vérifie qu'elle libère AUSSI les champs EMBEDDED
3. Si elle ne libère que le conteneur, le contenu EMBEDDED devient LEAK

- Free complet trouvé → FREED
- Free incomplet ou absent → continue à l'étape 4

ÉTAPE 4 — VÉRIFIER LES CONTENEURS

Si la mémoire est EMBEDDED : son conteneur est-il FREED avant elle ?
- Oui → la mémoire devient LEAK (Type 3)
- Non → la mémoire est LEAK (Type 1)

ÉTAPE 5 — CONCLURE

Type 1 : Aucun free() pour cette allocation → root cause = où insérer le free
Type 2 : Pointeur réassigné avant free → root cause = ligne de réassignation
Type 3 : Conteneur FREED avant contenu → root cause = ligne du free du conteneur

====================================================
FORMAT JSON (UNIQUEMENT, AUCUN TEXTE AVANT/APRÈS)
====================================================

{{
  "raisonnement": [
  "<Phrase courte décrivant cette étape d'analyse>",
  "<Utilise un français simple et concret>",
  "<Évite les termes techniques OWNER, TRANSFERRED, EMBEDDED, FREED, LEAK>",
  "<Remplace-les par : 'est responsable de', 'est retourné à', 'caché dans', 'libéré', 'devenu inaccessible'>",
  "<Continue sans limite de nombre>"
  ],
  "type_leak": <1, 2 ou 3>,
  "diagnostic": "Dans <fonction>(), <explication factuelle en 2 phrases max>",
  "cause_reelle": {{
    "file": "<fichier.c>",
    "function": "<fonction où se trouve la root cause>",
    "owner": "<propriétaire final de la mémoire - OBLIGATOIRE si type 3>",
    "root_cause_code": "<copie EXACTE de la ligne, SANS numéro>",
    "root_cause_comment": "<pourquoi cette ligne cause le leak>",
    "contributing_codes": [
      {{"code": "<ligne AVANT root_cause, SANS numéro>", "comment": "<son rôle>"}}
    ],
    "context_before_code": "<ligne juste avant ou vide>",
    "context_after_code": "<ligne juste après ou vide>"
  }},
  "resolution_principe": "Dans <fonction>(), <action à faire> avant/après <repère dans le code>",
  "resolution_code": "<code C exact à insérer>",
  "explications": "<pourquoi cette solution corrige le leak>"
}}

====================================================
RÈGLES
====================================================

- Remplis "raisonnement" AVANT de conclure, étape par étape
- Dans l'étape 1, cite la ligne EXACTE que tu lis dans le code
- Suis les étapes dans l'ordre
- Copie les lignes EXACTEMENT, sans numéro de ligne
- contributing_codes : uniquement des lignes AVANT root_cause_code
- owner : obligatoire pour Type 3
- Si free() n'apparaît pas dans le code, la mémoire N'EST PAS libérée
- Le propriétaire identifié dans "raisonnement" doit correspondre à ce qui est libéré dans "resolution_code"
- N'invente AUCUNE ligne de code qui n'existe pas

TRADUCTION POUR LE RAISONNEMENT :
- Utilise un français simple et pédagogique dans le champ "raisonnement"
- Remplace les labels techniques par des phrases concrètes :
  * OWNER → "est responsable de libérer cette mémoire"
  * TRANSFERRED → "est retourné à" / "passe à"
  * EMBEDDED → "caché à l'intérieur de" / "stocké dans la structure"
  * FREED → "libéré" / "détruit"
  * LEAK → "devenue inaccessible sans être libérée"
- Phrases courtes et progressives
- Raconte l'histoire de la mémoire étape par étape

- JSON uniquement, aucun texte autour
"""



    return prompt


def _call_mistral_api(prompt):
    """
    Effectue l'appel à l'API Mistral.

    Args:
        prompt: Le prompt construit

    Returns:
        str: Réponse de Mistral

    Raises:
        Exception: En cas d'erreur API
    """
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

        # Extraction du texte de la réponse
        return response.choices[0].message.content

    except Exception as e:
        raise Exception(f"Erreur lors de l'appel API Mistral : {str(e)}")


def main():
    """
    Fonction de test standalone.
    """
    # Exemple de test
    test_error = {
        'type': 'definitely lost',
        'size': '40 bytes',
        'address': '0x4a4f040',
        'function': 'main',
        'file': 'test.c',
        'line': 10,
        'backtrace': []
    }

    test_code = """=== CALL STACK WITH SOURCE CODE ===

--- Function 1: main ---
File: test.c
Line: 10

int main(void)
{
    char *str;

    str = malloc(40);
    printf("Hello\\n");
    return (0);
}
"""

    print("🔍 Test du module Mistral API...\n")
    result = analyze_memory_leak(test_error, test_code)
    print(result)


if __name__ == "__main__":
    main()

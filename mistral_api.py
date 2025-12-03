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


def _validate_contributing_lines(analysis):
    """
    Filtre les contributing_lines pour ne garder que celles AVANT root_cause
    ET qui ne sont pas la root_cause elle-même.
    """
    cause = analysis.get("cause_reelle")
    if not cause:
        return
    
    root_line = cause.get("line")
    root_code = cause.get("root_cause_line", "").strip()
    contributing = cause.get("contributing_lines", [])
    
    if not root_line or not contributing:
        return
    
    cleaned = []
    for contrib in contributing:
        contrib_line = contrib.get("line", 999999)
        contrib_code = contrib.get("code", "").strip()
        
        # Garde si : ligne < root ET code différent de root_cause
        if contrib_line < root_line and contrib_code != root_code:
            cleaned.append(contrib)
    
    cause["contributing_lines"] = cleaned

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
        if not analysis.get("cause_reelle") or not analysis["cause_reelle"].get("root_cause_line"):
            raise ValueError("cause_reelle manquante")
        
        # Validation file/line/function pour Type 2/3
        if analysis["type_leak"] in [2, 3]:
            cause = analysis.get("cause_reelle", {})
            if not cause.get("file") or not cause.get("line") or not cause.get("function"):
                raise ValueError("cause_reelle incomplète (manque file/line/function)")
        
        # Validation de l'ordre chronologique
        _validate_contributing_lines(analysis)

        return analysis
        
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSONDecodeError - {e}")
        print(f"DEBUG: response existe? {response if 'response' in locals() else 'NON'}")
        return {"error": f"JSON invalide : {str(e)}", "raw": response if 'response' in locals() else 'N/A'}
    except Exception as e:
        print(f"DEBUG: Exception - {e}")
        return {"error": str(e)}


def _build_prompt(error_data, code_context):

    print("="*60)
    print("CODE_CONTEXT REÇU :")
    print(code_context)
    print("="*60)
    
    prompt = f"""Tu es un expert en C et en gestion mémoire. Analyse le LEAK EXACT fourni.

====================================================
SECTION 1 — INPUT
====================================================

RAPPORT VALGRIND :
- Type (selon Valgrind) : {error_data.get('type', 'unknown')}
- Taille : {error_data.get('size', 'unknown')}
- Allocation : {error_data.get('function', 'unknown')}() [{error_data.get('file', 'unknown')}:{error_data.get('line', '?')}]

CODE SOURCE :
{code_context}

====================================================
SECTION 2 — ORDRE CHRONOLOGIQUE STRICT
====================================================

RÈGLE ABSOLUE : Tout code extrait doit respecter l'ordre du fichier source.



Tu dois COPIER les lignes EXACTEMENT comme elles apparaissent,
dans l'ordre CROISSANT de leurs numéros de ligne.

====================================================
SECTION 3 — RÈGLES D'ANALYSE STRICTES
====================================================

1. INTERDIT D'INVENTER
   - Aucune fonction, aucune variable, aucune structure inventée.
   - Si tu ne vois pas free() → la mémoire n'est PAS libérée.
   - Ne déduis JAMAIS une libération implicite ou supposée ailleurs.
   - N'interpréte jamais.

2. ANALYSE FACTUELLE UNIQUEMENT
   - Identifier l'allocation.
   - Identifier où elle devrait être libérée.
   - Identifier pourquoi elle ne l'est pas.

3. CLASSIFICATION DES TYPES DE LEAK (choisir uniquement 1, 2 ou 3) :
    - Type 1 : malloc() visible, aucun free() correspondant.
      
      → Si malloc() est dans une fonction qui RETOURNE le pointeur,
         la root_cause est dans la fonction APPELANTE qui perd ce pointeur.
      → Sinon, root_cause = ligne du malloc() lui-même.
    
    - Type 2 : pointeur écrasé/réassigné avant free.
    
    - Type 3 : pointeur devient inaccessible (ex: lien coupé, variable hors scope).
      ⚠️ POUR LE TYPE 3 AVEC POINTEURS MULTIPLES :
         Si plusieurs variables pointent vers la même mémoire allouée,
         le leak devient effectif quand le DERNIER pointeur valide est perdu/écrasé.
         → Identifie la ligne où PLUS AUCUN pointeur ne permet d'accéder à la mémoire.
         → Pas la première assignation à NULL, mais la DERNIÈRE.

    → Tu renvoies SEULEMENT le numéro dans "type_leak".
    → Je génère moi-même la phrase générique côté application.

4. STRUCTURE cause_reelle
    
    cause_reelle :
        * file : fichier contenant root_cause_line
        * line : numéro exact de root_cause_line
        * function : fonction contenant root_cause_line
        * root_cause_line : ligne EXACTE copiée du code
        * root_cause_comment : pourquoi cette ligne déclenche la fuite
      
        * contributing_lines : [
            {{"line": 80, "code": "ligne exacte", "comment": "..."}},
            {{"line": 82, "code": "ligne exacte", "comment": "..."}}
        ]
        
        RÈGLES ABSOLUES pour contributing_lines :
        
        1. INTERDICTION STRICTE : root_cause_line ne doit JAMAIS apparaître ici
        2. UNIQUEMENT des lignes dont le numéro est INFÉRIEUR à root_cause.line
        3. Ordre CROISSANT obligatoire (ex: ligne 102, puis 104, puis 105)
        4. Type 1 : TOUJOURS vide []
        5. Vérifie que chaque ligne de contributing_lines ≠ root_cause_line
        6. Type 3 avec pointeurs multiples : inclure TOUTES les assignations à NULL
          SAUF la dernière (qui est la root_cause)
      
      * context_before : ligne physiquement juste avant root_cause
        → Si root_cause = ligne 106, alors context_before = ligne 105
        → SAUF si ligne 105 déjà dans contributing_lines → alors prendre ligne précédente disponible ou laisser vide
        → COPIER la ligne EXACTEMENT
        
      * context_after : ligne physiquement juste après root_cause
        → Si root_cause = ligne 106, alors context_after = ligne 107
        → UNE SEULE ligne (si plusieurs instructions collées, les séparer ou prendre la première)
        → COPIER la ligne EXACTEMENT

5. DIAGNOSTIC
    - diagnostic : 2 phrases max, factuelles et pédagogique, commençant TOUJOURS par :
       "Dans {{nom_fonction}}() ..."

6. RÉSOLUTION
    - resolution_principe : UNE seule solution précise, pas plusieurs. Doit indiquer clairement où l'insérer ("avant X", "dans la fonction Y").
    - resolution_code : code C correspondant EXACTEMENT à resolution_principe.
    - Les deux doivent être cohérents.

    RÈGLES DE SÉCURITÉ MÉMOIRE :

    - JAMAIS accéder à un pointeur après free()
    - JAMAIS déréférencer (ptr->...) un pointeur libéré
    - Si tu proposes de libérer dans un ordre, vérifie que chaque free()
    n'utilise QUE des pointeurs encore valides
    - Privilégie toujours la solution la plus simple et sûre

    PRINCIPE DE SOLUTION NATURELLE (Type 2 uniquement) :
    
    Quand un pointeur est réassigné avant free (Type 2), privilégie TOUJOURS :
    → free(ptr) AVANT la réassignation
    → Puis faire le nouveau malloc
    
    Évite les variables temporaires sauf si le code montre explicitement 
    qu'on a BESOIN de conserver les deux allocations simultanément.
    
    Exemple de pattern à éviter :
    ✗ char *temp = ptr; ptr = malloc(...); free(temp);
    
    Exemple de pattern à privilégier :
    ✓ free(ptr); ptr = malloc(...);

====================================================
SECTION 4 — FORMAT SORTIE : JSON EXCLUSIF
====================================================

Réponds STRICTEMENT avec ce JSON :

{{
  "type_leak": 1,
  "diagnostic": "Dans nom_fonction(), explication factuelle et pédagogique (2 phrases max)",
  "cause_reelle": {{
    "file": "nom_fichier.c",
    "line": 106,
    "function": "nom_fonction",
    "root_cause_line": "ligne exacte copiée du code",
    "root_cause_comment": "pourquoi cette ligne est la root cause, quelques mots pas de phrase longue",
    "contributing_lines": [
        {{"line": 80, "code": "ligne exacte AVANT root_cause", "comment": "explication"}},
        {{"line": 82, "code": "ligne exacte AVANT root_cause", "comment": "explication"}}
    ],
    "context_before": "ligne juste avant root_cause (ou vide)",
    "context_after": "ligne juste après root_cause"
  }},
  "resolution_principe": "Une seule solution précise, avec emplacement exact (pas de numéro de ligne)",
  "resolution_code": "Code C exact et cohérent",
  "explications": "Apport pédagogique de la solution : ce qu'il faut comprendre au-delà du fix lui-même (1-2 phrases)"
}}

====================================================
SECTION 5 — RÈGLES FINALES
====================================================
- AUCUN texte en dehors du JSON.
- Pas d'interprétation. Pas de restructuration du code.
- Ignore tout ce qui n'est pas lié EXACTEMENT à ce leak.
- RESPECTE L'ORDRE CHRONOLOGIQUE DU FICHIER SOURCE.
- Pour Type 3 avec pointeurs multiples : root_cause = DERNIÈRE ligne qui perd l'accès.
"""

    # Affichage du prompt :
    # print("="*60)
    # print(prompt)
    # print("="*60)

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

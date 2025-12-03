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

        return analysis
          
    except json.JSONDecodeError as e:
        print(f"DEBUG: JSONDecodeError - {e}")
        print(f"DEBUG: response existe? {response if 'response' in locals() else 'NON'}")
        return {"error": f"JSON invalide : {str(e)}", "raw": response if 'response' in locals() else 'N/A'}
    except Exception as e:
        print(f"DEBUG: Exception - {e}")
        return {"error": str(e)}


def _build_prompt(error_data, code_context):

    # DEBUG affichage call trace
    # print("="*60)
    # print("CODE_CONTEXT REÇU :")
    # print(code_context)
    # print("="*60)
    
    prompt = f"""Tu es un expert en C et en gestion mémoire. Analyse le LEAK EXACT fourni.

====================================================
SECTION 1 – INPUT
====================================================

RAPPORT VALGRIND :
- Type (selon Valgrind) : {error_data.get('type', 'unknown')}
- Taille : {error_data.get('size', 'unknown')}
- Allocation : {error_data.get('function', 'unknown')}() [{error_data.get('file', 'unknown')}:{error_data.get('line', '?')}]

CODE SOURCE :
{code_context}

====================================================
SECTION 2 – ORDRE CHRONOLOGIQUE STRICT
====================================================

RÈGLE ABSOLUE : Tout code extrait doit respecter l'ordre du fichier source.

Tu dois COPIER les lignes EXACTEMENT comme elles apparaissent,
dans l'ordre CROISSANT de leurs numéros de ligne.

====================================================
SECTION 3 – RÈGLES D'ANALYSE STRICTES
====================================================

1. INTERDIT D'INVENTER
   - Aucune fonction, aucune variable, aucune structure inventée.
   - Si tu ne vois pas free() → la mémoire n'est PAS libérée.
   - Ne déduis JAMAIS une libération implicite ou supposée ailleurs.
   - N'interprète jamais.

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

        ⚠️ ATTENTION VALGRIND vs ROOT CAUSE :
        Valgrind indique toujours la ligne du malloc() qui leak.
        Mais pour Type 2, la root_cause est la ligne OÙ LE POINTEUR EST ÉCRASÉ.
        
        Dans le code fourni :
        - Valgrind pointe sur l'allocation initiale
        - Root cause : cherche APRÈS cette ligne où le pointeur est réassigné/écrasé
  
        → Tu dois TROUVER dans le code la ligne de réassignation, pas répéter ce que dit Valgrind.
    
    - Type 3 : pointeur devient inaccessible (ex: lien coupé, variable hors scope).
      
        ⚠️ POUR LE TYPE 3 AVEC POINTEURS MULTIPLES :
            Si plusieurs variables pointent vers la même mémoire allouée,
            le leak devient effectif quand le DERNIER pointeur valide est perdu/écrasé.
            → Identifie la ligne où PLUS AUCUN pointeur ne permet d'accéder à la mémoire.
            → Pas la première assignation à NULL, mais la DERNIÈRE.
            → PUIS trace TOUS les blocs mémoire perdus à partir de ce point.
            → La resolution_code doit libérer TOUS ces blocs, pas seulement le premier.
            → Exemple : si ptr->a->b->c existe, libère les 3 structures chaînées.
            
        ⚠️ CAS SPÉCIAL - CHAÎNE CASSÉE (ptr->next = NULL ou ptr->next = autre) :
            Si la root_cause coupe un lien dans une liste chaînée :
            
            ÉTAPE 1 - Identifier ce qui est perdu :
            → Quand tu fais "element->next = NULL" ou "element->next = autre_chose"
            → TOUT ce qui était accessible via l'ancien "element->next" devient perdu
            → Si l'ancienne chaîne était : element -> X -> Y -> Z
            → Alors X, Y et Z sont perdus
            
            ÉTAPE 2 - Solution :
            → Sauvegarder l'ancien "element->next" dans une variable temporaire AVANT la coupure
            → Parcourir et libérer TOUS les éléments de cette sous-chaîne avec une boucle
            → PUIS faire la coupure du lien
            
            Structure de code type :
            Type *temp = element->next;
            while (temp) {{
                Type *suivant = temp->next;
                free(temp->membre_alloue);
                free(temp);
                temp = suivant;
            }}
            element->next = NULL;


    → Tu renvoies SEULEMENT le numéro dans "type_leak".
    → Je génère moi-même la phrase générique côté application.

4. STRUCTURE cause_reelle
    
    cause_reelle :
        * file : fichier contenant root_cause
        * function : fonction contenant root_cause
        * root_cause_code : ligne EXACTE copiée du code (SANS le numéro de ligne)
        * root_cause_comment : pourquoi cette ligne déclenche la fuite
        
        * contributing_codes : [
            {{"code": "ligne exacte AVANT root_cause (sans numéro)", "comment": "explication"}},
            {{"code": "ligne exacte AVANT root_cause (sans numéro)", "comment": "explication"}}
        ]
        
        RÈGLES ABSOLUES pour contributing_codes :
        
        1. INTERDICTION STRICTE : root_cause_code ne doit JAMAIS apparaître ici
        2. UNIQUEMENT des lignes qui apparaissent PHYSIQUEMENT AVANT root_cause dans le fichier
        3. Les lignes doivent être PERTINENTES : allocation initiale, manipulation du pointeur
        4. JAMAIS de lignes APRÈS root_cause
        5. Type 1 : TOUJOURS vide []
        6. Type 3 avec pointeurs multiples : inclure TOUTES les assignations à NULL
           SAUF la dernière (qui est la root_cause)
        
        EXEMPLE CORRECT (Type 2) :
        Si le code est :
        42: node = create_node();
        43: process_data(node);
        44: node = create_node();  ← root_cause (réassignation)
        45: finalize(node);
        
        Alors :
        contributing_codes: [{{"code": "node = create_node();", "comment": "allocation initiale perdue"}}]
        root_cause_code: "node = create_node();"
        context_after_code: "finalize(node);"
        
        ✗ INTERDIT : mettre "finalize(node);" dans contributing_codes (c'est APRÈS root_cause)
      
      * context_before_code : ligne physiquement juste avant root_cause (SANS le numéro de ligne)
        → La ligne qui précède immédiatement root_cause dans le code source
        → Ne doit PAS être identique à une ligne déjà dans contributing_codes
        → COPIER la ligne EXACTEMENT
        
      * context_after_code : ligne physiquement juste après root_cause (SANS le numéro de ligne)
        → La ligne qui suit immédiatement root_cause dans le code source
        → Ne doit PAS être identique à root_cause ou à contributing_codes
        → UNE SEULE ligne
        → COPIER la ligne EXACTEMENT

====================================================
SECTION 4 – RÈGLES DE GÉNÉRATION DU CODE DE RÉSOLUTION
====================================================

RÈGLES DE SÉCURITÉ MÉMOIRE :

- JAMAIS accéder à un pointeur après free()
- JAMAIS déréférencer (ptr->...) un pointeur libéré
- Si tu proposes de libérer dans un ordre, vérifie que chaque free()
  n'utilise QUE des pointeurs encore valides
- Privilégie toujours la solution la plus simple et sûre

RÈGLE DES ALLOCATIONS MULTIPLES :

Si une structure contient des membres alloués dynamiquement,
tu DOIS libérer dans cet ordre :
1. D'abord les membres alloués (ex: free(obj->buffer))
2. Puis la structure elle-même (ex: free(obj))

Vérifie dans le code fourni les allocations imbriquées.
Chaque malloc/strdup/calloc doit avoir son free correspondant.

ORDRE DE LIBÉRATION CRITIQUE :

Quand tu libères une chaîne de structures liées (A->B->C->D) :

1. PRIVILÉGIE une boucle while si possible (plus robuste et maintenable)
2. SINON libère du DERNIER au PREMIER (D, puis C, puis B, puis A)
3. SINON sauvegarde chaque pointeur dans une variable temporaire AVANT tout free()

✓ MEILLEUR (boucle) :
while (liste != NULL) {{
    Type *tmp = liste->next;
    free(liste->data);
    free(liste);
    liste = tmp;
}}

✓ CORRECT (ordre inverse) :
free(dernier->data);
free(dernier);
free(avant_dernier->data);
free(avant_dernier);

✗ INVALIDE :
free(premier);
free(premier->suivant);  // premier est déjà libéré !

TIMING DE LA SOLUTION (Type 2 et Type 3) :

Si la root_cause DÉTRUIT un accès (assignation NULL, réassignation, fin de scope),
ta solution doit s'exécuter AVANT cette destruction.

Dans resolution_principe, tu DOIS préciser explicitement :
- "Insérer ce code AVANT la ligne qui détruit l'accès"
- OU "Remplacer la ligne problématique par ce code"
- OU "Supprimer la ligne problématique et ajouter ce code à la place"

Ne propose JAMAIS de code qui suppose que des pointeurs détruits existent encore.

PRINCIPE DE SOLUTION NATURELLE (Type 2 uniquement) :

Quand un pointeur est réassigné avant free (Type 2), privilégie TOUJOURS :
→ free(ptr) AVANT la réassignation
→ Puis faire le nouveau malloc

Évite les variables temporaires sauf si le code montre explicitement 
qu'on a BESOIN de conserver les deux allocations simultanément.

✓ CORRECT :
free(ptr);
ptr = malloc(...);

✗ À ÉVITER :
char *temp = ptr;
ptr = malloc(...);
free(temp);

====================================================
SECTION 5 – DIAGNOSTIC
====================================================

- diagnostic : 2 phrases max, factuelles et pédagogique, commençant TOUJOURS par :
   "Dans {{nom_fonction}}() ..."
- INTERDICTION : Les 2 phrases ne doivent PAS dire la même chose reformulée
- Première phrase : QUOI (le problème factuel)
- Deuxième phrase : POURQUOI/CONSÉQUENCE (l'impact pédagogique)

====================================================
SECTION 6 — RÉSOLUTION
====================================================

RÈGLE FONDAMENTALE DE PROPRIÉTÉ MÉMOIRE :

En C professionnel, le pointeur qui ALLOUE est celui qui doit LIBÉRER.
- Si pointeur_A reçoit le malloc(), alors c'est pointeur_A qui fait le free()
- Les autres pointeurs vers cette mémoire sont des alias/observateurs
- On libère via le propriétaire original AVANT toute manipulation

SOLUTION TYPE 3 AVEC POINTEURS MULTIPLES :

Quand plusieurs pointeurs partagent la même mémoire allouée :
1. Identifie le propriétaire (celui qui a directement reçu le retour de malloc)
2. Libère via ce propriétaire AVANT qu'il ne soit modifié/invalidé
3. TIMING CRITIQUE : free() doit s'exécuter AVANT que le propriétaire change
    → Si le propriétaire est modifié/invalidé à plusieurs endroits, 
        le free() doit être placé AVANT LA PREMIÈRE modification.
    
    Exemple : 
    owner = malloc(64);
    alias = owner;
    
    free(owner);      // ← ICI, avant toute modification
    owner = NULL;     // première modification
    alias = NULL;     // deuxième modification

Exemple de formulation attendue :
- "Libérer via [propriétaire] AVANT sa modification"
- "Insérer free([propriétaire]) avant la ligne qui invalide ce pointeur"

⚠️ COHÉRENCE OBLIGATOIRE :
Si tu proposes free(pointeur_X), vérifie que pointeur_X est encore VALIDE
au moment où tu proposes de l'utiliser.
Si pointeur_X est modifié ligne N, alors free(pointeur_X) doit être AVANT ligne N.

- resolution_principe : UNE seule solution précise, pas plusieurs. Doit indiquer clairement où l'insérer ("avant X", "dans la fonction Y").
- resolution_code : code C correspondant EXACTEMENT à resolution_principe.
- Les deux doivent être cohérents.

PRÉCISION DU PLACEMENT :

Ton resolution_principe DOIT être explicite sur l'emplacement :
❌ VAGUE : "Libérer via ptr1 AVANT sa modification"
✅ PRÉCIS : "Insérer free(ptr1); AVANT la ligne 58 (avant ptr1 = NULL;)"

Format attendu : "Insérer [code] AVANT la ligne qui [action]"

====================================================
SECTION 7 – FORMAT SORTIE : JSON EXCLUSIF
====================================================

IMPORTANT FORMATAGE :
- Dans tous les champs "code" du JSON, tu dois copier UNIQUEMENT le code source
- SANS le numéro de ligne devant (ex: "tmp = ft_strdup(str);" et PAS "42: tmp = ft_strdup(str);")
- Le numéro de ligne va dans le champ "line", pas dans "code"

IMPORTANT pour resolution_principe :
- [code_ligne_reference] = la ligne EXISTANTE du code source (celle avant laquelle insérer)
- PAS le code de la solution (qui est dans resolution_code)

Réponds STRICTEMENT avec ce JSON :

{{
  "type_leak": 1,
  "diagnostic": "Dans nom_fonction(), explication factuelle et pédagogique (2 phrases max)",
  "cause_reelle": {{
    "file": "nom_fichier.c",
    "function": "nom_fonction",
    "root_cause_code": "ligne exacte copiée du code (sans numéro)",
    "root_cause_comment": "pourquoi cette ligne est la root cause",
    "contributing_codes": [
        {{"code": "ligne exacte AVANT root_cause (sans numéro)", "comment": "explication"}},
        {{"code": "ligne exacte AVANT root_cause (sans numéro)", "comment": "explication"}}
    ],
    "context_before_code": "ligne juste avant root_cause (sans numéro, ou vide)",
    "context_after_code": "ligne juste après root_cause (sans numéro)"
  }},
  "resolution_principe": "Dans [nom_fonction] insérer le code ci-dessous avant la ligne [code_ligne_reference] qui [action_invalidante]",
  "resolution_code": "Code C exact",
  "explications": "Apport pédagogique (1-2 phrases)"
}}

====================================================
SECTION 8 – RÈGLES FINALES
====================================================
- AUCUN texte en dehors du JSON.
- Pas d'interprétation. Pas de restructuration du code.
- Ignore tout ce qui n'est pas lié EXACTEMENT à ce leak.
- RESPECTE L'ORDRE CHRONOLOGIQUE DU FICHIER SOURCE.
- Pour Type 3 avec pointeurs multiples : root_cause = DERNIÈRE ligne qui perd l'accès.
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

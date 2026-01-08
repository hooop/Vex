"""
memory_tracker.py

Memory tracking algorithm to find root cause of memory leaks.
Analyzes code execution flow and tracks memory ownership.
"""

from typing import Optional

from type_defs import TrackingEntry, RootCauseInfo, ProcessedFunction

# =============================================================================
# DATA STRUCTURES
# =============================================================================

# class TrackingEntry:
#     """Represents a tracked path to allocated memory."""

#     def __init__(self, target: str, segments: list[str], origin: Optional[str] = None):
#         self.target = target      # Full path to memory (e.g., "head->next->data")
#         self.segments = segments  # All prefixes (e.g., ["head", "head->next", "head->next->data"])
#         self.origin = origin      # If alias, the original path. Otherwise None


# class RootCause:
#     """Represents the identified root cause of a memory leak."""

#     def __init__(self, leak_type: int, line: str, function: str, file: str = "", steps: list[str] = None):
#         self.leak_type = leak_type  # 1, 2, or 3
#         self.line = line            # The responsible line of code
#         self.function = function    # Function where root cause is located
#         self.file = file            # Source file
#         self.steps = steps or []    # Memory path steps for explanation


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def build_segments(path: str) -> list[str]:
    """
    Decompose a path into all its prefixes.
    "head->next->data" → ["head", "head->next", "head->next->data"]
    "ptr" → ["ptr"]
    """
    if "->" not in path:
        return [path]

    segments = []
    parts = path.split("->")
    current_path = parts[0]
    segments.append(current_path)

    for i in range(1, len(parts)):
        current_path = current_path + "->" + parts[i]
        segments.append(current_path)

    return segments


def extract_root(path: str) -> str:
    """
    Extract the base variable from a path.
    "head->next->data" → "head"
    "ptr" → "ptr"
    """
    if "->" in path:
        return path.split("->")[0]
    return path

def extract_free_argument(line: str) -> str:
    """
    Extract the argument from a free() call.
    "free(second->next);" → "second->next"
    "    free(ptr);  " → "ptr"
    """
    start = line.index("free(") + 5
    end = line.index(")", start)
    return line[start:end].strip()


def extract_return_value(line: str) -> str:
    """
    Extract the returned value from a return statement.
    "return n;" → "n"
    "return (n);" → "n"  
    "return ptr->data;" → "ptr->data"
    """
    content = line.replace("return", "", 1).replace(";", "").strip()
    
    # Remove parentheses if present
    if content.startswith("(") and content.endswith(")"):
        content = content[1:-1].strip()
    
    return content


def extract_left_side(line: str) -> str:
    """
    Extract the left side of an assignment.
    "head->next = NULL;" → "head->next"
    "Node *second = head->next;" → "second"
    "char *str = malloc(10);" → "str"
    """
    left_part = line.split("=")[0].strip()

    # If it's a declaration (Type *var), extract just var
    if "*" in left_part:
        # Find the last * and take what's after
        last_star = left_part.rfind("*")
        return left_part[last_star + 1:].strip()

    return left_part


def extract_right_side(line: str) -> str:
    """
    Extract the right side of an assignment.
    "Node *second = head->next;" → "head->next"
    "head->next = NULL;" → "NULL"
    """
    right_part = line.split("=", 1)[1].replace(";", "").strip()
    return right_part


# =============================================================================
# OPERATION DETECTION
# =============================================================================

def is_malloc(line: str) -> bool:
    """Check if line contains a malloc call."""
    return "malloc(" in line


def is_return(line: str) -> bool:
    """Check if line is a return statement."""
    return line.strip().startswith("return ")


def is_free(line: str) -> bool:
    """Check if line contains a free call."""
    return "free(" in line


def is_null_assignment(line: str) -> bool:
    """Check if line assigns NULL/0/nullptr."""
    return "= NULL" in line or "= 0" in line or "= nullptr" in line


def is_alias(line: str, found_segment: str) -> bool:
    """
    Check if line creates an alias.
    True if:
    1. It's an assignment (contains "=")
    2. The found segment is on the RIGHT side of "="
    3. It's not NULL assignment
    """
    if "=" not in line:
        return False

    if is_null_assignment(line):
        return False

    right_side = extract_right_side(line)
    return found_segment in right_side


def is_reassignment(line: str, found_segment: str) -> bool:
    """
    Check if line reassigns a tracked segment.
    True if:
    1. It's an assignment (contains "=")
    2. The found segment is on the LEFT side of "="
    """
    if "=" not in line:
        return False

    left_side = line.split("=")[0]
    return found_segment in left_side

# =============================================================================
# SEGMENT MATCHING
# =============================================================================

def find_segment_in_line(line: str, tracking: dict[str, TrackingEntry]) -> tuple[bool, Optional[str], Optional[str], Optional[TrackingEntry], Optional[str]]:
    """
    Check if line manipulates any tracked segment.

    Returns: (found, root_key, found_segment, entry, operation_type)

    operation_type: "free", "return", "alias", "reassign", or None
    """

    # Collect all segments for lookup
    all_segments = {}
    for root_key, entry in tracking.items():
        for segment in entry["segments"]:
            all_segments[segment] = (root_key, entry)

    # CASE 1: free(...)
    if is_free(line):
        arg = extract_free_argument(line)
        if arg in all_segments:
            root_key, entry = all_segments[arg]
            return (True, root_key, arg, entry, "free")
        return (False, None, None, None, None)

    # CASE 2: return ...
    if is_return(line):
        ret_val = extract_return_value(line)
        if ret_val in all_segments:
            root_key, entry = all_segments[ret_val]
            return (True, root_key, ret_val, entry, "return")
        return (False, None, None, None, None)

    # CASE 3: assignment (x = y)
    if "=" in line:
        left = extract_left_side(line)
        right = extract_right_side(line)

        # Check for reassignment (left side is a tracked segment)
        if left in all_segments:
            root_key, entry = all_segments[left]
            return (True, root_key, left, entry, "reassign")

        # Check for alias (right side is a tracked segment)
        if right in all_segments and not is_null_assignment(line):
            root_key, entry = all_segments[right]
            return (True, root_key, right, entry, "alias")

    return (False, None, None, None, None)

# =============================================================================
# UPDATE RULES
# =============================================================================

def apply_init(line: str, tracking: dict[str, TrackingEntry]) -> None:
    """
    Create initial tracking structure from malloc line.
    "n->data = malloc(...);" → root="n", target="n->data"
    "ptr = malloc(...);" → root="ptr", target="ptr"
    """

    left_side = extract_left_side(line)
    root = extract_root(left_side)

    entry: TrackingEntry = {
    "target": left_side,
    "segments": build_segments(left_side),
    "origin": None
    }

    tracking[root] = entry


def apply_return(line: str, tracking: dict[str, TrackingEntry], caller_line: str) -> None:
    """
    Substitute local root with receiver in calling function.

    "return n;" with caller_line "head->next = create_node();"
    → n becomes head->next, n->data becomes head->next->data
    """

    returned_var = extract_return_value(line)
    receiver = extract_left_side(caller_line)
    new_root = extract_root(receiver)

    # Find entry of returned variable
    old_root = extract_root(returned_var)

    if old_root not in tracking:
        return

    old_entry = tracking[old_root]

    # Calculate suffix (what comes after returned variable in target)
    # If target = "n->data" and returned_var = "n", suffix = "->data"
    suffix = old_entry["target"].replace(returned_var, "", 1)

    # New target = receiver + suffix
    new_target = receiver + suffix

    new_entry: TrackingEntry = {
    "target": new_target,
    "segments": build_segments(new_target),
    "origin": None  # This becomes the new canonical form
    }

    # Remove old root, add new one
    del tracking[old_root]
    tracking[new_root] = new_entry


def apply_alias(line: str, aliased_segment: str, source_entry: TrackingEntry, tracking: dict[str, TrackingEntry]) -> None:
    """
    Add a new root that points to the same memory.

    "Node *second = head->next;" with aliased_segment = "head->next"
    and source_entry.target = "head->next->next->data"
    → suffix = "->next->data", new_target = "second->next->data"
    """

    new_name = extract_left_side(line)

    # Calculate suffix (what remains of target after aliased segment)
    suffix = source_entry["target"].replace(aliased_segment, "", 1)

    new_entry: TrackingEntry = {
    "target": new_name + suffix,
    "segments": build_segments(new_name + suffix),
    "origin": aliased_segment
    }

    tracking[new_name] = new_entry


def apply_reassignment(root_key: str, tracking: dict[str, TrackingEntry], line: str, function: str) -> Optional[RootCauseInfo]:
    """
    Remove the concerned root (path is broken).
    Aliases are NOT impacted (they have their own pointer).

    Returns RootCause if structure becomes empty (Type 2).
    """
    del tracking[root_key]

    if len(tracking) == 0:
        if len(tracking) == 0:
            return {
                "leak_type": 2,
                "line": line,
                "function": function,
                "file": "",
                "steps": []
            }

    return None


def apply_free(line: str, found_segment: str, entry: TrackingEntry, root_key: str, tracking: dict[str, TrackingEntry], function: str) -> Optional[RootCauseInfo]:
    """
    Handle free() call.

    If target STARTS WITH argument + "->" → freeing container before content (Type 3)
    Otherwise, remove this root.
    If structure becomes empty → Type 1 (never freed)
    """
    free_arg = extract_free_argument(line)

    # If target starts with free_arg + "->", we're freeing the container before its content
    if entry["target"].startswith(free_arg + "->"):
        return {
            "leak_type": 3,
            "line": line,
            "function": function,
            "file": "",
            "steps": []
        }

    # Otherwise, remove this root
    del tracking[root_key]

    if len(tracking) == 0:
        return {
            "leak_type": 1,
            "line": line,
            "function": function,
            "file": "",
            "steps": []
        }

    return None


# =============================================================================
# INTEGRATION HELPER
# =============================================================================

def convert_extracted_code(extracted_functions: list[dict]) -> list[dict]:
    """
    Convert code_extractor output to memory_tracker input format.

    Input format (from code_extractor):
        {'file': '...', 'function': '...', 'line': 23, 'code': "23: line1\n24: line2\n..."}

    Output format (for find_root_cause):
        {'function': '...', 'lines': ['line1', 'line2', ...], 'start_line': 23, 'file': '...'}
    """
    result = []

    for func in extracted_functions:
        lines = []

        # Parse the numbered code lines
        for code_line in func['code'].split('\n'):
            if not code_line.strip():
                continue

            # Remove line number prefix "23: " → "actual code"
            if ':' in code_line:
                # Find first colon and take everything after
                colon_pos = code_line.index(':')
                actual_code = code_line[colon_pos + 1:]
                lines.append(actual_code)

        result.append({
            'function': func['function'],
            'lines': lines,
            'start_line': func['line'],
            'file': func.get('file', 'unknown')
        })

    return result


# =============================================================================
# MAIN ALGORITHM
# =============================================================================

def find_root_cause(extracted_functions: list[ProcessedFunction]) -> Optional[RootCauseInfo]:
    """
    Main algorithm to find root cause of a memory leak.

    Args:
        extracted_functions: List of dicts with keys:
            - 'function': function name
            - 'lines': list of code lines (starting from Valgrind-indicated line)
            - 'start_line': line number of first line
            - 'file': source file path (optional)

    Returns:
        RootCause with type (1, 2, or 3), line, function, file, and steps
    """
    tracking: dict[str, TrackingEntry] = {}
    current_func_index = 0
    steps: list[str] = []  # Log des étapes pour Mistral

    # =========================================================================
    # STEP 1: INITIALIZATION (first line = malloc)
    # =========================================================================

    current_func = extracted_functions[0]
    first_line = current_func['lines'][0]
    current_file = current_func.get('file', 'unknown')

    apply_init(first_line, tracking)

     # Log l'allocation initiale
    root_key = list(tracking.keys())[0]
    target = tracking[root_key]["target"]
    steps.append(f"ALLOC: {target} in {current_func['function']}()")

    line_index = 1  # Start after malloc

    # =========================================================================
    # STEP 2: LINE BY LINE TRAVERSAL
    # =========================================================================

    while True:

        # Check if we finished current function
        if line_index >= len(current_func['lines']):

             # NOUVEAU : Si tracking non-vide, les variables locales sont perdues
            if tracking:
                steps.append(f"END: {current_func['function']}() exits with unreleased memory")
                
                return {
                    "leak_type": 2,
                    "line": "}",
                    "function": current_func['function'],
                    "file": current_file,
                    "steps": steps
                }
    
            # Move to next function if available
            current_func_index += 1

            if current_func_index >= len(extracted_functions):
                # End of code, structure not empty → Type 1

                return {
                    "leak_type": 1,
                    "line": "end of program",
                    "function": current_func['function'],
                    "file": current_file,
                    "steps": steps
                }

            current_func = extracted_functions[current_func_index]
            current_file = current_func.get('file', current_file)
            line_index = 1  # Skip first line (consumed by return)
            continue

        line = current_func['lines'][line_index]
        func_name = current_func['function']

        # =====================================================================
        # Check if line concerns us and get operation type
        # =====================================================================

        found, root_key, found_segment, entry, operation = find_segment_in_line(line, tracking)

        if not found:
            line_index += 1
            continue

        # =====================================================================
        # Apply rule based on operation type
        # =====================================================================

        if operation == "return":
            # Get first line of next function (the call)
            next_func = extracted_functions[current_func_index + 1]
            caller_line = next_func['lines'][0]

            old_target = entry["target"]
            apply_return(line, tracking, caller_line)

            # Log the return
            new_root = list(tracking.keys())[0]
            new_target = tracking[new_root]["target"]
            steps.append(f"RETURN: {old_target} -> {new_target} in {next_func['function']}()")

            # Move to next function, after the call line
            current_func_index += 1
            current_func = next_func
            current_file = current_func.get('file', current_file)
            line_index = 1  # Call line consumed by return
            continue

        if operation == "free":
            steps.append(f"FREE: {found_segment} in {func_name}()")

            root_cause = apply_free(line, found_segment, entry, root_key, tracking, func_name)

            if root_cause is not None:
                root_cause["file"] = current_file
                root_cause["steps"] = steps
                
                return root_cause

            line_index += 1
            continue

        if operation == "alias":
            new_name = extract_left_side(line)
            steps.append(f"ALIAS: {new_name} = {found_segment} in {func_name}()")

            apply_alias(line, found_segment, entry, tracking)

            line_index += 1
            continue

        if operation == "reassign":
            steps.append(f"REASSIGN: {found_segment} in {func_name}()")

            root_cause = apply_reassignment(root_key, tracking, line, func_name)

            if root_cause is not None:
                root_cause["file"] = current_file
                root_cause["steps"] = steps
                return root_cause

            line_index += 1
            continue

        # Unknown operation, skip
        line_index += 1

    return None

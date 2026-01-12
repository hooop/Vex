"""
memory_tracker.py

Memory tracking algorithm to find root cause of memory leaks.
Analyzes code execution flow and tracks memory ownership.
"""

from typing import Optional

from type_defs import TrackingEntry, RootCauseInfo, ProcessedFunction, ExtractedFunction

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def build_segments(path: str) -> list[str]:
    """Decompose a path into all its prefixes.
    
    Args:
        path: Memory path to decompose (e.g., "head->next->data")
        
    Returns:
        List of all prefixes (e.g., ["head", "head->next", "head->next->data"])
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
    """Extract the base variable from a path.
    
    Args:
        path: Memory path (e.g., "head->next->data")
        
    Returns:
        Base variable name (e.g., "head")
    """

    if "->" in path:
        return path.split("->")[0]
    return path

def extract_free_argument(line: str) -> str:
    """Extract the argument from a free() call.
    
    Args:
        line: Code line containing free() (e.g., "free(second->next);")
        
    Returns:
        Freed variable name (e.g., "second->next")
    """

    start = line.index("free(") + 5
    end = line.index(")", start)
    return line[start:end].strip()


def extract_return_value(line: str) -> str:
    """Extract the returned value from a return statement.
    
    Args:
        line: Code line with return statement (e.g., "return n;", "return (n);")
        
    Returns:
        Returned variable or expression (e.g., "n", "ptr->data")
    """

    content = line.replace("return", "", 1).replace(";", "").strip()
    
    # Remove parentheses if present
    if content.startswith("(") and content.endswith(")"):
        content = content[1:-1].strip()
    
    return content


def extract_left_side(line: str) -> str:
    """Extract the left side of an assignment.
    
    Args:
        line: Code line with assignment (e.g., "Node *second = head->next;")
        
    Returns:
        Left-hand side variable name (e.g., "second", "head->next")
    """

    left_part = line.split("=")[0].strip()

    # If it's a declaration (Type *var), extract just var
    if "*" in left_part:
        # Find the last * and take what's after
        last_star = left_part.rfind("*")
        return left_part[last_star + 1:].strip()

    return left_part


def extract_right_side(line: str) -> str:
    """Extract the right side of an assignment.
    
    Args:
        line: Code line with assignment (e.g., "Node *second = head->next;")
        
    Returns:
        Right-hand side value (e.g., "head->next", "NULL")
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
    """Check if line creates an alias to tracked memory.
    
    Args:
        line: Code line to analyze
        found_segment: Memory segment being tracked
        
    Returns:
        True if line is an assignment with found_segment on right side (not NULL)
    """

    if "=" not in line:
        return False

    if is_null_assignment(line):
        return False

    right_side = extract_right_side(line)
    return found_segment in right_side


def is_reassignment(line: str, found_segment: str) -> bool:
    """Check if line reassigns a tracked segment.
    
    Args:
        line: Code line to analyze
        found_segment: Memory segment being tracked
        
    Returns:
        True if line is an assignment with found_segment on left side
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
    """Create initial tracking structure from malloc line.
    
    Args:
        line: Code line with malloc (e.g., "ptr = malloc(10);", "n->data = malloc(...);")
        tracking: Dictionary of tracked memory paths (modified in place)
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
    """Substitute local root with receiver in calling function.
    
    Args:
        line: Return statement in callee (e.g., "return n;")
        tracking: Dictionary of tracked memory paths (modified in place)
        caller_line: Assignment line in caller (e.g., "head->next = create_node();")
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
    """Add a new root that points to the same memory.
    
    Args:
        line: Assignment creating alias (e.g., "Node *second = head->next;")
        aliased_segment: Memory segment being aliased (e.g., "head->next")
        source_entry: Original tracking entry for this memory
        tracking: Dictionary of tracked memory paths (modified in place)
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
    """Remove the concerned root (path is broken by reassignment).
    
    Args:
        root_key: Key of the root being reassigned
        tracking: Dictionary of tracked memory paths (modified in place)
        line: Code line performing reassignment
        function: Function name where reassignment occurs
        
    Returns:
        RootCauseInfo if tracking becomes empty (Type 2 leak), None otherwise
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
    """Handle free() call and detect improper memory release.
    
    Args:
        line: Code line with free() call
        found_segment: Memory segment being freed
        entry: Tracking entry for this memory
        root_key: Key of the root being freed
        tracking: Dictionary of tracked memory paths (modified in place)
        function: Function name where free occurs
        
    Returns:
        RootCauseInfo for Type 3 (freeing container before content) or Type 1 (never freed), 
        None otherwise
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

def convert_extracted_code(extracted_functions: list[ExtractedFunction]) -> list[ProcessedFunction]:
    """Convert code_extractor output to memory_tracker input format.
    
    Args:
        extracted_functions: List of extracted functions with numbered code lines
        
    Returns:
        List of functions with parsed code lines ready for memory tracking
    """
    result = []

    for func in extracted_functions:
        lines = []
        valgrind_line = func['line']  # La ligne mentionnée par Valgrind

        # Parse the numbered code lines
        for code_line in func['code'].split('\n'):
            if not code_line.strip():
                continue

            # Remove line number prefix "23: " → "actual code"
            if ':' in code_line:
                # Extract line number
                colon_pos = code_line.index(':')
                line_num_str = code_line[:colon_pos].strip()
                
                # Skip lines before Valgrind line
                if line_num_str.isdigit():
                    line_num = int(line_num_str)
                    if line_num < valgrind_line:
                        continue  # Skip this line
                
                actual_code = code_line[colon_pos + 1:]
                lines.append(actual_code)

        result.append({
            'function': func['function'],
            'lines': lines,
            'start_line': valgrind_line,
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
    steps: list[str] = []  # Step log for explanation

    # =========================================================================
    # STEP 1: INITIALIZATION (first line = malloc)
    # =========================================================================

    current_func = extracted_functions[0]
    first_line = current_func['lines'][0]
    current_file = current_func.get('file', 'unknown')

    apply_init(first_line, tracking)

    # Log initial allocation
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

            # If tracking non-empty, local variables are lost
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

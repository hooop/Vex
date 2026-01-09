"""
Valgrind report parser module.

Extracts structured memory leak information from Valgrind output reports.
Detects leaks, parses summary statistics, and extracts detailed leak entries.
"""

import re
from typing import Optional

from type_defs import ParsedValgrindReport, ValgrindSummary, ValgrindError, StackFrame


def parse_valgrind_report(report: str) -> ParsedValgrindReport:
    """
    Parse a Valgrind report and extract memory leak information.

    Args:
        report: Complete text of the Valgrind report.

    Returns:
        Structured dictionary containing leak information and summary.

    Example:
        >>> report = "==123== 24 bytes in 1 blocks are definitely lost..."
        >>> result = parse_valgrind_report(report)
        >>> print(result["has_leaks"])
        True
    """

    # Basic result structure
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

    # Quick check: are there any leaks?
    if "All heap blocks were freed -- no leaks are possible" in report:
        return result

    # Extract global summary
    summary = _extract_leak_summary(report)
    if summary:
        result["summary"] = summary
        
        # If definitely_lost or indirectly_lost > 0, we have leaks
        if summary["definitely_lost"] > 0 or summary["indirectly_lost"] > 0:
            result["has_leaks"] = True

    # Extract individual leaks
    leaks = _extract_individual_leaks(report)
    if leaks:
        result["leaks"] = leaks

    return result


def _extract_leak_summary(report: str) -> Optional[ValgrindSummary]:
    """
    Extract global leak summary from LEAK SUMMARY section.

    Searches for:
    ==PID== LEAK SUMMARY:
    ==PID==    definitely lost: X bytes in Y blocks
    ==PID==    indirectly lost: X bytes in Y blocks
    ...

    Args:
        report: Complete Valgrind report.

    Returns:
        Dictionary with bytes per leak type, or None if no summary found.
    """

    # Pattern to find LEAK SUMMARY section
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

    # Pattern to extract each summary line
    # Example: "==28==    definitely lost: 74 bytes in 2 blocks"
    line_pattern = r"==\d+==\s+(definitely lost|indirectly lost|possibly lost|still reachable):\s+(\d+)\s+bytes"

    matches = re.finditer(line_pattern, report)

    for match in matches:
        leak_type = match.group(1).replace(" ", "_")  # "definitely lost" -> "definitely_lost"
        bytes_leaked = int(match.group(2))

        if leak_type in summary:
            summary[leak_type] = bytes_leaked

    # Calculate total leaked (definitely + indirectly)
    summary["total_leaked"] = summary["definitely_lost"] + summary["indirectly_lost"]

    return summary


def _extract_individual_leaks(report: str) -> list[ValgrindError]:
    """
    Extract individual leak details (bytes, file, line).

    Searches for blocks like:
    ==PID== 24 bytes in 1 blocks are definitely lost in loss record 1 of 2
    ==PID==    at 0x4846828: malloc (...)
    ==PID==    by 0x109270: main (test_multiple_errors.c:37)

    Args:
        report: Complete Valgrind report.

    Returns:
        List of dictionaries, one per detected leak.
    """

    leaks = []


    # Pattern to detect leak start
    # Example: "==28== 24 bytes in 1 blocks are definitely lost in loss record 1 of 2"
    leak_header_pattern = r"==\d+==\s+(\d+)(?:\s+\([^)]+\))?\s+bytes in\s+(\d+)\s+blocks? (?:is |are )(definitely|possibly) lost"

    # Find all leak headers
    header_matches = list(re.finditer(leak_header_pattern, report))

    for header_match in header_matches:
        bytes_leaked = int(header_match.group(1))
        blocks_count = int(header_match.group(2))
        leak_type = header_match.group(3) + " lost"

        # Position in text where this leak starts
        start_pos = header_match.end()

        # Search for location (file:line) in following lines
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


def _parse_leak_location(report: str, start_pos: int) -> dict:
    """
    Parse complete leak location with full backtrace.

    Extracts ALL functions from the call stack, from allocation
    to entry point (main), for complete context.

    Args:
        report: Complete Valgrind report.
        start_pos: Position in report to start searching.

    Returns:
        Dictionary containing 'file', 'line', 'function' for first entry,
        and 'backtrace' with complete call stack.
    """

    # System functions to ignore
    SYSTEM_FUNCTIONS = {'malloc', 'calloc', 'realloc', 'free', 'strdup',
                        'memcpy', 'memmove', 'memset'}

    excerpt = report[start_pos:start_pos + 1000]
    lines = excerpt.split('\n')
    relevant_lines = []
    started = False

    for line in lines:
        if re.search(r'(?:at|by)\s+0x[0-9A-Fa-f]+:', line):
            relevant_lines.append(line)
            started = True
        elif started and (line.strip() == '' or re.match(r'==\d+==\s*$', line)):
            break
        elif started:
            relevant_lines.append(line)

    excerpt = '\n'.join(relevant_lines)
    location_pattern = r"(?:at|by)\s+0x[0-9A-Fa-f]+:\s+(\w+)\s+\(([^:)]+):(\d+)\)"
    matches = re.finditer(location_pattern, excerpt)

    backtrace = []
    allocation_line = None
    
    for match in matches:
        function = match.group(1)
        file = match.group(2)
        line = int(match.group(3))

        # Capture first system function (allocation)
        if allocation_line is None and function in SYSTEM_FUNCTIONS:
            allocation_line = match.group(0)  # Keep complete line
            continue  # Filter it from backtrace anyway

        # Filter system functions AND system files
        if function in SYSTEM_FUNCTIONS:
            continue
        if file.startswith("/usr/") or file.startswith("vg_"):
            continue

        backtrace.append({
            "function": function,
            "file": file,
            "line": line
        })

    backtrace.reverse()

    if backtrace:
        last = backtrace[-1]
        return {
            "function": last["function"],
            "file": last["file"],
            "line": last["line"],
            "backtrace": backtrace,
            "allocation_line": allocation_line
        }

    return {
        "function": "unknown",
        "file": "unknown",
        "line": 0,
        "backtrace": [],
        "allocation_line": allocation_line
    }
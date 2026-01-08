"""
Type definitions for Vex

Central repository for all TypedDict structures used across the project.
Ensures type consistency and provides IDE autocompletion support.
"""

from typing import TypedDict, Optional


class BuildResult(TypedDict):
    """Result of a project rebuild attempt."""
    success: bool
    output: str


class StackFrame(TypedDict):
    """Single frame from a Valgrind call stack."""
    file: str
    function: str
    line: int


class ExtractedFunction(TypedDict):
    """Function extracted from source code with its context."""
    file: str
    function: str
    line: int
    code: str


class ContributingCode(TypedDict):
    """Contributing line of code that led to a memory leak."""
    code: str
    comment: str


class ValgrindSummary(TypedDict):
    """Summary statistics from Valgrind leak report."""
    definitely_lost: int
    indirectly_lost: int
    possibly_lost: int
    still_reachable: int
    total_leaked: int


class RootCauseInfo(TypedDict):
    """Root cause information identified by tracking algorithm."""
    type: int
    line: str
    function: str
    file: str
    steps: list[str]


class RealCause(TypedDict):
    """Detailed information about the actual root cause of a leak."""
    file: str
    function: str
    owner: str
    root_cause_code: str
    root_cause_comment: str
    contributing_codes: list[ContributingCode]
    context_before_code: str
    context_after_code: str


class ValgrindError(TypedDict):
    """Individual memory leak information parsed from Valgrind output."""
    type: str
    bytes: int
    blocks: int
    file: str
    line: int
    function: str
    backtrace: list[StackFrame]
    allocation_line: str
    extracted_code: list[ExtractedFunction]
    root_cause: RootCauseInfo


class MistralAnalysis(TypedDict, total=False):
    """Structured analysis result from Mistral AI."""
    type_leak: int
    diagnostic: str
    raisonnement: list[str]
    resolution_principe: str
    resolution_code: str
    explications: str
    cause_reelle: RealCause
    error: str  # Optional field for error cases


class ParsedValgrindReport(TypedDict):
    """Complete parsed Valgrind report structure."""
    has_leaks: bool
    summary: ValgrindSummary
    leaks: list[ValgrindError]


class CodeLineInfo(TypedDict):
    """Information about a single code line."""
    line: int
    code: str


class ContributingLineInfo(TypedDict):
    """Contributing code line with comment."""
    line: int
    code: str
    comment: str


class CleanedCodeLines(TypedDict):
    """Cleaned and sorted code lines with line numbers."""
    root_line: int
    root_code: str
    root_comment: str
    contributing: list[ContributingLineInfo]
    context_before: Optional[CodeLineInfo]
    context_after: Optional[CodeLineInfo]
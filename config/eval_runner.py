"""Static configuration for the pmin and pmid skill eval runner."""

from pathlib import Path

REQUIRED_DIGEST_HEADERS: list[str] = [
    "**What it does**",
    "**Key inputs**",
    "**Done when**",
    "**Quick sample**",
]

PROSE_AUTHOR_PHRASES: list[str] = [
    "moved into",
    "extracted as",
    "replaced the softer",
    "changes from the original",
    "updated to match",
    "now names",
    "was added",
    "has been updated",
    "now includes",
    "changed from",
]

LLM_JUDGE_TRIGGERS: list[str] = [
    "structured XML prompt wrapping",
    "not the result of performing",
    "executor running the formatted prompt would produce",
    "not a description of what",
    "audit output",
    "self-correct mid-turn",
    "zero tool calls",
    "subagent",
    "plan mode",
    "AskUserQuestion",
    "preview gate",
]

PROCESS_ONLY_PATTERNS: list[str] = [
    ".draft-prompt.xml",
    "prompt_workflow_validate",
    "stripped before user-facing",
    "hook validation block",
    "re-validated until exit",
    "validation loop",
    # tool-use counts require live session data, not verifiable from saved output
    "zero tool calls made",
    "no tool calls of any kind",
]

DETERMINISTIC_COVERED_PATTERNS: list[str] = [
    "zero prose before",
    "zero prose between",
    "zero prose after",
    "zero intervening prose",
    "framing sentence before the fence",
    "four required bold headers",
    "each header is followed by at least one sentence",
    "no second ```xml fence",
    "not a markdown table",
    "quick sample contains zero prompt-authoring",
    "## outcome digest present immediately",
    "## outcome digest contains all four required bullets",
    "output is exactly one xml fence followed immediately",
    "output is one xml fence followed immediately",
    # boundary checks — already enforced by structural zero-prose checks
    "produces no audit output",
    "no validation metadata",
    # behavioral presence checks — absence of second structural element is verified structurally
    "preview gate turn",
    # digest format style — four headers with content already enforced by structural checks
    "bullets under each of the four required headers",
    # perspective/tone check — four-section format with correct content is the structural proxy
    "from the perspective of someone deciding",
    "no triple-backtick code fences inside the xml fence",
]

LLM_JUDGE_SYSTEM_PROMPT: str = """\
You are a strict eval judge for AI skill outputs. You assess whether a given
skill output meets a specific expected-behavior criterion. You respond ONLY
with a JSON object containing two keys:
- "verdict": "PASS" or "FAIL"
- "reason": one concise sentence explaining your decision

Do not include any other text. Do not use markdown fences.\
"""

LLM_JUDGE_MODEL: str = "claude-haiku-4-5"
GROQ_JUDGE_MODEL: str = "llama-3.3-70b-versatile"
GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
LLM_JUDGE_MAX_TOKENS: int = 256
LLM_JUDGE_OUTPUT_CHAR_LIMIT: int = 4000
REPORT_SEPARATOR_WIDTH: int = 70

EVAL_SPECS: list[tuple[str, Path, Path]] = [
    (
        "pmid",
        Path("skills/pmid/evals/pmid.json"),
        Path("data/prompts"),
    ),
    (
        "pmin",
        Path("skills/pmin/evals/pmin.json"),
        Path("data/prompts"),
    ),
]

VERDICT_ICONS: dict[str, str] = {"PASS": "✓", "FAIL": "✗", "SKIP": "○"}

ANSI_GREEN: str = "\033[32m"
ANSI_RED: str = "\033[31m"
ANSI_YELLOW: str = "\033[33m"
ANSI_RESET: str = "\033[0m"

VERDICT_COLORS: dict[str, str] = {
    "PASS": ANSI_GREEN,
    "FAIL": ANSI_RED,
    "SKIP": ANSI_YELLOW,
}

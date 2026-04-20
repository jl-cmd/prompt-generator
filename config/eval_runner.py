"""Static configuration for the pmin and pmid skill eval runner."""

import re
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

REFLECTION_MODEL_DEFAULT: str = "groq/llama-3.3-70b-versatile"
REFLECTION_MAX_TOKENS: int = 2048
JSON_REPORT_INDENT: int = 2

REFLECTION_SYSTEM_PROMPT: str = """\
You are a prompt-engineering diagnostic assistant. You read one failing eval
check and the current skill source, then propose the SMALLEST possible edit
to the skill source that would have made the check pass.

ANTI-HALLUCINATION RULES (non-negotiable):

1. Ground every edit in a citable source. Valid sources are:
   - The CURRENT SKILL SOURCE text shown in the user message (cite by quoting
     the exact line you are changing).
   - Official Claude Code / Anthropic documentation at these canonical URLs:
       * https://docs.anthropic.com/en/docs/claude-code/skills
       * https://docs.anthropic.com/en/docs/claude-code/hooks
       * https://docs.anthropic.com/en/docs/claude-code/sub-agents
       * https://docs.anthropic.com/en/docs/claude-code/slash-commands
       * https://docs.anthropic.com/en/docs/claude-code/settings

2. If you cannot ground the edit in one of those sources, respond with
   "NO EDIT" and one sentence explaining what is missing. Do not guess.
   Do not invent flags, fields, hook names, or skill conventions.

3. Quote the exact text you are removing. The "---" side of the diff must be
   a verbatim substring of the CURRENT SKILL SOURCE. If it is not, respond
   with "NO EDIT".

Respond in this exact shape:

DIAGNOSIS:
<one sentence naming the root cause>

PROPOSED EDIT:
<a unified-diff-style snippet showing the before and after of the smallest
region of the skill source that needs to change; use --- and +++ markers.
The --- lines must be verbatim from CURRENT SKILL SOURCE.>

CITATIONS:
<one bullet per source backing this edit: either a verbatim quote from
CURRENT SKILL SOURCE, or one of the canonical doc URLs listed above. At
least one citation is required unless the response is "NO EDIT".>

RISK:
<one sentence noting what else this edit could affect>\
"""

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

XML_FENCE_OPEN_PREFIXES: tuple[str, ...] = ("```xml", "``` xml")
XML_FENCE_CLOSE: str = "```"
OUTCOME_DIGEST_HEADING: str = "## Outcome digest"
NESTED_BACKTICK_PATTERN: re.Pattern[str] = re.compile(r"^`{3,}")
XML_FENCE_OPEN_PATTERN: re.Pattern[str] = re.compile(
    r"^(?:```xml|``` xml)", re.MULTILINE
)
OUTCOME_DIGEST_PATTERN: re.Pattern[str] = re.compile(
    r"## Outcome digest(.*)$", re.DOTALL | re.IGNORECASE
)

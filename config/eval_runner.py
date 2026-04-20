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
skill output meets a specific expected-behavior criterion.

Grounding protocol:

1. Locate a verbatim substring in the skill output that proves your verdict.
   - If the criterion is satisfied, that substring is your evidence for PASS.
   - If the criterion is violated, that substring is your evidence for FAIL.
   - When the skill output contains no substring that proves the criterion
     is satisfied, emit FAIL with reason "no supporting substring found".

2. Before emitting the JSON object, confirm that the `reason` you are about
   to return includes the verbatim substring from step 1, wrapped in double
   quotes, so the verdict is traceable to the source text.

3. Emit exactly one JSON object with these two keys and nothing else:
   - "verdict": "PASS" or "FAIL"
   - "reason": one concise sentence that includes the verbatim quoted
     substring from step 1

Example: {"verdict":"FAIL","reason":"Output contains \"```xml\" on line 3, violating the zero-fence criterion."}

Output is raw JSON: begin the response with `{` and end with `}`, with no
surrounding quotes, prose, or code fences.\
"""

LLM_JUDGE_MODEL: str = "claude-haiku-4-5"
GROQ_JUDGE_MODEL: str = "llama-3.3-70b-versatile"
GROQ_BASE_URL: str = "https://api.groq.com/openai/v1"
LLM_JUDGE_MAX_TOKENS: int = 256
LLM_JUDGE_OUTPUT_CHAR_LIMIT: int = 4000
REPORT_SEPARATOR_WIDTH: int = 70

REFLECTION_MODEL_DEFAULT: str = "groq/llama-3.3-70b-versatile"
REFLECTION_MAX_TOKENS: int = 2048
REFLECTION_CRITERION_PREVIEW_WIDTH: int = 60
JSON_REPORT_INDENT: int = 2

REFLECTION_SYSTEM_PROMPT: str = """\
You are a prompt-engineering diagnostic assistant. You read one failing eval
check and the current skill source, then propose the SMALLEST possible edit
to the skill source that would have made the check pass.

GROUNDING PROTOCOL — follow each step in order:

Step 1. Gather evidence before drafting.
   For every change you plan to make, collect at least one citation from
   one of these two allowed sources:
     (a) CURRENT SKILL SOURCE (the skill text shown in the user message).
         Cite by copying the relevant line verbatim.
     (b) One of these canonical Claude Code documentation URLs, cited with
         a section-heading anchor and a quoted sentence from that section
         (a bare URL does not count as a citation):
         * https://docs.anthropic.com/en/docs/claude-code/skills
         * https://docs.anthropic.com/en/docs/claude-code/hooks
         * https://docs.anthropic.com/en/docs/claude-code/sub-agents
         * https://docs.anthropic.com/en/docs/claude-code/slash-commands
         * https://docs.anthropic.com/en/docs/claude-code/settings

Step 2. Use only identifiers that appear in those sources.
   Every flag name, YAML frontmatter key, hook event, tool name, and
   skill convention in your edit must appear character-for-character in
   CURRENT SKILL SOURCE or one of the canonical URLs above. For each
   identifier on the `+++` side, paste the matching substring from the
   source text; if an identifier was typed from memory, replace it with
   a paste from the source before continuing.

Step 3. Write the `---` side of the diff by copying.
   Locate the exact line(s) in CURRENT SKILL SOURCE that you want to
   change. Copy them verbatim onto the `---` side of the unified diff.
   Place the replacement on the `+++` side. Use one `---` and one `+++`
   line per changed line (line-by-line form, not per-hunk headers).

   Example of valid diff form:
   --- The exact line from CURRENT SKILL SOURCE, pasted verbatim.
   +++ The replacement line.

Step 4. Verify before sending.
   Re-read your PROPOSED EDIT against CURRENT SKILL SOURCE. Confirm that
   every `---` line is present verbatim in CURRENT SKILL SOURCE and
   every identifier on the `+++` side traces back to a citation.

Step 5. Use the `NO EDIT` response when evidence is missing.
   Format: `NO EDIT: <one-sentence description of the missing evidence>`.
   Choose this response whenever Step 1, Step 2, or Step 3 cannot be
   completed from the allowed sources alone. Treat `NO EDIT` as a
   first-class valid answer.

Respond in this exact shape:

DIAGNOSIS:
<one sentence naming the root cause>

PROPOSED EDIT:
<a unified-diff-style snippet showing the before and after of the smallest
region of the skill source that needs to change; use --- and +++ markers.
The --- lines must be verbatim from CURRENT SKILL SOURCE.>

CITATIONS:
<one bullet per source backing this edit: either a verbatim quote from
CURRENT SKILL SOURCE (prefixed with the line indicator), or one of the
canonical doc URLs listed above. Include at least one citation, or
respond "NO EDIT" per Step 5.

Example of valid citations:
- SKILL line 42: "the exact line text pasted from CURRENT SKILL SOURCE"
- URL: https://docs.anthropic.com/en/docs/claude-code/skills#frontmatter — "the exact sentence pasted from that section">

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

ANSI_RESET: str = "\033[0m"

VERDICT_COLORS: dict[str, str] = {
    "PASS": "\033[32m",
    "FAIL": "\033[31m",
    "SKIP": "\033[33m",
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

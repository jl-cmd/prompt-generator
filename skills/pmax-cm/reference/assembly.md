# Assembly — Phases 4, 5, 6

## Contents

- Phase 4 build rules
- Sentence splitting
- Comment placement
- Phase 5 preview rules
- Phase 6 final handoff
- Word-check guarantee

## Phase 4 — Build the prompt

`scripts/assemble_prompt.py` performs mechanical assembly:

1. Group ledger entries by `section`.
2. For each section, emit an XML tag whose name is the section value (lowercase, underscores).
3. Within each tag, for each entry belonging to that section:
   a. Split the `answer` text into sentences using a rule-based splitter (period, question mark, exclamation mark, followed by whitespace or end-of-string).
   b. For each sentence, assign a sub-ID `E<root>.<n>`.
   c. Emit the HTML comment `<!-- E<root>.<n> -->` on its own line.
   d. Emit the sentence on the following line.
4. Close the XML tag.

Output example:

```xml
<instructions>
  <primary_task>
    <!-- E4.1 -->
    Add theme_db_id as the new primary key.
    <!-- E4.2 -->
    Allow content_id to be NULL going forward.
  </primary_task>
</instructions>
```

One sentence per line; no mid-sentence wrapping.

## Phase 5 — Preview the outcome

Emit `### Outcome preview` markdown with four bullets:

- **What it does** — one sentence.
- **Key inputs** — what the prompt needs.
- **Done when** — checkable success signal.
- **Quick sample** — ~20 lines of real executor output, not a description.

Bullets stay under 20 lines total (skimmability rule from TARGET_OUTPUT.md).

Then issue one AskUserQuestion:

- **Ship this outcome profile** (Recommended, listed first)
- **Alternate 1** — contextual alternative grounded in the ledger.
- **Alternate 2** — contextual alternative grounded in the ledger.
- **Refine with free text** — merges user text into the ledger, re-enters Phase 4.

Cap: 3 preview rounds unless the user raises the cap in chat.

Preview-completeness rule (Eval 7): every ledger entry must be represented in at least one preview bullet. The skill validates coverage before emitting the preview turn. On failure: plain-language report ("E5 and E7 are not reflected in the preview"), return to Phase 4.

## Phase 6 — Show the prompt

Final assistant message:

1. One ` ```xml ` fenced block containing the full prompt.
2. `## Outcome digest` after the closing fence, four tightened bullets.
3. Copy the XML (fence content only, excluding comments) to the clipboard unless `PROMPT_WORKFLOW_SKIP_CLIPBOARD=1`.

No other content in the final message.

## Word-check guarantee

Before emitting Phase 6, the validator confirms every sentence in the fenced XML has a matching `<!-- E#.# -->` comment on the preceding line. Any unbacked sentence fails the check and returns to Phase 4 with the specific offending line reported.

Mechanical guarantee that no prose was added during assembly — every sentence traces to a user-approved ledger entry.

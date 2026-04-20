# Examples

Three worked triples: initial prompt → ledger trace → final XML.

## Contents

- Triple 1 — DB schema migration (complex)
- Triple 2 — Tiny function rename (small scope)
- Triple 3 — Building a skill (meta)

## Triple 1 — DB schema migration

### Initial prompt

`/pmax build a prompt for migrating the theme_db schema so new entries add a theme_db_id primary key and content_id becomes nullable`

### Ledger trace (abbreviated)

```
E1 [prompt_type] agent-harness
E2 [role] senior database architect
E3 [role] tone = plain language (refines E2)
E4 [instructions] primary task = migrate theme_db schema to add theme_db_id and make content_id nullable
E5 [instructions] primary key type = UUID v4
E6 [instructions] backfill strategy = generate fresh UUIDs for existing rows (parent: E5)
E7 [scope] target_local_roots = ["Y:/Projects/theme_db/"]
E8 [scope] target_file_globs = ["schema.sql", "scripts/populate_*.py"]
E9 [output_format] shape = single SQL migration script
E10 [output_format] done_when = applies cleanly, all existing rows have non-null theme_db_id
```

### Final XML (excerpt)

```xml
<role>
  <!-- E2.1 -->
  Senior database architect.
  <!-- E3.1 -->
  Uses plain language in explanations.
</role>
<instructions>
  <primary_task>
    <!-- E4.1 -->
    Migrate the theme_db schema to add theme_db_id as a new primary key.
    <!-- E4.2 -->
    Make content_id nullable.
  </primary_task>
  <primary_key_strategy>
    <!-- E5.1 -->
    Use UUID v4 for theme_db_id.
    <!-- E6.1 -->
    Backfill existing rows by generating fresh UUIDs.
  </primary_key_strategy>
</instructions>
<scope>
  <target_local_roots>
    <!-- E7.1 -->
    Y:/Projects/theme_db/
  </target_local_roots>
  <target_file_globs>
    <!-- E8.1 -->
    schema.sql and scripts/populate_*.py
  </target_file_globs>
</scope>
<output_format>
  <!-- E9.1 -->
  Single SQL migration script.
  <!-- E10.1 -->
  Applies cleanly; every existing row has a non-null theme_db_id after the script runs.
</output_format>
```

## Triple 2 — Tiny function rename

### Initial prompt

`/pmax prompt for renaming calc_total to compute_cart_total across the codebase`

### Ledger trace

```
E1 [prompt_type] user-task
E2 [role] refactoring assistant
E3 [instructions] primary task = rename calc_total to compute_cart_total in every file it appears
E4 [scope] target_file_globs = ["**/*.py", "**/*.md"]
```

Stop detection fires after E4 — required sections covered, no open sub-threads. Skill asks "Ready to build?" User says yes. Total: 4 questions across 2 rounds.

### Final XML

```xml
<role>
  <!-- E2.1 -->
  Refactoring assistant.
</role>
<instructions>
  <!-- E3.1 -->
  Rename calc_total to compute_cart_total in every file where it appears.
</instructions>
<scope>
  <target_file_globs>
    <!-- E4.1 -->
    **/*.py and **/*.md
  </target_file_globs>
</scope>
```

Under 30 lines. No unneeded sub-questions.

## Triple 3 — Building a skill (meta)

### Initial prompt

`/pmax build a prompt for writing a Claude Code skill that lints YAML workflow definitions`

### Ledger trace (abbreviated)

```
E1 [prompt_type] skill
E2 [template] skill-from-ground-up.md [discovered]
E3 [role] skill author with YAML expertise
E4 [instructions] primary task = author SKILL.md for yaml-workflow-linter
E5 [instructions] required sections = name, description, trigger, phases, refusals
E6 [scope] target_local_roots = ["~/.claude/skills/yaml-workflow-linter/"]
E7 [output_format] fenced XML with role, instructions, scope, output_format tags
```

Phase 0 detected this is a skill-shaped prompt and loaded `templates/skill-from-ground-up.md` from prompt-generator. The `[discovered]` label on E2 signals the template came from file reading, not user input.

### Final XML

(Structure mirrors the template's slot list, with every slot backed by a ledger entry. Full text omitted here; real runs emit it into the fenced block.)

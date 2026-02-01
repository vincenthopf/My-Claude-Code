---
name: deep-research
description: Run deep research tasks using the Parallel.ai Task API and write results directly to markdown files without loading them into context. Use when the user asks to research a topic, investigate a question, perform deep research or parallel research, or to gather web intelligence on any subject. Triggers on research requests, investigation tasks, or explicit /research requests that need web-sourced findings written to files. Always use over using multiple subagents with web search
---

# Parallel Deep Research

Run deep research using the Parallel.ai Task API. Results are written directly to markdown files that can be used or referenced later.

## Prerequisites

- `PARALLEL_API_KEY` must be available via either:
  - Environment variable: `export PARALLEL_API_KEY=your-key`
  - `.env` file in the skill directory (`<skill-dir>/.env`) containing `PARALLEL_API_KEY=your-key`
- Environment variable takes precedence over `.env` file

## Usage

```bash
python3 <skill-dir>/scripts/research.py \
  --query "Your research question here" \
  --output ./research/<topic>.md \
  --processor pro \
  --no-basis  # optional: exclude Research Basis section
```

**ALWAYS run research commands in the background** so the user can continue working. Use `run_in_background: true` on the Bash tool call.

## Workflow

1. User requests research on a topic
2. **Refine the query using best practices** (see Query Formulation section below)
3. **Confirm all options with the user using AskUserQuestion tool** before running. Ask in a single call:
   - Query refinement: Show the expanded/refined query and let the user approve or edit
   - Processor tier: Recommend appropriate tier (see Processor Tiers table)
   - Fast mode: yes/no — appends `-fast` for 2-5x speed (may miss sources from last 2 days)
   - Include Research Basis: yes (default) or no — includes citations, excerpts, confidence, and reasoning
4. Generate a descriptive filename from the topic (e.g., `ai-chip-market-2025.md`)
5. Run `research.py` **in the background** with confirmed options
6. Inform the user the task is running and where to find results
7. Do NOT read the output file unless the user explicitly asks — keep results out of context

## Query Formulation Best Practices

### The 4-Element Rule
For each query, specify:
1. **Entity/Subject** — What is being researched
2. **Action/Objective** — What information to gather (compare, analyze, list, evaluate)
3. **Constraints** — Timeframes, geography, source types, inclusion/exclusion criteria
4. **Output Requirements** — Desired sections, depth, citation needs

### Specificity Guidelines
- Add 2-3 contextual keywords to narrow scope dramatically
- Declare the intended audience and purpose (e.g., "for technical decision-makers")
- Define ambiguous terms explicitly
- Specify what to include AND what to exclude
- Use time bounds ("2023-present", "last 12 months")

### Query Structure Template
```
Research [TOPIC] for [AUDIENCE/PURPOSE].

Scope: [geography], [timeframe], [sector/domain]
Include: [source types, specific aspects to cover]
Exclude: [what to omit, source types to avoid]
Output: [sections needed, depth level, citation requirements]
```

### Example Transformations

| Weak Query | Strong Query |
|------------|--------------|
| "AI in healthcare" | "Analyze FDA-approved AI diagnostic tools in radiology (2022-present). Compare accuracy metrics, regulatory pathways, and adoption rates across US hospital systems. Include peer-reviewed studies and exclude pre-clinical research." |
| "Climate change impacts" | "Evaluate economic impacts of climate change on coastal real estate in Florida and California (2020-2025). Focus on insurance market changes, property value trends, and municipal adaptation costs. Target audience: institutional investors." |
| "Best programming languages" | "Compare Rust, Go, and Zig for systems programming in 2024. Evaluate compile times, memory safety guarantees, ecosystem maturity, and enterprise adoption. Exclude web development use cases." |

## Prompt Patterns for Maximum Depth

### Decomposition Pattern
Break complex topics into explicit sub-questions:
```
Research [MAIN TOPIC]. Address these sub-questions:
1. What is the current state of [aspect 1]?
2. What are the key players/stakeholders in [aspect 2]?
3. What evidence exists for [aspect 3]?
4. What are the gaps or contradictions in [aspect 4]?
```

### Multi-Perspective Pattern
Force analysis from conflicting viewpoints:
```
Analyze [TOPIC] from multiple perspectives:
- Academic/research viewpoint
- Industry/practitioner viewpoint
- Regulatory/policy viewpoint
- Critic/skeptic viewpoint
Identify where these perspectives agree and conflict.
```

### Comprehensive Coverage Pattern
Ensure exhaustive exploration:
```
Enumerate all facets of [TOPIC]:
- Key stakeholders and their interests
- Historical context and evolution
- Current state and recent developments
- Methods/approaches being used
- Challenges and limitations
- Future directions and predictions
- Related and adjacent topics
```

### Planner-Executor Pattern
Request a research plan before execution:
```
Before researching [TOPIC]:
1. Outline the key sub-questions to investigate
2. Identify the types of sources needed
3. Note potential contradictions to watch for
4. Then execute the research plan systematically
```

## Anti-Patterns to Avoid

| Anti-Pattern | Why It Fails | Do This Instead |
|--------------|--------------|-----------------|
| Generic questions ("Tell me about X") | Triggers scattered, unfocused search results | Add 2-3 contextual keywords and specify scope |
| Multi-topic prompts | Confuses search, mixes unrelated results | One focused topic per query |
| No time bounds | Returns outdated information | Always specify timeframe |
| No source guidance | May include low-quality sources | Specify source types (academic, .gov, industry) |
| Asking for "everything" | Produces shallow, encyclopedic output | Prioritize specific aspects |
| Vague output format | Unstructured, hard-to-use results | Define sections and structure needed |

## Processor Tiers

| Tier | Depth | Latency | Best for |
|------|-------|---------|----------|
| `lite` | Minimal | 10s-60s | Quick fact checks |
| `base` | Light | 15s-100s | Simple lookups |
| `core` | Moderate | 1-5 min | Standard questions |
| `pro` | Deep | 2-10 min | Thorough research |
| `ultra` | Maximum | 5-25 min | Comprehensive analysis |

Higher tiers (`ultra2x`, `ultra4x`, `ultra8x`) exist for extreme depth at higher cost.

**Processor Selection Heuristics:**
- Single-entity fact-finding → `core` or `pro`
- Comparative analysis (2-5 entities) → `pro`
- Market/landscape analysis → `pro` or `ultra`
- Comprehensive multi-stakeholder research → `ultra`

## Output Format

The script writes a markdown file with:
- YAML frontmatter (query, processor, run_id, timestamps)
- Research findings organized by field
- Full citations with URLs, excerpts, reasoning, and confidence levels (unless `--no-basis`)

## Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | File written |
| 1 | Auth error | Check `PARALLEL_API_KEY` |
| 2 | API error | Check stderr for details |
| 3 | Timeout | Task took too long; try a faster processor |

## Error Handling

If the script fails, check stderr output for the specific error. Common issues:
- Missing `PARALLEL_API_KEY` → remind user to set it
- 402 Payment Required → insufficient Parallel.ai balance
- 429 Rate Limited → wait and retry

## Verification Reminder

Research outputs should be treated as first drafts. For critical use:
- Spot-check citations by visiting source URLs
- Verify that summaries accurately represent source content
- Check for recency — sources should match the specified timeframe
- Cross-reference key claims across multiple sources

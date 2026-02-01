# Skill Taxonomy: Non-Technical Skill Categories

> This document defines a taxonomy for non-technical skills based on their **core cognitive operation**. Different skill types require different methodologies, quality criteria, and generation approaches.

## Why Taxonomy Matters

Non-technical skills are NOT all the same. A "writing skill" and an "analysis skill" require fundamentally different:
- **Methodologies** to draw from
- **Quality criteria** to evaluate output
- **Prompting strategies** to generate effectively

Misclassifying a skill leads to mediocre results. For example:
- Treating an **Insight** task as **Summary** → Gets comprehensive but shallow output
- Treating a **Decision** task as **Research** → Gets information but no commitment

---

## The Core Taxonomy

### Overview Table

| Type | English | Core Operation | Input → Output |
|---|---|---|---|
| 总结类 | Summary | Compress | Many signals → Fewer, preserving coverage |
| 洞察类 | Insight | Extract | Many signals → Few KEY signals that explain WHY |
| 生成类 | Generation | Create | Constraints → New content |
| 决策类 | Decision | Choose | Options + criteria → Selection + rationale |
| 评估类 | Evaluation | Judge | Artifact → Quality score + gaps |
| 诊断类 | Diagnosis | Trace | Symptoms → Root cause + fix |
| 说服类 | Persuasion | Bridge | My goal → Their action |
| 规划类 | Planning | Decompose | Goal → Path with milestones |
| 调研类 | Research | Discover | Questions → Structured answers |
| 引导类 | Facilitation | Elicit | Hidden knowledge → Surfaced knowledge |
| 转化类 | Transformation | Map | Format A → Format B |

---

## Detailed Definitions

### 1. 总结类 (Summary)

**Core Operation**: Compress

**Essence**: Reduce information volume while preserving coverage. The goal is completeness in fewer words.

**Transformation**: Many → Fewer (equal weight compression)

**Example Output**:
```
"The candidate has experience in: backend development (5 years),
microservices (3 projects), cloud platforms (AWS, GCP), and
some AI/ML exposure. Education includes CS degree from..."
```

**Quality Criteria**:
- Completeness: Did it cover all important aspects?
- Accuracy: Is the compression faithful to the original?
- Structure: Is it well-organized and scannable?

**Methodology Sources**:
- Barbara Minto (Pyramid Principle)
- MECE frameworks
- Information architecture

**When to Use**: When the user needs a comprehensive overview, not a judgment.

---

### 2. 洞察类 (Insight)

**Core Operation**: Extract the exceptional

**Essence**: Find the few signals that actually matter. Filter out noise to reveal meaning.

**Transformation**: Many → Few (finding what's decisive)

**Analogy**:
- Summary = Panoramic photo (everything visible, no focus)
- Insight = Finding the focal point (background fades)

**Example Output**:
```
"The KEY issue with this candidate: microservices experience
is real but language mismatch is significant. The AI claim
is likely superficial—no quantified results, vague language."
```

**Quality Criteria**:
- Depth: Does it answer WHY, not just WHAT?
- Prioritization: Are insights ranked by importance?
- Actionability: Can you act on this insight?

**Methodology Sources**:
- NN/g Data → Findings → Insights framework
- Signal detection theory
- Topgrading (A-player identification)

**When to Use**: When the user needs to understand what really matters, not everything.

---

### 3. 生成类 (Generation)

**Core Operation**: Create under constraints

**Essence**: Produce new content that didn't exist, while meeting requirements.

**Transformation**: Constraints/Requirements → New artifact

**Example Tasks**:
- Write a cold outreach email
- Draft a PRD
- Create a presentation

**Quality Criteria**:
- Fit: Does it meet all constraints?
- Effectiveness: Will it achieve its goal?
- Style: Is tone/voice appropriate for audience?

**Methodology Sources**:
- Domain-specific writing frameworks
- Copywriting principles (if persuasive)
- Genre conventions

**When to Use**: When the user needs content created, not analyzed.

---

### 4. 决策类 (Decision)

**Core Operation**: Choose and commit

**Essence**: Weigh trade-offs between incommensurable factors and make a choice.

**Transformation**: Options + Criteria → Selection + Rationale

**Key Challenge**: Factors often can't be directly compared (speed vs quality, cost vs risk).

**Example Output**:
```
"Recommendation: Go with Option B.

Rationale: While Option A is cheaper, Option B's
time-to-market advantage outweighs the 20% cost increase
given current competitive pressure."
```

**Quality Criteria**:
- Clarity: Is the recommendation unambiguous?
- Rationale: Is the reasoning explicit and logical?
- Trade-off acknowledgment: Are downsides stated?

**Methodology Sources**:
- MCDA (Multi-Criteria Decision Analysis)
- Decision matrices
- Bezos "one-way vs two-way door" framework

**When to Use**: When the user needs a choice, not more options.

---

### 5. 评估类 (Evaluation)

**Core Operation**: Judge against standards

**Essence**: Compare an artifact to ideal standards and identify gaps.

**Transformation**: Artifact → Quality judgment + Gap analysis

**Example Tasks**:
- Code review
- Proposal evaluation
- Performance assessment

**Quality Criteria**:
- Objectivity: Based on clear standards, not preference
- Specificity: Exact issues identified, not vague complaints
- Constructiveness: Actionable improvements suggested

**Methodology Sources**:
- Domain-specific quality frameworks
- Rubrics and evaluation criteria
- Best practice checklists

**When to Use**: When the user needs quality judgment, not creation.

---

### 6. 诊断类 (Diagnosis)

**Core Operation**: Trace back to root cause

**Essence**: Reason backward from symptoms to underlying causes.

**Transformation**: Symptoms/Problems → Root cause + Fix

**Key Challenge**: Not stopping at surface-level causes.

**Example Output**:
```
"The build is failing not because of the syntax error (that's
the symptom), but because the dependency update changed the
API signature. Fix: Pin dependency to v2.3.x or update all
call sites."
```

**Quality Criteria**:
- Depth: Did it find the TRUE root cause?
- Completeness: Are all contributing factors identified?
- Actionability: Is the fix clear and executable?

**Methodology Sources**:
- 5 Whys
- Fishbone diagrams
- Systems thinking

**When to Use**: When something is broken and needs fixing.

---

### 7. 说服类 (Persuasion)

**Core Operation**: Bridge worldviews

**Essence**: Connect your goal to their action by understanding their mental model.

**Transformation**: My goal + Their worldview → Message that moves them

**Key Challenge**: Understanding what they already believe, fear, and want.

**Example Tasks**:
- Sales pitch
- Stakeholder buy-in
- Negotiation

**Quality Criteria**:
- Audience fit: Does it speak to THEIR concerns?
- Credibility: Is it believable?
- Call to action: Is next step clear?

**Methodology Sources**:
- Cialdini (Influence)
- SPIN Selling
- Aristotle's Rhetoric (Ethos, Pathos, Logos)

**When to Use**: When the user needs to change someone's mind or behavior.

---

### 8. 规划类 (Planning)

**Core Operation**: Decompose into steps

**Essence**: Break a goal into a sequence of achievable milestones.

**Transformation**: Goal → Path with milestones + Dependencies

**Key Challenge**: Right level of detail, handling uncertainty.

**Example Output**:
```
"Phase 1 (Week 1-2): Research & Design
  - Define API contract
  - Design database schema
Phase 2 (Week 3-4): Implementation
  - Core CRUD operations
  - Authentication integration
..."
```

**Quality Criteria**:
- Completeness: Are all necessary steps included?
- Sequencing: Are dependencies correct?
- Granularity: Right level of detail for the audience?

**Methodology Sources**:
- Work breakdown structures
- Agile planning
- Critical path analysis

**When to Use**: When the user needs a roadmap, not just a goal.

---

### 9. 调研类 (Research)

**Core Operation**: Discover and structure

**Essence**: Explore unknown territory and return with organized knowledge.

**Transformation**: Questions → Structured answers with sources

**Key Challenge**: Knowing when you have "enough", avoiding confirmation bias.

**Example Tasks**:
- Market research
- Competitive analysis
- Technology evaluation

**Quality Criteria**:
- Coverage: Were enough sources consulted?
- Objectivity: Is it balanced, not cherry-picked?
- Structure: Is knowledge organized usefully?

**Methodology Sources**:
- Research methodology
- Source evaluation frameworks
- Synthesis techniques

**When to Use**: When the user needs knowledge gathered, not generated.

---

### 10. 引导类 (Facilitation)

**Core Operation**: Elicit through questions

**Essence**: Help others surface their own knowledge through skilled questioning.

**Transformation**: Hidden/tacit knowledge → Explicit, articulated knowledge

**Key Challenge**: Not leading too much (bias) or too little (missing key info).

**Example Tasks**:
- User interviews
- Requirements elicitation
- Coaching conversations

**Quality Criteria**:
- Depth: Did it surface non-obvious information?
- Neutrality: Avoided leading questions?
- Completeness: Covered all important areas?

**Methodology Sources**:
- Mom Test (Rob Fitzpatrick)
- Motivational Interviewing
- SPIN Selling (for discovery)

**When to Use**: When the user needs to extract information from others.

---

### 11. 转化类 (Transformation)

**Core Operation**: Map between representations

**Essence**: Convert from one format/perspective to another while preserving meaning.

**Transformation**: Format A → Format B (isomorphic mapping)

**Key Challenge**: Knowing what to preserve vs. adapt.

**Example Tasks**:
- Technical → Business translation
- Meeting → Action items
- Long-form → Executive summary

**Quality Criteria**:
- Fidelity: Is essential meaning preserved?
- Fit: Is output appropriate for target format?
- Clarity: Is it clear in the new format?

**Methodology Sources**:
- Translation theory
- Information design
- Audience adaptation

**When to Use**: When content exists but needs reformatting or re-framing.

---

## How to Use This Taxonomy

### Step 1: Identify the Skill Type

When a user requests a skill, first determine its type:

| User says... | Likely type |
|---|---|
| "Help me write..." | Generation |
| "Help me understand..." | Insight or Summary |
| "Help me decide..." | Decision |
| "Help me evaluate..." | Evaluation |
| "Help me figure out why..." | Diagnosis |
| "Help me convince..." | Persuasion |
| "Help me plan..." | Planning |
| "Help me research..." | Research |
| "Help me interview..." | Facilitation |
| "Help me convert..." | Transformation |

### Step 2: Validate with User

Confirm the type with the user:

```
"It sounds like you need an INSIGHT-type skill (finding what really
matters) rather than a SUMMARY-type skill (comprehensive overview).
Is that right?"
```

### Step 3: Apply Type-Specific Generation

Use appropriate:
- Methodology sources for that type
- Quality criteria for that type
- Output format conventions for that type

---

## Common Confusions

| Often confused | How to distinguish |
|---|---|
| Summary vs Insight | Summary = complete coverage; Insight = key signals only |
| Decision vs Evaluation | Decision = make a choice; Evaluation = judge quality |
| Research vs Insight | Research = gather info; Insight = interpret meaning |
| Generation vs Transformation | Generation = create new; Transformation = convert existing |
| Diagnosis vs Evaluation | Diagnosis = find root cause; Evaluation = judge against standard |

---

## Version History

- v1.0 (2026-01-21): Initial taxonomy with 11 types

# Deep Technical Analysis: OpenClaw Architecture vs Claude Agent SDK

**Analysis Date**: February 2026
**Author**: Claude Code Analysis Agent
**Repositories**:
- OpenClaw: https://github.com/openclaw/openclaw (TypeScript, v2026.2.4)
- Claude Agent SDK: https://github.com/anthropics/claude-agent-sdk-python (Python, v0.1.29)

---

## Table of Contents

1. [Executive Summary](#executive-summary)
2. [Phase 1: OpenClaw Architecture](#phase-1-openclaw-architecture)
3. [Phase 2: Claude Agent SDK Architecture](#phase-2-claude-agent-sdk-architecture)
4. [Phase 3: Comparative Analysis](#phase-3-comparative-analysis)
5. [Phase 4: Gap Analysis](#phase-4-gap-analysis)
6. [Phase 5: "Better OpenClaw" Architecture Proposal](#phase-5-better-openclaw-architecture-proposal)
7. [Prioritized Recommendations](#prioritized-recommendations)

---

## Executive Summary

### Key Findings

| System | Strength | Weakness |
|--------|----------|----------|
| **OpenClaw** | Production-ready multi-channel platform with enterprise features | Complex monolith, tightly coupled, TypeScript-only |
| **Claude Agent SDK** | Clean API, excellent tool integration, type-safe | Anthropic-only, limited persistence, no multi-channel |

**Recommendation**: Use Claude Agent SDK as the core agent runtime, then selectively port OpenClaw's channel adapters and memory system. The Agent SDK provides a more maintainable foundation, while OpenClaw provides battle-tested platform integrations.

---

## Phase 1: OpenClaw Architecture

### 1.1 Project Overview

OpenClaw is a **TypeScript/Node.js monorepo** (4,968 files) that provides a personal AI assistant framework with:
- **24+ messaging channel integrations** (Telegram, WhatsApp, Discord, Slack, Signal, etc.)
- **50+ skills/plugins** for specific capabilities
- **Gateway-based architecture** for centralized control
- **Multi-model support** (Anthropic, OpenAI, Google, custom)
- **Web UI** for configuration and monitoring

```
~/analysis/openclaw/
├── src/                    # Core source (TypeScript)
│   ├── gateway/           # WebSocket control plane
│   ├── agents/            # LLM orchestration
│   ├── channels/          # Plugin system
│   ├── memory/            # Vector + FTS storage
│   ├── skills/            # Skill runtime
│   └── providers/         # Model integrations
├── extensions/            # 24+ channel plugins
├── skills/                # 50+ skill definitions
├── packages/              # Sub-packages
└── ui/                    # Vite + React control panel
```

### 1.2 Gateway Architecture

**Entry Point**: `src/entry.ts` → `src/cli/run-main.ts` → `src/cli/program.ts`

The gateway is a **WebSocket server** that acts as the central message broker:

```
┌─────────────────────────────────────────────────────────────────┐
│                        Gateway Server                            │
│  src/gateway/server-ws-runtime.ts                                │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐            │
│  │Telegram │  │Discord  │  │WhatsApp │  │ Slack   │  ...       │
│  │ Client  │  │ Client  │  │ Client  │  │ Client  │            │
│  └────┬────┘  └────┬────┘  └────┬────┘  └────┬────┘            │
│       │            │            │            │                  │
│       └────────────┴────────────┴────────────┘                  │
│                         │                                        │
│                    ┌────┴────┐                                   │
│                    │ Router  │                                   │
│                    │ + Auth  │                                   │
│                    └────┬────┘                                   │
│                         │                                        │
│       ┌─────────────────┼─────────────────┐                     │
│       │                 │                 │                     │
│  ┌────┴────┐      ┌────┴────┐      ┌────┴────┐                 │
│  │ Session │      │  Agent  │      │ Memory  │                 │
│  │ Manager │      │  Loop   │      │ Manager │                 │
│  └─────────┘      └─────────┘      └─────────┘                 │
└─────────────────────────────────────────────────────────────────┘
```

**Key Pattern**: Request-Response with streaming support

```typescript
// src/gateway/client.ts (lines 415-440)
async request<T>(method: string, params?: unknown): Promise<T> {
  const id = randomUUID();
  const frame: RequestFrame = { type: "req", id, method, params };
  this.pending.set(id, { resolve, reject, expectFinal });
  this.ws.send(JSON.stringify(frame));
  return promise;
}
```

### 1.3 Agent Loop Implementation

**Location**: `src/agents/pi-embedded-runner/run.ts`

The agent loop uses a **two-level queue** to prevent thundering herd:

```typescript
// Global lane: prevents concurrent runs across all sessions
const globalLane = resolveGlobalLane(params.lane);

// Session lane: prevents concurrent runs on same session
const sessionLane = resolveSessionLane(params.sessionKey);

return enqueueSession(() =>
  enqueueGlobal(async () => {
    // Context window validation
    const info = resolveContextWindowInfo({ model, ... });
    if (info.tokens < CONTEXT_WINDOW_HARD_MIN_TOKENS) {
      throw new Error("Model context too small");
    }

    // Create agent session with tools
    const session = await createAgentSession({ tools, customTools, ... });

    // Main loop: prompt → stream → tool calls → results → repeat
    await activeSession.prompt(effectivePrompt);
  })
);
```

**Tool Call Handling**: The `pi-ai` package handles tool invocation internally:
1. Stream LLM response
2. Detect `tool_use` blocks
3. Invoke tool handlers
4. Collect tool results
5. Continue until `stop_reason != "tool_use"`

**Context Compaction**: `src/agents/pi-embedded-runner/compact.ts`
- Triggered when context exceeds limits
- Uses LLM to summarize earlier messages
- Replaces original messages with summary

### 1.4 Memory System

**Location**: `src/memory/`

**Storage**: SQLite with vector extension (`sqlite-vec`) + FTS5 for keyword search

```typescript
// src/memory/memory-schema.ts
CREATE TABLE chunks (
  id TEXT PRIMARY KEY,
  path TEXT NOT NULL,
  source TEXT NOT NULL DEFAULT 'memory',  -- 'memory' or 'sessions'
  start_line INTEGER NOT NULL,
  end_line INTEGER NOT NULL,
  hash TEXT NOT NULL,
  model TEXT NOT NULL,
  text TEXT NOT NULL,
  embedding TEXT NOT NULL,
  updated_at INTEGER NOT NULL
);

CREATE VIRTUAL TABLE fts USING fts5(text, id UNINDEXED, ...);
```

**Hybrid Search**:
1. Vector search (cosine similarity)
2. FTS5 keyword search
3. BM25 ranking for final scoring

**Memory Sources**:
- `MEMORY.md` + `memory/*.md` files (explicit long-term memory)
- Session transcripts (conversation history)

### 1.5 Skills System

**Location**: `skills/` directory, `src/agents/skills/`

Skills are defined via **SKILL.md** files with YAML frontmatter:

```yaml
---
name: gemini
description: Gemini CLI for one-shot Q&A
metadata:
  openclaw:
    emoji: "♊️"
    requires:
      bins: ["gemini"]
    install:
      - { kind: "brew", formula: "gemini-cli" }
user-invocable: true
disable-model-invocation: false
---
```

**Eligibility Filtering** (`src/agents/skills/config.ts`):
1. Check if explicitly disabled in config
2. Check platform requirements (macOS, Linux, etc.)
3. Check required binaries are present
4. Check required environment variables

### 1.6 Multi-Channel Routing

**Plugin Interface** (`src/channels/plugins/types.plugin.ts`):

```typescript
type ChannelPlugin<ResolvedAccount> = {
  id: ChannelId;
  meta: ChannelMeta;
  capabilities: ChannelCapabilities;
  config: ChannelConfigAdapter<ResolvedAccount>;
  setup?: ChannelSetupAdapter;
  pairing?: ChannelPairingAdapter;
  security?: ChannelSecurityAdapter<ResolvedAccount>;
  outbound?: ChannelOutboundAdapter;
  messaging?: ChannelMessagingAdapter;
  streaming?: ChannelStreamingAdapter;
  agentTools?: ChannelAgentToolFactory;
};
```

**Session Keys** (`src/routing/session-key.ts`):
```
agent:${agentId}:${channel}:${peerKind}:${peerId}
```
- Hierarchical structure for multi-tenant isolation
- DM scope options: `main`, `per-peer`, `per-channel-peer`

---

## Phase 2: Claude Agent SDK Architecture

### 2.1 Project Overview

The Claude Agent SDK is a **Python library** (3,479 lines) that wraps the Claude Code CLI:
- **Two query interfaces**: `query()` (stateless) and `ClaudeSDKClient` (stateful)
- **In-process MCP servers** for custom tools
- **Bidirectional control protocol** for permissions and hooks
- **Bundled Claude Code CLI** for zero-config installation

```
~/analysis/claude-agent-sdk-python/
├── src/claude_agent_sdk/
│   ├── __init__.py          # Public API + MCP server implementation
│   ├── query.py             # Stateless query function
│   ├── client.py            # Stateful client class
│   ├── types.py             # Type definitions (837 lines)
│   └── _internal/
│       ├── query.py         # Control protocol (625 lines)
│       ├── message_parser.py # Message parsing
│       └── transport/       # CLI subprocess management
└── examples/                # 17 example files
```

### 2.2 Query Interface

**Stateless**: `query()` function
```python
async for message in query(
    prompt="Write a Python function",
    options=ClaudeAgentOptions(model="claude-opus-4-5")
):
    print(message)
```

**Stateful**: `ClaudeSDKClient` class
```python
async with ClaudeSDKClient(options=options) as client:
    await client.query("First question")
    async for msg in client.receive_response():
        print(msg)

    await client.query("Follow-up question")
    async for msg in client.receive_response():
        print(msg)
```

### 2.3 Agent Loop Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        User Application                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐           ┌─────────────────────┐              │
│  │   query()   │           │   ClaudeSDKClient   │              │
│  │ (stateless) │           │    (stateful)       │              │
│  └──────┬──────┘           └──────────┬──────────┘              │
│         │                              │                         │
│         └──────────────┬───────────────┘                         │
│                        │                                         │
│                 ┌──────┴──────┐                                  │
│                 │    Query    │                                  │
│                 │   (class)   │                                  │
│                 └──────┬──────┘                                  │
│                        │                                         │
│         ┌──────────────┼──────────────┐                         │
│         │              │              │                         │
│    ┌────┴────┐   ┌─────┴─────┐   ┌────┴────┐                   │
│    │ control │   │  message  │   │   MCP   │                   │
│    │ protocol│   │  stream   │   │ servers │                   │
│    └────┬────┘   └─────┬─────┘   └────┬────┘                   │
│         │              │              │                         │
└─────────┼──────────────┼──────────────┼─────────────────────────┘
          │              │              │
    ┌─────┴──────────────┴──────────────┴─────┐
    │         SubprocessCLITransport           │
    │  ┌────────┐  ┌────────┐  ┌────────┐     │
    │  │ stdin  │  │ stdout │  │ stderr │     │
    │  └────────┘  └────────┘  └────────┘     │
    └──────────────────┬───────────────────────┘
                       │
              ┌────────┴────────┐
              │  Claude Code    │
              │     CLI         │
              └─────────────────┘
```

**Control Protocol** (`_internal/query.py`):
- `control_request`: CLI asks SDK for permission/hook response
- `control_response`: SDK responds with allow/deny/hook output

### 2.4 Tool System (MCP Integration)

**In-Process MCP Server**:
```python
@tool("add", "Add two numbers", {"a": float, "b": float})
async def add(args):
    return {"content": [{"type": "text", "text": f"{args['a'] + args['b']}"}]}

server = create_sdk_mcp_server("calculator", tools=[add, subtract])
options = ClaudeAgentOptions(mcp_servers={"calc": server})
```

**Permission Model**:
```python
PermissionMode = Literal["default", "acceptEdits", "plan", "bypassPermissions"]

async def can_use_tool(tool_name: str, input: dict, context: ToolPermissionContext):
    if tool_name == "Edit" and "/secure/" in input.get("path", ""):
        return PermissionResultDeny(message="Cannot edit secure directory")
    return PermissionResultAllow()
```

### 2.5 Context Management

The SDK delegates context management to Claude Code CLI:
- **Beta features**: `betas=["context-1m-2025-08-07"]` for 1M context
- **Hook callbacks**: `PreCompact` event fires before compaction
- **Session management**: `resume`, `fork_session`, `continue_conversation`

### 2.6 Configuration: ClaudeAgentOptions

```python
@dataclass
class ClaudeAgentOptions:
    # Model
    model: str | None = None
    fallback_model: str | None = None

    # Tools
    allowed_tools: list[str] = field(default_factory=list)
    disallowed_tools: list[str] = field(default_factory=list)
    mcp_servers: dict[str, McpServerConfig] = field(default_factory=dict)

    # Prompting
    system_prompt: str | None = None
    max_thinking_tokens: int | None = None
    output_format: dict[str, Any] | None = None  # JSON schema

    # Limits
    max_turns: int | None = None
    max_budget_usd: float | None = None

    # Permissions
    permission_mode: PermissionMode | None = None
    can_use_tool: CanUseTool | None = None

    # Hooks
    hooks: dict[HookEvent, list[HookMatcher]] | None = None

    # Session
    resume: str | None = None
    continue_conversation: bool = False
    enable_file_checkpointing: bool = False
```

---

## Phase 3: Comparative Analysis

### 3.1 Comparison Table

| Aspect | OpenClaw | Claude Agent SDK | Winner & Why |
|--------|----------|------------------|--------------|
| **Agent Loop Sophistication** | Two-level queue (global + session), streaming with throttling, event broadcast to multiple clients | Single subprocess with asyncio, bidirectional control protocol | **OpenClaw** - Production-ready concurrent session handling |
| **Tool/Skill Architecture** | YAML frontmatter, eligibility filtering, binary/env requirements, install automation | `@tool` decorator, in-process MCP servers, type-safe Python | **Claude Agent SDK** - Cleaner API, better DX, type safety |
| **Context Management** | Automatic compaction with LLM summarization, token counting, context window guard | Delegated to CLI, `PreCompact` hook for notifications | **OpenClaw** - More sophisticated compaction logic |
| **Error Recovery** | `FailoverError` with typed reasons, auth profile rotation, exponential backoff | Basic exception handling, hooks for failures | **OpenClaw** - Enterprise-grade failover |
| **Security Model** | Channel-level policies (dm/group), pairing approval, cross-agent policy | Permission callbacks, sandbox settings, directory restrictions | **Tie** - Different approaches, both adequate |
| **Extensibility** | Plugin architecture with typed adapters, SKILL.md format | MCP servers, hooks, custom transport interface | **OpenClaw** - More extension points, but more complex |
| **Multi-Model Support** | Provider abstractions (Anthropic, OpenAI, Google, etc.) | Anthropic-only (via Claude Code) | **OpenClaw** - Model flexibility |
| **State Persistence** | SQLite with embeddings, session files, memory sources | File-based via CLI, session resumption | **OpenClaw** - Better persistence architecture |
| **Testability** | Vitest with mocks, Docker integration tests | pytest with type checking, E2E tests | **Claude Agent SDK** - Cleaner test structure |
| **Code Quality/Maintainability** | Large monorepo (4,968 files), complex dependencies | Small codebase (3,479 lines), focused scope | **Claude Agent SDK** - Easier to understand and maintain |

### 3.2 Architecture Diagrams

**OpenClaw Request Flow**:
```
User Message (Telegram/Discord/etc.)
           │
           ▼
┌─────────────────────┐
│   Channel Plugin    │  (extensions/telegram/src/...)
│   - Auth validation │
│   - Rate limiting   │
│   - Message parsing │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Gateway Server    │  (src/gateway/server-ws-runtime.ts)
│   - Routing         │
│   - Session lookup  │
│   - Broadcast       │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Session Manager   │  (src/sessions/)
│   - Lock acquire    │
│   - History load    │
│   - State tracking  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Agent Loop        │  (src/agents/pi-embedded-runner/)
│   - Queue (global)  │
│   - Queue (session) │
│   - Context guard   │
│   - Tool dispatch   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   pi-ai Package     │  (@mariozechner/pi-agent-core)
│   - LLM streaming   │
│   - Tool execution  │
│   - Result collect  │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│   Response Stream   │
│   - Delta throttle  │
│   - Broadcast       │
│   - Slow client drop│
└──────────┬──────────┘
           │
           ▼
User Response (via channel)
```

**Claude Agent SDK Request Flow**:
```
Python Application
         │
         ▼
┌────────────────────┐
│   query() or       │  (src/claude_agent_sdk/query.py)
│   ClaudeSDKClient  │  (src/claude_agent_sdk/client.py)
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│   Query Class      │  (src/claude_agent_sdk/_internal/query.py)
│   - Initialize     │
│   - Stream input   │
│   - Control loop   │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ SubprocessTransport│  (src/.../transport/subprocess_cli.py)
│   - Spawn CLI      │
│   - stdin/stdout   │
│   - Message parse  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Claude Code CLI   │  (bundled binary)
│   - Agent loop     │
│   - Tool execution │
│   - Context mgmt   │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│  Anthropic API     │
│   - Model inference│
│   - Tool use       │
│   - Streaming      │
└────────────────────┘
```

### 3.3 Overlap and Divergence

**Where They Overlap**:
- Both use streaming for real-time responses
- Both support tool/skill execution
- Both have hook/callback systems
- Both manage session state

**Where They Diverge**:

| Concern | OpenClaw | Claude Agent SDK |
|---------|----------|------------------|
| **Architecture** | Monolithic gateway | Library wrapping CLI |
| **Language** | TypeScript | Python |
| **Deployment** | Self-hosted server | Embedded in application |
| **Multi-tenancy** | Built-in (gateway) | Application-managed |
| **Model Providers** | Pluggable | Anthropic-only |
| **Channel Support** | 24+ built-in | None (application concern) |
| **Memory** | SQLite + vectors | File-based via CLI |

---

## Phase 4: Gap Analysis

### 4.1 What OpenClaw Has That Agent SDK Doesn't

| Feature | Description | Value |
|---------|-------------|-------|
| **Multi-channel routing** | 24+ messaging platforms with unified interface | High - Critical for consumer products |
| **Gateway architecture** | Centralized control plane for multiple clients | High - Essential for multi-tenant SaaS |
| **Vector memory** | SQLite + embeddings + FTS5 hybrid search | High - Long-term memory is crucial |
| **Context compaction** | LLM-powered summarization of history | Medium - Agent SDK has CLI compaction |
| **Multi-model support** | OpenAI, Google, etc. in addition to Anthropic | Medium - Useful for cost optimization |
| **Skill marketplace** | 50+ pre-built skills with install automation | Medium - Accelerates development |
| **Failover system** | Auth rotation, rate limit handling, backoff | High - Production reliability |
| **Web UI** | Control panel for configuration | Low - Nice to have |

### 4.2 What Agent SDK Has That OpenClaw Doesn't

| Feature | Description | Value |
|---------|-------------|-------|
| **In-process MCP** | Tools run as Python functions, not subprocesses | High - Better performance, simpler debug |
| **Type-safe API** | Full typing with strict mypy | High - Better DX, fewer bugs |
| **Clean abstraction** | Small codebase, focused scope | High - Maintainability |
| **Transport interface** | Pluggable transport (subprocess, custom) | Medium - Flexibility |
| **Permission callbacks** | Python callbacks for tool authorization | Medium - Better control |
| **Session resumption** | Built-in resume from transcript | Medium - Useful for recovery |
| **Bundled CLI** | Zero-config installation | Low - Developer convenience |

### 4.3 What Neither Does Well

| Gap | Description | Opportunity |
|-----|-------------|-------------|
| **Distributed state** | Both are single-machine; no Redis/Postgres clustering | Use external state store |
| **Observability** | Limited tracing, metrics, logging | Add OpenTelemetry |
| **Rate limiting** | Basic; no sophisticated quotas | Add token bucket per user |
| **Cost management** | Track usage but no budgeting per tenant | Add billing integration |
| **A/B testing** | No experiment framework | Add feature flags |
| **Multi-region** | No geographic distribution | Design for edge deployment |
| **Offline support** | Neither works offline | Add local model fallback |

---

## Phase 5: "Better OpenClaw" Architecture Proposal

### 5.1 Design Principles

1. **Claude Agent SDK as core runtime** - Leverage its clean API and Anthropic expertise
2. **Channel adapters as separate packages** - Port OpenClaw's channel plugins
3. **External state store** - Replace SQLite with Redis + PostgreSQL
4. **Event-driven architecture** - Use message queues for decoupling
5. **Observability first** - OpenTelemetry from day one

### 5.2 Component Diagram

```
                              ┌─────────────────────────┐
                              │      Control Plane      │
                              │  (FastAPI + WebSocket)  │
                              └───────────┬─────────────┘
                                          │
          ┌───────────────────────────────┼───────────────────────────────┐
          │                               │                               │
          ▼                               ▼                               ▼
┌─────────────────┐           ┌─────────────────┐            ┌─────────────────┐
│ Channel Gateway │           │  Agent Workers  │            │  Memory Service │
│   (Telegram)    │           │  (Pool of N)    │            │  (Vector DB)    │
├─────────────────┤           ├─────────────────┤            ├─────────────────┤
│ - Auth          │           │ - Claude Agent  │            │ - Embeddings    │
│ - Rate limit    │           │   SDK           │            │ - FTS search    │
│ - Transform     │           │ - MCP servers   │            │ - Session store │
│ - Enqueue       │           │ - Hooks         │            │ - Compaction    │
└────────┬────────┘           └────────┬────────┘            └────────┬────────┘
         │                             │                              │
         │                             │                              │
         └─────────────┬───────────────┘                              │
                       │                                               │
                       ▼                                               │
              ┌────────────────┐                                       │
              │  Message Queue │ ◄─────────────────────────────────────┘
              │  (Redis/NATS)  │
              └────────────────┘
                       │
                       ▼
              ┌────────────────┐
              │  State Store   │
              │  (PostgreSQL)  │
              └────────────────┘
```

### 5.3 Key Interfaces

**Channel Adapter Interface** (ported from OpenClaw):
```python
from abc import ABC, abstractmethod
from dataclasses import dataclass

@dataclass
class IncomingMessage:
    channel: str
    account_id: str
    peer_id: str
    peer_kind: Literal["dm", "group", "channel"]
    text: str
    attachments: list[Attachment]
    reply_to: str | None = None

@dataclass
class OutgoingMessage:
    text: str
    attachments: list[Attachment] = field(default_factory=list)
    reply_to: str | None = None

class ChannelAdapter(ABC):
    @abstractmethod
    async def start(self) -> None:
        """Start receiving messages."""

    @abstractmethod
    async def stop(self) -> None:
        """Stop receiving messages."""

    @abstractmethod
    async def send(self, peer_id: str, message: OutgoingMessage) -> None:
        """Send a message to a peer."""

    @abstractmethod
    def on_message(self, callback: Callable[[IncomingMessage], Awaitable[None]]) -> None:
        """Register callback for incoming messages."""
```

**Agent Worker Interface**:
```python
@dataclass
class AgentTask:
    session_id: str
    prompt: str
    images: list[bytes] = field(default_factory=list)
    context: dict[str, Any] = field(default_factory=dict)

@dataclass
class AgentResponse:
    text: str
    tool_results: list[ToolResult]
    usage: Usage
    cost_usd: float

class AgentWorker:
    def __init__(
        self,
        options: ClaudeAgentOptions,
        memory_service: MemoryService,
    ):
        self.client = ClaudeSDKClient(options=options)
        self.memory = memory_service

    async def process(self, task: AgentTask) -> AsyncIterator[AgentResponse]:
        # Load context from memory
        context = await self.memory.load_context(task.session_id)

        # Inject into prompt
        enriched_prompt = self._enrich_with_context(task.prompt, context)

        # Execute via Claude Agent SDK
        await self.client.query(enriched_prompt)
        async for message in self.client.receive_response():
            yield self._convert_to_response(message)

        # Save to memory
        await self.memory.save_turn(task.session_id, task.prompt, response)
```

**Memory Service Interface**:
```python
class MemoryService(ABC):
    @abstractmethod
    async def search(
        self,
        session_id: str,
        query: str,
        max_results: int = 10
    ) -> list[MemoryResult]:
        """Semantic search over memory."""

    @abstractmethod
    async def load_context(
        self,
        session_id: str,
        max_tokens: int = 8000
    ) -> list[Message]:
        """Load recent conversation history."""

    @abstractmethod
    async def save_turn(
        self,
        session_id: str,
        user_message: str,
        assistant_message: str
    ) -> None:
        """Save a conversation turn."""

    @abstractmethod
    async def compact(
        self,
        session_id: str,
        target_tokens: int
    ) -> None:
        """Compact history to fit target token budget."""
```

### 5.4 Data Flow

```
1. User sends message via Telegram
         │
         ▼
2. Telegram Adapter receives, validates auth
         │
         ▼
3. Adapter enqueues AgentTask to Redis
         │
         ▼
4. Available Worker dequeues task
         │
         ▼
5. Worker loads context from Memory Service
         │
         ▼
6. Worker executes via Claude Agent SDK
         │
         ├── SDK invokes MCP tools (in-process)
         ├── SDK fires hooks (Python callbacks)
         └── SDK streams response
         │
         ▼
7. Worker saves turn to Memory Service
         │
         ▼
8. Worker enqueues response to Redis
         │
         ▼
9. Telegram Adapter dequeues, sends to user
```

### 5.5 What to Build vs. Reuse

| Component | Build/Reuse | Rationale |
|-----------|-------------|-----------|
| **Agent runtime** | Reuse Claude Agent SDK | Clean API, maintained by Anthropic |
| **Channel adapters** | Port from OpenClaw | Battle-tested, but adapt to async Python |
| **Memory service** | Build new | Use modern vector DB (Qdrant/Pinecone/pgvector) |
| **Message queue** | Reuse Redis/NATS | Standard infrastructure |
| **State store** | Reuse PostgreSQL | Standard infrastructure |
| **Control plane** | Build new | FastAPI + WebSocket for admin/monitoring |
| **Observability** | Reuse OpenTelemetry | Standard infrastructure |

### 5.6 Complexity Assessment

| Task | Complexity | Estimate |
|------|------------|----------|
| Port Telegram adapter | Low | 1-2 days |
| Port Discord adapter | Low | 1-2 days |
| Port WhatsApp adapter | Medium | 3-5 days (Baileys complexity) |
| Build Memory Service (pgvector) | Medium | 1 week |
| Build Memory Service (Qdrant) | Low | 3-4 days |
| Build Worker pool | Low | 2-3 days |
| Build Control plane | Medium | 1 week |
| Add OpenTelemetry | Low | 2-3 days |
| **Total MVP** | | **3-4 weeks** |

---

## Prioritized Recommendations

### If Building From Scratch, Do These Differently:

1. **Use Claude Agent SDK as the core** (not a custom agent loop)
   - Why: Maintained by Anthropic, cleaner API, better tool integration
   - How: Wrap `ClaudeSDKClient` in a worker pool

2. **Use PostgreSQL + pgvector for memory** (not SQLite)
   - Why: Scalable, concurrent, production-ready
   - How: `CREATE EXTENSION vector;` then cosine similarity queries

3. **Use Redis for queuing** (not in-process queues)
   - Why: Decouples channels from workers, enables horizontal scaling
   - How: Redis Streams or simple LPUSH/BRPOP

4. **Port channel adapters to async Python** (not TypeScript)
   - Why: Same language as Agent SDK, better interop
   - How: Use `aiogram` (Telegram), `hikari` (Discord), etc.

5. **Add OpenTelemetry from day one**
   - Why: Production debugging is critical
   - How: Instrument with `opentelemetry-instrumentation-*`

6. **Implement cost management early**
   - Why: LLM costs can surprise you
   - How: Track per-session, set budgets, alert on thresholds

7. **Use feature flags for experiments**
   - Why: A/B test prompts, models, tools
   - How: LaunchDarkly, Unleash, or simple Redis-based

8. **Design for multi-region from the start**
   - Why: Latency matters for chat
   - How: Redis Cluster, PostgreSQL replicas, edge workers

### Decision Framework: "Should I Build on Agent SDK?"

**YES if**:
- You're primarily using Anthropic models
- You want a clean, maintainable codebase
- You're building a Python application
- You need custom tool authorization
- You want in-process MCP tools

**NO if**:
- You need multi-model support (OpenAI, Google, etc.)
- You're already invested in TypeScript
- You need the specific channel integrations OpenClaw provides
- You need the advanced failover system

### Honest Assessment

**OpenClaw**:
- ✅ Production-ready with 24+ channels
- ✅ Sophisticated failover and error handling
- ✅ Good memory system with vector search
- ❌ Complex monolith (4,968 files)
- ❌ Tightly coupled to pi-ai package
- ❌ TypeScript-only

**Claude Agent SDK**:
- ✅ Clean, focused API (3,479 lines)
- ✅ Excellent tool integration (MCP)
- ✅ Type-safe Python
- ✅ Maintained by Anthropic
- ❌ Anthropic-only (no multi-model)
- ❌ No built-in persistence
- ❌ No multi-channel support

**Bottom line**: The Agent SDK is the better foundation for new projects. Port the valuable parts of OpenClaw (channel adapters, memory architecture) rather than building on OpenClaw's monolith.

---

## Appendix: Key Code Snippets

### OpenClaw: Gateway Request Handler
```typescript
// src/gateway/client.ts:415-440
async request<T = Record<string, unknown>>(
  method: string,
  params?: unknown,
  opts?: { expectFinal?: boolean },
): Promise<T> {
  if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
    throw new Error("gateway not connected");
  }
  const id = randomUUID();
  const frame: RequestFrame = { type: "req", id, method, params };
  const expectFinal = opts?.expectFinal === true;
  const p = new Promise<T>((resolve, reject) => {
    this.pending.set(id, { resolve, reject, expectFinal });
  });
  this.ws.send(JSON.stringify(frame));
  return p;
}
```

### OpenClaw: Context Window Guard
```typescript
// src/agents/context-window-guard.ts
export const CONTEXT_WINDOW_HARD_MIN_TOKENS = 16_000;
export const CONTEXT_WINDOW_WARN_BELOW_TOKENS = 32_000;

export function evaluateContextWindowGuard(params: {
  info: ContextWindowInfo;
}): ContextWindowGuardResult {
  return {
    ...params.info,
    shouldWarn: params.info.tokens < CONTEXT_WINDOW_WARN_BELOW_TOKENS,
    shouldBlock: params.info.tokens < CONTEXT_WINDOW_HARD_MIN_TOKENS,
  };
}
```

### Claude Agent SDK: MCP Tool Definition
```python
# src/claude_agent_sdk/__init__.py:73-143
@dataclass
class SdkMcpTool(Generic[T]):
    name: str
    description: str
    input_schema: type[T] | dict[str, Any]
    handler: Callable[[T], Awaitable[dict[str, Any]]]

def tool(
    name: str,
    description: str,
    input_schema: type | dict[str, Any]
) -> Callable[[...], SdkMcpTool[Any]]:
    def decorator(handler):
        return SdkMcpTool(
            name=name,
            description=description,
            input_schema=input_schema,
            handler=handler,
        )
    return decorator
```

### Claude Agent SDK: Control Protocol Handler
```python
# src/claude_agent_sdk/_internal/query.py:237-278
async def _handle_control_request(self, request: dict[str, Any]) -> None:
    subtype = request.get("subtype")
    if subtype == "can_use_tool":
        response = await self.can_use_tool(
            request["tool_name"],
            request["input"],
            ToolPermissionContext(...)
        )
        if isinstance(response, PermissionResultAllow):
            response_data = {"behavior": "allow", ...}
        elif isinstance(response, PermissionResultDeny):
            response_data = {"behavior": "deny", "message": response.message}
        await self._send_control_response(request["id"], response_data)
```

---

*Report generated by Claude Code analysis agent. For questions or corrections, please open an issue.*

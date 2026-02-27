/task-plan --detailed we have excellent research, design, arch, and planing docs in docs/claude/. make a detailed and complete implimentation plan for the autonomus development and testing of the program by claude code.
Context:
    - 90% testing coverage required
    - Update relevant documentation (architecture, features, ADRs) following CLAUDE.md standards (Arc42, Diataxis, C4)
    - Commit documentation and changes together
Instructions:
1. **Generate PLAN_ID**: `[kebab-case-task]-[YYYY-MM-DD]`
2. **Resolve Directories**:
    ```bash
    PLANS_DIR=$(jq -r '.plansDirectory // ".claude/plans"' .claude/settings.json 2>/dev/null || echo ".claude/plans")
    mkdir -p $PLANS_DIR/$PLAN_ID .claude/tasks/$PLAN_ID .claude/outputs/$PLAN_ID .claude/state/$PLAN_ID
    ```
3. **Resource Discovery** - Analyze task domain and identify:
    **Relevant Skills** (auto-activate via /skill-name):
        | Domain | Skill | Trigger |
        |--------|-------|---------|
        | Architecture | /architecture-decision | Technology choices, design patterns |
        | Documentation | /unified-documentation | Arc42, Diataxis, C4 docs |
        | Code Quality | /code-review | Before completion, security review |
        | Testing | /test-automation | Coverage analysis, test validation |
        | Config | /config-validation | Settings, environment validation |
        | Multi-agent | /agent-coordination | Complex delegated work |
        | Doc Health | /documentation-health | Doc structure validation |
    **Recommended Agents** (via /team):
        | Category | Agent | Use For |
        |----------|-------|---------|
        | **Core** | tech-lead | Architecture review, code review, coordination |
        | | backend-engineer | APIs, databases, server-side logic |
        | | javascript-developer | Node.js, TypeScript, frontend |
        | | flutter-developer | Mobile, Dart, cross-platform |
        | | qa-devops-engineer | CI/CD, testing infrastructure, deployment |
        | | ux-ui-designer | UI components, design systems |
        | | autonomous-coding-specialist | Long-running, multi-file refactoring |
        | **AI** | ai-integration-specialist | LLM APIs, AI features |
        | | prompt-engineer | Prompt optimization |
        | | research-specialist | Deep analysis (extended thinking) |
        | **Infrastructure** | security-specialist | Threat modeling, audits |
        | | cloud-infrastructure-architect | GCP, IaC, scaling |
        | | data-engineer-analyst | Pipelines, analytics |
    **Available MCPs** (external integrations):
        | MCP | Use For |
        |-----|---------|
4. **Complexity Assessment**: SIMPLE / MEDIUM / COMPLEX / EPIC
    **Thinking effort mapping** (adaptive reasoning depth per task):
        | Complexity | Thinking Effort | Est. Tokens | Use When |
        |------------|----------------|-------------|----------|
        | SIMPLE (S) | low | ~10k | Single-file edits, config changes |
        | MEDIUM (M) | medium | ~25k | Multi-file features, moderate logic |
        | COMPLEX (L) | high | ~50k | Architecture changes, complex integrations |
        | EPIC (XL) | max | ~80k+ | System-wide refactors, must split into subtasks |
5. **Execution Strategy** - Select based on task structure:
    | Mode | When to Use | Agent Pattern |
    |------|-------------|---------------|
    | /work | Single-agent, linear tasks | autonomous-coding-specialist |
    | /parallel | Independent subtasks | Multiple agents in parallel |
    | /pipeline | Phased, sequential stages | Agents per stage |
    | /orchestrate | Complex, mixed patterns | tech-lead coordinating team |
    | /teams | Real-time collaboration, shared context | Agent Teams (requires CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1) |
6. **Create Plan** in `$PLANS_DIR/$PLAN_ID/`:
    - plan.md (scope, design, tasks, risks)
    - resources.md (selected skills, agents, MCPs with rationale)
    - execution.md (command sequence, agent assignments)
    State files in `.claude/state/$PLAN_ID/`:
    - context-budget.md, orchestration-plan.md, progress.md
7. **Plan Structure** - Include these sections:
    ```markdown
    # Plan: [Task Name]
        Version: 2.0
        Plan ID: $PLAN_ID
        Created: [timestamp]
        Status: DRAFT
    ## Resources
    ### Skills to Activate
        - [x] /skill-name - [reason for inclusion]
    ### Agents to Delegate
        | Phase | Agent | Responsibility |
        |-------|-------|----------------|
        | Design | tech-lead | Architecture review |
        | Implement | backend-engineer | API development |
        | Test | qa-devops-engineer | Test infrastructure |
    ### MCPs Required
    ## Scope
        ### In Scope / Out of Scope / Success Criteria
    ## Technical Design
        ### Architecture / Key Decisions / Components
    ## Task Breakdown
        ### Overview
        - Total tasks: [N] ([N] parallelizable, [N] sequential)
        - Estimated total tokens: [N]k
        - Thinking effort range: [lowest]-[highest]
        | ID | Task | Agent | Depends On | Complexity | Effort | Est. Tokens | Status |
        |----|------|-------|------------|------------|--------|-------------|--------|
        | 001 | [Task] | [agent] | - | S | low | ~10k | pending |
    ### Checkpoint Strategy
        Auto-compaction handles context management. Explicit checkpoints only for:
        - Before destructive operations
        - At phase boundaries in /pipeline mode
        - Before external system interactions
    ## Risks
        | Risk | Likelihood | Impact | Mitigation |
        |------|------------|--------|------------|
    ## Execution Plan
        ### Mode: [/work | /parallel | /pipeline | /orchestrate | /teams]
        ### Rationale: [Why this mode]
        ### Command Sequence:
            1. /[mode] --plan $PLAN_ID
            2. [checkpoint/resume strategy]
    ```
8. Decompose into `.claude/tasks/$PLAN_ID/` if >5 subtasks
9. **Native Task Integration** (when `--native-tasks` flag used):
    - TaskCreate per task with metadata: `{ planId, complexity, effort, estTokens }`
    - TaskUpdate with addBlockedBy to mirror dependency chains
10. **Memory Persistence**: Record to project auto-memory: Plan ID, location, task count, mode, status (DRAFT), timestamp
11. **Output Summary**:
    ```
    PLAN CREATED: $PLANS_DIR/$PLAN_ID/plan.md

    Version: 2.0
    Plan ID: $PLAN_ID
    Resources:
    - Skills: [list activated skills]
    - Agents: [list assigned agents]
    - MCPs: [list required MCPs]
    Tasks: [N] total ([N] parallel, [N] sequential)
    Estimated total tokens: [N]k
    Thinking effort range: [lowest]-[highest]
    Execution: [recommended mode]
    [If --native-tasks: Native tasks created: [N]]
    [If AGENT_TEAMS env detected: Agent Teams available]

    Directories created:
    - $PLANS_DIR/$PLAN_ID/
    - .claude/tasks/$PLAN_ID/
    - .claude/outputs/$PLAN_ID/
    - .claude/state/$PLAN_ID/

    Next: Review plan, then run /execute $PLAN_ID
    ```
Flags:
    | Flag | Effect |
    |------|--------|
    | `--quick` | Skip detailed design and risks, minimal plan |
    | `--detailed` | Include all sections with maximum depth |
    | `--template=[name]` | Use specific template (feature, bugfix, refactor, migration) |
    | `--teams` | Force Agent Teams execution mode recommendation |
    | `--native-tasks` | Create TaskCreate entries for each plan task |
    | `--fast` | Skip design & risks, minimal output (implies --quick) |
    Recommended combo: `--teams --native-tasks` for full v2 experience

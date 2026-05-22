#!/usr/bin/env bash
# PostToolUse hook: enforce mandatory skill-to-skill handoffs.
#
# Fires on every Skill tool call. Reads stdin JSON to identify the completed
# skill, then prints a mandatory next-step directive if a chain applies.

input=$(cat)
skill_name=$(echo "$input" | jq -r '.tool_input.skill // empty')

case "$skill_name" in

  flagrare:intake)
    cat >&2 <<'EOF'
MANDATORY: /flagrare:intake has completed. You MUST now invoke
/flagrare:atdd-plan via the Skill tool, passing the full context brief
as the args parameter. Do NOT ask for user approval first. Do NOT call
ExitPlanMode. Do NOT proceed to implementation. The next action you take
MUST be invoking /flagrare:atdd-plan.
EOF
    ;;

  flagrare:wrap-up)
    cat >&2 <<'EOF'
MANDATORY: /flagrare:wrap-up has completed. You MUST now invoke
/flagrare:implementation-review via the Skill tool. Pass the staged diff
context. Do NOT commit yet. Do NOT skip this step. The implementation
review must pass before any commit is made.
EOF
    ;;

  flagrare:staleness-audit)
    cat >&2 <<'EOF'
MANDATORY: /flagrare:staleness-audit has completed. After the commit
lands, you MUST invoke /flagrare:release-check via the Skill tool.
This determines whether a release is due and drafts a CHANGELOG entry.
Do NOT skip this step.
EOF
    ;;

  *)
    exit 0
    ;;
esac

exit 0

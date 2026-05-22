#!/usr/bin/env bash
# PreToolUse hook: remind to run /flagrare:codebase-explore before atdd-plan.
#
# Fires on every Skill tool call. Checks if the skill about to be invoked
# is flagrare:atdd-plan. If so, injects mandatory guidance via additionalContext.

input=$(cat)
skill_name=$(echo "$input" | jq -r '.tool_input.skill // empty')

if [[ "$skill_name" != "flagrare:atdd-plan" ]]; then
  exit 0
fi

jq -n '{
  hookSpecificOutput: {
    hookEventName: "PreToolUse",
    additionalContext: "MANDATORY: Before writing ANY acceptance tests or implementation phases, you MUST invoke /flagrare:codebase-explore via the Skill tool first. Pass the context brief as args. Wait for its findings (file paths, conventions, reusable utilities, analogous features) before proceeding to Step 2 of atdd-plan. If you have ALREADY run /flagrare:codebase-explore in this session, proceed normally."
  }
}'

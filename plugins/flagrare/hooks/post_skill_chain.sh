#!/usr/bin/env bash
# PostToolUse hook: remind Claude of mandatory skill-to-skill handoffs.
#
# Fires on every Skill tool call, which is when the skill loads, not when it
# finishes, so each note says what to do once the skill is done. The note goes
# to Claude as additionalContext; plain output with exit 0 reaches nobody.

input=$(cat)
skill_name=$(echo "$input" | jq -r '.tool_input.skill // empty')

case "$skill_name" in

  flagrare:wrap-up)
    msg="MANDATORY: When /flagrare:wrap-up finishes, you MUST invoke /flagrare:implementation-review via the Skill tool, passing the staged diff context. Do NOT commit before the implementation review passes. Do NOT skip this step."
    ;;

  flagrare:staleness-audit)
    msg="MANDATORY: When /flagrare:staleness-audit finishes and its commit lands, you MUST invoke /flagrare:release-check via the Skill tool. It decides whether a release is due and drafts a CHANGELOG entry. Do NOT skip this step."
    ;;

  *)
    exit 0
    ;;
esac

jq -n --arg msg "$msg" '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $msg}}'
exit 0

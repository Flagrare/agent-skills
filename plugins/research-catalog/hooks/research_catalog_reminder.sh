#!/usr/bin/env bash
# PostToolUse reminder for research-catalog.
#
# Fires after Agent, WebFetch, and WebSearch calls. Most Agent calls are NOT
# external research (Explore agent reading repo files, Plan agent designing
# code, etc.) — the reminder is deliberately phrased as a conditional so it's
# a check, not a blanket demand.
#
# Why this exists: the SKILL.md says "run this skill immediately after a
# research session, before the synthesis is sent back to the user." That's
# pure instruction-following — no enforcement. In practice the assistant
# would synthesize first, say "I'll catalog later," and forget. This hook
# fires at exactly the moment the assistant is about to start writing the
# synthesis, which is when the discipline lapses.

cat >&2 <<'EOF'
⚠ research-catalog reminder
If this tool call pulled in external sources (papers, vendor docs,
upstream library source, blog posts, GitHub issues outside the consuming
repo), invoke the /research-catalog skill BEFORE writing the synthesis
in your response. Do not just say "I'll document this after" — that is
the exact failure mode this hook exists to prevent.

If this call was purely internal (Explore agent reading repo files, Plan
agent designing code with no URLs fetched, WebSearch with no useful
hit), no action is needed — proceed normally.
EOF
exit 0

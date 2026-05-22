#!/usr/bin/env bash
# PostToolUse reminder for research-catalog.
#
# Fires after Agent, WebFetch, and WebSearch calls. Most Agent calls are NOT
# external research (Explore agent reading repo files, Plan agent designing
# code, etc.) — the reminder is deliberately phrased as a conditional so it's
# a check, not a blanket demand.

cat >&2 <<'EOF'
If this tool call pulled in external sources (papers, vendor docs,
upstream library source, blog posts, GitHub issues outside the consuming
repo), invoke /flagrare:research-catalog BEFORE writing the synthesis
in your response.

If this call was purely internal (Explore agent reading repo files, Plan
agent designing code with no URLs fetched, WebSearch with no useful
hit), no action is needed.
EOF
exit 0

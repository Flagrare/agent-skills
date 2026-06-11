#!/usr/bin/env python3
"""PostToolUse hook: flag em-dashes (and en-dashes used as separators) in generated
Markdown. Reads the Claude Code hook JSON from stdin, inspects the written .md file,
and exits 2 with a message if a dash slips into prose. Real code fences (```bash,
```json, ```mermaid, etc.) and inline code spans are ignored, so example commands and
literal samples don't false-positive.
"""
import json, re, sys, pathlib

EM, EN = "—", "–"
CODE_LANGS = {
    'bash','sh','shell','zsh','console','shellsession','json','jsonc','yaml','yml',
    'toml','ini','mermaid','dot','graphviz','ts','tsx','typescript','js','jsx',
    'javascript','python','py','go','golang','rust','rs','java','kotlin','ruby','rb',
    'sql','html','xml','css','scss','less','diff','c','cpp','cs','php','swift','proto',
    'dockerfile','make','makefile','http','groovy','gradle','hcl','tf',
}
fence_re = re.compile(r'^(\s*)(`{3,}|~{3,})\s*([^\s`]*)')

def offending_lines(text):
    hits, in_fence, is_code = [], False, False
    for n, line in enumerate(text.split('\n'), 1):
        m = fence_re.match(line)
        if m:
            if not in_fence:
                in_fence, is_code = True, m.group(3).strip().lower() in CODE_LANGS
            else:
                in_fence = is_code = False
            continue
        if in_fence and is_code:
            continue
        stripped = re.sub(r'`[^`]*`', '', line)  # drop inline code
        if EM in stripped or EN in stripped:
            hits.append((n, line.strip()))
    return hits

def main():
    try:
        payload = json.load(sys.stdin)
    except Exception:
        sys.exit(0)
    path = (payload.get('tool_input') or {}).get('file_path', '')
    if not path.endswith('.md'):
        sys.exit(0)
    p = pathlib.Path(path)
    if not p.exists():
        sys.exit(0)
    hits = offending_lines(p.read_text(encoding='utf-8'))
    if not hits:
        sys.exit(0)
    msg = [f"Em-dash/en-dash found in generated Markdown: {path}",
           "Replace with a comma, colon, or parentheses (ranges use a hyphen). Offending lines:"]
    for n, t in hits[:10]:
        msg.append(f"  L{n}: {t[:100]}")
    print('\n'.join(msg), file=sys.stderr)
    sys.exit(2)

if __name__ == '__main__':
    main()

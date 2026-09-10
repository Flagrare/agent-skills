// Usage: node <skill>/scripts/compare-measures.mjs <outRoot> <baseVariant> <otherVariant...>
// Prints every target with the base values, and the other variants' values only where they differ.
import fs from 'node:fs';
import path from 'node:path';

const [outRoot, base, ...others] = process.argv.slice(2);
if (!outRoot || !base || !others.length) throw new Error('usage: compare-measures.mjs <outRoot> <base> <other...>');
const load = v => JSON.parse(fs.readFileSync(path.join(outRoot, `measure.${v}.json`), 'utf8')).out;
const rgb = s => (s || '').replace('rgb(', '').replace(')', '');
const fmt = v => v ? [v.fontSize, v.fontWeight, v.lineHeight, rgb(v.color), v.letterSpacing !== 'normal' ? `ls:${v.letterSpacing}` : null, v.bg && v.bg !== 'rgba(0, 0, 0, 0)' ? `bg:${rgb(v.bg)}` : null, v.border && !v.border.startsWith('0px') ? `bd:${v.border}` : null, v.radius && v.radius !== '0px' ? `r:${v.radius}` : null, v.padding && v.padding !== '0px' ? `p:${v.padding}` : null, v.height ? `h:${v.height}` : null, v.width ? `w:${v.width}` : null].filter(Boolean).join(' ') : 'NOT FOUND';
const B = load(base); const O = Object.fromEntries(others.map(o => [o, load(o)]));
let changed = 0;
for (const key of Object.keys(B)) {
  const b = fmt(B[key]);
  const diffs = others.filter(o => fmt(O[o][key]) !== b);
  console.log(key.padEnd(34) + (diffs.length ? ` [${diffs.join(', ')} differ]` : ''));
  console.log(`   ${base.padEnd(14)} ${b}`);
  for (const o of diffs) { console.log(`   ${o.padEnd(14)} ${fmt(O[o][key])}`); changed++; }
}
console.log(`\n${changed} differing rows`);

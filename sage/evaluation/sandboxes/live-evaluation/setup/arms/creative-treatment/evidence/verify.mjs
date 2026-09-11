import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const base = new URL('../', import.meta.url);
const read = async path => readFile(new URL(path, base), 'utf8');
const load = async name => JSON.parse(await read(`evidence/${name}/observations.json`));
const main = await load('browser-attempt-2');
const focused = await load('browser-focused-1');
const demonstration = await load('browser-demonstration-1');
const expected = ['Find your focus.', 'Watch the pattern.', 'Correct · 1 of 3', 'Correct · 2 of 3', 'Perfect echo.', 'Watch the pattern.', 'Not quite · step 1', 'Watch the pattern.', 'Correct · 1 of 3', 'Correct · 2 of 3', 'Perfect echo.'];
for (const o of main.observations) {
  assert.equal(o.steps[0].focus, 'start');
  expected.forEach((text, i) => assert.ok(o.steps[i].visible.includes(text), `${o.viewport.width} main step ${i}: ${text}`));
  assert.equal(o.metrics.scrollWidth, o.metrics.innerWidth);
}
for (const o of focused.observations) {
  for (const i of [2, 7]) { assert.ok(o.steps[i].visible.includes('Watch the pattern.')); assert.ok(o.steps[i].visible.includes('0 / 3 steps repeated')); }
  assert.equal(o.steps[10].focus, 'pad-2');
  assert.ok(o.steps[10].visible.includes('Correct · 1 of 3'));
  assert.equal(o.steps[13].focus, 'pad-4');
  assert.ok(o.steps[13].visible.includes('Correct · 2 of 3'));
}
for (const o of demonstration.observations) {
  [2, 4, 1].forEach((pad, i) => { const visible = o.steps[i + 2].visible; assert.ok(visible.includes(`Watch · step ${i + 1} of 3`)); assert.ok(visible.includes(`Pad ${pad}. Remember`)); assert.equal((visible.match(/● WATCH/g) || []).length, 1); });
  assert.ok(o.steps[5].visible.includes('Your turn. Echo the pattern.'));
}
const html = await read('work/index.html');
assert.ok(html.includes('prefers-reduced-motion: reduce'));
assert.ok(html.includes('aria-live="polite"'));
assert.ok(html.includes('aria-label="Pad 1"'));
assert.equal((html.match(/<button\b/g) || []).length, 5);
assert.ok(!/(?:src|href)\s*=\s*["']https?:|@import|fetch\(|new Audio|<script[^>]+src=/i.test(html));
const performance = [main, focused, demonstration].flatMap((d, run) => d.observations.map(o => ({run:['supplied-flow','focused-flow','demonstration-flow'][run], viewport:o.viewport, fileNavigationWallMs:o.loadWallMs, navigationSamples:1, keyboardSamples:o.steps.length, keyboardToTwoFramesMs:{min:Math.min(...o.steps.map(s=>s.inputToTwoFramesMs)), max:Math.max(...o.steps.map(s=>s.inputToTwoFramesMs)),mean:o.steps.reduce((a,s)=>a+s.inputToTwoFramesMs,0)/o.steps.length}})));
const paths = ['work/index.html', 'inputs/game.json', 'inputs/flow.json', 'evidence/focused-flow.json', 'evidence/demonstration-flow.json', ...['browser-attempt-2','browser-focused-1','browser-demonstration-1'].flatMap(d=>['observations.json','viewport-1280x800.png','viewport-390x844.png'].map(f=>`evidence/${d}/${f}`))];
const hashes = {};
for (const path of paths) hashes[path] = createHash('sha256').update(await readFile(new URL(path, base))).digest('hex');
const result = {checkedAt:new Date().toISOString(),status:'passed',checks:['supplied keyboard success/mistake/recovery at both viewports','first Tab focuses Start; Enter starts','no horizontal overflow at both viewports','demonstration ignores guesses','native pad 2 and 4 buttons activate with Enter','demonstration visibly shows only 2, then 4, then 1, then announces input','static native-control/accessibility/reduced-motion/self-contained checks'],platform:'Darwin 27.0.0 arm64; Google Chrome owned headless; Node v26.7.0; deviceScaleFactor=1; mobile=false',performanceScope:'Each load is one local file navigation after the owned browser exists, awaiting readyState complete. Keyboard-to-two-frame wall duration includes CDP keyDown/keyUp and two animation frames, no CPU or network throttling. Different viewports share a process within each run; each run starts a fresh owned profile. These are local samples, not general performance or cost claims.',performance,hashes,limitations:['Reduced-motion media rule inspected statically, not emulated.','Screen-reader speech and physical touch/mouse input untested.','Exact wall-clock time from demonstration start to input not directly timestamped by this frozen recorder; source schedules 1650 ms and temporal samples observe the progression and readiness before a two-second programmed wait.','Only the declared viewports and installed Chrome were exercised.','Effective model identity, tokens and monetary cost are null.']};
await writeFile(new URL('evidence/check-results.json', base), JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));

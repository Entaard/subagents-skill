import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
import assert from 'node:assert/strict';
const base = new URL('../', import.meta.url);
const read = path => readFile(new URL(path,base),'utf8');
const json = async path => JSON.parse(await read(path));
const hash = async path => createHash('sha256').update(await readFile(new URL(path,base))).digest('hex');
const old = await json('evidence/check-results.json');
for (const [path, expected] of Object.entries(old.hashes)) assert.equal(await hash(path === 'work/index.html' ? 'evidence/original-index.html' : path), expected, 'preservation: '+path);
const repairedSha256 = await hash('work/index.html');
assert.equal(repairedSha256,'3daf1331277df84d6f9abe9e18576a872fc6e564aa6d4e621d815b649cc667c0');
const main = await json('evidence/browser-repair-main/observations.json');
const disabled = await json('evidence/browser-repair-disabled/observations.json');
const focus = await json('evidence/browser-repair-focus/observations.json');
const platform = await json('evidence/platform-metadata.json');
assert.ok(platform.os.product && platform.os.version && platform.os.build && platform.os.architecture && platform.browser.product && platform.browser.installedVersion && platform.runtime.version);
const expected = ['Find your focus.','Watch the pattern.','Correct · 1 of 3','Correct · 2 of 3','Perfect echo.','Watch the pattern.','Not quite · step 1','Watch the pattern.','Correct · 1 of 3','Correct · 2 of 3','Perfect echo.'];
for (const o of main.observations) {
  assert.equal(o.steps.length,11); assert.equal(o.steps[0].focus,'start');
  expected.forEach((t,i)=>assert.ok(o.steps[i].visible.includes(t),t));
  assert.equal(o.metrics.scrollWidth,o.metrics.innerWidth);
}
function state(step) {const value = JSON.parse(step.visible.split('DIAGNOSTIC ')[1]); assert.equal(value.sourceSha256,repairedSha256); return value;}
const terminalObservations=[];
for (const o of disabled.observations) {
  for (const i of [4,8,14]) {
    const s=state(o.steps[i]);assert.equal(s.pads.length,4);assert.ok(s.pads.every(p=>p.disabled===true));
    assert.equal(s.phase,i===8?'Try again':'Complete');
    terminalObservations.push({viewport:o.viewport,step:i,phase:s.phase,pads:s.pads});
  }
  for (const i of [5,6,9,10]) assert.ok(!o.steps[i].focus.startsWith('pad-'));
  for (const i of [2,3,12,13]) assert.ok(state(o.steps[i]).pads.every(p=>p.disabled===false));
}
for (const o of focus.observations) {
  assert.equal(o.steps[2].focus,'pad-1');
  assert.equal(o.steps[3].focus,'start');assert.equal(state(o.steps[3]).phase,'Try again');
  assert.ok(state(o.steps[3]).pads.every(p=>p.disabled===true));
  assert.equal(o.steps[7].focus,'pad-1');
  assert.equal(o.steps[8].focus,'start');assert.equal(state(o.steps[8]).phase,'Complete');
  assert.ok(state(o.steps[8]).pads.every(p=>p.disabled===true));
}
const paths=['work/index.html','evidence/original-index.html','evidence/platform-metadata.json','evidence/outer-independent-review.md','evidence/disabled-probe.html','evidence/make-disabled-probe.mjs','evidence/repair-flow.json','evidence/repair-focus-flow.json',...['browser-repair-main','browser-repair-disabled','browser-repair-focus'].flatMap(d=>['observations.json','viewport-1280x800.png','viewport-390x844.png'].map(p=>'evidence/'+d+'/'+p))];
const hashes={};for(const p of paths)hashes[p]=await hash(p);
const result={observedAt:new Date().toISOString(),status:'coordinator checks passed; independent recheck pending',checks:['All original candidate bytes, raw sources and prior browser observations/screenshots match retained hashes.','Supplied success-mistake-recovery keyboard flow passes at both declared viewports on repaired real candidate.','Actual diagnostic DOM observations show all four pads disabled after success and mistake, enabled again on input.','Terminal Tab events do not focus pads.','Native Enter on Pad 1 transfers focus to Restart after both mistake and success.','Explicit observed platform/browser installation/runtime metadata and sample counts retained.','Both repaired real-candidate screenshots actually viewed; visible focus/outcome styling retained, no horizontal overflow.'],terminalObservations,performance:main.observations.map(o=>({viewport:o.viewport,navigationN:1,keyboardN:o.steps.length,loadWallMs:o.loadWallMs,inputToTwoFramesMs:{min:Math.min(...o.steps.map(s=>s.inputToTwoFramesMs)),max:Math.max(...o.steps.map(s=>s.inputToTwoFramesMs))}})),performanceScope:platform.method,diagnosticLimit:'Disabled/focus probes use a hash-linked derived HTML with appended read-only DOM observers and visible output; they are distinct from the uninstrumented main candidate and their timings/layout are not product performance/layout measurements.',hashes,unknowns:['Independent recheck has not occurred.','Original process browser version was not captured; platform observation applies to installation before repair runs.','Reduced-motion runtime emulation, screen-reader speech and physical touch/mouse untested.','Effective model/effort, tokens and money remain null.']};
await writeFile(new URL('evidence/repair-check-results.json',base),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result,null,2));

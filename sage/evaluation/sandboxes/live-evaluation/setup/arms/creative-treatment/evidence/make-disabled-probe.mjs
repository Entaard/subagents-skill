import {readFile, writeFile} from 'node:fs/promises';
import {createHash} from 'node:crypto';
const base = new URL('../', import.meta.url);
const html = await readFile(new URL('work/index.html', base), 'utf8');
const sourceHash = createHash('sha256').update(html).digest('hex');
const probe = `<script>
(() => {
  const output = document.createElement('output');
  output.id = 'diagnostic-disabled-state';
  const pads = [...document.querySelectorAll('.pad')];
  document.body.append(output);
  function record() {
    output.textContent = 'DIAGNOSTIC ' + JSON.stringify({sourceSha256:'${sourceHash}', pads:pads.map(p=>({id:p.id,disabled:p.disabled})), phase:document.querySelector('#phase').textContent});
  }
  pads.forEach(pad => new MutationObserver(record).observe(pad, {attributes:true, attributeFilter:['disabled']}));
  new MutationObserver(record).observe(document.querySelector('#phase'), {childList:true,subtree:true,characterData:true});
  record();
})();
</script>`;
await writeFile(new URL('evidence/disabled-probe.html', base), html.replace('</body>', probe+'\n</body>'));
console.log(JSON.stringify({source:'work/index.html',sourceSha256:sourceHash,probe:'evidence/disabled-probe.html',method:'Derived diagnostic copy, unchanged candidate code plus an appended output and read-only DOM mutation observers of pad disabled attributes and phase text. Observer does not change game controls, focus or handlers.'}));

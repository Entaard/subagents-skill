// Evaluation-only, owned headless process; never connects to a personal browser.
import {spawn} from 'node:child_process';
import {mkdir, readFile, writeFile} from 'node:fs/promises';
import {resolve, dirname} from 'node:path';
import {pathToFileURL} from 'node:url';
const [htmlArg, flowArg, outputArg] = process.argv.slice(2);
if (!outputArg) throw Error('usage: node browser-harness.mjs HTML FLOW_JSON FRESH_OUTPUT_DIR');
const boundary = resolve(dirname(new URL(import.meta.url).pathname));
const html=resolve(htmlArg), flowPath=resolve(flowArg), output=resolve(outputArg);
for (const path of [html,flowPath,output]) if (!path.startsWith(boundary+'/')) throw Error('path outside setup');
await mkdir(output); // fresh output avoids overwriting evidence
const profile=output+'/owned-profile'; await mkdir(profile);
const flow=JSON.parse(await readFile(flowPath,'utf8'));
const chrome=spawn('/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',[
  '--headless','--disable-gpu','--no-first-run','--no-default-browser-check',
  '--disable-background-networking','--disable-component-update','--disable-sync',
  '--disable-extensions','--disable-default-apps','--metrics-recording-only',
  '--host-resolver-rules=MAP * ~NOTFOUND, EXCLUDE localhost',
  '--remote-debugging-port=0','--remote-debugging-address=127.0.0.1',
  '--user-data-dir='+profile,'about:blank'
],{env:{...process.env,TMPDIR:output},stdio:['ignore','ignore','pipe']});
let stderr='';chrome.stderr.on('data',d=>stderr+=d);
let ws;const observations=[];let sequence=0;const pending=new Map();
const pause=ms=>new Promise(r=>setTimeout(r,ms));
async function send(method,params={}) {
  const id=++sequence;
  return await new Promise((resolve,reject)=>{
    const timer=setTimeout(()=>{pending.delete(id);reject(Error('CDP timeout '+method));},10000);
    pending.set(id,{resolve:v=>{clearTimeout(timer);resolve(v)},reject:e=>{clearTimeout(timer);reject(e)}});
    ws.send(JSON.stringify({id,method,params}));
  });
}
async function evaluate(expression){return (await send('Runtime.evaluate',{expression,returnByValue:true})).result.value;}
try {
  let port;
  for(let i=0;i<100;i++) {try {port=(await readFile(profile+'/DevToolsActivePort','utf8')).split('\n')[0];break;} catch {} await pause(100);}
  if(!port)throw Error('owned Chrome did not expose a debugging endpoint');
  const pages=await (await fetch('http://127.0.0.1:'+port+'/json/list')).json();
  ws=new WebSocket(pages.find(p=>p.type==='page').webSocketDebuggerUrl);
  await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});
  ws.onmessage=e=>{const m=JSON.parse(e.data);const p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(Error(JSON.stringify(m.error))):p.resolve(m.result)}};
  await send('Page.enable'); await send('Runtime.enable');await send('Network.enable');
  await send('Network.setBlockedURLs',{urls:['http://*','https://*','ws://*','wss://*']});
  for(const viewport of flow.viewports) {
    await send('Emulation.setDeviceMetricsOverride',{...viewport,deviceScaleFactor:1,mobile:false});
    const start=performance.now();await send('Page.navigate',{url:pathToFileURL(html).href});
    for(let i=0;i<100;i++){if(await evaluate('document.readyState')==='complete')break;await pause(20);}
    const loadWallMs=performance.now()-start;
    const steps=[];
    for(const action of flow.actions) {
      if(action.wait_ms){await pause(action.wait_ms);continue;}
      const before=performance.now();
      const key=action.key, code=/^[0-9]$/.test(key)?'Digit'+key:/^[a-z]$/.test(key)?'Key'+key.toUpperCase():key, vk=key==='Tab'?9:key==='Enter'?13:key.toUpperCase().charCodeAt(0);
      await send('Input.dispatchKeyEvent',{type:'keyDown',key,code,windowsVirtualKeyCode:vk,...(key==='Enter'?{text:'\r',unmodifiedText:'\r'}:{})});
      await send('Input.dispatchKeyEvent',{type:'keyUp',key,code,windowsVirtualKeyCode:vk});
      await send('Runtime.evaluate',{expression:'new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)))',awaitPromise:true});
      steps.push({key,inputToTwoFramesMs:performance.now()-before,visible:await evaluate('document.body.innerText'),focus:await evaluate('document.activeElement?.id')});
    }
    const shot=await send('Page.captureScreenshot',{format:'png'});
    const screenshot=`viewport-${viewport.width}x${viewport.height}.png`;
    await writeFile(output+'/'+screenshot,Buffer.from(shot.data,'base64'));
    observations.push({viewport,loadWallMs,steps,screenshot,metrics:await evaluate('({scrollWidth:document.documentElement.scrollWidth,innerWidth,nav:performance.getEntriesByType("navigation").map(x=>({duration:x.duration,domContentLoadedEventEnd:x.domContentLoadedEventEnd,loadEventEnd:x.loadEventEnd}))})')});
  }
  await writeFile(output+'/observations.json',JSON.stringify({kind:'direct owned-headless harness observations',scope:'one local file navigation and keyboard sequence per viewport, no throttle; wall includes CDP and frame waits; not population performance or monetary cost',observations},null,2)+'\n');
} catch(error){await writeFile(output+'/failure.json',JSON.stringify({error:String(error)},null,2));throw error;}
finally {if(ws)ws.close();chrome.kill('SIGTERM');await writeFile(output+'/chrome-stderr.txt',stderr);}

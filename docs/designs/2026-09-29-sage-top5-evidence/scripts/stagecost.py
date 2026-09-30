# Dollar attribution per stage for one /sage-promote session.
# Parent $ = the parent model's costUSD (cost-state) x the parent's stage share (stages.py weights).
# Subagent $ = that model's costUSD split across units of that model by weighted tokens; each unit mapped to a stage by its description.
import json,sys,glob,re,collections,subprocess
sess,parent_model,stop=sys.argv[1],sys.argv[2],(sys.argv[3] if len(sys.argv)>3 and sys.argv[3]!='-' else None)
unitmap=json.loads(sys.argv[4])  # description-substring -> stage
cost=None
for l in open(sess+'.jsonl'):
    d=json.loads(l)
    if d.get('type')=='cost-state': cost=d
mu=cost['modelUsage']
def W(u): return u.get('input_tokens',0)+1.25*u.get('cache_creation_input_tokens',0)+0.1*u.get('cache_read_input_tokens',0)+5*u.get('output_tokens',0)
# units
units=[]
for m in glob.glob(sess+'/subagents/*.meta.json'):
    meta=json.load(open(m)); seen={}; model=None
    for l in open(m.replace('.meta.json','.jsonl')):
        r=json.loads(l)
        if r.get('type')=='assistant':
            seen[r['message']['id']]=r['message'].get('usage',{}); model=model or r['message'].get('model')
    w=sum(W(u) for u in seen.values())
    st='other'
    for k,v in unitmap.items():
        if k.lower() in meta['description'].lower(): st=v; break
    units.append((meta['description'],model,w,st))
bymodel=collections.defaultdict(float)
for d,mo,w,st in units: bymodel[mo]+=w
def model_cost(mo):
    for k,v in mu.items():
        if mo and k.split('[')[0]==mo: return v['costUSD']
    return 0.0
stage=collections.defaultdict(float)
sub_same_model_w=bymodel.get(parent_model,0)
for d,mo,w,st in units:
    if mo==parent_model: continue
    c=model_cost(mo)*(w/bymodel[mo] if bymodel[mo] else 0)
    stage[st]+=c
# parent: stages.py share
out=subprocess.run(['python3','/tmp/claude-0/-app-code-subagents-skill/490ef7e5-fac4-4973-aed3-a805887ce97f/scratchpad/promote/stages.py',sess+'.jsonl']+([stop] if stop else []),capture_output=True,text=True).stdout
# parent weight up to stop vs total
pw_all=0;pw_stop=0;seen={}
for l in open(sess+'.jsonl'):
    d=json.loads(l)
    if d.get('type')!='assistant': continue
    seen[d['message']['id']]=(d['timestamp'],d['message'].get('usage',{}))
for ts,u in seen.values():
    pw_all+=W(u)
    if not stop or ts<=stop: pw_stop+=W(u)
pc=model_cost(parent_model)*(pw_stop/pw_all)
for line in out.strip().split('\n'):
    st=line.split()[0]; share=float(re.search(r'costshare=\s*([\d.]+)',line).group(1))/100
    stage['parent:'+st]+=pc*share
tot=sum(stage.values())
print(f"total attributed ${tot:.2f} (session ${cost['totalCostUSD']:.2f}; parent to stop ${pc:.2f})")
groups=collections.defaultdict(float)
for k,v in stage.items(): groups[k.replace('parent:','')]+=v
for k in ['pre','consol','stage0','review','stage1','stage2','stage3','wrap','lane','other']:
    if k in groups: print(f"  {k:7s} ${groups[k]:6.2f} {100*groups[k]/tot:5.1f}%   (subagent part ${stage.get(k,0):.2f})")

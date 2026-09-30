# Approximate stage attribution of PARENT cost in /sage-promote sessions.
# Each parent API message is classified by keywords in its visible text / tool descriptions,
# carrying the previous stage forward when nothing matches. Cost weight in input-price units:
# input 1, cache write 1.25, cache read 0.1, output 5 (Anthropic list ratios). Relative shares only.
import json,sys,re,collections
f=sys.argv[1]; stop=sys.argv[2] if len(sys.argv)>2 else None
rules=[
 ('wrap',   r'pass-end|re-verify every|re-verify all|final invariant|final re-verif|journal lines|print the (final )?(repo )?(git )?diff|sage-promote — 20|report'),
 ('stage3', r'stage.?three|lineup|vendor|identity probe|changelog|stamp|opus 5\.5|pricing|mythos|message\.model|claude --version|release-notes|model docs|snapshot table|alt conf|agent model lines|probe'),
 ('stage2', r'stage.?two|band tag|calibration tag|unrecorded standing|checklist-pricing'),
 ('stage1', r'stage.?one|shared.?ki draft|shared-rule|refuted candidate|refusal recorded|refute stage'),
 ('review', r'ki review|review signals|stale notice|stale|slate|crossing|promotion signals|miss, contradiction'),
 ('stage0', r'stage.?zero|defect|lint|budget|repair|cut-candidate|one-home|second home|degradation gate|carve-out|handover|spot-check|drafts?\b'),
 ('consol', r'consolidat|mint|confirm|use bump|drain|archive|reconcil|snapshot memory|back up|provenance|misses heading|miss notes'),
 ('pre',    r'preflight|root|source-repo|diff template|structural invariant|memory contract|journal grammar|ki index|sage-index|tree contents|read the sage journal|sage.s skill\.md'),
]
seen={}; order=[]; texts=collections.defaultdict(str); ts={}
for l in open(f):
    d=json.loads(l)
    if d.get('type')!='assistant': continue
    if stop and d['timestamp']>stop: break
    m=d['message']; mid=m['id']
    if mid not in seen: order.append(mid); ts[mid]=d['timestamp']
    seen[mid]=m.get('usage',{})
    for c in m.get('content',[]):
        if c.get('type')=='text': texts[mid]+=' '+c['text'][:400]
        elif c.get('type')=='tool_use':
            i=c['input']; texts[mid]+=' '+str(i.get('description',''))+' '+str(i.get('subagent_type',''))+' '+str(i.get('url',''))+' '+str(i.get('prompt',''))[:120]
cur='pre'; agg=collections.defaultdict(lambda:[0,0.0,0])
for mid in order:
    t=texts[mid].lower()
    for st,rx in rules:
        if re.search(rx,t): cur=st; break
    u=seen[mid]
    w=u.get('input_tokens',0)+1.25*u.get('cache_creation_input_tokens',0)+0.1*u.get('cache_read_input_tokens',0)+5*u.get('output_tokens',0)
    a=agg[cur]; a[0]+=1; a[1]+=w; a[2]+=u.get('output_tokens',0)
tot=sum(a[1] for a in agg.values())
for st in ['pre','consol','stage0','review','stage1','stage2','stage3','wrap']:
    a=agg.get(st,[0,0,0])
    print(f"{st:7s} msgs={a[0]:3d} out={a[2]:6d} costshare={100*a[1]/tot:5.1f}%")

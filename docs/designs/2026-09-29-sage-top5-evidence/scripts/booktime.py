import json, sys, re
from datetime import datetime
BOOK = re.compile(r'sage-lint|sage-watch|journal\.md|sage-index|memory/(shared|local)/|sage-ledger|sha256sum|readlink|check-ignore')
def ts(s): return datetime.fromisoformat(s.replace('Z','+00:00')).timestamp()
for path in sys.argv[1:]:
    lines=[]
    for l in open(path):
        try: lines.append(json.loads(l))
        except: pass
    # assistant message id -> (first ts, last ts, tool inputs); tool_result ts by tool_use_id
    msgs={}; order=[]; tr={}
    prev_ts=None; prev_of={}
    for r in lines:
        t=r.get('timestamp')
        if r.get('type')=='assistant':
            m=r['message']; mid=m.get('id')
            if not mid or not t: continue
            if mid not in msgs:
                msgs[mid]={'start_prev':prev_ts,'first':ts(t),'last':ts(t),'tus':[]}; order.append(mid)
            msgs[mid]['last']=ts(t)
            for c in m.get('content') or []:
                if isinstance(c,dict) and c.get('type')=='tool_use': msgs[mid]['tus'].append((c['id'],json.dumps(c.get('input'))))
        elif r.get('type')=='user' and t:
            cont=r.get('message',{}).get('content')
            if isinstance(cont,list):
                for c in cont:
                    if isinstance(c,dict) and c.get('type')=='tool_result' and c.get('tool_use_id') not in tr: tr[c['tool_use_id']]=ts(t)
        if t and r.get('type') in ('user','assistant'): prev_ts=ts(t)
    tot=0; book=0
    for mid in order:
        m=msgs[mid]
        if m['start_prev'] is None or not m['tus']: continue
        gen=m['last']-m['start_prev']
        ends=[tr.get(i) for i,_ in m['tus'] if tr.get(i)]
        exe=(max(ends)-m['last']) if ends else 0
        d=max(gen,0)+max(exe,0)
        if d>1800: continue  # skip idle/user gaps
        tot+=d
        if all(BOOK.search(s) for _,s in m['tus']): book+=d
    print(f"{path.split('/')[-1][:8]} tool-turn time {tot/60:.0f} min; bookkeeping-only turns {book/60:.0f} min ({100*book/max(tot,1):.0f}%)")

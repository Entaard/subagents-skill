import json, sys, re, collections
for path in sys.argv[1:]:
    hits = collections.Counter(); runs=0; samples=[]
    tu_ids = {}
    with open(path) as fh:
        lines = [json.loads(l) for l in fh if l.strip()]
    # map tool_use id -> command
    for r in lines:
        if r.get('type')=='assistant':
            for c in r.get('message',{}).get('content',[]) or []:
                if isinstance(c,dict) and c.get('type')=='tool_use':
                    tu_ids[c['id']] = json.dumps(c.get('input'))
    seen=set()
    for r in lines:
        if r.get('type')!='user': continue
        cont = r.get('message',{}).get('content')
        if not isinstance(cont,list): continue
        for c in cont:
            if not isinstance(c,dict) or c.get('type')!='tool_result': continue
            tid=c.get('tool_use_id')
            if tid in seen: continue
            seen.add(tid)
            cmd = tu_ids.get(tid,'')
            if 'sage-lint' not in cmd: continue
            runs+=1
            txt = c.get('content')
            if isinstance(txt,list): txt=' '.join(x.get('text','') for x in txt if isinstance(x,dict))
            for m in re.finditer(r'sage-lint ([a-z-]+) (\S+)', txt or ''):
                hits[m.group(1)]+=1
                if len(samples)<6: samples.append(m.group(0)[:160])
    print(path.split('/')[-1][:8], 'lint-invoking calls', runs, 'violation lines by check:', dict(hits))
    for s in samples: print('     ', s)

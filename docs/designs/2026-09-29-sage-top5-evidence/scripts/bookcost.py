import json, sys, re
BOOK = re.compile(r'sage-lint|sage-watch|journal\.md|sage-index|memory/(shared|local)/|sage-ledger|sha256sum|readlink|check-ignore')
for path in sys.argv[1:]:
    recs={}; order=[]
    for l in open(path):
        try: r=json.loads(l)
        except: continue
        if r.get('type')!='assistant': continue
        m=r.get('message',{}); mid=m.get('id')
        if not mid: continue
        if mid not in recs: order.append(mid)
        recs[mid]=m
    tot_out=0; book_out=0; nb=0; n=0; api_book_ms=0
    for mid in order:
        m=recs[mid]; u=m.get('usage') or {}
        o=u.get('output_tokens') or 0
        tot_out+=o; n+=1
        tus=[json.dumps(c.get('input')) for c in (m.get('content') or []) if isinstance(c,dict) and c.get('type')=='tool_use']
        if tus and all(BOOK.search(t) for t in tus):
            book_out+=o; nb+=1
    print(f"{path.split('/')[-1][:8]} msgs={n} out={tot_out} bookkeeping-only msgs={nb} ({100*nb/max(n,1):.0f}%) out={book_out} ({100*book_out/max(tot_out,1):.0f}%)")

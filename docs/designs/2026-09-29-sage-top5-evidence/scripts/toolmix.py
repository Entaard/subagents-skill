import json, sys, re, collections
def load(path):
    recs = {}
    order = []
    with open(path) as fh:
        for line in fh:
            try: r = json.loads(line)
            except: continue
            if r.get('type') != 'assistant': continue
            m = r.get('message', {})
            mid = m.get('id')
            if not mid: continue
            if mid not in recs: order.append(mid)
            recs[mid] = m
    return [recs[i] for i in order]
cats = [
 ('lint', r'sage-lint'),
 ('watch/status', r'sage-watch'),
 ('journal', r'journal\.md'),
 ('index/KI', r'sage-index|memory/(shared|local)/'),
 ('skill-read', r'skills/sage/(references|SKILL)|sage-claude/(references|SKILL)'),
 ('ledger', r'sage-ledger'),
 ('sha256/resume', r'sha256sum'),
 ('readlink', r'readlink'),
 ('check-ignore', r'check-ignore'),
]
for path in sys.argv[1:]:
    msgs = load(path)
    tus = []
    for m in msgs:
        for c in m.get('content', []) or []:
            if isinstance(c, dict) and c.get('type') == 'tool_use':
                tus.append((c.get('name'), json.dumps(c.get('input'))))
    tot = len(tus); totc = sum(len(s) for _, s in tus)
    out = collections.OrderedDict()
    assigned = [None]*tot
    for name, pat in cats:
        n=0; ch=0
        for i,(tn, s) in enumerate(tus):
            if re.search(pat, s):
                n+=1; ch+=len(s)
                if assigned[i] is None: assigned[i]=name
        out[name]=(n,ch)
    book = sum(1 for a in assigned if a in ('lint','watch/status','journal','index/KI','ledger','sha256/resume','readlink','check-ignore'))
    bookc = sum(len(tus[i][1]) for i,a in enumerate(assigned) if a in ('lint','watch/status','journal','index/KI','ledger','sha256/resume','readlink','check-ignore'))
    names = collections.Counter(tn for tn,_ in tus)
    print(path.split('/')[-1][:8], f"msgs={len(msgs)} tool_uses={tot} chars={totc}", dict(names))
    for k,(n,ch) in out.items(): print(f"   {k:14s} {n:4d} calls {ch:7d} chars")
    print(f"   BOOKKEEPING(any of lint/watch/journal/index/ledger/sha/readlink) {book} calls ({100*book/max(tot,1):.0f}%) {bookc} chars ({100*bookc/max(totc,1):.0f}%)")

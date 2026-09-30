#!/usr/bin/env python3
"""Wall-clock analysis of /sage parent transcripts.

Usage: python3 analyze.py [session-prefix ...] [--json out.json]

For each session:
  * finds the sage run window (first /sage invocation -> end of the turn that
    appended the journal `run` line, or the turn that stopped the watchdog);
  * walks parent records in file order and assigns every gap between two
    consecutive records to one state:
      gen:<cat>        parent model generation (API call in flight), attributed
                       to the categories of the tool calls that message emits
      tool:<cat>       waiting on a tool the parent called
      idle:agents      parent turn ended, background agents still running
      idle:human       parent turn ended, next input is a human prompt
      idle:bg          parent turn ended, waiting on a background Bash
      compaction       gap that ends at a compact_boundary record
      api-stall        gap that ends at a synthetic API-error record
  * attributes each deduplicated API message's output / thinking tokens to the
    categories of its tool calls (equal split per tool call);
  * fits gen_time = a + b * output_tokens per session (least squares) to split
    per-call latency from per-token generation time;
  * splits the run into phases (S1-2, S3-4, S5, S6) by ledger-write and
    review-dispatch timestamps;
  * lists every subagent segment (first->last record, split at each new parent
    prompt, e.g. a SendMessage resume) with its model.
"""
import glob
import json
import re
import sys
from collections import defaultdict, Counter
from datetime import datetime

DEFAULT = ['a58bd85c', '61de7190', 'e4bebf20', '54dd10c5', 'd4096102', '9832cdf3', 'c81599fd']
REVIEW_TYPES = {'verifier', 'verifier-alt', 'refuter-alt'}


def ts(s):
    return datetime.fromisoformat(s.replace('Z', '+00:00')).timestamp()


def load(prefix):
    f = glob.glob(f'/root/.claude/projects/*/{prefix}*.jsonl')[0]
    return f, [json.loads(l) for l in open(f)]


# ---------------------------------------------------------------- categories
def bash_cat(cmd):
    """Category of one shell command (or one chunk of one).
    Installed-skill paths (~/.claude/skills/sage) are bookkeeping; the sage SOURCE
    repo (sage-claude/, claude-skills/, --corpus lint) is task work in the runs whose
    task is the skill itself (d4096102, 9832cdf3)."""
    c = cmd
    if 'sage-ledger' in c or '.claude/plans' in c:
        return 'ledger'
    if 'sage-claude/' in c or 'claude-skills/' in c or 'claude-agents' in c or '--corpus' in c:
        return 'task-other'
    if 'END RUN BLOCK' in c:
        return 'skill-read'
    if 'sage-lint' in c:
        return 'lint'
    if 'sage-watch' in c:
        return 'watch'
    if 'journal.md' in c or 'sage-index' in c:
        return 'journal/memory'
    if re.search(r'skills/(sage|diff-review|clean-code|concurrency)|agents/[a-z-]+\.md', c):
        return 'skill-read'
    if re.search(r'\b(go (test|build|vet)|gofmt|dotnet\b|npm (test|run)|pytest|make\b|bash -n|shellcheck|install\.sh)', c):
        return 'test/build'
    if re.search(r'(^|[;&|(]\s*)git\b', c):
        return 'git'
    return 'task-other'


def tool_cat(name, inp):
    if name == 'Bash':
        return 'bash:' + bash_cat(inp.get('command', ''))
    if name in ('Edit', 'Write', 'Read', 'NotebookEdit'):
        p = inp.get('file_path', '')
        if 'sage-ledger' in p:
            return 'bash:ledger'
        if 'journal.md' in p:
            return 'bash:journal/memory'
        if '/skills/' in p:
            return 'bash:skill-read'
        return name.lower() + ':task'
    if name in ('Monitor',):
        return 'watch'
    if name == 'TaskStop':
        return 'watch' if 'task_id' in inp and not str(inp.get('task_id', '')).startswith('a') else 'agent-ctl'
    if name in ('Agent', 'Task'):
        return 'agent-dispatch'
    if name == 'SendMessage':
        return 'agent-steer'
    if name == 'TaskOutput':
        return 'agent-wait(TaskOutput)'
    if name == 'Skill':
        return 'skill-read'
    return 'task-tool:' + name


BOOKKEEPING = {'bash:ledger', 'bash:lint', 'bash:watch', 'watch', 'bash:journal/memory', 'bash:skill-read', 'skill-read'}


def is_bookkeeping(cat):
    return cat in BOOKKEEPING


# ---------------------------------------------------------------- prompt kinds
def prompt_kind(text):
    t = text.lstrip()
    if 'This session is being continued from a previous conversation' in t:
        return 'compact-summary'
    if t.startswith('Another Claude session sent a message') or '<agent-message' in t[:200]:
        return 'agent-message'
    if t.startswith('<task-notification>'):
        return 'task-notification'
    if t.startswith('<system-reminder>') or t.startswith('Base directory for this skill') or t.startswith('<local-command') \
            or t.startswith('<command-name>/model') or t.startswith('<command-name>/effort') or t.startswith('<command-name>/clear') \
            or t.startswith('<command-name>/login') or t.startswith('Caveat'):
        return 'meta'
    return 'human'


def user_texts(r):
    c = r['message']['content']
    if isinstance(c, str):
        return [c]
    return [x.get('text', '') for x in c if x.get('type') == 'text']


# ---------------------------------------------------------------- run window
def run_window(recs):
    start = None
    journal_idx = None
    stop_idx = None
    for i, r in enumerate(recs):
        if r.get('type') == 'user' and start is None:
            for t in user_texts(r):
                if '<command-name>/sage</command-name>' in t:
                    start = i
        if r.get('type') == 'assistant' and start is not None:
            for x in r['message']['content']:
                if x['type'] == 'tool_use':
                    cmd = x['input'].get('command', '') if isinstance(x['input'], dict) else ''
                    if 'journal.md' in cmd and '>>' in cmd:
                        journal_idx = i
                    if x['name'] == 'TaskStop':
                        stop_idx = i
    anchor = max([k for k in (journal_idx, stop_idx) if k is not None], default=len(recs) - 1)
    end = len(recs) - 1
    for i in range(anchor, len(recs)):
        r = recs[i]
        if r.get('type') == 'system' and r.get('subtype') == 'turn_duration':
            end = i
            break
    return start, end


# ---------------------------------------------------------------- subagents
def subagent_segments(session_file):
    d = session_file[:-6] + '/subagents/'
    out = []
    for m in sorted(glob.glob(d + 'agent-*.meta.json')):
        meta = json.load(open(m))
        j = m.replace('.meta.json', '.jsonl')
        recs = [json.loads(l) for l in open(j)]
        aid = m.split('agent-')[-1].split('.meta')[0]
        models = Counter(r['message'].get('model') for r in recs if r.get('type') == 'assistant')
        model = models.most_common(1)[0][0] if models else None
        segs = []
        cur = None
        prev_was_prompt = False
        for r in recs:
            if 'timestamp' not in r:
                continue
            t = ts(r['timestamp'])
            new_prompt = False
            if r.get('type') == 'user':
                c = r['message']['content']
                if isinstance(c, str) or not any(x.get('type') == 'tool_result' for x in c):
                    new_prompt = True
            if new_prompt and cur is not None and not prev_was_prompt and t - cur[1] > 30:
                segs.append(cur)
                cur = None
            if cur is None:
                cur = [t, t]
            cur[1] = max(cur[1], t)
            prev_was_prompt = new_prompt
        if cur:
            segs.append(cur)
        # output tokens (dedup)
        per = {}
        for r in recs:
            if r.get('type') == 'assistant':
                u = r['message'].get('usage') or {}
                per[r['message'].get('id')] = u.get('output_tokens', 0)
        out.append(dict(id=aid, type=meta.get('agentType'), desc=meta.get('description', ''), model=model,
                        segs=segs, out_tokens=sum(per.values()), calls=len(per)))
    return out


# ---------------------------------------------------------------- main pass
def analyze(prefix):
    f, recs = load(prefix)
    s_idx, e_idx = run_window(recs)
    R = recs[s_idx:e_idx + 1]
    t0 = ts(R[0]['timestamp'])
    t_end = ts(R[-1]['timestamp'])
    subs = subagent_segments(f)
    agent_ivals = [(a, s[0], s[1]) for a in subs for s in a['segs']]

    def agents_running(ta, tb):
        return any(s < tb and e > ta for _, s, e in agent_ivals)

    buckets = defaultdict(float)          # state -> seconds
    tokens = defaultdict(float)           # cat -> output tokens
    think = defaultdict(float)            # cat -> thinking tokens
    ncalls = Counter()                    # cat -> tool calls
    vis_chars = defaultdict(int)          # cat -> tool_use input chars
    api_msgs = {}                         # msg id -> dict
    outstanding = {}                      # tool_use id -> (cat, t)
    tu_cat = {}
    state = 'gen'                         # gen | idle
    last_t = t0
    cur_msg = None
    pending_gen = 0.0                     # gen seconds not yet attributed to a message
    phase_marks = {}
    first_ledger = None
    first_review = None
    last_agent_result = None
    tu_times = []
    compaction_ms = 0
    n_compact = 0
    api_errors = []
    turns = []
    msg_gen = defaultdict(float)
    idle_log = []

    def msg_cats(mid):
        m = api_msgs.get(mid)
        if not m or not m['cats']:
            return ['text']
        return m['cats']

    for r in R:
        typ = r.get('type')
        if 'timestamp' not in r or typ in ('attachment', 'queue-operation', 'file-history-snapshot', 'file-history-delta'):
            continue
        t = ts(r['timestamp'])
        gap = max(0.0, t - last_t)
        # ---- classify the gap that ends at this record
        is_err = typ == 'assistant' and r['message'].get('model') == '<synthetic>'
        is_cb = typ == 'system' and r.get('subtype') == 'compact_boundary'
        if is_cb:
            buckets['compaction'] += gap
        elif is_err:
            buckets['api-stall/error'] += gap
        elif outstanding:
            cat = min(outstanding.values(), key=lambda v: v[1])[0]
            buckets['tool:' + cat] += gap
        elif state == 'idle':
            kind = None
            if typ == 'user':
                kinds = [prompt_kind(x) for x in user_texts(r)]
                kind = kinds[0] if kinds else None
            if agents_running(last_t, t) or kind in ('agent-message',):
                k = 'idle:agents'
            elif kind == 'human':
                k = 'idle:human'
            elif kind == 'task-notification':
                k = 'idle:bg'
            else:
                k = 'idle:other'
            buckets[k] += gap
            idle_log.append((last_t - t0, gap, k))
        else:
            if typ == 'assistant':
                mid = r['message'].get('id')
                msg_gen[mid] += gap + pending_gen
                pending_gen = 0.0
            else:
                pending_gen += gap   # e.g. between end_turn text and turn_duration; folded into next msg
        last_t = t

        # ---- update state from this record
        if typ == 'assistant' and not is_err:
            m = r['message']
            mid = m.get('id')
            u = m.get('usage') or {}
            d = api_msgs.setdefault(mid, dict(out=0, think=0, cats=[], t_first=t, t_last=t))
            d['out'] = max(d['out'], u.get('output_tokens', 0) or 0)
            d['think'] = max(d['think'], ((u.get('output_tokens_details') or {}).get('thinking_tokens', 0) or 0))
            d['t_last'] = t
            for x in m['content']:
                if x['type'] == 'tool_use':
                    inp = x['input'] if isinstance(x['input'], dict) else {}
                    cat = tool_cat(x['name'], inp)
                    if x['id'] not in tu_cat:
                        tu_cat[x['id']] = cat
                        d['cats'].append(cat)
                        ncalls[cat] += 1
                        vis_chars[cat] += len(json.dumps(inp))
                        tu_times.append((t, x['name'], cat, inp))
                    outstanding[x['id']] = (cat, t)
                    if cat == 'bash:ledger' and first_ledger is None and (
                            ('cat >' in inp.get('command', '') and 'sage-ledger' in inp.get('command', '')) or x['name'] == 'Write'
                            or 'sage-ledger' in inp.get('command', '')):
                        first_ledger = t
                    if x['name'] in ('Agent', 'Task') and inp.get('subagent_type') in REVIEW_TYPES \
                            and 'probe' not in inp.get('description', '').lower() and first_review is None:
                        first_review = t
                elif x['type'] == 'text':
                    vis_chars['text'] += len(x.get('text', ''))
            if m.get('stop_reason') in ('end_turn', 'stop_sequence') and not outstanding:
                pass
        elif is_err:
            api_errors.append((t - t0, json.dumps(r['message']['content'])[:120]))
        elif typ == 'user':
            c = r['message']['content']
            if not isinstance(c, str):
                for x in c:
                    if x.get('type') == 'tool_result':
                        outstanding.pop(x.get('tool_use_id'), None)
            kinds = [prompt_kind(x) for x in user_texts(r)]
            if any(k in ('agent-message', 'task-notification') for k in kinds):
                txt = ' '.join(user_texts(r))
                if '<agent-message' in txt or re.search(r'<task-id>a[0-9a-f]{16}', txt):
                    last_agent_result = t
            if kinds and not all(k == 'meta' for k in kinds):
                state = 'gen'
            if 'compact-summary' in kinds:
                state = 'gen'
        elif typ == 'system' and r.get('subtype') == 'turn_duration':
            state = 'idle'
            outstanding.clear()
            turns.append((t - t0, r.get('durationMs'), r.get('pendingBackgroundAgentCount')))
        elif is_cb:
            n_compact += 1
            compaction_ms += (r.get('compactMetadata') or {}).get('durationMs', 0) or 0

    # attribute generation time and tokens to categories
    gen_by_cat = defaultdict(float)
    for mid, d in api_msgs.items():
        cats = d['cats'] or ['text']
        g = msg_gen.get(mid, 0.0)
        for c in cats:
            gen_by_cat[c] += g / len(cats)
            tokens[c] += d['out'] / len(cats)
            think[c] += d['think'] / len(cats)
        buckets['gen'] += g
    buckets['gen'] += pending_gen

    # least-squares gen_time = a + b*tokens over messages with 0 < gen < 600s
    pts = [(d['out'], msg_gen[mid]) for mid, d in api_msgs.items() if 0 < msg_gen.get(mid, 0) < 600 and d['out'] > 0]
    n = len(pts)
    if n > 2:
        mx = sum(p[0] for p in pts) / n
        my = sum(p[1] for p in pts) / n
        sxx = sum((p[0] - mx) ** 2 for p in pts)
        sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
        b = sxy / sxx if sxx else 0
        a = my - b * mx
    else:
        a = b = 0

    # phases (mechanical definition, see report):
    #   S1-2  run start -> first non-probe Agent dispatch
    #   S3-4  first dispatch -> last result of the first wave (dispatches within 6 min of the first)
    #   S5    end of first wave -> last agent result of the run
    #   S6    last agent result -> run end
    disp = [(tt, inp) for (tt, name, c, inp) in tu_times if name in ('Agent', 'Task')
            and 'probe' not in inp.get('description', '').lower()]
    first_disp = disp[0][0] if disp else t_end
    wave_ids = {a['id'] for a in subs for s0 in a['segs'][:1] if first_disp - 5 <= s0[0] <= first_disp + 360}
    wave_end = max([s['segs'][0][1] for s in subs if s['id'] in wave_ids] or [first_disp])
    last_res = max([seg[1] for s in subs for seg in s['segs']
                    if 'probe' not in s['desc'].lower()] or [wave_end])
    last_res = min(max(last_res, wave_end), t_end)
    bounds = [('S1-2 decompose/plan (+inline work)', t0, first_disp), ('S3-4 brief/first wave', first_disp, wave_end),
              ('S5 triage/fix/re-review', wave_end, last_res), ('S6 close/record', last_res, t_end + 1)]
    phase = {}
    for name, a0, a1 in bounds:
        mids = [mid for mid, d in api_msgs.items() if a0 <= d['t_last'] < a1]
        ph_tools = Counter(c for (tt, _, c, _) in tu_times if a0 <= tt < a1)
        g = sum(msg_gen.get(m, 0) for m in mids)
        phase[name] = dict(min=(a1 - a0) / 60, gen_min=g / 60, calls=len(mids), out=sum(api_msgs[m]['out'] for m in mids),
                           think=sum(api_msgs[m]['think'] for m in mids),
                           tools=sum(ph_tools.values()),
                           book=sum(v for k, v in ph_tools.items() if is_bookkeeping(k)),
                           book_out=sum(api_msgs[m]['out'] * sum(1 for c in api_msgs[m]['cats'] if is_bookkeeping(c)) /
                                        max(1, len(api_msgs[m]['cats'])) for m in mids))

    _msg_gen = {k: v for k, v in msg_gen.items()}
    return dict(msg_gen=_msg_gen, session=prefix, file=f, start=R[0]['timestamp'], end=R[-1]['timestamp'], wall_min=(t_end - t0) / 60,
                buckets={k: v / 60 for k, v in buckets.items()}, gen_by_cat={k: v / 60 for k, v in gen_by_cat.items()},
                tokens=dict(tokens), think=dict(think), ncalls=dict(ncalls), vis_chars=dict(vis_chars),
                api_calls=len(api_msgs), out_total=sum(d['out'] for d in api_msgs.values()),
                think_total=sum(d['think'] for d in api_msgs.values()), fit=(a, b, n),
                phase=phase, n_compact=n_compact, compaction_min=compaction_ms / 60000,
                api_errors=api_errors, turns=turns, idle_log=idle_log,
                subs=[dict(id=s['id'][:8], type=s['type'], desc=s['desc'][:60], model=s['model'], out=s['out_tokens'],
                           calls=s['calls'],
                           segs=[((a0 - t0) / 60, (a1 - a0) / 60) for a0, a1 in s['segs']]) for s in subs],
                effort=Counter(r.get('effort') for r in R if r.get('type') == 'assistant').most_common(1)[0][0],
                model=Counter(r['message'].get('model') for r in R if r.get('type') == 'assistant').most_common(1)[0][0])


def fmt(res):
    o = []
    p = o.append
    p(f"## {res['session']}  model={res['model']} effort={res['effort']}  run {res['start']} -> {res['end']}  wall={res['wall_min']:.1f} min")
    p(f"API calls={res['api_calls']} out={res['out_total']:,} thinking={res['think_total']:,} "
      f"fit: gen_s = {res['fit'][0]:.1f} + {res['fit'][1]*1000:.1f}ms*tok (n={res['fit'][2]})  compactions={res['n_compact']} ({res['compaction_min']:.1f} min)")
    p('buckets (min): ' + ', '.join(f"{k}={v:.1f}" for k, v in sorted(res['buckets'].items(), key=lambda kv: -kv[1])))
    p('gen by cat (min): ' + ', '.join(f"{k}={v:.1f}" for k, v in sorted(res['gen_by_cat'].items(), key=lambda kv: -kv[1])))
    p('calls by cat: ' + ', '.join(f"{k}={v}" for k, v in sorted(res['ncalls'].items(), key=lambda kv: -kv[1])))
    p('out tokens by cat: ' + ', '.join(f"{k}={v/1000:.1f}k" for k, v in sorted(res['tokens'].items(), key=lambda kv: -kv[1])))
    for k, v in res['phase'].items():
        p(f"  phase {k}: {v['min']:.1f} min (parent gen {v['gen_min']:.1f}), api={v['calls']}, out={v['out']/1000:.1f}k, think={v['think']/1000:.1f}k, tools={v['tools']} (bookkeeping {v['book']}, ~{v['book_out']/1000:.1f}k out)")
    for s in res['subs']:
        segs = '; '.join(f"@{a:.1f}m +{b:.1f}m" for a, b in s['segs'])
        p(f"  sub {s['id']} {s['type']:<13} {str(s['model']):<22} out={s['out']/1000:.1f}k calls={s['calls']} {segs} | {s['desc']}")
    if res['api_errors']:
        p('  api errors: ' + '; '.join(f"@{a/60:.1f}m {b}" for a, b in res['api_errors']))
    big = [x for x in res['idle_log'] if x[1] > 60]
    p('  idle gaps >1m: ' + '; '.join(f"@{a/60:.1f}m {b/60:.1f}m {k}" for a, b, k in big))
    return '\n'.join(o)


# =====================================================================
# Second pass: waits by awaited agent, bookkeeping by chunked chars,
# review rounds, post-compaction recovery.
# =====================================================================
WRITER_RE = re.compile(r'(?i)^(writer|fix |consolidated .*fix round)')
PROBE_RE = re.compile(r'(?i)probe')


def role_of(sub, seg_idx):
    d = sub['desc']
    if PROBE_RE.search(d):
        return 'probe'
    if sub['type'] == 'implementer' or WRITER_RE.search(d):
        return 'writer'
    if sub['type'] == 'explorer':
        return 'scout'
    return 'review-r1' if seg_idx == 0 else 'review-steer'


HEREDOC_RE = re.compile(r"<<-?\s*['\"]?([A-Za-z_]+)['\"]?")


def chunk_command(cmd):
    """Split a Bash command into (category, chars) pieces. A heredoc body goes to
    the category of the line that opens it; other lines are split on ; && ||."""
    pieces = []
    lines = cmd.split('\n')
    i = 0
    while i < len(lines):
        line = lines[i]
        m = HEREDOC_RE.search(line)
        if m:
            tag = m.group(1)
            body = []
            j = i + 1
            while j < len(lines) and lines[j].strip() != tag:
                body.append(lines[j])
                j += 1
            block = line + '\n' + '\n'.join(body)
            head = line
            # python heredocs name their target inside the body
            target = block if 'python' in head else head
            cat = bash_cat(target)
            if cat == 'task-other' and 'python' in head:
                cat = bash_cat('\n'.join(body[:15]))
            pieces.append((cat, len(block)))
            i = j + 1
            continue
        for part in re.split(r'\s*(?:;|&&|\|\|)\s*', line):
            if part.strip():
                pieces.append((bash_cat(part), len(part)))
        i += 1
    return pieces


def second_pass(prefix, msg_gen=None):
    msg_gen = msg_gen or {}
    f, recs = load(prefix)
    s_idx, e_idx = run_window(recs)
    R = recs[s_idx:e_idx + 1]
    t0 = ts(R[0]['timestamp'])
    subs = subagent_segments(f)
    by_id = {s['id']: s for s in subs}

    # ---- waits: idle gap -> the agent whose report ended it
    waits = defaultdict(float)
    wait_rows = []
    last_t = t0
    state = 'gen'
    outstanding = set()
    taskoutput_wait = 0.0
    for r in R:
        typ = r.get('type')
        if 'timestamp' not in r or typ in ('attachment', 'queue-operation', 'file-history-snapshot', 'file-history-delta'):
            continue
        t = ts(r['timestamp'])
        gap = max(0.0, t - last_t)
        if state == 'idle' and typ == 'user':
            txt = ' '.join(user_texts(r))
            m = re.search(r'agent-message from="(a[0-9a-f]+)"', txt) or re.search(r'<task-id>(a[0-9a-f]{16})</task-id>', txt)
            if m and m.group(1) in by_id:
                sub = by_id[m.group(1)]
                seg_idx = 0
                for k, (a0, a1) in enumerate(sub['segs']):
                    if a0 <= t + 5:
                        seg_idx = k
                role = role_of(sub, seg_idx)
                waits[role] += gap
                wait_rows.append(((last_t - t0) / 60, gap / 60, role, sub['type'], sub['model'], sub['desc'][:50]))
            elif prompt_kind(txt) == 'human':
                waits['human'] += gap
            else:
                waits['other'] += gap
        if typ == 'assistant':
            for x in r['message']['content']:
                if x['type'] == 'tool_use' and x['name'] == 'TaskOutput':
                    outstanding.add(x['id'])
        if typ == 'user' and not isinstance(r['message']['content'], str):
            for x in r['message']['content']:
                if x.get('type') == 'tool_result' and x.get('tool_use_id') in outstanding:
                    taskoutput_wait += gap
                    outstanding.discard(x.get('tool_use_id'))
        if typ == 'system' and r.get('subtype') == 'turn_duration':
            state = 'idle'
        elif typ == 'user':
            state = 'gen'
        last_t = t
    if taskoutput_wait:
        waits['writer(TaskOutput block)'] += taskoutput_wait

    # ---- bookkeeping by chunked visible chars, and tokens apportioned by chars
    msgs = {}
    order = []
    for r in R:
        if r.get('type') != 'assistant' or r['message'].get('model') == '<synthetic>':
            continue
        m = r['message']
        mid = m['id']
        if mid not in msgs:
            msgs[mid] = dict(out=0, think=0, pieces=[], seen=set())
            order.append(mid)
        d = msgs[mid]
        u = m.get('usage') or {}
        d['out'] = max(d['out'], u.get('output_tokens', 0) or 0)
        d['think'] = max(d['think'], ((u.get('output_tokens_details') or {}).get('thinking_tokens', 0) or 0))
        for x in m['content']:
            key = x.get('id') or (x['type'], len(x.get('text', '')))
            if key in d['seen']:
                continue
            d['seen'].add(key)
            if x['type'] == 'text':
                d['pieces'].append(('text', len(x.get('text', ''))))
            elif x['type'] == 'tool_use':
                inp = x['input'] if isinstance(x['input'], dict) else {}
                if x['name'] == 'Bash':
                    d['pieces'].extend(chunk_command(inp.get('command', '')))
                else:
                    c = tool_cat(x['name'], inp)
                    c = c.replace('bash:', '')
                    d['pieces'].append((c, len(json.dumps(inp))))
    chars = defaultdict(int)
    tok = defaultdict(float)
    gen = defaultdict(float)
    think_tok = defaultdict(float)
    for mid in order:
        d = msgs[mid]
        tot = sum(c for _, c in d['pieces']) or 1
        g = msg_gen.get(mid, 0.0)
        if not d['pieces']:
            gen['(empty)'] += g
            tok['(empty)'] += d['out']
            continue
        for cat, c in d['pieces']:
            chars[cat] += c
            tok[cat] += d['out'] * c / tot
            think_tok[cat] += d['think'] * c / tot
            gen[cat] += g * c / tot

    # ---- review rounds: group review dispatches / steers within 4 min
    events = []
    for r in R:
        if r.get('type') != 'assistant':
            continue
        for x in r['message']['content']:
            if x['type'] == 'tool_use' and x['name'] in ('Agent', 'Task', 'SendMessage'):
                inp = x['input']
                desc = inp.get('description') or inp.get('summary') or ''
                if PROBE_RE.search(desc):
                    continue
                if x['name'] != 'SendMessage' and (inp.get('subagent_type') == 'implementer' or WRITER_RE.search(desc)
                                                   or inp.get('subagent_type') == 'explorer'):
                    kind = 'writer' if inp.get('subagent_type') != 'explorer' else 'scout'
                else:
                    kind = 'review'
                events.append((ts(r['timestamp']), x['name'], kind, desc[:45], x['id']))
    seen_ids = set()
    ev2 = []
    for e in events:
        if e[4] in seen_ids:
            continue
        seen_ids.add(e[4])
        ev2.append(e)
    rounds = []
    for e in ev2:
        if e[2] != 'review':
            rounds.append([e])
            continue
        if rounds and rounds[-1][0][2] == 'review' and e[0] - rounds[-1][-1][0] < 240:
            rounds[-1].append(e)
        else:
            rounds.append([e])

    # ---- post-compaction recovery: calls/time from summary to first task-work call
    recov = []
    i = 0
    while i < len(R):
        r = R[i]
        if r.get('type') == 'user' and any(prompt_kind(x) == 'compact-summary' for x in user_texts(r)):
            tstart = ts(r['timestamp'])
            ncalls = 0
            j = i + 1
            tend = None
            while j < len(R):
                q = R[j]
                if q.get('type') == 'assistant':
                    tus = [x for x in q['message']['content'] if x['type'] == 'tool_use']
                    for x in tus:
                        inp = x['input'] if isinstance(x['input'], dict) else {}
                        cat = tool_cat(x['name'], inp)
                        ncalls += 1
                        if not is_bookkeeping(cat):
                            tend = ts(q['timestamp'])
                            break
                    if tend:
                        break
                if q.get('type') == 'system' and q.get('subtype') in ('compact_boundary', 'turn_duration'):
                    tend = ts(q['timestamp'])
                    break
                j += 1
            recov.append(((tstart - t0) / 60, ncalls - 1 if tend else ncalls, ((tend or tstart) - tstart) / 60))
        i += 1

    return dict(waits={k: v / 60 for k, v in waits.items()}, wait_rows=wait_rows,
                chars=dict(chars), tok=dict(tok), gen={k: v / 60 for k, v in gen.items()}, think_tok=dict(think_tok),
                rounds=[[((e[0] - t0) / 60, e[1], e[2], e[3]) for e in rd] for rd in rounds],
                recov=recov)


def fmt2(prefix, res):
    o = [f"### {prefix} (second pass)"]
    o.append('waits by awaited role (min): ' + ', '.join(f"{k}={v:.1f}" for k, v in sorted(res['waits'].items(), key=lambda kv: -kv[1])))
    tot = sum(res['tok'].values()) or 1
    o.append('parent output tokens by chunk category: ' + ', '.join(
        f"{k}={v/1000:.1f}k({100*v/tot:.0f}%)" for k, v in sorted(res['tok'].items(), key=lambda kv: -kv[1])))
    o.append('parent gen minutes by chunk category: ' + ', '.join(
        f"{k}={v:.1f}" for k, v in sorted(res['gen'].items(), key=lambda kv: -kv[1]) if v >= 0.1))
    ct = sum(res['chars'].values()) or 1
    o.append('visible chars by chunk category: ' + ', '.join(
        f"{k}={v/1000:.1f}k({100*v/ct:.0f}%)" for k, v in sorted(res['chars'].items(), key=lambda kv: -kv[1]) if v >= 500))
    for k, rd in enumerate(res['rounds']):
        o.append(f"  dispatch-group {k+1} @{rd[0][0]:.1f}m: " + '; '.join(f"{e[1][0]}:{e[2]}:{e[3]}" for e in rd))
    if res['recov']:
        o.append(f"  post-compaction recovery: n={len(res['recov'])} calls-before-task-work={sum(x[1] for x in res['recov'])} "
                 f"minutes={sum(x[2] for x in res['recov']):.1f}")
    return '\n'.join(o)


# =====================================================================
# Third pass: per-subagent timeline (generation vs tool vs other) and a
# per-model token-rate fit. Run with --subagents.
# =====================================================================
def subagent_timeline(path):
    recs = [json.loads(l) for l in open(path)]
    last = None
    outstanding = {}
    gen = tool = other = 0.0
    tool_by = defaultdict(float)
    per = {}
    msg_gen = defaultdict(float)
    for r in recs:
        if 'timestamp' not in r or r.get('type') not in ('assistant', 'user'):
            continue
        t = ts(r['timestamp'])
        if last is None:
            last = t
        gap = max(0.0, t - last)
        if outstanding:
            nm = min(outstanding.values(), key=lambda v: v[1])[0]
            tool += gap
            tool_by[nm] += gap
        elif r.get('type') == 'assistant':
            gen += gap
            msg_gen[r['message'].get('id')] += gap
        else:
            other += gap
        last = t
        if r.get('type') == 'assistant':
            m = r['message']
            u = m.get('usage') or {}
            per[m.get('id')] = u.get('output_tokens', 0) or 0
            for x in m['content']:
                if x['type'] == 'tool_use':
                    nm = x['name']
                    if nm == 'Bash':
                        nm = 'Bash:' + bash_cat(x['input'].get('command', ''))
                    outstanding[x['id']] = (nm, t)
        else:
            c = r['message']['content']
            if not isinstance(c, str):
                for x in c:
                    if x.get('type') == 'tool_result':
                        outstanding.pop(x.get('tool_use_id'), None)
    pts = [(per[k], msg_gen[k]) for k in per if 0 < msg_gen.get(k, 0) < 600 and per[k] > 0]
    return dict(gen=gen / 60, tool=tool / 60, other=other / 60, tool_by={k: v / 60 for k, v in tool_by.items()},
                out=sum(per.values()), calls=len(per), pts=pts)


def fit(pts):
    n = len(pts)
    if n < 3:
        return None
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    b = sxy / sxx if sxx else 0
    return my - b * mx, b, n


def subagent_report(prefixes):
    lines = []
    model_pts = defaultdict(list)
    for p in prefixes:
        f = glob.glob(f'/root/.claude/projects/*/{p}*.jsonl')[0]
        d = f[:-6] + '/subagents/'
        for m in sorted(glob.glob(d + 'agent-*.meta.json')):
            meta = json.load(open(m))
            j = m.replace('.meta.json', '.jsonl')
            tl = subagent_timeline(j)
            models = Counter(json.loads(l).get('message', {}).get('model') for l in open(j) if '"type":"assistant"' in l or '"type": "assistant"' in l)
            model = models.most_common(1)[0][0] if models else None
            model_pts[model] += tl['pts']
            top = ', '.join(f"{k}={v:.1f}" for k, v in sorted(tl['tool_by'].items(), key=lambda kv: -kv[1])[:3])
            lines.append(f"{p} {meta.get('agentType'):<15} {str(model):<24} gen={tl['gen']:.1f}m tool={tl['tool']:.1f}m "
                         f"other={tl['other']:.1f}m out={tl['out']/1000:.1f}k calls={tl['calls']} [{top}] | {meta.get('description','')[:55]}")
    lines.append('')
    for model, pts in model_pts.items():
        ft = fit(pts)
        if ft:
            tot_tok = sum(p[0] for p in pts)
            tot_s = sum(p[1] for p in pts)
            lines.append(f"rate {str(model):<26} fit gen_s={ft[0]:.1f}+{ft[1]*1000:.1f}ms*tok n={ft[2]}  "
                         f"aggregate {tot_tok/max(tot_s,1):.0f} tok/s over {tot_tok/1000:.0f}k tok")
    return '\n'.join(lines)


if __name__ == '__main__' and '--subagents' in sys.argv:
    print(subagent_report([a for a in sys.argv[1:] if not a.startswith('--')] or DEFAULT))
    sys.exit(0)


# =====================================================================
# Fourth pass: critical path. Union of non-probe subagent segments inside
# the run window = agent-covered time; the rest is parent-serial time,
# split by the first-pass state of each gap. Also waits per review round,
# phase boundaries by first/last non-probe report, and thinking share.
# =====================================================================
def union(ivals):
    out = []
    for a, b in sorted(ivals):
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


def critical(prefix):
    f, recs = load(prefix)
    s_idx, e_idx = run_window(recs)
    R = recs[s_idx:e_idx + 1]
    t0 = ts(R[0]['timestamp'])
    t_end = ts(R[-1]['timestamp'])
    subs = subagent_segments(f)
    real = [s for s in subs if not PROBE_RE.search(s['desc'])]
    cov = union([[max(a, t0), min(b, t_end)] for s in real for a, b in s['segs'] if b > t0 and a < t_end])

    def covered(ta, tb):
        tot = 0.0
        for a, b in cov:
            lo, hi = max(a, ta), min(b, tb)
            if hi > lo:
                tot += hi - lo
        return tot

    # replay first-pass state machine, splitting each gap into covered / serial
    serial = defaultdict(float)
    overlap = defaultdict(float)
    last_t = t0
    state = 'gen'
    outstanding = {}
    first_report = None
    last_report = None
    by_id = {s['id']: s for s in subs}
    report_times = []
    for r in R:
        typ = r.get('type')
        if 'timestamp' not in r or typ in ('attachment', 'queue-operation', 'file-history-snapshot', 'file-history-delta'):
            continue
        t = ts(r['timestamp'])
        gap = max(0.0, t - last_t)
        is_err = typ == 'assistant' and r['message'].get('model') == '<synthetic>'
        is_cb = typ == 'system' and r.get('subtype') == 'compact_boundary'
        if is_cb:
            k = 'compaction'
        elif is_err:
            k = 'api-stall'
        elif outstanding:
            k = 'tool:' + min(outstanding.values(), key=lambda v: v[1])[0]
        elif state == 'idle':
            txt = ' '.join(user_texts(r)) if typ == 'user' else ''
            k = 'idle:human' if (typ == 'user' and prompt_kind(txt) == 'human') else 'idle:wait'
        else:
            k = 'gen'
        c = covered(last_t, t)
        overlap[k] += c
        serial[k] += gap - c
        last_t = t
        if typ == 'assistant' and not is_err:
            for x in r['message']['content']:
                if x['type'] == 'tool_use':
                    inp = x['input'] if isinstance(x['input'], dict) else {}
                    outstanding[x['id']] = (tool_cat(x['name'], inp), t)
        elif typ == 'user':
            cc = r['message']['content']
            if not isinstance(cc, str):
                for x in cc:
                    if x.get('type') == 'tool_result':
                        outstanding.pop(x.get('tool_use_id'), None)
            txt = ' '.join(user_texts(r))
            m = re.search(r'agent-message from="(a[0-9a-f]+)"', txt) or re.search(r'<task-id>(a[0-9a-f]{16})</task-id>', txt)
            if m and m.group(1) in by_id and not PROBE_RE.search(by_id[m.group(1)]['desc']):
                report_times.append(t)
            kinds = [prompt_kind(x) for x in user_texts(r)]
            if kinds and not all(k2 == 'meta' for k2 in kinds):
                state = 'gen'
        elif typ == 'system' and r.get('subtype') == 'turn_duration':
            state = 'idle'
            outstanding.clear()
    # TaskOutput blocks also count as report arrival
    # longest agent segment per session (critical agent)
    longest = sorted(((b - a) / 60, s['type'], s['model'], s['desc'][:45]) for s in real for a, b in s['segs'])[-3:]
    return dict(wall=(t_end - t0) / 60, covered=sum(b - a for a, b in cov) / 60,
                serial={k: v / 60 for k, v in serial.items()}, overlap={k: v / 60 for k, v in overlap.items()},
                first_report=((min(report_times) - t0) / 60) if report_times else None,
                last_report=((max(report_times) - t0) / 60) if report_times else None,
                longest=longest)


def round_waits(prefix, rounds):
    """Idle waits keyed by the dispatch group (round) of the agent whose report ended them."""
    f, recs = load(prefix)
    s_idx, e_idx = run_window(recs)
    R = recs[s_idx:e_idx + 1]
    t0 = ts(R[0]['timestamp'])
    subs = subagent_segments(f)
    by_id = {s['id']: s for s in subs}
    # map (agent start time) -> group index using the rounds' dispatch times
    starts = []
    for gi, rd in enumerate(rounds):
        for e in rd:
            starts.append((t0 + e[0] * 60, gi, e[2]))
    def group_of(t_arrive, sub):
        seg = max([sg for sg in sub['segs'] if sg[0] <= t_arrive + 5], default=sub['segs'][0], key=lambda sg: sg[0])
        best = min(starts, key=lambda x: abs(x[0] - seg[0]))
        return best[1], best[2]
    out = defaultdict(float)
    last_t = t0
    state = 'gen'
    for r in R:
        typ = r.get('type')
        if 'timestamp' not in r or typ in ('attachment', 'queue-operation', 'file-history-snapshot', 'file-history-delta'):
            continue
        t = ts(r['timestamp'])
        gap = max(0.0, t - last_t)
        if state == 'idle' and typ == 'user':
            txt = ' '.join(user_texts(r))
            m = re.search(r'agent-message from="(a[0-9a-f]+)"', txt) or re.search(r'<task-id>(a[0-9a-f]{16})</task-id>', txt)
            if m and m.group(1) in by_id:
                gi, kind = group_of(t, by_id[m.group(1)])
                out[(gi + 1, kind)] += gap / 60
        if typ == 'system' and r.get('subtype') == 'turn_duration':
            state = 'idle'
        elif typ == 'user':
            state = 'gen'
        last_t = t
    return dict(out)


# =====================================================================
# Summary table (per session) and cross-session aggregates. --table
# =====================================================================
BOOK_CHUNKS = {'ledger', 'lint', 'watch', 'journal/memory', 'skill-read'}


def call_mix(prefix):
    """Per parent tool call: bookkeeping-only / mixed / task-only, by chunk category."""
    f, recs = load(prefix)
    s_idx, e_idx = run_window(recs)
    R = recs[s_idx:e_idx + 1]
    seen = set()
    mix = Counter()
    status_reads = 0
    for r in R:
        if r.get('type') != 'assistant':
            continue
        for x in r['message']['content']:
            if x['type'] != 'tool_use' or x['id'] in seen:
                continue
            seen.add(x['id'])
            inp = x['input'] if isinstance(x['input'], dict) else {}
            if x['name'] == 'Bash':
                cmd = inp.get('command', '')
                if '--status' in cmd and 'skills/sage/bin/sage-watch' in cmd:
                    status_reads += 1
                cats = {c for c, _ in chunk_command(cmd)}
            else:
                cats = {tool_cat(x['name'], inp).replace('bash:', '')}
            if x['name'] in ('Monitor', 'TaskStop') and 'watch' in tool_cat(x['name'], inp):
                cats = {'watch'}
            b = cats & BOOK_CHUNKS
            if b and b == cats:
                mix['book-only'] += 1
            elif b:
                mix['mixed'] += 1
            else:
                mix['task-only'] += 1
    return dict(mix), status_reads


def table(results):
    hdr = ('| session | parent model / effort | run wall | parent gen (serial) | idle on agents | compaction | '
           'API stall + human | parent tool wait | agents (rounds) | parent API calls | parent out / thinking | '
           'bookkeeping calls (only/mixed) | bookkeeping out tokens | bookkeeping gen min | longest agent |')
    sep = '|' + '---|' * 15
    rows = [hdr, sep]
    agg = defaultdict(float)
    for r in results:
        b = r['buckets']
        cr = r['critical']
        idle_agents = b.get('idle:agents', 0) + b.get('tool:agent-wait(TaskOutput)', 0)
        stall = b.get('api-stall/error', 0) + b.get('idle:human', 0)
        comp = b.get('compaction', 0)
        toolw = sum(v for k, v in b.items() if k.startswith('tool:') and 'TaskOutput' not in k)
        tok = r['second']['tok']
        gen2 = r['second']['gen']
        book_tok = sum(v for k, v in tok.items() if k in BOOK_CHUNKS)
        book_gen = sum(v for k, v in gen2.items() if k in BOOK_CHUNKS)
        mix, st = r['mix'], r['status_reads']
        nag = len([s for s in r['subs'] if 'probe' not in s['desc'].lower()])
        nprobe = len(r['subs']) - nag
        longest = cr['longest'][-1]
        rows.append(f"| {r['session']} | {r['model'].replace('claude-','')} / {r['effort']} | {r['wall_min']:.0f} | "
                    f"{b.get('gen',0):.0f} ({cr['serial'].get('gen',0):.0f}) | {idle_agents:.0f} | {comp:.0f} | {stall:.0f} | "
                    f"{toolw:.0f} | {nag}+{nprobe}p ({r['n_rounds']}) | {r['api_calls']} | "
                    f"{r['out_total']/1000:.0f}k / {r['think_total']/1000:.0f}k | "
                    f"{mix.get('book-only',0)}/{mix.get('mixed',0)} of {sum(mix.values())} ({st} --status) | "
                    f"{book_tok/1000:.0f}k ({100*book_tok/max(r['out_total'],1):.0f}%) | {book_gen:.1f} | "
                    f"{longest[0]:.0f}m {longest[1]} ({longest[2]}) |")
        for k, v in (('wall', r['wall_min']), ('gen', b.get('gen', 0)), ('gen_serial', cr['serial'].get('gen', 0)),
                     ('idle_agents', idle_agents), ('comp', comp), ('stall', stall), ('toolw', toolw),
                     ('book_tok', book_tok), ('book_gen', book_gen), ('out', r['out_total']), ('think', r['think_total'])):
            agg[(r['session'] in SLOW, k)] += v
    return '\n'.join(rows), agg


SLOW = {'a58bd85c', '61de7190', 'e4bebf20', '54dd10c5', 'd4096102'}
N_ROUNDS = {'a58bd85c': 5, '61de7190': 3, 'e4bebf20': 5, '54dd10c5': 3, 'd4096102': 3, '9832cdf3': 2, 'c81599fd': 2}


# =====================================================================
# Fifth pass: the post-round-1 loop. Window = first report of the first
# review group -> last non-probe report. Inside it: parent gen, waits,
# tool time. --loop
# =====================================================================
def loop_window(prefix, rounds):
    f, recs = load(prefix)
    s_idx, e_idx = run_window(recs)
    R = recs[s_idx:e_idx + 1]
    t0 = ts(R[0]['timestamp'])
    subs = subagent_segments(f)
    by_id = {s['id']: s for s in subs}
    rev = [rd for rd in rounds if rd[0][2] == 'review']
    if not rev:
        return None
    r1_start = t0 + rev[0][0][0] * 60
    # reports
    reports = []
    for r in R:
        if r.get('type') == 'user':
            txt = ' '.join(user_texts(r))
            m = re.search(r'agent-message from="(a[0-9a-f]+)"', txt) or re.search(r'<task-id>(a[0-9a-f]{16})</task-id>', txt)
            if m and m.group(1) in by_id and not PROBE_RE.search(by_id[m.group(1)]['desc']):
                reports.append(ts(r['timestamp']))
        if r.get('type') == 'user' and not isinstance(r['message']['content'], str):
            for x in r['message']['content']:
                if x.get('type') == 'tool_result' and 'TaskOutput' in json.dumps(x.get('content'))[:0]:
                    pass
    after = [t for t in reports if t > r1_start]
    if not after:
        return None
    first_r1 = min(after)
    last = max(after)
    return dict(r1_dispatch=(r1_start - t0) / 60, r1_first_report=(first_r1 - t0) / 60, last_report=(last - t0) / 60,
                loop_min=(last - first_r1) / 60, n_groups_after=len([rd for rd in rounds if t0 + rd[0][0] * 60 > first_r1]))


if __name__ == '__main__' and '--loop' in sys.argv:
    for p in DEFAULT:
        r2 = second_pass(p)
        print(p, loop_window(p, r2['rounds']))
    sys.exit(0)


def window_breakdown(prefix, w0_min, w1_min):
    """First-pass states summed inside [w0, w1] minutes from run start."""
    f, recs = load(prefix)
    s_idx, e_idx = run_window(recs)
    R = recs[s_idx:e_idx + 1]
    t0 = ts(R[0]['timestamp'])
    w0, w1 = t0 + w0_min * 60, t0 + w1_min * 60
    out = defaultdict(float)
    last_t = t0
    state = 'gen'
    outstanding = {}
    for r in R:
        typ = r.get('type')
        if 'timestamp' not in r or typ in ('attachment', 'queue-operation', 'file-history-snapshot', 'file-history-delta'):
            continue
        t = ts(r['timestamp'])
        lo, hi = max(last_t, w0), min(t, w1)
        gap = max(0.0, hi - lo)
        is_err = typ == 'assistant' and r['message'].get('model') == '<synthetic>'
        is_cb = typ == 'system' and r.get('subtype') == 'compact_boundary'
        if is_cb:
            k = 'compaction'
        elif is_err:
            k = 'api-stall'
        elif outstanding:
            k = 'tool'
        elif state == 'idle':
            k = 'idle'
        else:
            k = 'gen'
        out[k] += gap
        last_t = t
        if typ == 'assistant' and not is_err:
            for x in r['message']['content']:
                if x['type'] == 'tool_use':
                    outstanding[x['id']] = t
        elif typ == 'user':
            cc = r['message']['content']
            if not isinstance(cc, str):
                for x in cc:
                    if x.get('type') == 'tool_result':
                        outstanding.pop(x.get('tool_use_id'), None)
            kinds = [prompt_kind(x) for x in user_texts(r)]
            if kinds and not all(k2 == 'meta' for k2 in kinds):
                state = 'gen'
        elif typ == 'system' and r.get('subtype') == 'turn_duration':
            state = 'idle'
            outstanding.clear()
    return {k: v / 60 for k, v in out.items()}


if __name__ == '__main__' and '--loopsplit' in sys.argv:
    for p in DEFAULT:
        r2 = second_pass(p)
        lw = loop_window(p, r2['rounds'])
        if not lw or lw['loop_min'] <= 0:
            print(p, 'no loop')
            continue
        b = window_breakdown(p, lw['r1_first_report'], lw['last_report'])
        pre = window_breakdown(p, 0, r2['rounds'][0][0][0])
        print(p, f"loop {lw['r1_first_report']:.1f}->{lw['last_report']:.1f} = {lw['loop_min']:.1f} min:",
              ', '.join(f"{k}={v:.1f}" for k, v in sorted(b.items(), key=lambda kv: -kv[1])),
              '| pre-first-dispatch:', ', '.join(f"{k}={v:.1f}" for k, v in sorted(pre.items(), key=lambda kv: -kv[1])))
    sys.exit(0)


def phases2(prefix):
    """Four phases by event, not by ledger step word:
       P1 pre-dispatch  = run start -> first non-probe dispatch (decompose, plan, ledger, and any parent-kept inline work)
       P2 round 1       = first dispatch -> first report of the first review group
       P3 loop          = that report -> last non-probe report (triage, fixes, re-reviews)
       P4 close         = last report -> run end (record, journal, lint, watchdog stop)
    Per phase: wall, parent gen, API calls, output/thinking tokens, bookkeeping share of output."""
    f, recs = load(prefix)
    s_idx, e_idx = run_window(recs)
    R = recs[s_idx:e_idx + 1]
    t0 = ts(R[0]['timestamp'])
    t_end = ts(R[-1]['timestamp'])
    r2 = second_pass(prefix)
    lw = loop_window(prefix, r2['rounds'])
    first_disp = r2['rounds'][0][0][0] if r2['rounds'] else (t_end - t0) / 60
    b = [0.0, first_disp, lw['r1_first_report'] if lw else first_disp, lw['last_report'] if lw else first_disp,
         (t_end - t0) / 60]
    if lw and lw['loop_min'] <= 0:
        b[3] = b[2]
    names = ['P1 pre-dispatch', 'P2 round-1 wait', 'P3 triage/fix/re-review loop', 'P4 close']
    # message table with pieces
    msgs = {}
    for r in R:
        if r.get('type') != 'assistant' or r['message'].get('model') == '<synthetic>':
            continue
        m = r['message']
        d = msgs.setdefault(m['id'], dict(out=0, think=0, t=ts(r['timestamp']), pieces=[], seen=set()))
        u = m.get('usage') or {}
        d['out'] = max(d['out'], u.get('output_tokens', 0) or 0)
        d['think'] = max(d['think'], ((u.get('output_tokens_details') or {}).get('thinking_tokens', 0) or 0))
        d['t'] = ts(r['timestamp'])
        for x in m['content']:
            key = x.get('id') or (x['type'], len(x.get('text', '')))
            if key in d['seen']:
                continue
            d['seen'].add(key)
            if x['type'] == 'tool_use':
                inp = x['input'] if isinstance(x['input'], dict) else {}
                if x['name'] == 'Bash':
                    d['pieces'].extend(chunk_command(inp.get('command', '')))
                else:
                    d['pieces'].append((tool_cat(x['name'], inp).replace('bash:', ''), len(json.dumps(inp))))
            elif x['type'] == 'text':
                d['pieces'].append(('text', len(x.get('text', ''))))
    out = []
    for k in range(4):
        a0, a1 = t0 + b[k] * 60, t0 + b[k + 1] * 60 + (1 if k == 3 else 0)
        sel = [d for d in msgs.values() if a0 <= d['t'] < a1]
        book = 0.0
        for d in sel:
            tot = sum(c for _, c in d['pieces']) or 1
            book += d['out'] * sum(c for cat, c in d['pieces'] if cat in BOOK_CHUNKS) / tot
        wb = window_breakdown(prefix, b[k], b[k + 1])
        out.append(dict(name=names[k], min=b[k + 1] - b[k], gen=wb.get('gen', 0), idle=wb.get('idle', 0),
                        tool=wb.get('tool', 0), other=wb.get('compaction', 0) + wb.get('api-stall', 0),
                        calls=len(sel), out=sum(d['out'] for d in sel), think=sum(d['think'] for d in sel), book=book))
    return out


if __name__ == '__main__' and '--phases' in sys.argv:
    print('| session | phase | wall min | parent gen | idle (agents/human) | tool | compaction+stall | API calls | out | thinking | bookkeeping out |')
    print('|---|---|---|---|---|---|---|---|---|---|---|')
    for p in DEFAULT:
        for ph in phases2(p):
            print(f"| {p} | {ph['name']} | {ph['min']:.1f} | {ph['gen']:.1f} | {ph['idle']:.1f} | {ph['tool']:.1f} | {ph['other']:.1f} | "
                  f"{ph['calls']} | {ph['out']/1000:.1f}k | {ph['think']/1000:.1f}k | {ph['book']/1000:.1f}k ({100*ph['book']/max(ph['out'],1):.0f}%) |")
    sys.exit(0)


if __name__ == '__main__':
    args = sys.argv[1:]
    out_json = None
    if '--json' in args:
        k = args.index('--json')
        out_json = args[k + 1]
        args = args[:k] + args[k + 2:]
    res = [analyze(s) for s in (args or DEFAULT)]
    for r in res:
        print(fmt(r))
        r2 = second_pass(r['session'], r['msg_gen'])
        r['second'] = r2
        print(fmt2(r['session'], r2))
        cr = critical(r['session'])
        r['critical'] = cr
        rw = round_waits(r['session'], r2['rounds'])
        r['round_waits'] = {f"{k[0]}:{k[1]}": v for k, v in rw.items()}
        print(f"critical: wall={cr['wall']:.1f} agent-covered={cr['covered']:.1f} first-report@{cr['first_report']} last-report@{cr['last_report']}")
        print('  serial (no agent running): ' + ', '.join(f"{k}={v:.1f}" for k, v in sorted(cr['serial'].items(), key=lambda kv: -kv[1]) if v >= 0.1))
        print('  overlapped (agents running): ' + ', '.join(f"{k}={v:.1f}" for k, v in sorted(cr['overlap'].items(), key=lambda kv: -kv[1]) if v >= 0.1))
        print('  longest agent segments: ' + '; '.join(f"{a:.1f}m {b} {c} {d}" for a, b, c, d in cr['longest']))
        print('  idle waits by round (group:kind): ' + ', '.join(f"{k}={v:.1f}" for k, v in sorted(r['round_waits'].items())))
        print()
    for r in res:
        r['mix'], r['status_reads'] = call_mix(r['session'])
        r['n_rounds'] = N_ROUNDS.get(r['session'], 0)
    t, agg = table(res)
    print(t)
    print()
    for slow in (True, False):
        g = {k[1]: v for k, v in agg.items() if k[0] == slow}
        if not g:
            continue
        w = g['wall']
        print(('SLOW-5' if slow else 'FAST-2') + ' totals (min): ' + ', '.join(
            f"{k}={v:.1f}" + (f" ({100*v/w:.0f}%)" if k not in ('wall', 'book_tok', 'out', 'think') else '')
            for k, v in g.items()))
    if out_json:
        for r in res:
            r.pop('msg_gen', None)
        json.dump(res, open(out_json, 'w'), indent=1, default=str)

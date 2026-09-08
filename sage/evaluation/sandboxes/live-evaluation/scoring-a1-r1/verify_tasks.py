"""Scorer-authored independent grammar oracle and raw-count recomputation."""
import csv, importlib.util, itertools, math, random, shutil, subprocess, sys
from fractions import Fraction
from audit import OUT, ARMS, load, save, sha

def module(p):
    spec=importlib.util.spec_from_file_location('candidate',p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m
def oracle(wire,limit):
    frames=[]; pos=0
    while pos<len(wire):
        colon=wire.find(b':',pos)
        if colon<0: raise ValueError()
        h=wire[pos:colon]
        if not h or any(x<48 or x>57 for x in h) or (len(h)>1 and h[0]==48): raise ValueError()
        n=int(h)
        if n>limit or colon+1+n>=len(wire) or wire[colon+1+n]!=44: raise ValueError()
        frames.append(wire[colon+1:colon+1+n]); pos=colon+2+n
    return frames
def code(arm):
    work=OUT/arm/'work'; work.parent.mkdir(exist_ok=True)
    shutil.copytree(ARMS/arm/'work',work,dirs_exist_ok=True)
    shutil.copytree(ARMS/arm/'inputs',work.parent/'inputs',dirs_exist_ok=True)
    p=subprocess.run([sys.executable,'-m','unittest','-v'],cwd=work,capture_output=True,text=True)
    m=module(work/'decoder.py'); count=0; failures=[]
    def check(wire,limit,chunks):
        nonlocal count
        count+=1
        try: expect=oracle(wire,limit); valid=True
        except ValueError: expect=None; valid=False
        d=m.Decoder(limit); got=[]
        try:
            for chunk in chunks: got+=d.feed(chunk)
            d.finish(); observed=True
        except m.FrameError: observed=False
        if valid!=observed or (valid and got!=expect): failures.append({'wire_hex':wire.hex(),'limit':limit,'valid':valid,'observed':observed})
    for length in range(7):
        for t in itertools.product(b'012:,x',repeat=length):
            w=bytes(t)
            for split in range(length+1): check(w,2,[w[:split],b'',w[split:]])
    rng=random.Random(917)
    for _ in range(100):
        payloads=[bytes(rng.randrange(256) for _ in range(rng.randrange(80))) for _ in range(rng.randrange(1,7))]
        w=b''.join(str(len(p)).encode()+b':'+p+b',' for p in payloads)
        for split in range(len(w)+1): check(w,80,[w[:split],w[split:]])
    w=b'256:'+bytes(range(256))+b',0:,2:\xc3\xa9,'
    for split in range(len(w)+1): check(w,256,[w[:split],w[split:]])
    negative=0
    def raises(t,fn):
        nonlocal negative
        negative+=1
        try: fn()
        except t: return
        raise AssertionError('Expected '+t.__name__)
    for limit in [-1,True,False,1.1,'2',None,[],{}]: raises(ValueError,lambda:m.Decoder(limit))
    for bad in [None,bytearray(b'a'),memoryview(b'a'),'a',4,[],{}]:
        d=m.Decoder(); assert d.feed(b'3:a')==[]; raises(TypeError,lambda:d.feed(bad)); assert d.feed(b'bc,')==[b'abc']; d.finish()
    for bad in [b':',b'00',b'-1',b' 1',b'1:x;',b'3:xx',b'0:',b'1',b'1:']:
        d=m.Decoder()
        def consume(): d.feed(bad); d.finish()
        raises(m.FrameError,consume)
        raises(m.FrameError,lambda:d.feed(b'')); raises(m.FrameError,d.finish)
        d.reset(); assert d.feed(b'0:,')==[b'']; d.finish(); assert d.feed(b'1:x,')==[b'x']
    for limit,prefix,last in [(0,b'',b'1'),(2,b'',b'3'),(1024,b'102',b'5'),(10,b'1',b'1')]:
        d=m.Decoder(limit); d.feed(prefix); raises(m.FrameError,lambda:d.feed(last))
    result={'arm':arm,'candidate_sha256':sha(work/'decoder.py'),'delivered_tests':{'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},'oracle_stream_chunk_cases':count,'negative_assertions':negative,'mismatches':failures,'scope':'Python interpreter of this scorer, independent whole-wire parser, exhaustive short streams every split, binary random payloads every split, poison/reset/type/immediate limit checks','ok':p.returncode==0 and not failures}
    save(arm+'-checks.json',result); return {k:v for k,v in result.items() if k!='delivered_tests'}

def data(arm):
    work=OUT/arm/'work'; work.parent.mkdir(exist_ok=True)
    shutil.copytree(ARMS/arm/'work',work,dirs_exist_ok=True)
    shutil.copytree(ARMS/arm/'inputs',work.parent/'inputs',dirs_exist_ok=True)
    runs=[]
    for i in range(2):
        target=work.parent/f'regenerated-{i}.json'
        r=subprocess.run([sys.executable,str(work/'analysis.py'),'--output',str(target)],capture_output=True,text=True)
        runs.append({'exit_code':r.returncode,'stdout':r.stdout,'stderr':r.stderr,'sha256':sha(target),'equals_original':target.read_bytes()==(ARMS/arm/'work/summary.json').read_bytes()})
    s=load(work/'summary.json')
    with (ARMS/arm/'inputs/sessions.csv').open() as f: rows=list(csv.DictReader(f))
    groups={'overall':rows}
    groups.update({f'crowd_{b}':[r for r in rows if r['crowd_block']==b] for b in ['quiet','busy']})
    groups.update({f'week_{w}':[r for r in rows if r['week']==w] for w in ['1','2']})
    groups.update({f'week_{w}_{b}':[r for r in rows if r['week']==w and r['crowd_block']==b] for w in ['1','2'] for b in ['quiet','busy']})
    treatment=arm.endswith('treatment'); comparisons=0; expected={}
    def flatten(g):
        if treatment: return g
        return {'overall':g['overall'],**{'crowd_'+b:v for b,v in g['by_crowd_block'].items()},**{'week_'+w:v for w,v in g['by_week'].items()},**{'week_'+w+'_'+b:v for w,blocks in g['by_week_and_crowd_block'].items() for b,v in blocks.items()}}
    scenarios=[(None,flatten(s['observed_rows'] if treatment else s['observed']))]
    rawsc=s['missing_count_sensitivity']['scenarios'] if treatment else s['sensitivity']['scenarios']
    assert [x['M09_completed' if treatment else 'm09_completed'] for x in rawsc]==list(range(21))
    scenarios += [(i,flatten(x['comparisons'])) for i,x in enumerate(rawsc)]
    for k,actual in scenarios:
        for group,rs in groups.items():
            rates={}; records={}
            for sign in ['old','new']:
                selected=[r for r in rs if r['sign']==sign and (r['completed']!='' or k is not None)]
                numerator=sum(int(r['completed']) if r['completed']!='' else k for r in selected)
                denom=sum(int(r['visitors']) for r in selected); rate=Fraction(numerator,denom)
                a=actual[group][sign]
                assert a['completed' if treatment else 'known_completed']==numerator
                assert a['denominator' if treatment else 'known_outcome_visitors']==denom
                assert math.isclose(a['fraction' if treatment else 'fraction_known_outcomes'],float(rate),abs_tol=1e-14)
                rates[sign]=rate; records[sign]={'completed':numerator,'denominator':denom,'fraction':float(rate)}
                comparisons+=3
            diff=float(100*(rates['new']-rates['old']))
            assert math.isclose(actual[group]['difference_new_minus_old_pp' if treatment else 'new_minus_old_pp_known_outcomes'],diff,abs_tol=1e-12)
            comparisons+=1; records['difference_pp']=diff
            expected.setdefault(str(k),{})[group]=records
    def wilson(k,n):
        # Algebraically independent Wilson formula expressed in count space.
        z2=1.96**2; center=(k+z2/2)/(n+z2); radius=1.96*math.sqrt(k*(n-k)/n+z2/4)/(n+z2)
        return [center-radius,center+radius]
    intervals=[]
    for sign in ['old','new']:
        e=expected['None']['overall'][sign]; actual=s['observed_rows']['overall'][sign]['wilson_95'] if treatment else s['overall_wilson_95']['signs'][sign]['fraction_interval']
        if treatment: actual=[actual['lower'],actual['upper']]
        exp=wilson(e['completed'],e['denominator']); assert all(math.isclose(a,b,abs_tol=1e-14) for a,b in zip(actual,exp)); intervals.append({'sign':sign,'interval':exp})
    for i,x in enumerate(rawsc):
        actual=x['comparisons']['overall']['new']['wilson_95'] if treatment else x['new_overall_wilson']
        if treatment: actual=[actual['lower'],actual['upper']]
        assert all(math.isclose(a,b,abs_tol=1e-14) for a,b in zip(actual,wilson(229+i,400)))
    bounds_checked=0
    if treatment:
        for group in groups:
            records=[expected[str(k)][group] for k in range(21)]; a=s['missing_count_sensitivity']['bounds'][group]
            reference={'new_fraction_min':min(r['new']['fraction'] for r in records),'new_fraction_max':max(r['new']['fraction'] for r in records),'new_denominator':records[0]['new']['denominator'],'old_fraction':records[0]['old']['fraction'],'old_denominator':records[0]['old']['denominator'],'difference_new_minus_old_pp_min':min(r['difference_pp'] for r in records),'difference_new_minus_old_pp_max':max(r['difference_pp'] for r in records)}
            for key,value in reference.items(): assert math.isclose(a[key],value,abs_tol=1e-12); bounds_checked+=1
        envelope=s['missing_count_sensitivity']['overall_new_wilson_envelope']; assert math.isclose(envelope['lower'],wilson(229,400)[0],abs_tol=1e-14); assert math.isclose(envelope['upper'],wilson(249,400)[1],abs_tol=1e-14); bounds_checked+=2
    else:
        selections={'new_overall_fraction':('overall',True),'overall_new_minus_old_pp':('overall',False),'busy_new_minus_old_pp':('crowd_busy',False),'week_2_new_minus_old_pp':('week_2',False),'week_2_busy_new_minus_old_pp':('week_2_busy',False)}
        for key,(group,fraction) in selections.items():
            values=[expected[str(k)][group]['new']['fraction'] if fraction else expected[str(k)][group]['difference_pp'] for k in range(21)]
            assert math.isclose(s['sensitivity'][key]['min'],min(values),abs_tol=1e-12); assert math.isclose(s['sensitivity'][key]['max'],max(values),abs_tol=1e-12); bounds_checked+=2
    for filename,digest in s['source_sha256'].items(): assert sha(ARMS/arm/'inputs'/filename)==digest
    result={'arm':arm,'runs':runs,'group_scenario_numeric_assertions':comparisons,'group_count':len(groups),'missing_scenarios':21,'intervals_checked':23,'sensitivity_bound_assertions':bounds_checked,'overall_wilson':intervals,'independent_recomputation':expected,'ok':all(r['exit_code']==0 and r['equals_original'] for r in runs)}
    save(arm+'-checks.json',result); return {k:v for k,v in result.items() if k!='independent_recomputation'}
if __name__=='__main__':
    if '--data-only' not in sys.argv:
        for arm in ['code-treatment','code-baseline']: print(code(arm))
    for arm in ['data-baseline','data-treatment']: print(data(arm))

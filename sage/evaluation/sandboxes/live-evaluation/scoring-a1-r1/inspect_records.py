"""Condense primary event/lifecycle evidence without asserting journal authenticity."""
import json
from pathlib import Path
from audit import OUT, BASE, ARMS, load, save, sha

def inspect():
    evidence=[]; events=[]
    for row in load(OUT/'state-audit.json'):
        summary={'arm':row['arm'],'run':row['run'],'typed_evidence':{},'plans':[],'assignments':[],'findings':[],'notes':[]}
        for e in row['events']:
            p=e['payload']; typ=e['type']
            if typ=='evidence.recorded':
                summary['typed_evidence'][p['kind']]=summary['typed_evidence'].get(p['kind'],0)+1
                loc=p['locator']; path=Path(loc.split('#')[0]); resolution='absolute locator'
                if not path.is_absolute(): path=ARMS/row['arm']/path; resolution='arm-relative locator resolved using explicit case root'
                actual=sha(path) if path.is_file() else None
                evidence.append({'arm':row['arm'],'run':row['run'],'event':e['event_id'],'locator':loc,'resolution':resolution,'kind':p['kind'],'expected':p.get('sha256'),'actual':actual,'hash_matches':actual==p.get('sha256') if p.get('sha256') and actual else None})
            elif typ=='plan.revised': summary['plans'].append(e)
            elif typ in ['agent.requested','agent.observed','task.admitted','task.result']: summary['assignments'].append(e)
            elif typ.startswith('finding.') or typ=='check.recorded' and p['outcome']!='passed': summary['findings'].append(e)
            elif typ=='note.recorded': summary['notes'].append(e)
        events.append(summary)
    save('record-inspection.json',{'events':events,'evidence_bindings':evidence})
    ops=[]
    for arm in ['code-treatment','code-baseline','data-baseline','data-treatment','creative-treatment','recovery-treatment','promotion-treatment']:
        x=load(BASE/'observations'/f'{arm}.json')
        ops.append({'arm':arm,'keys':list(x),'lifecycle_sections':{k:v for k,v in x.items() if k not in ['lifecycle_observations','actor_messages','actor_final_summary','final_actor_claim','final_actor_summary','outer_readonly_checks']}})
    save('operational-inspection.json',ops)
    print(json.dumps({'evidence_hash_mismatches':[x for x in evidence if x['hash_matches'] is False], 'typed_evidence':[{k:x[k] for k in ['arm','run','typed_evidence']} for x in events]},indent=2))
if __name__=='__main__': inspect()

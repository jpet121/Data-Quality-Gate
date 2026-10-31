"""Reproducible single-process demo benchmark; no invented production SLO."""
import argparse,json,random,statistics,sys,time,tracemalloc,tempfile,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from event_validator import load_matrix,validate
from event_validator.storage import SQLiteRepository

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--count',type=int,default=1000)
    p.add_argument('--seed',type=int,default=1701)
    p.add_argument('--db',action='store_true')
    args=p.parse_args();rng=random.Random(args.seed)
    matrix=load_matrix(Path(__file__).resolve().parents[1]/'examples/matrix_v1.json')
    corpus=[json.loads(line)['raw'] for line in (Path(__file__).resolve().parents[1]/'examples/valid.jsonl').read_text().splitlines()]
    errors=[json.loads(line)['raw'] for line in (Path(__file__).resolve().parents[1]/'examples/invalid.jsonl').read_text().splitlines()]
    data=[]
    for i in range(args.count):
        s=rng.choice(errors) if rng.random()<.10 else rng.choice(corpus)
        # varying event id makes each replay independent
        s=s.replace('EVT-001',f'EVT-BENCH-{i:07d}').replace('EVT-002',f'EVT-BENCH-{i:07d}').replace('EVT-003',f'EVT-BENCH-{i:07d}').replace('EVT-004',f'EVT-BENCH-{i:07d}').replace('EVT-005',f'EVT-BENCH-{i:07d}')
        data.append(s)
    dbpath=None;repo=None
    if args.db:
        fd,dbpath=tempfile.mkstemp(suffix='.sqlite');os.close(fd);repo=SQLiteRepository(dbpath);repo.migrate()
    tracemalloc.start();latencies=[];success=0;failed=0
    start=time.perf_counter();cpu=time.process_time()
    try:
        for i,s in enumerate(data):
            t=time.perf_counter();r=validate(s,f'benchmark/{i}',matrix,i)
            if repo:repo.persist(r,r.record.tenant_id if r.record else 'REJECTED',r.record.event_id if r.record else f'reject/{i}')
            latencies.append((time.perf_counter()-t)*1000)
            if r.status=='ACCEPTED':success+=1
            else:failed+=1
        elapsed=time.perf_counter()-start;cpu_elapsed=time.process_time()-cpu
        _,peak=tracemalloc.get_traced_memory()
        print(json.dumps({'seed':args.seed,'count':args.count,'db_enabled':args.db,'seconds':round(elapsed,5),'cpu_seconds':round(cpu_elapsed,5),'events_per_sec':round(args.count/max(elapsed,1e-9),1),'p50_ms':round(statistics.median(latencies),3) if latencies else 0,'p95_ms':round(sorted(latencies)[int(len(latencies)*.95)],3) if latencies else 0,'peak_tracemalloc_bytes':peak,'accepted':success,'rejected':failed,'db_counts':repo.counts() if repo else None},sort_keys=True))
    finally:
        tracemalloc.stop()
        if repo:repo.close();os.unlink(dbpath)
if __name__=='__main__':main()

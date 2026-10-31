"""Read-only PyPI advisory-metadata check for recorded dependency pins."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import urllib.request
import urllib.parse

ROOT=Path(__file__).resolve().parents[1]

def check(pin: str) -> dict:
    name,version=pin.split('==',1)
    url='https://pypi.org/pypi/'+urllib.parse.quote(name,safe='')+'/'+urllib.parse.quote(version,safe='')+'/json'
    try:
        with urllib.request.urlopen(url,timeout=20) as r:body=r.read(8*1024*1024)
        data=json.loads(body)
        return {'package':name,'version':version,'url':url,'response_sha256':hashlib.sha256(body).hexdigest(),
                'queried_at':datetime.now(timezone.utc).isoformat(),'status':'QUERIED',
                'advisories':data.get('vulnerabilities',[])}
    except Exception as exc:
        return {'package':name,'version':version,'url':url,'status':'UNAVAILABLE','error_type':type(exc).__name__}

def main() -> int:
    pins=[s for s in (ROOT/'requirements-verification.lock').read_text().splitlines() if s and not s.startswith('#')]
    with ThreadPoolExecutor(max_workers=4) as pool:results=list(pool.map(check,pins))
    report={'source':'PyPI version JSON vulnerability metadata over verified HTTPS','scope':'recorded verifier dependencies; not a full production security certification',
            'dependencies':results,'unavailable':sum(r['status']!='QUERIED' for r in results),
            'advisory_count':sum(len(r.get('advisories',[])) for r in results)}
    (ROOT/'continuation_evidence/dependency_advisories.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({'queried':len(results)-report['unavailable'],'unavailable':report['unavailable'],'advisories':report['advisory_count']}))
    return 0 if report['unavailable']==report['advisory_count']==0 else 1

if __name__=='__main__':raise SystemExit(main())

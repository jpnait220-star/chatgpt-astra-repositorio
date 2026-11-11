from pathlib import Path
import argparse,urllib.request,urllib.parse,json,subprocess,base64
R=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--endpoint',required=True);p.add_argument('--revision',required=True,type=int);p.add_argument('--key',required=True,type=Path);a=p.parse_args()
u=urllib.parse.urlsplit(a.endpoint)
assert u.scheme=='https' and u.hostname and not u.username and not u.password and not u.query and not u.fragment and u.path in ['', '/'] and a.revision>=2
base=a.endpoint.rstrip('/')
request=urllib.request.Request(base+'/health',headers={'User-Agent':'DuckClientZ-RouteActivation/241','Cache-Control':'no-cache'})
with urllib.request.urlopen(request,timeout=15) as response:
 assert response.status==200 and response.url==base+'/health'
 health=json.load(response);assert health.get('status')=='online' and health.get('service')=='duck-cosmetics' and health.get('protocol')==1
payload=json.dumps({'protocol':1,'type':'duck-service-route','revision':a.revision,'enabled':True,'endpoint':base},separators=(',',':')).encode()
work=R/'build/signing';work.mkdir(parents=True,exist_ok=True);(work/'active-route.payload').write_bytes(payload)
subprocess.run(['openssl','pkeyutl','-sign','-rawin','-inkey',str(a.key),'-in',str(work/'active-route.payload'),'-out',str(work/'active-route.sig')],check=True,capture_output=True)
envelope={'payload':base64.b64encode(payload).decode(),'signature':base64.b64encode((work/'active-route.sig').read_bytes()).decode()}
(R/'dist/DuckClientZ-service.json').write_text(json.dumps(envelope,separators=(',',':'))+'\n')
(R/'activation-report.json').write_text(json.dumps({'endpoint':base,'revision':a.revision,'health':health,'published':False},indent=2)+'\n')
print('Prepared signed active route revision',a.revision,'for',base,'after real HTTPS health check. Private key not copied.')

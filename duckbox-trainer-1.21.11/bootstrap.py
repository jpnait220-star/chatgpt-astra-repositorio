from pathlib import Path
import urllib.request,json,zipfile,subprocess,concurrent.futures
B=Path(__file__).parent;T=B/'tools';T.mkdir(exist_ok=True)
def get(url,path):
 path=Path(path)
 if not path.exists():
  path.parent.mkdir(parents=True,exist_ok=True)
  with urllib.request.urlopen(url,timeout=90) as r:path.write_bytes(r.read())
 return path
for part in ['asm','asm-tree','asm-analysis','asm-commons','asm-util']:get('https://repo.maven.apache.org/maven2/org/ow2/asm/'+part+'/9.7.1/'+part+'-9.7.1.jar',T/'asm'/(part+'.jar'))
get('https://maven.fabricmc.net/net/fabricmc/tiny-remapper/0.10.4/tiny-remapper-0.10.4-fat.jar',T/'remapper.jar')
get('https://maven.fabricmc.net/net/fabricmc/yarn/1.21.11+build.6/yarn-1.21.11+build.6-v2.jar',T/'yarn.jar')
with zipfile.ZipFile(T/'yarn.jar') as z:(T/'yarn.tiny').write_bytes(z.read('mappings/mappings.tiny'))
cached=Path('/workspace/duckclientz/tools/minecraft-1.21.11.json')
if cached.exists():meta=json.loads(cached.read_text())
else:
 manifest=json.loads(urllib.request.urlopen('https://piston-meta.mojang.com/mc/game/version_manifest_v2.json').read())
 entry=next(v for v in manifest['versions'] if v['id']=='1.21.11');meta=json.loads(urllib.request.urlopen(entry['url']).read())
(T/'minecraft.json').write_text(json.dumps(meta))
original=T/'minecraft-original.jar'
if not original.exists():
 import shutil
 cached_game=Path('/workspace/duckclientz/tools/minecraft-1.21.11-client')
 if cached_game.exists():shutil.copyfile(cached_game,original)
 else:get(meta['downloads']['client']['url'],original)
get('https://maven.fabricmc.net/net/fabricmc/intermediary/1.21.11/intermediary-1.21.11-v2.jar',T/'intermediary.jar')
with zipfile.ZipFile(T/'intermediary.jar') as z:(T/'intermediary.tiny').write_bytes(z.read('mappings/mappings.tiny'))
get('https://maven.fabricmc.net/net/fabricmc/sponge-mixin/0.15.5+mixin.0.8.7/sponge-mixin-0.15.5+mixin.0.8.7.jar',T/'mixin.jar')
get('https://maven.fabricmc.net/net/fabricmc/fabric-loader/0.16.10/fabric-loader-0.16.10.jar',T/'fabric-loader.jar')
for url,name in [('https://repo.maven.apache.org/maven2/com/google/code/findbugs/jsr305/3.0.2/jsr305-3.0.2.jar','jsr305.jar'),('https://repo.maven.apache.org/maven2/org/jetbrains/annotations/24.1.0/annotations-24.1.0.jar','jetbrains.jar')]:get(url,T/'libraries/annotations'/name)
def lib(e):
 d=e.get('downloads',{}).get('artifact')
 if d:return get(d['url'],T/'libraries'/d['path'])
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as ex:paths=[p for p in ex.map(lib,meta['libraries']) if p]
api=get('https://maven.fabricmc.net/net/fabricmc/fabric-api/fabric-api/0.141.3+1.21.11/fabric-api-0.141.3+1.21.11.jar',T/'fabric-api.jar')
with zipfile.ZipFile(api) as z:
 for n in z.namelist():
  if n.startswith('META-INF/jars/') and n.endswith('.jar'):(T/n.rsplit('/',1)[1]).write_bytes(z.read(n))
if not (T/'minecraft-intermediary.jar').exists():
 subprocess.run(['java','-Xmx1500m','-jar',str(T/'remapper.jar'),str(T/'minecraft-original.jar'),str(T/'minecraft-intermediary.jar'),str(T/'intermediary.tiny'),'official','intermediary'],check=True)
if not (T/'minecraft-named.jar').exists():
 subprocess.run(['java','-Xmx1500m','-jar',str(T/'remapper.jar'),str(T/'minecraft-intermediary.jar'),str(T/'minecraft-named.jar'),str(T/'yarn.tiny'),'intermediary','named','--fixPackageAccess'],check=True)
# Remap the small Fabric modules actually used by the trainer to the compile namespace.
for p in T.glob('fabric-*.jar'):
 if p.name=='fabric-api.jar':continue
 if not any(p.name.startswith(n) for n in ['fabric-api-base-','fabric-lifecycle-events-v1-','fabric-command-api-v2-','fabric-events-interaction-v0-','fabric-entity-events-v1-','fabric-networking-api-v1-','fabric-rendering-v1-','fabric-screen-api-v1-']):continue
 out=T/'named'/p.name;out.parent.mkdir(exist_ok=True)
 if not out.exists():subprocess.run(['java','-jar',str(T/'remapper.jar'),str(p),str(out),str(T/'yarn.tiny'),'intermediary','named',str(T/'minecraft-named.jar')],check=True)
print('READY named Minecraft1.21.11, real libraries and Fabric modules')

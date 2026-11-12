from pathlib import Path
import subprocess,os,zipfile,json,hashlib
R=Path(__file__).resolve().parent;BASE=Path('/workspace/duckclientz-246/dist');T=Path('/workspace/duckclientz/tools');B=R/'build';B.mkdir(exist_ok=True)
ASM=os.pathsep.join(str(T/n) for n in ['asm-9.7.1.jar','asm-tree-9.7.1.jar','asm-commons-9.7.1.jar','asm-util-9.7.1.jar','asm-analysis-9.7.1.jar'])
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-cp',ASM,'-d',str(B/'classes'),str(R/'src/Revision247Patch.java')],check=True)
common=B/'common';common.mkdir(exist_ok=True)
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-source','17','-target','17','-d',str(common),'-cp',os.pathsep.join(['/workspace/duckbox-trainer-1.20.1/tools/minecraft-intermediary.jar',*map(str,Path('/workspace/duckbox-trainer/tools/libraries').rglob('*.jar'))]),*map(str,(R/'src/com').rglob('*.java'))],check=True)
report={}
for mc in ['1.20.1','1.21.1','1.21.4','1.21.11']:
 source=BASE/f'DuckClientZ-{mc}-1.5.28-beta.2.46.jar';patch=B/mc/'patch';patch.mkdir(parents=True,exist_ok=True)
 subprocess.run(['java','-cp',str(B/'classes')+os.pathsep+ASM,'Revision247Patch',str(source),str(patch),mc,str(common)],check=True)
 with zipfile.ZipFile(source) as z:data={n:z.read(n) for n in z.namelist()}
 modified={p.relative_to(patch).as_posix():p.read_bytes() for p in patch.rglob('*.class')}
 meta=json.loads(data['fabric.mod.json']);meta['version']='1.5.28-beta.2.47';modified['fabric.mod.json']=(json.dumps(meta,indent=2,ensure_ascii=False)+'\n').encode()
 dest=R/'dist'/f'DuckClientZ-{mc}-1.5.28-beta.2.47.jar'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
  for n,v in (data|modified).items():z.writestr(n,v)
 with zipfile.ZipFile(dest) as z:
  assert z.testzip() is None
  changed=[n for n in data if data[n]!=z.read(n)];added=[n for n in z.namelist() if n not in data]
  assert set(changed)=={'fabric.mod.json','com/duckswords/render/TargetTop242.class','com/duckswords/modules/TargetHighlight.class'}
  assert set(added)=={'com/duckswords/render/BlockShadow247.class','com/duckswords/render/TargetOverlay247.class','com/duckswords/render/TargetRawLine247.class'}
  for n in ['com/duckswords/render/TargetTopGeometry242.class','com/duckswords/modules/CpsDisplay.class','com/duckswords/input/AdaptiveCps243.class','com/duckswords/input/SmoothCps244.class','com/duckswords/input/AttackBindings246.class','com/duckswords/render/WebLineLayers.class','com/duckswords/update/ClientUpdater229.class','com/duckswords/connect/ServiceRoute241.class']:
   assert data[n]==z.read(n),n
  configs=[n for n in data if n.endswith('mixins.json')]
  assert any(b'MixinWebLines218' in data[n] for n in configs)
 report[mc]={'file':dest.name,'version':meta['version'],'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'size':dest.stat().st_size,'base':source.name,'changed':changed,'added':added}
 print('Preservation and packaging PASS',mc)
(R/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')

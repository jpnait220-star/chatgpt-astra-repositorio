from pathlib import Path
import subprocess,os,zipfile,json,hashlib
R=Path(__file__).resolve().parent;BASE=Path('/workspace/duckclientz-247/dist');T=Path('/workspace/duckclientz/tools');B=R/'build';B.mkdir(exist_ok=True)
ASM=os.pathsep.join(str(T/n) for n in ['asm-9.7.1.jar','asm-tree-9.7.1.jar','asm-util-9.7.1.jar','asm-analysis-9.7.1.jar'])
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-cp',ASM,'-d',str(B/'classes'),str(R/'src/Revision248Patch.java')],check=True)
report={}
for mc in ['1.20.1','1.21.1','1.21.4','1.21.11']:
 source=BASE/f'DuckClientZ-{mc}-1.5.28-beta.2.47.jar';patch=B/mc/'patch';patch.mkdir(parents=True,exist_ok=True)
 subprocess.run(['java','-cp',str(B/'classes')+os.pathsep+ASM,'Revision248Patch',str(source),str(patch),mc],check=True)
 with zipfile.ZipFile(source) as z:data={n:z.read(n) for n in z.namelist()}
 removed={'com/duckswords/modules/FireworkKey.class','assets/duckswords/textures/gui/icons/fireworkkey.png',*[n for n in data if n.startswith('com/duckswords/input/Firework') and n.endswith('.class')]}
 modified={p.relative_to(patch).as_posix():p.read_bytes() for p in patch.rglob('*.class')}
 if mc=='1.21.1':
  removed.add('com/duckswords/mixin/MixinElytraGlidingFix1211.class')
  config=json.loads(data['duckswords.mixins.json']);config['client'].remove('MixinElytraGlidingFix1211');modified['duckswords.mixins.json']=(json.dumps(config,indent=2)+'\n').encode()
  def clean(value):
   if isinstance(value,dict):return {k:clean(v) for k,v in value.items() if 'MixinElytraGlidingFix1211' not in k}
   if isinstance(value,list):return [clean(v) for v in value]
   return value
  modified['duckswords.refmap.json']=(json.dumps(clean(json.loads(data['duckswords.refmap.json'])),indent=2)+'\n').encode()
 meta=json.loads(data['fabric.mod.json']);meta['version']='1.5.28-beta.2.48';modified['fabric.mod.json']=(json.dumps(meta,indent=2,ensure_ascii=False)+'\n').encode()
 dest=R/'dist'/f'DuckClientZ-{mc}-1.5.28-beta.2.48.jar'
 with zipfile.ZipFile(dest,'w',zipfile.ZIP_DEFLATED) as z:
  for n,v in (data|modified).items():
   if n not in removed:z.writestr(n,v)
 with zipfile.ZipFile(dest) as z:
  assert z.testzip() is None
  changed=[n for n in data if n not in removed and data[n]!=z.read(n)];added=[n for n in z.namelist() if n not in data]
  expected={'fabric.mod.json','com/duckswords/module/ModuleManager.class','com/duckswords/input/AutoClickerRuntime.class','com/duckswords/modules/ElytraFeature.class'}
  expected.update({'duckswords.mixins.json','duckswords.refmap.json'} if mc=='1.21.1' else {'com/duckswords/mixin/MixinLivingEntity.class'})
  assert set(changed)==expected;assert not added;assert set(data)-set(z.namelist())==removed
  for n in z.namelist():
   if n.endswith('.class'):assert all(token not in z.read(n) for token in [b'FireworkKey',b'FireworkTiming',b'FireworkUse',b'bugFix']),n
  for n in ['com/duckswords/render/TargetTop242.class','com/duckswords/render/TargetOverlay247.class','com/duckswords/render/BlockShadow247.class','com/duckswords/render/TargetRawLine247.class','com/duckswords/modules/TargetHighlight.class','com/duckswords/modules/CpsDisplay.class','com/duckswords/input/AdaptiveCps243.class','com/duckswords/input/SmoothCps244.class','com/duckswords/input/AttackBindings246.class','com/duckswords/update/ClientUpdater229.class','com/duckswords/connect/ServiceRoute241.class']:assert data[n]==z.read(n),n
 report[mc]={'file':dest.name,'version':meta['version'],'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'size':dest.stat().st_size,'base':source.name,'changed':changed,'removed':sorted(removed),'added':added}
 print('PASS exact removal, no dangling feature references, preservation of all other entries',mc)
(R/'build-report.json').write_text(json.dumps(report,indent=2)+'\n')

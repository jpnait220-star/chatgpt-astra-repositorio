from pathlib import Path
import subprocess,os,zipfile,json
R=Path(__file__).resolve().parent;B=R/'build';T=Path('/workspace/duckclientz/tools')
asm=os.pathsep.join(str(T/n) for n in ['asm-9.7.1.jar','asm-tree-9.7.1.jar','asm-util-9.7.1.jar','asm-analysis-9.7.1.jar'])
def run(a):subprocess.run(a,check=True)
javac=['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none']
run(javac+['-cp',asm,'-d',str(B/'checks'),str(R/'tests/Removal248Check.java'),str(R/'tests/NativeLoadCheck.java')])
for mc in ['1.20.1','1.21.1','1.21.4','1.21.11']:
 jar=R/'dist'/f'DuckClientZ-{mc}-1.5.28-beta.2.48.jar';before=Path('/workspace/duckclientz-247/dist')/f'DuckClientZ-{mc}-1.5.28-beta.2.47.jar'
 run(['java','-cp',str(B/'checks')+os.pathsep+asm,'Removal248Check',str(before),str(jar),mc])
 with zipfile.ZipFile(jar) as z:
  meta=json.loads(z.read('fabric.mod.json'))
  for config in meta['mixins']:
   spec=json.loads(z.read(config if isinstance(config,str) else config['config']))
   for part in ['mixins','client','server']:
    for mixin in spec.get(part,[]):assert (spec['package']+'.'+mixin).replace('.','/')+'.class' in z.namelist(),(mc,mixin)
 print('PASS all active mixin entries resolve to packaged classes',mc,flush=True)
 tools=Path('/workspace')/('duckbox-trainer' if mc=='1.21.4' else 'duckbox-trainer-'+mc)/'tools'
 cp=[B/'checks',jar,tools/'minecraft-intermediary.jar',tools/'fabric-loader.jar',tools/'mixin.jar',*tools.glob('fabric-*.jar'),*tools.glob('libraries/**/*.jar')]
 changed=['com.duckswords.module.ModuleManager','com.duckswords.input.AutoClickerRuntime','com.duckswords.modules.ElytraFeature']
 if mc!='1.21.1':changed.append('com.duckswords.mixin.MixinLivingEntity')
 run(['java','-Xverify:all','-cp',os.pathsep.join(map(str,cp)),'NativeLoadCheck',*changed])
 out=B/mc/'runtime';out.mkdir(exist_ok=True)
 run(javac+['-cp',os.pathsep.join(map(str,cp)),'-d',str(out),*map(str,(R/'tests/stubs').rglob('*.java')),str(R/'tests/Elytra248Test.java')])
 run(['java','-Xverify:all','-cp',os.pathsep.join(map(str,[out,*cp])),'Elytra248Test',mc])

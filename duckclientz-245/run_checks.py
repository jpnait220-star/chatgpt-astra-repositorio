from pathlib import Path
import subprocess,os,zipfile
R=Path(__file__).resolve().parent;B=R/'build';T=Path('/workspace/duckclientz/tools')
asm=os.pathsep.join(str(T/n) for n in ['asm-9.7.1.jar','asm-tree-9.7.1.jar','asm-util-9.7.1.jar','asm-analysis-9.7.1.jar'])
def run(a):subprocess.run(a,check=True)
javac=['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none']
run(javac+['-cp',asm,'-d',str(B/'checks'),str(R/'tests/ExtractCps245.java'),str(R/'tests/TargetDepth245Check.java')])
run(javac+['-cp',str(B/'common'),'-d',str(B/'checks'),str(R/'tests/Cps245Test.java')])
run(['java','-cp',str(B/'checks')+os.pathsep+str(B/'common'),'com.duckswords.input.Cps245Test'])
for mc in ['1.20.1','1.21.1','1.21.4','1.21.11']:
 jar=R/'dist'/f'DuckClientZ-{mc}-1.5.28-beta.2.45.jar';out=B/mc/'runtime';out.mkdir(exist_ok=True)
 run(['java','-cp',str(B/'checks')+os.pathsep+asm,'ExtractCps245',str(jar),str(out)])
 run(javac+['-cp',str(out),'-d',str(out),*map(str,(R/'tests/cps-stubs').rglob('*.java')),str(R/'tests/Cps243Clock.java'),str(R/'tests/Cps245IntegrationTest.java')])
 run(['java','-Xverify:all','-cp',str(out),'Cps245IntegrationTest',mc])
 game=Path('/workspace')/('duckbox-trainer' if mc=='1.21.4' else 'duckbox-trainer-'+mc)/'tools/minecraft-intermediary.jar'
 run(['java','-cp',str(B/'checks')+os.pathsep+asm,'TargetDepth245Check',str(jar),mc,str(game)])
 target=B/mc/'target';target.mkdir(exist_ok=True)
 with zipfile.ZipFile(jar) as z:
  p=target/'com/duckswords/render/TargetTop242.class';p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(z.read('com/duckswords/render/TargetTop242.class'))
 run(javac+['-cp',str(target)+os.pathsep+str(jar),'-d',str(target),*map(str,(R/'tests/target-stubs').rglob('*.java')),str(R/'tests/TargetDepth245Test.java')])
 run(['java','-Xverify:all','-cp',str(target)+os.pathsep+str(jar),'TargetDepth245Test',mc])

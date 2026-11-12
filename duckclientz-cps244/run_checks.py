from pathlib import Path
import os,subprocess
R=Path(__file__).resolve().parent;B=R/'build';T=Path('/workspace/duckclientz/tools')
asm=os.pathsep.join(str(T/n) for n in ['asm-9.7.1.jar','asm-tree-9.7.1.jar','asm-util-9.7.1.jar','asm-analysis-9.7.1.jar'])
def run(a):subprocess.run(a,check=True)
javac=['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none']
run(javac+['-cp',asm,'-d',str(B/'checks'),str(R/'tests/ExtractCps244.java')])
run(javac+['-cp',str(B/'common'),'-d',str(B/'checks'),str(R/'tests/SmoothCps244Test.java')])
run(['java','-cp',str(B/'checks')+os.pathsep+str(B/'common'),'com.duckswords.input.SmoothCps244Test'])
for mc in ['1.20.1','1.21.1','1.21.4','1.21.11']:
 out=B/mc/'runtime';out.mkdir(exist_ok=True);jar=R/'dist'/f'DuckClientZ-{mc}-1.5.28-beta.2.44.jar'
 run(['java','-cp',str(B/'checks')+os.pathsep+asm,'ExtractCps244',str(jar),str(out)])
 run(javac+['-cp',str(out),'-d',str(out),*map(str,(R/'tests/stubs').rglob('*.java')),str(R/'tests/Cps243Clock.java'),str(R/'tests/Cps244IntegrationTest.java')])
 run(['java','-Xverify:all','-cp',str(out),'Cps244IntegrationTest',mc])

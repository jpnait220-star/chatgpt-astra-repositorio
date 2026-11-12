from pathlib import Path
import subprocess,os,shutil
R=Path(__file__).resolve().parent;B=R/'build';T=Path('/workspace/duckclientz/tools')
asm=os.pathsep.join(str(T/n) for n in ['asm-9.7.1.jar','asm-tree-9.7.1.jar','asm-util-9.7.1.jar','asm-analysis-9.7.1.jar'])
def run(a):subprocess.run(a,check=True)
javac=['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none']
run(javac+['-cp',asm,'-d',str(B/'checks'),str(R/'tests/ExtractCps246.java')])
run(javac+['-cp',str(B/'common'),'-d',str(B/'checks'),str(R/'tests/Cps246Test.java')])
run(['java','-cp',str(B/'checks')+os.pathsep+str(B/'common'),'com.duckswords.input.Cps246Test'])
for mc in ['1.20.1','1.21.1','1.21.4','1.21.11']:
 game=Path('/workspace')/('duckbox-trainer' if mc=='1.21.4' else 'duckbox-trainer-'+mc)/'tools/minecraft-intermediary.jar'
 native=subprocess.check_output(['java','-m','jdk.jdeps/com.sun.tools.javap.Main','-p','-classpath',str(game),'net.minecraft.class_310','net.minecraft.class_315','net.minecraft.class_304','net.minecraft.class_3675$class_306'],text=True)
 for signature in ['net.minecraft.class_315 field_1690;','net.minecraft.class_310 method_1551();','net.minecraft.class_304 field_1886;','java.lang.String method_1428();','java.lang.String method_1441();']:assert signature in native,(mc,signature)
 jar=R/'dist'/f'DuckClientZ-{mc}-1.5.28-beta.2.46.jar';out=B/mc/'runtime';out.mkdir(exist_ok=True)
 run(['java','-cp',str(B/'checks')+os.pathsep+asm,'ExtractCps246',str(jar),str(out)])
 run(javac+['-cp',str(out),'-d',str(out),*map(str,(R/'tests/stubs').rglob('*.java')),str(R/'tests/Cps243Clock.java'),str(R/'tests/Cps246IntegrationTest.java'),str(R/'tests/VanillaBindings246Test.java')])
 run(['java','-Xverify:all','-cp',str(out),'Cps246IntegrationTest',mc])
 run(['java','-Xverify:all','-cp',str(out),'Cps246IntegrationTest',mc,'vanilla'])
 vanilla=B/mc/'without-optional';shutil.rmtree(vanilla,ignore_errors=True);shutil.copytree(out,vanilla,ignore=shutil.ignore_patterns('us','Cps246IntegrationTest.class'))
 run(['java','-Xverify:all','-cp',str(vanilla),'VanillaBindings246Test'])

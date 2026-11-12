from pathlib import Path
import subprocess,os
R=Path(__file__).resolve().parent;B=R/'build';T=Path('/workspace/duckclientz/tools')
asm=os.pathsep.join(str(T/n) for n in ['asm-9.7.1.jar','asm-tree-9.7.1.jar','asm-util-9.7.1.jar','asm-analysis-9.7.1.jar'])
def run(a):subprocess.run(a,check=True)
javac=['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none']
run(javac+['-cp',asm,'-d',str(B/'checks'),str(R/'tests/ExtractTarget247.java')])
run(javac+['-cp',str(B/'common'),'-d',str(B/'checks'),str(R/'tests/BlockShadow247Test.java')])
run(['java','-cp',str(B/'checks')+os.pathsep+str(B/'common'),'BlockShadow247Test'])
for mc in ['1.20.1','1.21.1','1.21.4','1.21.11']:
 jar=R/'dist'/f'DuckClientZ-{mc}-1.5.28-beta.2.47.jar';out=B/mc/'runtime';out.mkdir(exist_ok=True)
 run(['java','-cp',str(B/'checks')+os.pathsep+asm,'ExtractTarget247',str(jar),str(out)])
 run(javac+['-cp',str(out)+os.pathsep+str(jar),'-d',str(out),*map(str,(R/'tests/stubs').rglob('*.java')),str(R/'tests/Capture247.java'),str(R/'tests/BlockShadow247Test.java'),str(R/'tests/Target247Test.java')])
 run(['java','-Xverify:all','-cp',str(out)+os.pathsep+str(jar),'Target247Test',mc])
 game=Path('/workspace')/('duckbox-trainer' if mc=='1.21.4' else 'duckbox-trainer-'+mc)/'tools/minecraft-intermediary.jar'
 native=subprocess.check_output(['java','-m','jdk.jdeps/com.sun.tools.javap.Main','-p','-classpath',str(game),'net.minecraft.class_3726','net.minecraft.class_4970$class_4971','net.minecraft.class_265','net.minecraft.class_638'],text=True)
 for signature in ['net.minecraft.class_3726 method_16194();','net.minecraft.class_265 method_26202(net.minecraft.class_1922, net.minecraft.class_2338, net.minecraft.class_3726);','java.util.List<net.minecraft.class_238> method_1090();']:
  assert signature in native,(mc,signature)
 print('PASS native shape API',mc,flush=True)

run(javac+['-d',str(B/'native-check'),str(R/'tests/NativeLoadCheck.java')])
for mc in ['1.20.1','1.21.1','1.21.4','1.21.11']:
 tools=Path('/workspace')/('duckbox-trainer' if mc=='1.21.4' else 'duckbox-trainer-'+mc)/'tools'
 cp=[B/'native-check',R/'dist'/f'DuckClientZ-{mc}-1.5.28-beta.2.47.jar',tools/'minecraft-intermediary.jar',tools/'fabric-loader.jar',tools/'mixin.jar',*tools.glob('fabric-*.jar'),*tools.glob('libraries/**/*.jar')]
 run(['java','-Xverify:all','-cp',os.pathsep.join(map(str,cp)),'NativeLoadCheck','com.duckswords.render.TargetTop242','com.duckswords.render.TargetOverlay247','com.duckswords.render.TargetRawLine247','com.duckswords.render.BlockShadow247','com.duckswords.modules.TargetHighlight'])

from pathlib import Path
import os,subprocess
B=Path(__file__).parent;T=B/'tools';out=B/'build/tests';out.mkdir(exist_ok=True)
cp=os.pathsep.join(map(str,[out,B/'build/named.jar',T/'minecraft-named.jar',T/'fabric-loader.jar',*T.glob('named/*.jar'),*T.glob('libraries/**/*.jar'),T/'mixin.jar']))
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-cp',cp,'-d',str(out),str(B/'tests/CoreTest.java'),str(B/'tests/CosmeticMeshTest.java')],check=True)
from zipfile import ZipFile
with ZipFile(out/'test-named.jar','w') as z:
 for p in out.glob('*.class'):z.write(p,p.name)
(out/'test-runtime.jar').unlink(missing_ok=True)
subprocess.run(['java','-jar',str(T/'remapper.jar'),str(out/'test-named.jar'),str(out/'test-runtime.jar'),str(T/'yarn.tiny'),'named','intermediary',str(T/'minecraft-named.jar'),str(B/'build/named.jar')],check=True)
runtime=os.pathsep.join(map(str,[out/'test-runtime.jar',B/'dist/DuckBoxTrainer-1.21.4-0.3.3-alpha.jar',T/'minecraft-intermediary.jar',T/'fabric-loader.jar',*T.glob('fabric-*.jar'),*T.glob('libraries/**/*.jar'),T/'mixin.jar']))
subprocess.run(['java','-Xverify:all','-cp',runtime,'CoreTest',str(B/'dist/DuckBoxTreino/level.dat')],cwd=B,check=True)
subprocess.run(['java','-Xverify:all','-cp',runtime,'CosmeticMeshTest'],cwd=B,check=True)

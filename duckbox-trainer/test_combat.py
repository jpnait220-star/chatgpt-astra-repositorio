from pathlib import Path
from zipfile import ZipFile
import os,subprocess,shutil
B=Path(__file__).parent;T=B/'tools';out=B/'build/combat-tests';out.mkdir(exist_ok=True)
cp=os.pathsep.join(map(str,[out,B/'build/named.jar',T/'minecraft-named.jar',T/'fabric-loader.jar',*T.glob('named/*.jar'),*T.glob('libraries/**/*.jar'),T/'mixin.jar']))
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-cp',cp,'-d',str(out),str(B/'tests/NativeModBootstrap.java'),str(B/'tests/CombatServerTest.java')],check=True)
with ZipFile(out/'named.jar','w') as z:
 for p in out.glob('*.class'):z.write(p,p.name)
(out/'runtime.jar').unlink(missing_ok=True)
subprocess.run(['java','-jar',str(T/'remapper.jar'),str(out/'named.jar'),str(out/'runtime.jar'),str(T/'yarn.tiny'),'named','intermediary',str(T/'minecraft-named.jar'),str(B/'build/named.jar')],check=True)
runtime=os.pathsep.join(map(str,[out/'runtime.jar',B/'dist/DuckBoxTrainer-1.21.4-0.3.29-alpha.jar',T/'minecraft-intermediary.jar',T/'fabric-loader.jar',*T.glob('fabric-*.jar'),*T.glob('libraries/**/*.jar'),T/'mixin.jar']))
world=out/'worlds';shutil.rmtree(world,ignore_errors=True)
subprocess.run(['java','-Xmx1800m','-Xverify:all','-cp',runtime,'CombatServerTest',str(world)],cwd=out,check=True,timeout=100)

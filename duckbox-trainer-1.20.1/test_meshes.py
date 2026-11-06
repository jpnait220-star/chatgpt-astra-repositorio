from pathlib import Path
from zipfile import ZipFile
import os,subprocess,shutil
B=Path(__file__).parent;T=B/'tools';out=B/'build/mesh-tests';out.mkdir(exist_ok=True)
cp=os.pathsep.join(map(str,[out,B/'build/named.jar',T/'minecraft-named.jar',T/'fabric-loader.jar',*T.glob('named/*.jar'),*T.glob('libraries/**/*.jar'),T/'mixin.jar']))
subprocess.run(['java','-m','jdk.compiler/com.sun.tools.javac.Main','-proc:none','-cp',cp,'-d',str(out),str(B/'tests/NativeModBootstrap.java'),str(B/'tests/ClientMeshSmoke.java')],check=True)
with ZipFile(out/'named.jar','w') as z:
 for p in out.glob('*.class'):z.write(p,p.name)
(out/'runtime.jar').unlink(missing_ok=True)
subprocess.run(['java','-jar',str(T/'remapper.jar'),str(out/'named.jar'),str(out/'runtime.jar'),str(T/'yarn.tiny'),'named','intermediary',str(T/'minecraft-named.jar'),str(B/'build/named.jar')],check=True)
runtime=os.pathsep.join(map(str,[out/'runtime.jar',B/'dist/DuckBoxTrainer-1.20.1-0.3.31-alpha.jar',T/'minecraft-intermediary.jar',T/'fabric-loader.jar',*T.glob('fabric-*.jar'),*T.glob('libraries/**/*.jar'),T/'mixin.jar']))
subprocess.run(['java','-Xverify:all','-cp',runtime,'ClientMeshSmoke'],cwd=out,check=True,timeout=90)
